# config.py
# Central configuration and env variable bindings.
# Customize only via environment variables in the container/task definition.

import os

# Google credentials: prefer JSON string in env var GOOGLE_CREDENTIALS_JSON_CONTENT
GOOGLE_SERVICE_ACCOUNT_INFO = {
    "type": "service_account",
  "project_id": "mediaportfolioautomation",
  "private_key_id": "6f3efe66e42f2daa3ff6cb5df85744a99da22700",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCoXGTLd2/bkPHK\nNZqWgSPlsU2o7Zf5HMeJz5+v1wGlJPPO2eRVXFsmviT/ccVf+ncWylmseVB7NezK\nK3thW1I4kfyjoEPpxECBlUHs1WpDb/WcFOs5HsGEEVIDIlsnSuj32fDuEdzItMIU\n1b1oHd2BacVuhV/476qWKp9XnQkJoSseR5gb8HirpyX7d/RwmepIhu6SLgO40zIk\nf8TQx45NCjgk/WeC115uPI2hVzvTrrt7V4g9nvhTBDFmCrdZrL4peMUD1cELDePt\n8FfRwxMJ1XtY6wxE2oszXECO6A6FIMVfg0fLd0tprKX2Xq6Icp86nxBw6hE3QS2a\nVU5rDNZBAgMBAAECggEAS1ou8rHeKpNQ5IPhUIM0IdWdQII2hpRO6ms2uWitn9BO\nHsJ+44WWdlycCohNIovjSRv/zqXtU3frJwEXE5ff0NnmDQXp33KqvFSlUO6jxNMT\nRmxGayZMzmNCJYz25zsr0eKFZsgv3NSqGNEhGLxlK0q/xpuDPNNnshYZgwkRxnDW\nBEDa4j9QHpcwSVmdMau6MlVQEzeEUwdQYIq3BwEz4k27vo8OBl6GZY8jtXQiSr9W\ndbwdCMnS/Ij1tfzUEnSkk4xUHAIdh5KIlIOnJKiGQPpwDWSIjXLrKco4kOM/zXFH\nWIcKAt8LEuYdwaBy36vJZX5vw6hSUtXH0mdWgOVoUQKBgQDV3zO6dEVaARENZFtS\nBpnsyK2bv3JMEFwHaU0UvAPDyZh6Vq236qKYCW5FU6q7RsLirtaJsG8sQbcUMQXN\nRTZtAaeYFpon4joIArEytKfIYB60CP5SXZ58+glg+RdJ48jU3Am4Hk8wEz+/C59Z\nG/ZHa3cWj+1NfHX0c932mANZLwKBgQDJhjxD2Knyc+wXQkwXOz8cIgxXiBAZvB+U\nyogeNZQuvw7AdOFu0qRO0u+Bnx8vmjVA5KO9v9og2FPVDlDlnhvWRK4pvzN8TvwB\nSBtmQRo4Ct1Gqvd2MbQkmHF4MAR/64Tut6U/S5tmV/xqAkII7vVnZzGQx4lnA6bJ\nyJlEsPcLjwKBgQCam+WYR8+O1jCOntsJfC4wJ46hhg/JfxYYYX5Qm+6YzhbFcf3Z\nc+ygvkiSI37MLcZa+wuqs/paYxNHrHzGPN+wg761SrmcVYWgHtocjs6wIxRvEAVS\nY81cCaFYEhpM1zdq8bqw+HBEj9XIdU13rKgoTz7i958UIgJfepeeWZwqDwKBgQCs\nuJpqZAa0wNo2zSG+P49Fo4EEfJ+gDvbaZgPoMG/C6QnRtduJSox86plQdXsbJ4ZB\nCjW06fwgbojbcJuxUaP2L4M+UJvmDSQ8TPr+1wmLwvQIH3xdFxiYzPdj1XPl14xl\ntYyyBTE5tGuoyCqk0XoPmAiJWBvR6PVIuN90WmBCzQKBgAp2OIUb0DNGxrp5X/jD\nbngkl9zU8kaF6BSfkJ3FwvzKjEMixcdPinwGzf3+lPAQxJP/ZfUiS/FUBV/eiqlY\nf9EF4j5IJGg1gnTM03+L8qpwQXL69Y+HQI6asQ3G79Akwr/Wdahq3u8ANl0yr6Q5\nJ7h1CobhIdbOUyqG0n4yCsJE\n-----END PRIVATE KEY-----\n",
  "client_email": "media-automation-sa@mediaportfolioautomation.iam.gserviceaccount.com",
  "client_id": "108007230247315878584",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/media-automation-sa%40mediaportfolioautomation.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
GOOGLE_CREDENTIALS_JSON_FILE = os.environ.get("GOOGLE_CREDENTIALS_JSON", "credentials.json")  # fallback (not used in cloud)

MASTERSHEET_ID = os.environ.get(
    "MP_MASTERSHEET_ID",
    "1Q0-14NJLQ5q-alqCKXc5fNAUUzrXo91sfpHc6kNJtuA"
)
MASTERSHEET_NAME = os.environ.get("MP_MASTERSHEET_NAME", "Mastersheet")
VALIDATION_SHEET_NAME = os.environ.get("MP_VALIDATION_SHEET_NAME", "Validation")
UPLOADED_DATA_SHEET = os.environ.get("MP_UPLOADED_DATA_SHEET", "Uploaded Data")

# -------- GOOGLE DRIVE STRUCTURE (CRITICAL) --------

# Drive folder ID of "Project Folders"
PROJECT_ROOT_FOLDER_ID = os.environ.get(
    "MP_PROJECT_ROOT_FOLDER_ID",
    "1XjPhRjgQppoACpfuFhhkJ3iOD6VpyNeH"
)

# Drive folder ID of "Output_Folders" (inside Project Folders)
OUTPUT_ROOT_FOLDER_ID = os.environ.get(
    "MP_OUTPUT_ROOT_FOLDER_ID",
    "1GrC6e-jbgyIWfkrJwv1gIVVjt1gh0E4M"
)

# AWS & Rekognition
S3_BUCKET = os.environ.get("MP_S3_BUCKET", "media-portfolio-students")
AWS_REGION = os.environ.get("MP_AWS_REGION", "ap-south-1")
REKOG_COLLECTION = os.environ.get("MP_REKOG_COLLECTION", "StudentCollection")

# Storage keys in S3 for persistent state
MP_PROCESSED_TRACKER_KEY = os.environ.get("MP_PROCESSED_TRACKER_KEY", "state/processed_drive_files.json")
MP_FACE_MAP_KEY = os.environ.get("MP_FACE_MAP_KEY", "state/faceid_map.csv")

# Rekognition threshold
MIN_FACE_MATCH_CONFIDENCE = int(os.environ.get("MIN_FACE_MATCH_CONFIDENCE", "85"))

# ExternalImageId format
EXTERNAL_ID_FORMAT = "{srno}_{name}_{class_name}_{section}"

# Controls
SKIP_ALREADY_INDEXED = os.environ.get("SKIP_ALREADY_INDEXED", "true").lower() in ("1","true","yes")
