import os
import json
import re
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def route_question(question):
    """
    Agent 1 (Router): decides what data is needed to answer the question.
    """
    prompt = f"""You are a routing assistant. Given a user's question about
cloud costs, decide what data categories are needed to answer it.

Respond with ONLY a JSON object, no other text, no markdown formatting,
no code fences - just the raw JSON, in this exact format:
{{"needs_historical": true or false, "needs_forecast": true or false}}

- needs_historical: true if the question is about past/current spend, totals, or breakdowns
- needs_forecast: true if the question is about future/predicted spend

USER QUESTION: {question}
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )

    text = response.text.strip()
    fence = chr(96) * 3
    if text.startswith(fence):
        text = text.strip(fence).replace("json", "", 1).strip()

    try:
        decision = json.loads(text)
        return {
            "needs_historical": bool(decision.get("needs_historical", True)),
            "needs_forecast": bool(decision.get("needs_forecast", False)),
        }
    except json.JSONDecodeError:
        return {"needs_historical": True, "needs_forecast": True}


def draft_answer(question, historical_data, forecast_data):
    """
    Agent 2 (Analyst): drafts an answer using ONLY the data provided.
    """
    historical_section = "Not retrieved (not needed for this question)."
    if historical_data:
        historical_section = (
            f"Total cost: {historical_data['total_cost']} USD. "
            f"Top services: {historical_data['top_services']}. "
            f"Recent daily trend: {historical_data['trend'][-10:]}."
        )

    forecast_section = "Not retrieved (not needed for this question)."
    if forecast_data:
        forecast_section = (
            f"Predicted total for next 30 days: {forecast_data['predicted_total']} USD "
            f"(model average error: {forecast_data['model_confidence']['mae']} USD/day, "
            f"based on {forecast_data['model_confidence']['based_on_days']} days of history)."
        )

    prompt = f"""You are a cloud cost analyst. Answer the user's question
using ONLY the data below. Never invent numbers not present here. Do not
use comma thousands-separators in numbers you write (write 4287.98, not
4,287.98) so your figures can be verified exactly against source data.
If the available data does not answer the question, say so plainly.

HISTORICAL DATA: {historical_section}

FORECAST DATA: {forecast_section}

USER QUESTION: {question}

Answer in 2-4 sentences, citing specific numbers from the data above.
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )
    return response.text


def verify_answer(draft, historical_data, forecast_data):
    """
    Agent 3 (Verifier): checks the drafted answer's monetary figures
    against real source data. Day-counts (e.g. "30 days", "90 days of
    history") are legitimate non-monetary numbers that naturally appear
    in answers and are explicitly allowed, since they describe the time
    period rather than a cost figure that could be hallucinated.
    """
    known_numbers = set()
    allowed_day_counts = set()

    def normalize(value):
        try:
            return round(float(str(value).replace(",", "")), 2)
        except (ValueError, TypeError):
            return None

    if historical_data:
        n = normalize(historical_data["total_cost"])
        if n is not None:
            known_numbers.add(n)
        for s in historical_data["top_services"]:
            n = normalize(s["amount"])
            if n is not None:
                known_numbers.add(n)

    if forecast_data:
        n = normalize(forecast_data["predicted_total"])
        if n is not None:
            known_numbers.add(n)
        n = normalize(forecast_data["model_confidence"]["mae"])
        if n is not None:
            known_numbers.add(n)
        allowed_day_counts.add(30)  # forecast window
        allowed_day_counts.add(forecast_data["model_confidence"]["based_on_days"])

    cleaned_draft = draft.replace(",", "")
    numbers_in_draft = re.findall(r"(?<![A-Za-z])\d+\.?\d*", cleaned_draft)

    unverified = []
    for raw in numbers_in_draft:
        value = normalize(raw)
        if value is None or value <= 1:
            continue
        if value in allowed_day_counts:
            continue
        if any(abs(value - known) < 0.1 for known in known_numbers):
            continue
        unverified.append(raw)

    if unverified:
        return {
            "verified": False,
            "note": (
                "Note: this answer contained figures that could not be "
                "directly matched to source data and should be treated "
                "with caution."
            ),
        }

    return {"verified": True, "note": None}
