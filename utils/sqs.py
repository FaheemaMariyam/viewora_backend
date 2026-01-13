import json
import os

import boto3

sqs = boto3.client(
    "sqs",
    region_name=os.getenv("AWS_REGION"),
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)


def send_interest_created_event(data: dict):
    sqs.send_message(
        QueueUrl=os.getenv("SQS_INTEREST_QUEUE_URL"),
        MessageBody=json.dumps(data),
    )
