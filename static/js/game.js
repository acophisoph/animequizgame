// game.js

console.log('game.js loaded');

const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('error', (error) => {
    console.error('Socket error:', error);
});

socket.on('update_players', (data) => {
    console.log('Updating players:', data);
    const playersDiv = document.getElementById('players');
    if (playersDiv) {
        playersDiv.innerHTML = '<h2>Players in waiting room:</h2>';
        data.players.forEach(player => {
            playersDiv.innerHTML += `<p>${player}</p>`;
        });
    } else {
        console.warn('Players div not found');
    }
});

socket.on('update_num_rounds', (data) => {
    console.log('Updating number of rounds:', data.num_rounds);
    const numRoundsInput = document.getElementById('num-rounds');
    if (numRoundsInput) {
        numRoundsInput.value = data.num_rounds;
    } else {
        console.warn('Number of rounds input not found');
    }
});

socket.on('game_started', () => {
    console.log('Game started event received');
    // Update UI to show the game has started
    document.body.innerHTML = '<h1>Quiz Game</h1><div id="timer"></div><div id="round-number"></div><div id="question-container"></div><div id="result"></div>';
});

socket.on('new_question', (question) => {
    console.log('New question received:', question);
    const questionContainer = document.getElementById('question-container');
    if (questionContainer) {
        questionContainer.innerHTML = `
            <img id="question-image" src="${question.image}" alt="Question Image">
            <div id="choices"></div>
        `;
        const choicesDiv = document.getElementById('choices');
        question.choices.forEach(choice => {
            const button = document.createElement('button');
            button.textContent = choice;
            button.onclick = () => submitAnswer(choice);
            choicesDiv.appendChild(button);
        });
    } else {
        console.warn('Question container not found');
    }

    // Update round number
    const roundNumberDiv = document.getElementById('round-number');
    if (roundNumberDiv) {
        roundNumberDiv.textContent = `Round ${question.round_number}`;
    } else {
        console.warn('Round number div not found');
    }

    document.getElementById('result').textContent = '';
});

socket.on('timer_update', (data) => {
    console.log('Timer update:', data.time);
    const timerDiv = document.getElementById('timer');
    if (timerDiv) {
        timerDiv.textContent = `Time left: ${data.time}s`;
    } else {
        console.warn('Timer div not found');
    }
});

socket.on('answer_result', (data) => {
    console.log('Answer result:', data);
    const resultDiv = document.getElementById('result');
    if (resultDiv) {
        resultDiv.textContent = data.message;
    } else {
        console.warn('Result div not found');
    }
});

socket.on('game_ended', (data) => {
    console.log('Game ended:', data);
    document.body.innerHTML = '<h1>Game Over</h1><div id="scores"></div><button id="play-again">Play Again</button>';
    const scoresDiv = document.getElementById('scores');
    scoresDiv.innerHTML = '<h2>Final Scores:</h2>';
    Object.entries(data.scores).forEach(([player, score]) => {
        scoresDiv.innerHTML += `<p>${player}: ${score}</p>`;
    });
    document.getElementById('play-again').onclick = () => socket.emit('play_again');
});

socket.on('reset_game', () => {
    console.log('Game reset');
    window.location.href = '/waiting_room';
});

function submitAnswer(answer) {
    console.log('Submitting answer:', answer);
    socket.emit('submit_answer', { answer: answer });
    const buttons = document.querySelectorAll('#choices button');
    buttons.forEach(button => button.disabled = true);
}

document.addEventListener("DOMContentLoaded", () => {
    console.log("DOM fully loaded");
    
    const startButton = document.getElementById("start-game");
    if (startButton) {
        console.log("Start game button found");
        startButton.onclick = () => {
            console.log("Start game button clicked");
            socket.emit("start_game");
        };
    } else {
        console.log("Start game button not found");
    }

    const numRoundsInput = document.getElementById('num-rounds');
    if (numRoundsInput) {
        console.log("Number of rounds input found");
        numRoundsInput.addEventListener('input', () => {
            const numRounds = parseInt(numRoundsInput.value);
            socket.emit('update_num_rounds', { num_rounds: numRounds });
        });
    } else {
        console.log("Number of rounds input not found");
    }
});

// Debug function to check the current state
function debugState() {
    console.log('Current DOM state:');
    console.log('Body innerHTML:', document.body.innerHTML);
    console.log('Question container:', document.getElementById('question-container'));
    console.log('Choices:', document.getElementById('choices'));
    console.log('Timer:', document.getElementById('timer'));
    console.log('Result:', document.getElementById('result'));
}

// Call debugState every 5 seconds
setInterval(debugState, 5000);
