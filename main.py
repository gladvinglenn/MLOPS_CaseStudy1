import os
import json

import requests
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_anthropic import ChatAnthropic
from google import genai

import gradio as gr

load_dotenv()

if not os.getenv("GOOGLE_API_KEY"):
    raise RuntimeError("GOOGLE_API_KEY is missing. Add it to the .env file.")

client = genai.Client()
remote_model = "gemini-3.6-flash"
ollama_url = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "llama3.2")
available_providers = [
    "Gemini Remote",
    "Local Model (Ollama)",
]
remote_models = [
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]
#llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
#llm = ChatAnthropic(model="claude-3-5-sonnet-20241022", streaming=True)

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


def _stream_ollama(messages):
    try:
        response = requests.post(
            f"{ollama_url}/api/chat",
            json={"model": ollama_model, "messages": messages, "stream": True},
            stream=True,
            timeout=30,
        )
        response.raise_for_status()
    except requests.RequestException as error:
        yield (
            "Local Model is unavailable. Start Ollama and run "
            f"'ollama pull {ollama_model}'. Details: {error}"
        )
        return

    partial_message = ""
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        event = json.loads(line)
        partial_message += event.get("message", {}).get("content", "")
        if partial_message:
            yield partial_message


def stream_response(message, history, selected_provider):
    print(f"Input: {message}. Provider: {selected_provider}. History: {history}\n")

    messages = _conversation_messages(message, history)
    if message is None:
        return

    if selected_provider == "Local Model (Ollama)":
        yield from _stream_ollama(messages)
    else:
        prompt = "\n".join(
            f"{item['role'].title()}: {item['content']}" for item in messages
        )
        partial_message = ""
        for event in client.interactions.create(
            model=remote_model, input=prompt, stream=True
        ):
            if event.event_type == "step.delta":
                delta = getattr(event, "delta", None)
                if getattr(delta, "type", None) == "text":
                    partial_message += delta.text
                    yield partial_message


model_selector = gr.Dropdown(
    choices=available_providers,
    value=available_providers[0],
    label="Model",
    info="Choose Gemini Remote or a local Ollama model.",
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
    demo_interface.launch(debug=True)