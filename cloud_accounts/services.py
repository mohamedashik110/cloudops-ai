import boto3
from datetime import date, timedelta
from botocore.exceptions import ClientError


def fetch_aws_cost_data(cloud_account):
    """
    Fetch cost data from AWS Cost Explorer for a given CloudAccount.
    Returns a list of dicts: [{"service": ..., "amount": ..., "date": ...}, ...]
    Raises an exception on failure - caller (Celery task) handles retries/logging.

    Note: AWS Cost Explorer typically has a processing lag of a few days for the
    most recent data, so we end the query window 3 days before today rather than
    today itself, to avoid DataUnavailableException on unprocessed recent days.
    """
    client = boto3.client(
        "ce",
        aws_access_key_id=cloud_account.aws_access_key_id,
        aws_secret_access_key=cloud_account.aws_secret_access_key,
        region_name="us-east-1",
    )

    end = date.today() - timedelta(days=3)
    start = end - timedelta(days=30)

    try:
        response = client.get_cost_and_usage(
            TimePeriod={
                "Start": start.strftime("%Y-%m-%d"),
                "End": end.strftime("%Y-%m-%d"),
            },
            Granularity="DAILY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )
    except ClientError as e:
        raise RuntimeError(f"AWS Cost Explorer request failed: {e}")

    records = []
    for day in response.get("ResultsByTime", []):
        record_date = day["TimePeriod"]["Start"]
        for group in day.get("Groups", []):
            service_name = group["Keys"][0]
            amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
            if amount > 0:
                records.append({
                    "service": service_name,
                    "amount": amount,
                    "date": record_date,
                })

    return records
