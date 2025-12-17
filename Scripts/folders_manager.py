from .gdrive_helpers import get_drive_service
from .config import PROJECT_ROOT_FOLDER_ID
from .refs_manager import get_mastersheet_rows


def clean_name(name: str) -> str:
    """
    Normalize names to match refs / rekognition naming.
    Example: 'Aaradhya Choudhary' -> 'Aaradhya_Choudhary'
    """
    return "_".join(name.strip().split())


def get_or_create_drive_folder(service, name, parent_id):
    """
    Returns Google Drive folder ID if it exists,
    otherwise creates it under the given parent.

    Shared Drive compatible.
    """

    query = (
        f"name='{name}' and "
        f"mimeType='application/vnd.google-apps.folder' and "
        f"'{parent_id}' in parents and trashed=false"
    )

    # 🔹 LIST folders (Shared Drive safe)
    resp = service.files().list(
        q=query,
        fields="files(id, name)",
        supportsAllDrives=True,
        includeItemsFromAllDrives=True
    ).execute()

    files = resp.get("files", [])
    if files:
        return files[0]["id"]

    metadata = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
        "parents": [parent_id]
    }

    # 🔹 CREATE folder (Shared Drive safe)
    folder = service.files().create(
        body=metadata,
        fields="id",
        supportsAllDrives=True
    ).execute()

    return folder["id"]


def create_output_structure():
    """
    Creates Google Drive folder structure:

    Project Folders
      └── Output_Folders
            └── Class-Section
                  └── SrNo-Name-Class-Section
    """

    service = get_drive_service()
    rows = get_mastersheet_rows()

    if not rows:
        return

    # 🔹 Always ensure Output_Folders exists under Project Root
    output_root_id = get_or_create_drive_folder(
        service,
        "Output_Folders",
        PROJECT_ROOT_FOLDER_ID
    )

    for row in rows:
        if len(row) < 4:
            continue

        srno = row[0].strip()
        name = row[1].strip()
        class_ = row[2].strip()
        section = row[3].strip()

        if not (srno and name and class_ and section):
            continue

        class_section = f"{class_}-{section}"
        student_folder = f"{srno}-{clean_name(name)}-{class_}-{section}"

        # 🔹 Create Class-Section folder
        class_folder_id = get_or_create_drive_folder(
            service,
            class_section,
            output_root_id
        )

        # 🔹 Create Student folder inside Class-Section
        get_or_create_drive_folder(
            service,
            student_folder,
            class_folder_id
        )
