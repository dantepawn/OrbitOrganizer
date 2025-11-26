# OrbitOrganizer
A serverless AI agent that organizes documents, manages tasks, and keeps track of calendar events


📄 DeepSeek OCR (Modal Function)

This module provides a serverless OCR pipeline powered by DeepSeek OCR, deployed on Modal. It retrieves an image from cloud storage (e.g., Google Drive), processes it using DeepSeek’s vision model, and returns clean, structured Markdown output.

Key Features

Fetches images directly from Drive via file ID or URL.

Runs OCR through a lightweight, scalable Modal function.

Outputs well-formatted Markdown, preserving layout, lists, tables, and headings.

Designed as the document-ingestion entry point for the personal AI secretary system.
