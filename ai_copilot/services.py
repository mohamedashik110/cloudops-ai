import os
from google import genai

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


from analytics.services import get_cost_summary
from ml_engine.services import generate_forecast


def ask_copilot(organization, question, days=90):
    """
    Answers a natural-language question about cloud costs, grounded in
    real CostRecord data AND the ML cost forecast.
    """
    if organization is None:
        return {
            "answer": "This account is not linked to an organization, so I "
                       "don't have any cost data to reference. Please contact "
                       "an administrator to set up your organization.",
            "sources": {},
        }

    summary = get_cost_summary(organization, days=days)

    forecast_context = "No forecast is available (not enough historical data yet)."
    forecast_data = None
    try:
        forecast_data = generate_forecast(organization, days_ahead=30)
        predicted = forecast_data["predicted_total"]
        mae = forecast_data["model_confidence"]["mae"]
        based_on = forecast_data["model_confidence"]["based_on_days"]
        forecast_context = (
            f"Predicted total for next 30 days: {predicted} USD "
            f"(model average error: {mae} USD per day, "
            f"based on {based_on} days of history)."
        )
    except ValueError:
        pass

    if summary["total_cost"] == 0:
        context_note = (
            "IMPORTANT: There is no historical cost data available for this "
            "period. You MUST tell the user no data is available rather than "
            "guessing or inventing any numbers."
        )
    else:
        context_note = ""

    prompt = f"""You are a cloud cost analysis assistant. Answer the user's
question using ONLY the data provided below. Do not invent, estimate, or
assume any numbers that are not explicitly present in this data. If the
data does not contain enough information to answer, say so clearly. This
includes forecast questions - only cite the forecast number given below,
never make up your own prediction.

{context_note}

HISTORICAL COST DATA (last {days} days):
- Total cost: {summary['total_cost']} USD
- Top services by cost: {summary['top_services']}
- Daily trend (last 10 days shown): {summary['trend'][-10:]}

FORECAST DATA:
{forecast_context}

USER QUESTION: {question}

Answer in 2-4 sentences, citing specific numbers from the data above.
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )

    sources = {
        "total_cost": summary["total_cost"],
        "top_services": summary["top_services"],
        "period": summary["period"],
    }
    if forecast_data:
        sources["forecast_predicted_total"] = forecast_data["predicted_total"]
        sources["forecast_mae"] = forecast_data["model_confidence"]["mae"]

    return {
        "answer": response.text,
        "sources": sources,
    }
