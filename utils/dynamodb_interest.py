# utils/dynamodb_interest.py
import os
import time
from datetime import datetime

import boto3

dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

table = dynamodb.Table("PropertyInterestEvents")


def record_property_interest(property_id, user):
    """
    Store interest event ONLY for analytics / AI.
    Never used for business logic.
    """
    ttl = int(time.time()) + (60 * 60 * 24 * 90)  # 90 days

    profile = getattr(user, "profile", None)

    table.put_item(
        Item={
            "property_id": str(property_id),
            "interested_at": datetime.utcnow().isoformat(),
            "user_id": str(user.id),
            "city": getattr(profile, "city", "unknown"),
            "role": getattr(profile, "role", "unknown"),
            "ttl": ttl,
        }
    )

