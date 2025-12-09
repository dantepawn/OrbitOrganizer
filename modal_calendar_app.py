# modal_calendar_app.py
#!/usr/bin/env python3
# modal_app.py

import os
import json
import requests
from typing import List, TypedDict
from datetime import datetime
from pathlib import Path

import modal

# ---------------------------------------------------------------------------
# Modal App + Image
# ---------------------------------------------------------------------------

app = modal.App("telegram-calendar-scheduler")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "fastapi",
        "requests",
        "python-dateutil",
        "pytz",
        "google-api-python-client",
        "google-auth",
        "google-auth-oauthlib",
        "langchain-openai",
        "langgraph",
    )
)

# Volume mount path
VOLUME_PATH = "/data"
TOKEN_PATH = Path(VOLUME_PATH) / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.events"]

# ---------------------------------------------------------------------------
# Google Calendar Service Loader
# ---------------------------------------------------------------------------

def get_calendar_service():
    """Load Google Calendar API using credentials stored in Modal volume."""
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    
    creds = None

    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(str(TOKEN_PATH), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            TOKEN_PATH.write_text(creds.to_json())
        else:
            raise RuntimeError(
                "OAuth token expired or missing. Upload fresh token.json to Modal volume."
            )

    service = build("calendar", "v3", credentials=creds, cache_discovery=False)
    return service

def create_calendar_event(summary: str, start_iso: str, end_iso: str, description: str = "") -> str:
    """Create an event in Google Calendar."""
    service = get_calendar_service()

    event_body = {
        "summary": summary,
        "start": {"dateTime": start_iso},
        "end": {"dateTime": end_iso},
        "description": description,
    }

    event = service.events().insert(calendarId="primary", body=event_body).execute()
    return f"Created: {event.get('summary')} at {event.get('start', {}).get('dateTime')}"

# ---------------------------------------------------------------------------
# LangGraph State Definition
# ---------------------------------------------------------------------------

class ScheduleState(TypedDict):
    instructions: str
    events: List[dict]
    results: List[str]

def get_booking_graph():
    """Build the LangGraph at runtime when secrets are available."""
    from langchain_openai import ChatOpenAI
    from langgraph.graph import START, END, StateGraph

    planner_llm = ChatOpenAI(
        model="gpt-5-mini", 
        temperature=0,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )

    def plan_events_node(state: ScheduleState) -> ScheduleState:
        """Use LLM to convert instructions into an array of events."""
        local_offset = datetime.now().astimezone().strftime("%z")
        today_iso = datetime.now().astimezone().date().isoformat()

        prompt = f"""
        You are a scheduling planner. Today is {today_iso}. UTC offset is {local_offset}.
        Based on the user request produce between 1 and 7 events as a JSON array.
        Fields per event: summary, start_iso, end_iso, description.
        All times must include timezone offset {local_offset}.
        If duration is missing, default to 30 minutes.
        User request: {state['instructions']}
        Return ONLY valid JSON array.
        """

        raw = planner_llm.invoke(prompt).content

        # Clean potential markdown code blocks
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        try:
            events = json.loads(raw.strip())
            if not isinstance(events, list):
                raise ValueError("Expected a list of events")
        except Exception as e:
            events = []
            print(f"Failed to parse events: {e}")

        return {
            "instructions": state["instructions"],
            "events": events,
            "results": [],
        }

    def book_events_node(state: ScheduleState) -> ScheduleState:
        """Create Google Calendar events from the ScheduleState."""
        results = list(state.get("results", []))

        for ev in state.get("events", []):
            try:
                msg = create_calendar_event(
                    summary=ev["summary"],
                    start_iso=ev["start_iso"],
                    end_iso=ev["end_iso"],
                    description=ev.get("description", "")
                )
                results.append(msg)
            except Exception as exc:
                results.append(f"Failed to book {ev.get('summary', 'event')}: {exc}")

        return {
            "instructions": state["instructions"],
            "events": state["events"],
            "results": results,
        }

    graph_builder = StateGraph(ScheduleState)
    graph_builder.add_node("plan_events", plan_events_node)
    graph_builder.add_node("book_events", book_events_node)
    graph_builder.add_edge(START, "plan_events")
    graph_builder.add_edge("plan_events", "book_events")
    graph_builder.add_edge("book_events", END)

    return graph_builder.compile()

# ---------------------------------------------------------------------------
# Telegram Webhook Endpoint
# ---------------------------------------------------------------------------

@app.function(
    image=image,
    secrets=[modal.Secret.from_name("custom-secret")],
    volumes={"/data": modal.Volume.from_name("calendar-volume")}
)
@modal.fastapi_endpoint(method="POST")
def telegram_webhook(data: dict):
    """Handle Telegram → Modal webhook."""
    
    import os
    import json
    import requests
    from typing import List, TypedDict
    from datetime import datetime
    from pathlib import Path
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    
    message = data.get("message", {})
    text = message.get("text")
    chat_id = message.get("chat", {}).get("id")

    if not chat_id or not text:
        return {"status": "ignored"}

    # ✅ Build graph at runtime when secrets are available
    booking_graph = get_booking_graph()

    # Run the LangGraph
    result_state = booking_graph.invoke({
        "instructions": text,
        "events": [],
        "results": [],
    })

    result = "\n".join(result_state["results"]) if result_state["results"] else "No events were scheduled."

    # ✅ Get token at runtime
    telegram_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    telegram_api_url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"

    requests.post(
        telegram_api_url,
        json={"chat_id": chat_id, "text": result}
    )

    return {"status": "ok"}


