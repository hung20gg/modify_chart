from PIL import Image
import os
from utils import open_image
from llm import Gemini, RotateGemini
import json


generate_questions_prompt = """
You are an AI assistant that generates requests based on the content of a chart.

You will be provided with an image of a chart and, and you are tasked to generate a command to modify the chart.
It can be either:
- Change the chart type (e.g., "Change the chart type to bar chart")
- Add a title (e.g., "Add a title 'Sales Data'")
- Modify the axis labels (e.g., "Change the x-axis label to 'Months'")
- Change the color scheme (e.g., "Change the color scheme to blue")
- Add new data
- Remove data series (e.g., "Remove the second data series")

You only need to generate the command, do not provide any explanations or additional text.
You command can contain multiple modifications.
Answer human-friendly and concise.

Return ONE command in the following format:

### Command:
your command here
"""

def get_question(text) -> str:
    """
    Extract questions from the given string.
    
    :param str: The input string containing questions.
    :return: A list of questions extracted from the string.
    """
    if '### Command:' not in text:
        return text.strip()
    question = text.split('### Command:')[1].strip()
    return question


def generate_question(llm, image_path: str) -> list[str]:
    """
    Generate questions based on the content of the image.
    """
    image = open_image(image_path)

    messages = [
        {
            'role': 'system',
            'content': generate_questions_prompt
        },
        {
            'role': 'user',
            'content': [
                {
                    'type': 'image',
                    'image': image
                },
                {
                    'type': 'text',
                    'text': "Please generate a command to modify the chart."
                }
            ]
        }
    ]

    response = llm(messages)
    question = get_question(response)

    result = {
        'question': question,
        'image_path': image_path
    }

    with open('chart_modification.jsonl', 'a') as f:
        f.write(json.dumps(result) + '\n')

def multithread_generate_questions(image_paths: list[str], llm, num_threads: int = 4):
    """
    Generate questions for multiple images using multithreading.
    """
    from concurrent.futures import ThreadPoolExecutor

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(generate_question, llm, image_path) for image_path in image_paths]
        for future in futures:
            future.result()  # Wait for all tasks to complete

def sequential_generate_questions(image_paths: list[str], llm):
    """
    Generate questions for multiple images sequentially.
    """
    for image_path in image_paths:
        generate_question(llm, image_path)

done_images = set()

if os.path.exists('chart_modification.jsonl'):
    with open('chart_modification.jsonl', 'r') as f:
        for line in f:
            data = json.loads(line)
            done_images.add(data['image_path'])


path = '/Volumes/External Drive/chart_data/images'

images = []
for root, dirs, files in os.walk(path):
    for file in files:
        if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            if os.path.join(root, file) in done_images:
                continue
            images.append(os.path.join(root, file))

llm = RotateGemini(model_name='gemini-2.0-flash', temperature=0.2, max_tokens=1000)

sequential_generate_questions(images, llm)
