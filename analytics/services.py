from django.db.models import Sum
from django.core.cache import cache
from datetime import date, timedelta
from cloud_accounts.models import CostRecord


def get_cost_summary(organization, days=30):
    """
    Returns total cost, top services, and daily trend
    for an organization over the last N days.
    Cached for 5 minutes to avoid recomputing on every request.
    """
    cache_key = f"cost_summary:{organization.id}:{days}"
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    records = CostRecord.objects.filter(
        cloud_account__organization=organization,
        date__gte=start_date,
        date__lte=end_date,
    )

    total_cost = records.aggregate(total=Sum("amount"))["total"] or 0

    top_services = (
        records.values("service")
        .annotate(amount=Sum("amount"))
        .order_by("-amount")[:5]
    )

    trend = (
        records.values("date")
        .annotate(amount=Sum("amount"))
        .order_by("date")
    )

    result = {
        "total_cost": float(total_cost),
        "period": f"last_{days}_days",
        "top_services": [
            {"service": s["service"], "amount": float(s["amount"])}
            for s in top_services
        ],
        "trend": [
            {"date": str(t["date"]), "amount": float(t["amount"])}
            for t in trend
        ],
    }

    cache.set(cache_key, result, timeout=300)  # cache for 5 minutes
    return result
