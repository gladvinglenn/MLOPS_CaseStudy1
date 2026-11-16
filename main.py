import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors, types

import gradio as gr

load_dotenv()

client = None
remote_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")

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


def stream_response(message, history):
    global client

    messages = _conversation_messages(message, history)
    if message is None:
        return

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
            message = "Gemini is busy or your API quota has been reached. Try again shortly."
        elif error.code == 404:
            message = "The configured Gemini model is unavailable. Update GEMINI_MODEL in .env to a model available to your account and restart the app."
        else:
            message = f"Gemini could not complete the request (HTTP {error.code}). Check your API access and try again."
        yield f"{partial_message}\n\n{message}".strip()

demo_interface = gr.ChatInterface(
    stream_response,
    textbox=gr.Textbox(
        placeholder="Send to the LLM...",
        container=False,
        autoscroll=True,
        scale=7,
    ),
)

if __name__ == "__main__":
    demo_interface.launch(
        server_name="0.0.0.0",
        server_port=7860,
        debug=False
    )
