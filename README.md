---
title: Gemini API Chatbot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.26.0
app_file: main.py
hardware: cpu-basic
pinned: false
---

# Gemini API Chatbot

This Gradio chatbot uses Gemini through the Google API.

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

Open http://localhost:7860 to chat with Gemini.

The app requires a valid Google API key and an internet connection. It does not download or run a local language model.

The direct dependencies are Gradio (UI), python-dotenv (configuration), and google-genai (Gemini API). A fresh virtual environment avoids retaining packages from the old dependency list.

On Hugging Face Spaces, configure `GOOGLE_API_KEY` as a Space secret for Gemini.

## Team notifications

The `Notify Team` GitHub Actions workflow sends test and deployment results to Slack or Discord after the tracked workflows finish. Add a repository secret named `TEAM_WEBHOOK_URL` containing either a Slack incoming webhook URL or a Discord webhook URL. The webhook is never stored in the repository.

## Performance benchmark

Run `Benchmark Gemini API` manually from GitHub Actions to measure Gemini response time and response length.
