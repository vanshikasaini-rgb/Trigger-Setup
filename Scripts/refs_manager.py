# refs_manager.py
# Phase 1 — Build reference images directly from Google Drive → S3

import os
import tempfile
from tqdm import tqdm
from googleapiclient.errors import HttpError

from .gdrive_helpers import (
    get_sheets_service,
    get_drive_service,
    parse_drive_link,
    download_file_from_drive,
    download_from_public_url,
)

from .config import (
    MASTERSHEET_ID,
    MASTERSHEET_NAME,
    S3_BUCKET,
    AWS_REGION,
)

import boto3

SHEET_RANGE = f"{MASTERSHEET_NAME}!A:E"

s3 = boto3.client("s3", region_name=AWS_REGION)


def clean_name(name):
    return "_".join(name.strip().split())


def ensure_ext_from_link(link):
    if link and any(link.lower().endswith(x) for x in (".jpg", ".jpeg", ".png")):
        return os.path.splitext(link)[1]
    return ".jpg"


def get_mastersheet_rows():
    sheets = get_sheets_service()
    resp = sheets.spreadsheets().values().get(
        spreadsheetId=MASTERSHEET_ID,
        range=SHEET_RANGE
    ).execute()
    values = resp.get("values", [])
    return values[1:] if values else []


def phase1_build_refs():
    """
    ONLINE-ONLY:
    Google Drive → TEMP FILE → S3 (refs/)
    """
    rows = get_mastersheet_rows()
    drive = get_drive_service()

    for row in tqdm(rows, desc="Processing mastersheet rows"):
        srno = row[0].strip() if len(row) > 0 else ""
        name = row[1].strip() if len(row) > 1 else ""
        class_ = row[2].strip() if len(row) > 2 else ""
        section = row[3].strip() if len(row) > 3 else ""
        link = row[4].strip() if len(row) > 4 else ""

        if not (srno and name and link):
            continue

        clean = clean_name(name)
        ext = ensure_ext_from_link(link)
        filename = f"{srno}-{clean}-{class_}-{section}{ext}"
        s3_key = f"refs/{filename}"

        # TEMP FILE
        with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
            tmp_path = tmp.name

        try:
            file_id = parse_drive_link(link)

            if file_id:
                download_file_from_drive(drive, file_id, tmp_path)
            else:
                download_from_public_url(link, tmp_path)

            # Upload directly to S3
            s3.upload_file(tmp_path, S3_BUCKET, s3_key)

        except HttpError as e:
            print("❌ Failed:", srno, name, e)

        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)