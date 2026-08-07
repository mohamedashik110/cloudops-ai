import random
from datetime import date, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from cloud_accounts.models import CloudAccount, CostRecord
from users.models import Organization


SERVICES = [
    ("Amazon EC2", 15.0, 45.0),
    ("Amazon S3", 2.0, 8.0),
    ("Amazon RDS", 10.0, 30.0),
    ("AWS Lambda", 0.5, 3.0),
    ("Amazon CloudFront", 1.0, 5.0),
    ("Amazon VPC", 0.5, 2.0),
]


class Command(BaseCommand):
    help = "Generate synthetic cost data for demo purposes (clearly flagged is_synthetic=True)"

    def add_arguments(self, parser):
        parser.add_argument("--org", type=str, required=True, help="Organization name")
        parser.add_argument("--days", type=int, default=90, help="Number of days of history to generate")

    def handle(self, *args, **options):
        org_name = options["org"]
        days = options["days"]

        try:
            org = Organization.objects.get(name=org_name)
        except Organization.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"Organization '{org_name}' not found."))
            return

        cloud_account, created = CloudAccount.objects.get_or_create(
            organization=org,
            name="Demo AWS Account",
            defaults={
                "aws_access_key_id": "demo-key",
                "aws_secret_access_key": "demo-secret",
                "aws_region": "us-east-1",
                "status": CloudAccount.Status.CONNECTED,
            },
        )

        today = date.today()
        created_count = 0

        for day_offset in range(days):
            current_date = today - timedelta(days=day_offset)
            # simulate gradual growth over time + weekly seasonality
            growth_factor = 1 + (days - day_offset) / days * 0.3
            weekday_factor = 0.7 if current_date.weekday() >= 5 else 1.0  # lower cost on weekends

            for service_name, low, high in SERVICES:
                base_amount = random.uniform(low, high)
                amount = Decimal(str(round(base_amount * growth_factor * weekday_factor, 4)))

                CostRecord.objects.create(
                    cloud_account=cloud_account,
                    service=service_name,
                    amount=amount,
                    currency="USD",
                    date=current_date,
                    region="us-east-1",
                    is_synthetic=True,
                )
                created_count += 1

        self.stdout.write(self.style.SUCCESS(
            f"Created {created_count} synthetic cost records for '{org_name}' over {days} days."
        ))
