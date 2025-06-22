import json


def calculate_score(results, num_samples = 150):

    first_score = 0
    last_score = 0
    avg_iter = 0
    for result in results:
        # first_score += result['first_score']
        if result['score'] == 0:
            print(f"Warning: Result with score 0 found. Skipping this result.")

        last_score += result['score']
        avg_iter += result['number_iter']

    # Fail execution if the number of results is less than num_samples
    avg_iter += num_samples- len(results)

    first_score /= num_samples
    last_score /= num_samples
    avg_iter /= num_samples

    print(f" - First score: {first_score}")
    print(f" - Last score: {last_score}")
    print(f" - Avg iter: {avg_iter}")
    return {
        # 'first_score': first_score,
        'last_score': last_score,
        'avg_iter': avg_iter
    }


paths = [
    'mcts_gpt-4.1-mini_gpt-4.1-mini_html_eval.jsonl',
]

for path in paths:
    print(f"Evaluating {path}...")
    with open(path, 'r') as f:
        results = [json.loads(line) for line in f.readlines()]

    score = calculate_score(results, num_samples=len(results))
    print(f"Score for {path}: {score}")
    print()