# connects the backend to AWS DynamoDB
import os
from datetime import date

import boto3

dynamodb = boto3.resource(
    "dynamodb",
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_REGION"),
)

table = dynamodb.Table("PropertyViewEvents")


def record_property_view(property_id, city, locality):
    today = date.today().isoformat()

    table.update_item(
        Key={
            "property_id": str(property_id),
            "date": today,
        },
        UpdateExpression="ADD view_count :inc SET city=:city, locality=:locality",
        ExpressionAttributeValues={
            ":inc": 1,
            ":city": city,
            ":locality": locality,
        },
    )
