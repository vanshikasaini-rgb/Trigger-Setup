# s3_tracker.py
# Persist processed Drive file IDs to S3 so every scheduled run shares state.
import json
import boto3
from botocore.exceptions import ClientError
from .config import S3_BUCKET, AWS_REGION, MP_PROCESSED_TRACKER_KEY

_s3 = boto3.client("s3", region_name=AWS_REGION)

def load_processed_ids_from_s3():
    try:
        resp = _s3.get_object(Bucket=S3_BUCKET, Key=MP_PROCESSED_TRACKER_KEY)
        body = resp['Body'].read().decode('utf-8')
        data = json.loads(body)
        return set(data)
    except ClientError as e:
        code = e.response['Error']['Code']
        if code in ("NoSuchKey","404","NoSuchBucket"):
            return set()
        raise

def save_processed_ids_to_s3(id_set):
    payload = json.dumps(list(id_set), ensure_ascii=False)
    _s3.put_object(Bucket=S3_BUCKET, Key=MP_PROCESSED_TRACKER_KEY, Body=payload.encode('utf-8'))
