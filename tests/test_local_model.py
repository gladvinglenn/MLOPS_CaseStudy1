import main


class FakeTokenizer:
    def apply_chat_template(self, messages, tokenize, add_generation_prompt):
        assert messages[-1]["content"] == "What is machine learning?"
        assert tokenize is False
        assert add_generation_prompt is True
        return "User: What is machine learning?\nAssistant:"


class FakePipeline:
    tokenizer = FakeTokenizer()

    def __call__(self, prompt, **kwargs):
        assert prompt.endswith("Assistant:")
        assert kwargs["return_full_text"] is False
        return [{"generated_text": "Machine learning is a way for computers to learn from data."}]


def test_local_model_response(monkeypatch):
    monkeypatch.setattr(main, "transformers_pipeline", FakePipeline())

    response = main.local_response("What is machine learning?")

    assert isinstance(response, str)
    assert len(response.strip()) > 0
