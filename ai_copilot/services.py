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


def ask_copilot(organization, question, days=90):
    """
    Answers a natural-language question about cloud costs, grounded in
    real CostRecord data. The LLM is instructed to ONLY use the provided
    data and to explicitly say when it lacks information, rather than
    guessing or inventing numbers.
    """
    if organization is None:
        return {
            "answer": "This account is not linked to an organization, so I "
                       "don't have any cost data to reference. Please contact "
                       "an administrator to set up your organization.",
            "sources": {},
        }

    summary = get_cost_summary(organization, days=days)

    if summary["total_cost"] == 0:
        context_note = (
            "IMPORTANT: There is no cost data available for this period. "
            "You MUST tell the user no data is available rather than "
            "guessing or inventing any numbers."
        )
    else:
        context_note = ""

    prompt = f"""You are a cloud cost analysis assistant. Answer the user's
question using ONLY the data provided below. Do not invent, estimate, or
assume any numbers that are not explicitly present in this data. If the
data does not contain enough information to answer, say so clearly.

{context_note}

COST DATA (last {days} days):
- Total cost: ${summary['total_cost']}
- Top services by cost: {summary['top_services']}
- Daily trend (last 10 days shown): {summary['trend'][-10:]}

USER QUESTION: {question}

Answer in 2-4 sentences, citing specific numbers from the data above.
"""

    response = client.models.generate_content(
        model="gemini-flash-lite-latest",
        contents=prompt,
    )

    return {
        "answer": response.text,
        "sources": {
            "total_cost": summary["total_cost"],
            "top_services": summary["top_services"],
            "period": summary["period"],
        },
    }
