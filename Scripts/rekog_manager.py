# rekog_manager.py
# Phase 2 — Rekognition indexing (ONLINE ONLY, S3-based)

import time
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm

from .config import (
    S3_BUCKET,
    AWS_REGION,
    REKOG_COLLECTION,
    SKIP_ALREADY_INDEXED,
    EXTERNAL_ID_FORMAT,
    MASTERSHEET_ID,
    MASTERSHEET_NAME,
)

from .s3_face_map import read_face_map_from_s3, write_face_map_to_s3
from .gdrive_helpers import get_sheets_service

s3 = boto3.client("s3", region_name=AWS_REGION)
rekog = boto3.client("rekognition", region_name=AWS_REGION)


# ------------------------------------------------------
# AWS SETUP
# ------------------------------------------------------

def ensure_bucket_exists():
    try:
        s3.head_bucket(Bucket=S3_BUCKET)
    except ClientError:
        s3.create_bucket(
            Bucket=S3_BUCKET,
            CreateBucketConfiguration={"LocationConstraint": AWS_REGION}
        )


def ensure_collection():
    existing = rekog.list_collections().get("CollectionIds", [])
    if REKOG_COLLECTION not in existing:
        rekog.create_collection(CollectionId=REKOG_COLLECTION)


# ------------------------------------------------------
# INDEX FACES FROM S3
# ------------------------------------------------------

def list_ref_images_from_s3():
    """
    List all reference images under refs/ in S3.
    """
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=S3_BUCKET, Prefix="refs/")

    files = []
    for page in pages:
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith((".jpg", ".jpeg", ".png")):
                files.append(key)
    return files


def index_faces_and_record(update_sheet=True):
    """
    Index faces directly from S3 and persist FaceId mapping.
    """
    ensure_bucket_exists()
    ensure_collection()

    existing_map = read_face_map_from_s3() or {}
    records = list(existing_map.values())

    s3_keys = list_ref_images_from_s3()

    for s3_key in tqdm(s3_keys, desc="Indexing faces"):
        filename = s3_key.split("/")[-1]
        base = filename.rsplit(".", 1)[0]
        parts = base.split("-")

        if len(parts) < 4:
            continue

        srno, name, class_, section = parts[0], parts[1], parts[2], parts[3]

        external_id = EXTERNAL_ID_FORMAT.format(
            srno=srno,
            name=name,
            class_name=class_,
            section=section
        )

        if SKIP_ALREADY_INDEXED and external_id in existing_map:
            continue

        try:
            resp = rekog.index_faces(
                CollectionId=REKOG_COLLECTION,
                Image={"S3Object": {"Bucket": S3_BUCKET, "Name": s3_key}},
                ExternalImageId=external_id,
                DetectionAttributes=["DEFAULT"]
            )
        except Exception as e:
            print("❌ Indexing failed:", s3_key, e)
            continue

        face_records = resp.get("FaceRecords", [])
        if not face_records:
            print("⚠️ No face detected in:", s3_key)
            continue

        face_id = face_records[0]["Face"]["FaceId"]

        records.append({
            "ExternalImageId": external_id,
            "FaceId": face_id,
            "S3Key": s3_key,
            "FileName": filename
        })

        time.sleep(0.05)

    write_face_map_to_s3(records)

    if update_sheet:
        update_mastersheet_faceids(records)

    return records


# ------------------------------------------------------
# UPDATE GOOGLE SHEET
# ------------------------------------------------------

def update_mastersheet_faceids(records):
    """
    Writes FaceID (F) and ExternalFaceID (G) to Mastersheet.
    """

    if not records:
        return

    sheets = get_sheets_service()

    resp = sheets.spreadsheets().values().get(
        spreadsheetId=MASTERSHEET_ID,
        range=f"{MASTERSHEET_NAME}!A:A"
    ).execute()

    values = resp.get("values", [])
    if not values:
        return

    srno_to_row = {
        row[0]: idx + 1
        for idx, row in enumerate(values)
        if idx > 0 and row
    }

    updates = []

    for rec in records:
        external_id = rec["ExternalImageId"]
        face_id = rec["FaceId"]
        srno = external_id.split("_", 1)[0]

        row_num = srno_to_row.get(srno)
        if not row_num:
            continue

        updates.append({
            "range": f"{MASTERSHEET_NAME}!F{row_num}:G{row_num}",
            "values": [[face_id, external_id]]
        })

    if updates:
        sheets.spreadsheets().values().batchUpdate(
            spreadsheetId=MASTERSHEET_ID,
            body={
                "valueInputOption": "USER_ENTERED",
                "data": updates
            }
        ).execute()
