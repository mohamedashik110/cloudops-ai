import os
import json
from google import genai

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def route_question(question):
    """
    Agent 1 (Router): decides what data is needed to answer the question.
    Returns a dict like {"needs_historical": true, "needs_forecast": false}.

    This is a genuine agent step - a small, focused LLM call whose only
    job is classification/planning, not answering. Separating this from
    the actual answer generation is what makes this multi-agent rather
    than a single monolithic prompt.
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

    # Strip markdown code fences if the model added them anyway,
    # without relying on backtick characters in this source file.
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
        # If routing fails for any reason, default to fetching both -
        # safer to over-provide grounding data than under-provide it.
        return {"needs_historical": True, "needs_forecast": True}


def draft_answer(question, historical_data, forecast_data):
    """
    Agent 2 (Analyst): drafts an answer using ONLY the data provided by
    the router-directed retrieval step. This agent's only job is
    generating a natural-language answer, nothing else - it does not
    decide what data to fetch (that was Agent 1) and it does not
    self-verify (that's Agent 3).
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
using ONLY the data below. Never invent numbers not present here. If the
available data does not answer the question, say so plainly.

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
    Agent 3 (Verifier): checks the drafted answer against the real source
    data and flags it if the draft appears to cite a number that does not
    actually appear anywhere in the retrieved data. This is a genuine,
    separate hallucination check performed AFTER generation, not just
    prompt instructions hoping the model behaves - a real defense in depth.
    """
    known_numbers = set()

    if historical_data:
        known_numbers.add(str(historical_data["total_cost"]))
        for s in historical_data["top_services"]:
            known_numbers.add(str(s["amount"]))

    if forecast_data:
        known_numbers.add(str(forecast_data["predicted_total"]))
        known_numbers.add(str(forecast_data["model_confidence"]["mae"]))

    import re
    numbers_in_draft = re.findall(r"\d+\.?\d*", draft)

    unverified = [
        n for n in numbers_in_draft
        if n not in known_numbers and float(n) > 1
    ]

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
