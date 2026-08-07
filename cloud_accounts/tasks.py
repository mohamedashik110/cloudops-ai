from celery import shared_task
from django.utils import timezone
from .models import CloudAccount, CostRecord
from .services import fetch_aws_cost_data


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_cloud_account_costs(self, cloud_account_id):
    """
    Pulls real AWS cost data for a CloudAccount and stores it as CostRecords.
    Retries up to 3 times on failure, with a 60-second delay between attempts.
    """
    try:
        cloud_account = CloudAccount.objects.get(id=cloud_account_id)
    except CloudAccount.DoesNotExist:
        return f"CloudAccount {cloud_account_id} not found - skipping."

    try:
        records = fetch_aws_cost_data(cloud_account)
    except Exception as exc:
        cloud_account.status = CloudAccount.Status.FAILED
        cloud_account.save(update_fields=["status"])
        raise self.retry(exc=exc)

    created_count = 0
    for record in records:
        CostRecord.objects.update_or_create(
            cloud_account=cloud_account,
            service=record["service"],
            date=record["date"],
            defaults={
                "amount": record["amount"],
                "currency": "USD",
                "is_synthetic": False,
            },
        )
        created_count += 1

    cloud_account.status = CloudAccount.Status.CONNECTED
    cloud_account.last_synced_at = timezone.now()
    cloud_account.save(update_fields=["status", "last_synced_at"])

    return f"Synced {created_count} cost records for {cloud_account.name}."
