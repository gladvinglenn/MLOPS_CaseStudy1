import json
import os
import time
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main

PROMPTS = [
    {
        "label": "capital",
        "prompt": "What is the capital of France?",
        "expected": "Paris",
    },
    {
        "label": "math",
        "prompt": "What is 17 * 23?",
        "expected": "391",
    },
    {
        "label": "author",
        "prompt": "Who wrote Pride and Prejudice?",
        "expected": "Jane Austen",
    },
    {
        "label": "planet",
        "prompt": "Which planet is known as the Red Planet?",
        "expected": "Mars",
    },
    {
        "label": "moon",
        "prompt": "What year did the first moon landing happen?",
        "expected": "1969",
    },
    {
        "label": "colors",
        "prompt": "Name the three primary colors.",
        "expected": "red blue yellow",
    },
    {
        "label": "photosynthesis",
        "prompt": "Explain photosynthesis in two sentences.",
        "expected": "plant",
    },
    {
        "label": "gravity",
        "prompt": "Give a brief explanation of how gravity works.",
        "expected": "mass",
    },
    {
        "label": "square_root",
        "prompt": "What is the square root of 144?",
        "expected": "12",
    },
    {
        "label": "prime",
        "prompt": "Is the number 9 prime?",
        "expected": "No",
    },
]


def normalize(text):
    return " ".join((text or "").lower().replace("\n", " ").split())


def looks_correct(answer, expected):
    if not answer:
        return False
    answer_norm = normalize(answer)
    expected_norm = normalize(expected)
    return expected_norm in answer_norm or answer_norm in expected_norm


def evaluate_local(prompt_data, runs=2):
    results = []
    for i in range(runs):
        start = time.perf_counter()
        answer = main.local_response(prompt_data["prompt"])
        elapsed = time.perf_counter() - start
        correct = looks_correct(answer, prompt_data["expected"])
        results.append({
            "run": i + 1,
            "seconds": round(elapsed, 3),
            "answer": answer[:700],
            "expected": prompt_data["expected"],
            "matches_expected": correct,
        })
    return results


def evaluate_gemini(prompt_data, runs=2):
    if not os.getenv("GOOGLE_API_KEY"):
        return {"status": "skipped", "reason": "GOOGLE_API_KEY not set"}
    results = []
    for i in range(runs):
        start = time.perf_counter()
        chunks = list(main.stream_response(prompt_data["prompt"], [], "Gemini Remote"))
        elapsed = time.perf_counter() - start
        answer = "".join(chunks) if chunks else ""
        correct = looks_correct(answer, prompt_data["expected"])
        results.append({
            "run": i + 1,
            "seconds": round(elapsed, 3),
            "answer": answer[:700],
            "expected": prompt_data["expected"],
            "matches_expected": correct,
        })
    return results


def main_eval():
    report = []
    for item in PROMPTS:
        row = {
            "label": item["label"],
            "prompt": item["prompt"],
            "expected": item["expected"],
            "local": evaluate_local(item, runs=2),
            "gemini": evaluate_gemini(item, runs=2),
        }
        report.append(row)
    print(json.dumps(report, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main_eval()
