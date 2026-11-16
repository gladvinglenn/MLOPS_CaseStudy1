import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import main


PROMPT = "Explain machine learning in one short paragraph."


def measure_gemini():
    started = time.perf_counter()
    chunks = list(main.stream_response(PROMPT, []))
    elapsed = time.perf_counter() - started
    response = chunks[-1] if chunks else ""
    if response.startswith("Gemini Remote requires"):
        raise RuntimeError(response)
    return {
        "provider": "Gemini Remote",
        "elapsed_seconds": round(elapsed, 3),
        "response_characters": len(response.strip()),
    }


def main_benchmark():
    if not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("GOOGLE_API_KEY is required to benchmark Gemini.")
    results = [measure_gemini()]
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main_benchmark()
