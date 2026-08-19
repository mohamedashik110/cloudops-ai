import boto3
from datetime import date, timedelta
from botocore.exceptions import ClientError


def fetch_aws_cost_data(cloud_account):
    """
    Fetch cost data from AWS Cost Explorer using temporary credentials
    obtained by assuming the company's IAM Role via AWS STS.

    This backend never stores or handles the company's permanent AWS
    credentials - only a Role ARN and External ID, both non-secret
    identifiers. Temporary credentials expire automatically (~1 hour).
    """
    sts_client = boto3.client("sts")

    try:
        assumed_role = sts_client.assume_role(
            RoleArn=cloud_account.role_arn,
            RoleSessionName="CloudOpsAI-CostSync",
            ExternalId=cloud_account.external_id,
            DurationSeconds=3600,
        )
    except ClientError as e:
        raise RuntimeError(f"Failed to assume role {cloud_account.role_arn}: {e}")

    temp_credentials = assumed_role["Credentials"]

    client = boto3.client(
        "ce",
        aws_access_key_id=temp_credentials["AccessKeyId"],
        aws_secret_access_key=temp_credentials["SecretAccessKey"],
        aws_session_token=temp_credentials["SessionToken"],
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
