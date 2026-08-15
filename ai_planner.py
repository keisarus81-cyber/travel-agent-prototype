"""
ai_planner.py

AI infrastructure for the Travel Agent prototype.
"""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()

DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6")


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        return None

    return OpenAI(api_key=api_key)


def prepare_places_for_ai(places, max_places=40):
    prepared_places = []

    for place in places[:max_places]:
        prepared_places.append({
            "name": place.get("name"),
            "category": place.get("category"),
            "type": place.get("type"),
            "lat": place.get("lat"),
            "lon": place.get("lon"),
            "distance": place.get("distance")
        })

    return prepared_places


def build_trip_context(
    destination,
    number_of_days,
    travelers,
    budget,
    pace,
    interests,
    notes,
    places,
    weather=None
):
    return {
        "destination": destination,
        "number_of_days": number_of_days,
        "travelers": travelers,
        "budget": budget,
        "pace": pace,
        "interests": interests or [],
        "notes": notes or "",
        "places": prepare_places_for_ai(places),
        "weather": weather or []
    }


def validate_trip_context(context):
    if not context.get("destination"):
        return False, "Destination is missing."

    if context.get("number_of_days", 0) < 1:
        return False, "Number of days must be at least 1."

    if not context.get("places"):
        return False, "No places were provided."

    return True, None


def check_ai_connection():
    client = get_openai_client()

    if client is None:
        return {
            "status": "not_connected",
            "message": "OPENAI_API_KEY was not found."
        }

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            input="Reply with exactly: CONNECTED"
        )

        return {
            "status": "connected",
            "message": response.output_text.strip(),
            "model": DEFAULT_MODEL
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
            "model": DEFAULT_MODEL
        }


def plan_trip_with_ai(context):
    is_valid, error = validate_trip_context(context)

    if not is_valid:
        return {
            "status": "error",
            "message": error,
            "plan": None
        }

    client = get_openai_client()

    if client is None:
        return {
            "status": "not_connected",
            "message": "OPENAI_API_KEY was not found.",
            "plan": None
        }

    trip_data = json.dumps(
        context,
        ensure_ascii=False,
        indent=2
    )

    instructions = """
You are the planning engine of a travel application.

Use only the trip information and candidate places supplied by the application.
Do not invent opening hours, prices, bookings, or facts that were not supplied.
Create a practical draft itinerary in Hebrew.
Take into account pace, interests, notes, weather, and geographic practicality.

This is only an early prototype. Keep the result concise.
"""

    try:
        response = client.responses.create(
            model=DEFAULT_MODEL,
            instructions=instructions,
            input=trip_data
        )

        return {
            "status": "connected",
            "message": "AI plan created successfully.",
            "plan": response.output_text,
            "model": DEFAULT_MODEL
        }

    except Exception as error:
        return {
            "status": "error",
            "message": str(error),
            "plan": None,
            "model": DEFAULT_MODEL
        }
