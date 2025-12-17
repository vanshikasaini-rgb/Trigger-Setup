# sorter.py
# Phase 4 — ONLINE-ONLY photo sorting (Drive → Rekognition → Drive)

import os
import tempfile
import boto3
from tqdm import tqdm
from .s3_tracker import load_processed_ids_from_s3, save_processed_ids_to_s3


from .config import (
    REKOG_COLLECTION,
    AWS_REGION,
    MASTERSHEET_ID,
    VALIDATION_SHEET_NAME,
    UPLOADED_DATA_SHEET,
    MIN_FACE_MATCH_CONFIDENCE,
)

from .s3_face_map import read_face_map_from_s3
from .gdrive_helpers import (
    get_drive_service,
    get_sheets_service,
    parse_drive_folder_link,
    download_file_from_drive,
    walk_drive_folder_recursive,
)


rekog = boto3.client("rekognition", region_name=AWS_REGION)


# ------------------------------------------------------
# FACE MAP
# ------------------------------------------------------

def load_face_map_dict():
    """
    Build FaceId → record mapping from S3.
    """
    raw = read_face_map_from_s3() or {}
    face_map = {}
    for _, row in raw.items():
        face_map[row["FaceId"]] = row
    return face_map


# ------------------------------------------------------
# REKOGNITION
# ------------------------------------------------------

def detect_and_match_faces_bytes(image_bytes):
    """
    Send image bytes directly to Rekognition.
    """
    resp = rekog.search_faces_by_image(
        CollectionId=REKOG_COLLECTION,
        Image={"Bytes": image_bytes},
        FaceMatchThreshold=MIN_FACE_MATCH_CONFIDENCE,
        MaxFaces=15,
    )
    return resp.get("FaceMatches", [])


# ------------------------------------------------------
# DRIVE HELPERS
# ------------------------------------------------------

def get_student_folder_id(service, external_id):
    """
    Find student folder ID based on ExternalImageId.
    Folder name format: SrNo-Name-Class-Section
    """
    folder_name = external_id.replace("_", "-")

    query = (
        f"name='{folder_name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"trashed=false"
    )

    resp = service.files().list(
        q=query,
        fields="files(id)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = resp.get("files", [])
    return files[0]["id"] if files else None


def copy_drive_file(service, file_id, dest_folder_id):
    service.files().copy(
        fileId=file_id,
        body={"parents": [dest_folder_id]},
        supportsAllDrives=True
    ).execute()



# ------------------------------------------------------
# MAIN SORTING LOGIC
# ------------------------------------------------------

def phase4_sort_uploads():
    """
    Reads Validation sheet folders, processes images,
    matches faces, copies images into student folders,
    and logs results in Uploaded Data sheet.
    """

    drive = get_drive_service()
    sheets = get_sheets_service()
    face_map = load_face_map_dict()
    processed_ids = load_processed_ids_from_s3()
    new_processed_ids = set(processed_ids)


    # -------------------------------
    # Read Validation Sheet (Column A)
    # -------------------------------
    resp = sheets.spreadsheets().values().get(
        spreadsheetId=MASTERSHEET_ID,
        range=f"{VALIDATION_SHEET_NAME}!A:A"
    ).execute()

    values = resp.get("values", [])

    # Skip header row
    folder_links = [r[0] for r in values[1:] if r]

    upload_folder_ids = []
    for link in folder_links:
        fid = parse_drive_folder_link(link)
        if not fid:
            print(f"⚠️ Skipping invalid folder entry: {link}")
            continue
        upload_folder_ids.append(fid)

    report_rows = []

    # -------------------------------
    # Process each upload folder
    # -------------------------------
    for folder_id in upload_folder_ids:
        files_iter = walk_drive_folder_recursive(drive, folder_id)

        for file in tqdm(list(files_iter), desc="Processing uploads"):
            mime = file.get("mimeType", "")

            # Skip folders / Google Docs
            if mime.startswith("application/vnd.google-apps"):
                continue

            file_id = file["id"]
            file_name = file["name"]
            # Skip already processed images
            if file_id in processed_ids:
                continue


            # -------------------------------
            # Temp download
            # -------------------------------
            with tempfile.NamedTemporaryFile(delete=False) as tmp:
                tmp_path = tmp.name

            try:
                download_file_from_drive(drive, file_id, tmp_path)

                with open(tmp_path, "rb") as fh:
                    img_bytes = fh.read()

                try:
                    matches = detect_and_match_faces_bytes(img_bytes)
                except Exception:
                    print(f"⚠️ Unsupported or corrupted image: {file_name}")
                    continue

                matched_faceids = []
                matched_external = []
                copied_to = []

                # -------------------------------
                # Handle matches
                # -------------------------------
                for m in matches:
                    face_id = m["Face"]["FaceId"]
                    matched_faceids.append(face_id)

                    rec = face_map.get(face_id)
                    if not rec:
                        continue

                    external = rec["ExternalImageId"]
                    matched_external.append(external)

                    student_folder_id = get_student_folder_id(drive, external)
                    if not student_folder_id:
                        continue

                    copy_drive_file(drive, file_id, student_folder_id)
                    copied_to.append(external)

                    from datetime import datetime

                    report_rows.append([
                        datetime.now().isoformat(),          # Timestamp
                        file_name,                           # File Name
                        len(matches),                        # Faces Detected
                    
                        "\n".join(matched_faceids),          # Face IDs Matched (new line)
                        "\n".join(matched_external),         # External Face IDs (new line)
                        "\n".join(copied_to),                # Copied to Folders (new line)
                    ])
                    new_processed_ids.add(file_id)
                    save_processed_ids_to_s3(new_processed_ids)




            finally:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)

    # -------------------------------
    # Write report to Uploaded Data
    # -------------------------------
    if report_rows:
        sheets.spreadsheets().values().append(
            spreadsheetId=MASTERSHEET_ID,
            range=f"{UPLOADED_DATA_SHEET}!A1",
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": report_rows},
        ).execute()
