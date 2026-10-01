---
title: Gemini and Qwen Chatbot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.26.0
app_file: main.py
hardware: cpu-basic
pinned: false
---

# Gemini and Qwen Chatbot

This Gradio chatbot has two options: Gemini Remote using your Google API key, and Local Model (Transformers) using `Qwen/Qwen2.5-0.5B-Instruct` on CPU.

## Run locally

Use Python 3.11 or 3.12. In PowerShell:

```powershell
python -m venv .venv-chatbot
.\.venv-chatbot\Scripts\python.exe -m pip install -r requirements.txt
```

If you do not already have a `.env` file, copy `.env.example` to `.env`. Set `GOOGLE_API_KEY` to your Gemini API key. `GEMINI_MODEL` defaults to `gemini-3.8-flash`; set it to a model available to your API account if needed.

```powershell
.\.venv-chatbot\Scripts\python.exe main.py
```

Open http://localhost:7860 and select a model under **Model settings**.

Qwen needs no API key or GPU. Its first response downloads the model weights from Hugging Face, so allow extra time and an internet connection. Later runs reuse the cached weights. Qwen loads only when selected. `TRANSFORMERS_MODEL` optionally overrides its model ID.

The five direct dependencies are Gradio (UI), python-dotenv (configuration), google-genai (Gemini API), Transformers and PyTorch (local Qwen). A fresh virtual environment avoids retaining packages from the old dependency list.

On Hugging Face Spaces, configure `GOOGLE_API_KEY` as a Space secret for Gemini. Qwen runs on the Space's CPU.

## Team notifications

The `Notify Team` GitHub Actions workflow sends test and deployment results to Slack or Discord after the tracked workflows finish. Add a repository secret named `TEAM_WEBHOOK_URL` containing either a Slack incoming webhook URL or a Discord webhook URL. The webhook is never stored in the repository.
