# reporting.py
# Phase 5 — Reporting to Google Sheets (Uploaded Data)

from .gdrive_helpers import get_sheets_service
from .config import MASTERSHEET_ID, UPLOADED_DATA_SHEET
import datetime


HEADERS = [
    "Timestamp",
    "File Name",
    "Faces Detected",
    "Face IDs Matched",
    "External Face IDs",
    "Copied to Folders"
]


def ensure_headers_exist(sheets):
    """
    Ensure header row exists in Uploaded Data sheet.
    """
    resp = sheets.spreadsheets().values().get(
        spreadsheetId=MASTERSHEET_ID,
        range=f"{UPLOADED_DATA_SHEET}!A1:F1"
    ).execute()

    values = resp.get("values", [])
    if not values or values[0] != HEADERS:
        sheets.spreadsheets().values().update(
            spreadsheetId=MASTERSHEET_ID,
            range=f"{UPLOADED_DATA_SHEET}!A1:F1",
            valueInputOption="USER_ENTERED",
            body={"values": [HEADERS]}
        ).execute()


def append_uploaded_data(rows):
    """
    rows format (from sorter):
    [
        file_name,
        faces_detected,
        face_ids_csv,
        external_ids_csv,
        copied_to_csv
    ]
    """
    if not rows:
        return

    sheets = get_sheets_service()
    ensure_headers_exist(sheets)

    now = datetime.datetime.utcnow().isoformat()

    body_rows = []
    for r in rows:
        body_rows.append([
            now,
            r[0],   # File Name
            r[1],   # Faces Detected
            r[2],   # Face IDs Matched
            r[3],   # External Face IDs
            r[4],   # Copied to Folders
        ])

    sheets.spreadsheets().values().append(
        spreadsheetId=MASTERSHEET_ID,
        range=f"{UPLOADED_DATA_SHEET}!A:F",
        valueInputOption="USER_ENTERED",
        insertDataOption="INSERT_ROWS",
        body={"values": body_rows}
    ).execute()
