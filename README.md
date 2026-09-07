---
title: Gemini and Ollama Chatbot
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 6.26.0
app_file: main.py
hardware: cpu-basic
pinned: false
---

# Gemini and Ollama Chatbot

This Gradio app supports Gemini Remote, Local Model (Ollama), and Local Model (Transformers) providers.

On Hugging Face Spaces, configure `GOOGLE_API_KEY` as a Space secret for Gemini. The Transformers provider runs inside the Space using `TRANSFORMERS_MODEL`, which defaults to `Qwen/Qwen2.5-0.5B-Instruct`. A local `127.0.0.1` Ollama service is only available when running the app on your own machine.

## Team notifications

The `Notify Team` GitHub Actions workflow sends test and deployment results to Slack or Discord after the tracked workflows finish. Add a repository secret named `TEAM_WEBHOOK_URL` containing either a Slack incoming webhook URL or a Discord webhook URL. The webhook is never stored in the repository.
