# Usage Examples

## Test with local server

1. Run: python local_test_server.py (in one terminal)
2. Run: python client/gradio_app.py (in another terminal)
3. Open browser to http://localhost:7860
4. Connect to http://localhost:8000 in the app
5. Test prompts and data updates

## Deploy to Modal

1. Run: modal setup (authenticate)
2. Run: python deploy_server.py
3. Copy the Modal URL from deployment output
4. Run: python client/gradio_app.py
5. Connect to your Modal URL in the app

## Example Prompts

- "Where am I currently located?"
- "What book am I reading?"
- "Show me my uploaded image"
- "Give me all my personal data"
- "What's my current status?"
