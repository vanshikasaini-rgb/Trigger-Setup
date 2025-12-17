# s3_face_map.py
# Persist face map to S3 so rekognition mapping is shared across runs.

import boto3
import csv
import io
from botocore.exceptions import ClientError
from .config import S3_BUCKET, AWS_REGION, MP_FACE_MAP_KEY

_s3 = boto3.client("s3", region_name=AWS_REGION)


def read_face_map_from_s3():
    try:
        resp = _s3.get_object(Bucket=S3_BUCKET, Key=MP_FACE_MAP_KEY)
        body = resp["Body"].read().decode("utf-8")
        f = io.StringIO(body)
        reader = csv.DictReader(f)
        return {row["ExternalImageId"]: row for row in reader}

    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("NoSuchKey", "404"):
            return {}
        raise  # real S3 error → surface it


def write_face_map_to_s3(records):
    if not records:
        return

    f = io.StringIO()
    fieldnames = ["ExternalImageId", "FaceId", "S3Key", "FileName"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()

    for r in records:
        writer.writerow(r)

    _s3.put_object(
        Bucket=S3_BUCKET,
        Key=MP_FACE_MAP_KEY,
        Body=f.getvalue().encode("utf-8")
    )
