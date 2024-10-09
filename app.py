import logging
from flask import Flask, render_template, session, request, redirect, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room
import threading
from questions import fetch_questions_from_json
from flask_basicauth import BasicAuth
import os

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
socketio = SocketIO(app)

app.config['BASIC_AUTH_USERNAME'] = os.getenv('BASIC_AUTH_USERNAME')
app.config['BASIC_AUTH_PASSWORD'] = os.getenv('BASIC_AUTH_PASSWORD')
app.config['BASIC_AUTH_FORCE'] = True  # Protect all routes

basic_auth = BasicAuth(app)

players = {}
game_state = {
    'started': False,
    'current_question': 0,
    'scores': {},
    'answers': {},
    'timer': 30,
    'num_rounds': 5,
    'questions': []
}

timer_thread = None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/join', methods=['POST'])
def join():
    username = request.form['username']
    if username in players:
        return "Username already taken", 400
    session['username'] = username
    players[username] = {'score': 0}
    return redirect(url_for('waiting_room'))

@app.route('/waiting_room')
def waiting_room():
    if 'username' not in session:
        return redirect(url_for('index'))
    return render_template('waiting_room.html', username=session['username'])

@app.route('/game')
def game():
    if 'username' not in session or not game_state['started']:
        return redirect(url_for('waiting_room'))
    return render_template('game.html')

@socketio.on('connect')
def handle_connect():
    username = session.get('username')
    if username:
        join_room('game')
        players[username] = {'score': 0, 'sid': request.sid}
        emit('update_players', {'players': list(players.keys())}, room='game')

@socketio.on('disconnect')
def handle_disconnect():
    username = session.get('username')
    if username:
        leave_room('game')
        del players[username]
        emit('update_players', {'players': list(players.keys())}, room='game')

@socketio.on('update_num_rounds')
def handle_update_num_rounds(data):
    num_rounds = data.get('num_rounds')
    if num_rounds and 1 <= num_rounds <= 20:
        game_state['num_rounds'] = num_rounds
        emit('update_num_rounds', {'num_rounds': num_rounds}, room='game')

@socketio.on('start_game')
def handle_start_game():
    global timer_thread
    logging.debug("Start game event received")
    if not game_state['started']:
        logging.debug("Starting new game")
        game_state['started'] = True
        game_state['current_question'] = 0
        game_state['scores'] = {player: 0 for player in players}
        game_state['answers'] = {}
        num_rounds = game_state.get('num_rounds', 5)
        game_state['questions'] = fetch_questions_from_json(num_questions=num_rounds)
        emit('game_started', room='game')
        logging.debug("Emitted game_started event")
        send_question()
        timer_thread = threading.Thread(target=countdown)
        timer_thread.start()
    else:
        logging.debug("Game already in progress")

def send_question():
    logging.debug(f"Sending question {game_state['current_question']}")
    if game_state['current_question'] < len(game_state['questions']):
        question = game_state['questions'][game_state['current_question']]
        question_data = question.copy()
        question_data['round_number'] = game_state['current_question'] + 1
        emit('new_question', question_data, room='game')
        logging.debug(f"Emitted new_question event with data: {question_data}")
        game_state['timer'] = 30  # Reset timer for each question
        game_state['answers'] = {}
        emit('timer_update', {'time': game_state['timer']}, room='game')  # Send initial timer value
    else:
        end_game()

def countdown():
    while game_state['started']:
        while game_state['timer'] > 0:
            socketio.sleep(1)  # Wait 1 second
            game_state['timer'] -= 1
            socketio.emit('timer_update', {'time': game_state['timer']}, room='game')  # Send countdown updates
        handle_question_end()

def handle_question_end():
    logging.debug("Question ended")
    # For players who haven't answered, mark their answer as incorrect
    unanswered_players = set(players.keys()) - set(game_state['answers'].keys())
    for username in unanswered_players:
        emit('answer_result', {
            'correct': False,
            'message': f"Time's up! The correct answer is {game_state['questions'][game_state['current_question']]['correct']}"
        }, room=players[username]['sid'])
    game_state['current_question'] += 1
    if game_state['current_question'] < len(game_state['questions']):
        socketio.sleep(3)  # Give players time to see their results
        send_question()  # Move to the next question
    else:
        end_game()  # If no more questions, end the game

@socketio.on('submit_answer')
def handle_submit_answer(data):
    username = session.get('username')
    if username and username not in game_state['answers']:
        game_state['answers'][username] = data['answer']
        if data['answer'] == game_state['questions'][game_state['current_question']]['correct']:
            game_state['scores'][username] += 1
            emit('answer_result', {'correct': True, 'message': 'Correct!'}, room=request.sid)
        else:
            emit('answer_result', {
                'correct': False,
                'message': f"Incorrect. The correct answer is {game_state['questions'][game_state['current_question']]['correct']}"
            }, room=request.sid)
    
    if len(game_state['answers']) == len(players):
        handle_question_end()  # If all players have answered, move to the next question

def end_game():
    global timer_thread
    logging.debug("Ending game")
    game_state['started'] = False
    sorted_scores = sorted(game_state['scores'].items(), key=lambda x: x[1], reverse=True)
    emit('game_ended', {'scores': dict(sorted_scores)}, room='game')
    if timer_thread:
        timer_thread.join()
        timer_thread = None

@socketio.on('play_again')
def handle_play_again():
    global game_state
    game_state = {
        'started': False,
        'current_question': 0,
        'scores': {},
        'answers': {},
        'timer': 30,
        'num_rounds': 5,
        'questions': []
    }
    emit('reset_game', room='game')

import eventlet
eventlet.monkey_patch()

socketio.run(app, host='0.0.0.0', port=5000, debug=True)

#if __name__ == '__main__':
#    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
