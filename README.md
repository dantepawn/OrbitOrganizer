# OrbitOrganizer
A serverless AI agent that organizes documents, manages tasks, and keeps track of calendar events

### Telegram Calendar Scheduler Agent 📅🤖
#### Description: AI-powered assistant that connects your Telegram bot 💬 to Google Calendar via Modal ☁️, so you can schedule events using natural language.
#### How it works:
You send messages like “Schedule a team meeting tomorrow at 3pm” or “Book gym sessions every Monday and Wednesday at 7am” to your Telegram bot.
The agent parses your request using GPT-5-mini and LangGraph 🕸️ to turn it into structured events.
It then calls the Google Calendar API to automatically create the corresponding events ✅.
#### Tech stack: Modal (serverless hosting), LangGraph (agent workflow), LangChain OpenAI, Google Calendar API, Telegram Bot API.

### 📄 DeepSeek OCR (Modal Function)

This module provides a serverless OCR pipeline powered by DeepSeek OCR, deployed on Modal. It retrieves an image from cloud storage (e.g., Google Drive), processes it using DeepSeek’s vision model, and returns clean, structured Markdown output.

#### Key Features

Fetches images directly from Drive via file ID or URL.

Runs OCR through a lightweight, scalable Modal function.

Outputs well-formatted Markdown, preserving layout, lists, tables, and headings.

Designed as the document-ingestion entry point for the personal AI secretary system.
