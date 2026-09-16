import os
from google import genai
from analytics.services import get_cost_summary
from ml_engine.services import generate_forecast
from .agents import route_question, draft_answer, verify_answer

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def test_llm_connection():
    """
    Basic sanity check that we can reach the Gemini API.
    """
    response = client.models.generate_content(
        model="gemini-flash-latest",
        contents="Say hello in one short sentence.",
    )
    return response.text


def ask_copilot(organization, question, days=90):
    """
    Multi-agent pipeline for answering cloud cost questions:

      Agent 1 (Router)   -> decides what data is actually needed
      Retrieval          -> fetches only that data (plain Python, not an LLM)
      Agent 2 (Analyst)  -> drafts an answer using only the retrieved data
      Agent 3 (Verifier) -> checks the draft's numbers against real source data

    This separation of concerns - planning, retrieval, drafting, and
    verification as distinct steps - is what makes this a genuine
    multi-agent system rather than one large prompt doing everything.
    """
    if organization is None:
        return {
            "answer": "This account is not linked to an organization, so I "
                       "don't have any cost data to reference. Please contact "
                       "an administrator to set up your organization.",
            "sources": {},
            "verified": True,
        }

    # Agent 1: decide what data is needed
    plan = route_question(question)

    # Retrieval: fetch only what the router decided is needed
    historical_data = None
    if plan["needs_historical"]:
        historical_data = get_cost_summary(organization, days=days)

    forecast_data = None
    if plan["needs_forecast"]:
        try:
            forecast_data = generate_forecast(organization, days_ahead=30)
        except ValueError:
            forecast_data = None

    # Agent 2: draft the answer from only the retrieved data
    draft = draft_answer(question, historical_data, forecast_data)

    # Agent 3: verify the draft's numbers against the real source data
    verification = verify_answer(draft, historical_data, forecast_data)

    final_answer = draft
    if not verification["verified"]:
        final_answer = f"{draft}\n\n{verification['note']}"

    sources = {}
    if historical_data:
        sources["total_cost"] = historical_data["total_cost"]
        sources["top_services"] = historical_data["top_services"]
        sources["period"] = historical_data["period"]
    if forecast_data:
        sources["forecast_predicted_total"] = forecast_data["predicted_total"]
        sources["forecast_mae"] = forecast_data["model_confidence"]["mae"]

    return {
        "answer": final_answer,
        "sources": sources,
        "verified": verification["verified"],
        "agent_plan": plan,
    }
