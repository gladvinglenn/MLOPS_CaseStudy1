import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import main


def test_gemini_stream_preserves_history(monkeypatch):
    def generate_content_stream(**kwargs):
        assert kwargs["model"] == main.remote_model
        assert kwargs["config"].system_instruction == main.system_message
        assert [item.role for item in kwargs["contents"]] == ["user", "model", "user"]
        assert [item.parts[0].text for item in kwargs["contents"]] == [
            "Hi", "Hello", "Explain gravity",
        ]
        return iter([
            SimpleNamespace(text=None),
            SimpleNamespace(text="Gravity "),
            SimpleNamespace(text="attracts masses."),
        ])

    monkeypatch.setattr(main, "client", SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=generate_content_stream)
    ))
    result = list(main.stream_response(
        "Explain gravity",
        [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}],
    ))
    assert result == ["Gravity ", "Gravity attracts masses."]


def test_gemini_without_api_key(monkeypatch):
    monkeypatch.setattr(main, "client", None)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    assert list(main.stream_response("Hi", [])) == [
        "Gemini Remote requires the GOOGLE_API_KEY secret."
    ]


@pytest.mark.parametrize("code", [404, 429, 503])
def test_gemini_api_errors_are_readable(monkeypatch, code):
    def generate_content_stream(**kwargs):
        raise main.errors.APIError(code, {"error": {"message": "Test error"}})

    monkeypatch.setattr(main, "client", SimpleNamespace(
        models=SimpleNamespace(generate_content_stream=generate_content_stream)
    ))
    response = list(main.stream_response("Hi", []))
    assert len(response) == 1
    assert "GEMINI_MODEL" in response[0] if code == 404 else "Try again" in response[0]
