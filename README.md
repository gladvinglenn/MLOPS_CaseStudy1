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

This Gradio app supports Gemini Remote and Local Model (Ollama) providers.

On Hugging Face Spaces, configure `GOOGLE_API_KEY` as a Space secret for Gemini. A local `127.0.0.1` Ollama service is not available in a hosted Space; use an externally reachable Ollama endpoint by setting `OLLAMA_URL` and `OLLAMA_MODEL` as Space variables if needed.
