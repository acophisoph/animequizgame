import json
import random

# Load the anime_screenshots.json file that contains the title and screenshot URLs
with open('anime_screenshots.json', 'r') as f:
    anime_data = json.load(f)

def fetch_questions_from_json(num_questions=5):
    # Create a list of anime titles
    anime_titles = list(anime_data.keys())
    
    # Prepare questions for the quiz game
    formatted_questions = []
    
    for _ in range(num_questions):
        # Randomly pick an anime for the correct answer
        correct_anime = random.choice(anime_titles)
        correct_screenshot = random.choice(anime_data[correct_anime])

        # Pick 3 other wrong anime titles
        wrong_anime_titles = random.sample([title for title in anime_titles if title != correct_anime], 3)

        # Combine the correct and wrong titles and shuffle the choices
        choices = [correct_anime] + wrong_anime_titles
        random.shuffle(choices)

        # Format the question
        formatted_questions.append({
            'image': correct_screenshot,
            'choices': choices,
            'correct': correct_anime
        })

    return formatted_questions

# Fetch questions when this module is run
questions = fetch_questions_from_json()

if __name__ == "__main__":
    # This will print the questions if you run this file directly
    # It's useful for testing
    for i, q in enumerate(questions, 1):
        print(f"Question {i}:")
        print(f"Image: {q['image']}")
        print(f"Choices: {q['choices']}")
        print(f"Correct Answer: {q['correct']}")
        print()
