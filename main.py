import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import gradio as gr

load_dotenv()

client = None
remote_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
transformers_model = os.getenv(
    "TRANSFORMERS_MODEL", "Qwen/Qwen2.5-0.5B-Instruct"
)
available_providers = [
    "Gemini Remote",
    "Local Model (Transformers)",
]

system_message = "You act like a teacher"

def _conversation_messages(message, history):
    messages = [{"role": "system", "content": system_message}]

    for item in history or []:
        if isinstance(item, dict):
            role = item.get("role")
            content = item.get("content", "")
            if role in ("user", "assistant"):
                if isinstance(content, list):
                    content = "".join(
                        part.get("text", "")
                        for part in content
                        if isinstance(part, dict)
                    )
                messages.append({"role": role, "content": str(content)})
        else:
            human, ai = item
            messages.append({"role": "user", "content": str(human)})
            messages.append({"role": "assistant", "content": str(ai)})

    if message is not None:
        messages.append({"role": "user", "content": message})
    return messages


transformers_pipeline = None


def _stream_transformers(messages):
    global transformers_pipeline

    if transformers_pipeline is None:
        try:
            from transformers import pipeline

            transformers_pipeline = pipeline(
                "text-generation",
                model=transformers_model,
                device=-1,
            )
        except Exception as error:
            yield f"Transformers model could not be loaded: {error}"
            return

    prompt = transformers_pipeline.tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=True
    )
    result = transformers_pipeline(
        prompt,
        max_new_tokens=256,
        do_sample=True,
        temperature=0.7,
        return_full_text=False,
    )
    yield result[0]["generated_text"]


def local_response(prompt):
    """Return one response from the configured local Transformers model."""
    response = next(
        _stream_transformers(_conversation_messages(prompt, [])),
        "",
    )
    return response


def stream_response(message, history, selected_provider):
    global client

    messages = _conversation_messages(message, history)
    if message is None:
        return

    if selected_provider == "Local Model (Transformers)":
        yield from _stream_transformers(messages)
    elif selected_provider == "Gemini Remote":
        if client is None:
            if not os.getenv("GOOGLE_API_KEY"):
                yield "Gemini Remote requires the GOOGLE_API_KEY secret."
                return
            client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
        contents = [
            types.Content(
                role="model" if item["role"] == "assistant" else "user",
                parts=[types.Part.from_text(text=item["content"])],
            )
            for item in messages if item["role"] != "system"
        ]
        partial_message = ""
        try:
            for event in client.models.generate_content_stream(
                model=remote_model,
                contents=contents,
                config=types.GenerateContentConfig(
                    system_instruction=system_message,
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
                ),
            ):
                if event.text:
                    partial_message += event.text
                    yield partial_message
        except errors.APIError as error:
            if error.code in (429, 503):
                message = "Gemini is busy or your API quota has been reached. Try again shortly or select the local Qwen model."
            elif error.code == 404:
                message = "The configured Gemini model is unavailable. Update GEMINI_MODEL in .env to a model available to your account and restart the app."
            else:
                message = f"Gemini could not complete the request (HTTP {error.code}). Check your API access and try again."
            yield f"{partial_message}\n\n{message}".strip()
    else:
        raise ValueError(f"Unknown model provider: {selected_provider}")


model_selector = gr.Dropdown(
    choices=available_providers,
    value=available_providers[0],
    label="Model",
    info="Choose Gemini via API or Qwen running locally on CPU.",
)

demo_interface = gr.ChatInterface(
    stream_response,
    textbox=gr.Textbox(
        placeholder="Send to the LLM...",
        container=False,
        autoscroll=True,
        scale=7,
    ),
    additional_inputs=model_selector,
    additional_inputs_accordion="Model settings",
)

if __name__ == "__main__":
    demo_interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=False
    )
