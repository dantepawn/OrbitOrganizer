# OrbitOrganizer
A serverless AI agent that organizes documents, manages tasks, and keeps track of calendar events

An AI-powered scheduling assistant that integrates Telegram with Google Calendar, deployed on [Modal](https://modal.com). Send natural language scheduling requests to your Telegram bot (e.g., "Schedule a team meeting tomorrow at 3pm" or "Book gym sessions every Monday and Wednesday at 7am"), and the agent will automatically parse your intent using GPT-4o-mini and create the corresponding events in your Google Calendar. Built with [LangGraph](https://github.com/langchain-ai/langgraph) for structured agent workflow orchestration, the app features a two-node graph: a planner node that converts natural language into structured event data, and a booking node that interfaces with the Google Calendar API. The serverless architecture on Modal ensures the bot is always available without managing infrastructure, while Modal Volumes securely store your Google OAuth credentials.


📄 DeepSeek OCR (Modal Function)

This module provides a serverless OCR pipeline powered by DeepSeek OCR, deployed on Modal. It retrieves an image from cloud storage (e.g., Google Drive), processes it using DeepSeek’s vision model, and returns clean, structured Markdown output.

Key Features

Fetches images directly from Drive via file ID or URL.

Runs OCR through a lightweight, scalable Modal function.

Outputs well-formatted Markdown, preserving layout, lists, tables, and headings.

Designed as the document-ingestion entry point for the personal AI secretary system.
