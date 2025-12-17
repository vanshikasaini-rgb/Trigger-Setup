# Scripts/gdrive_helpers.py
"""
Google Drive & Google Sheets helper module

AUTHENTICATION:
- Uses Google Service Account JSON hardcoded in config.py
- NO API keys
- NO OAuth login
- Suitable for college projects / demos

⚠️ NOT PRODUCTION SAFE
Move credentials to env vars / secrets manager before real deployment
"""

import os
import io
import re
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google.oauth2 import service_account
from googleapiclient.errors import HttpError

from .config import (
    GOOGLE_SERVICE_ACCOUNT_INFO,
    GOOGLE_CREDENTIALS_JSON_FILE,
)


# ------------------------------------------------------
# GOOGLE API SCOPES
# ------------------------------------------------------

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets"
]

# ------------------------------------------------------
# AUTHENTICATION
# ------------------------------------------------------

def build_creds():
    """
    Build Google credentials from service account JSON
    stored in config.py
    """
    creds = service_account.Credentials.from_service_account_info(
        GOOGLE_SERVICE_ACCOUNT_INFO,
        scopes=SCOPES
    )
    return creds


def get_drive_service():
    """Return authenticated Google Drive service"""
    return build("drive", "v3", credentials=build_creds())


def get_sheets_service():
    """Return authenticated Google Sheets service"""
    return build("sheets", "v4", credentials=build_creds())


# ------------------------------------------------------
# LOCAL TEMP DIRECTORY HELPERS
# ------------------------------------------------------

import tempfile
TMP_DIR = tempfile.gettempdir()


# ------------------------------------------------------
# DRIVE LINK PARSING
# ------------------------------------------------------

def parse_drive_link(link):
    """
    Extract file ID from Google Drive file link.
    """
    if not link:
        return None

    patterns = [
        r"https?://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)",
        r"https?://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)

    return None


def parse_drive_folder_link(link):
    """
    Extract folder ID from Google Drive folder link.
    Supports:
    - https://drive.google.com/drive/folders/<id>
    - https://drive.google.com/drive/u/0/folders/<id>
    - raw folder ID
    """
    if not link:
        return None

    link = link.strip()

    patterns = [
        r"/folders/([a-zA-Z0-9_-]+)",
        r"id=([a-zA-Z0-9_-]+)"
    ]

    for pattern in patterns:
        match = re.search(pattern, link)
        if match:
            return match.group(1)

    # If it already looks like a Drive ID, return it
    if re.fullmatch(r"[a-zA-Z0-9_-]{10,}", link):
        return link

    return None



# ------------------------------------------------------
# DRIVE DOWNLOAD UTILITIES
# ------------------------------------------------------

def download_file_from_drive(service, file_id, dest_path):
    """
    Download a single file from Google Drive using file ID.
    """
    request = service.files().get_media(fileId=file_id)
    fh = io.FileIO(dest_path, "wb")
    downloader = MediaIoBaseDownload(fh, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    fh.close()
    return dest_path


def list_files_in_folder(service, folder_id):
    """
    List all files in a Drive folder (non-recursive).
    Shared Drive compatible.
    """
    query = f"'{folder_id}' in parents and trashed=false"
    results = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, modifiedTime)",
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        results.extend(response.get("files", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return results


def download_folder_recursive(service, folder_id, processed_ids=None):
    """
    Recursively download a Drive folder into a TEMP directory.
    """
    import tempfile

    local_dest = tempfile.mkdtemp(prefix="mp_drive_")
    downloaded = []


    items = list_files_in_folder(service, folder_id)

    for item in items:
        file_id = item["id"]
        name = item["name"]
        mime = item["mimeType"]

        if processed_ids and file_id in processed_ids:
            continue

        if mime == "application/vnd.google-apps.folder":
            subfolder = os.path.join(local_dest, name)
            downloaded.extend(
                download_folder_recursive(
                    service,
                    file_id,
                    subfolder,
                    processed_ids
                )
            )
        else:
            local_path = os.path.join(local_dest, name)
            base, ext = os.path.splitext(local_path)
            i = 1
            while os.path.exists(local_path):
                local_path = f"{base}_{i}{ext}"
                i += 1

            try:
                download_file_from_drive(service, file_id, local_path)
                downloaded.append({
                    "id": file_id,
                    "name": name,
                    "local_path": local_path,
                    "mimeType": mime,
                    "modifiedTime": item.get("modifiedTime")
                })
            except HttpError as e:
                print("❌ Failed to download:", name, e)

    return downloaded


# ------------------------------------------------------
# VALIDATION SHEET HELPERS
# ------------------------------------------------------

def get_upload_folder_ids_from_validation_sheet(
    sheet_service,
    spreadsheet_id,
    validation_sheet_name="Validation",
    column_range="A:A"
):
    """
    Reads Validation sheet column A.
    Each cell must contain a Drive folder link or folder ID.
    """
    range_name = f"{validation_sheet_name}!{column_range}"
    result = sheet_service.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,
        range=range_name
    ).execute()

    values = result.get("values", [])
    folder_ids = []

    for row in values:
        if not row:
            continue
        folder_ids.append(parse_drive_folder_link(row[0]))

    return folder_ids
import requests

def download_from_public_url(url, dest_path):
    """
    Downloads a file from a public HTTP/HTTPS URL.
    Used when Drive file ID is not available.
    """
    response = requests.get(url, stream=True, timeout=30)
    response.raise_for_status()

    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    return dest_path

def walk_drive_folder_recursive(service, folder_id):
    """
    Recursively yield all files inside a Drive folder
    (including nested subfolders).
    """
    query = f"'{folder_id}' in parents and trashed=false"

    page_token = None
    while True:
        resp = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()

        for item in resp.get("files", []):
            if item["mimeType"] == "application/vnd.google-apps.folder":
                # recurse into subfolder
                yield from walk_drive_folder_recursive(service, item["id"])
            else:
                yield item

        page_token = resp.get("nextPageToken")
        if not page_token:
            break

