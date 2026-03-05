import os
import tempfile
from pydantic import BaseModel
from fastapi import BackgroundTasks
from google.oauth2 import service_account
from googleapiclient.discovery import build, Resource
from googleapiclient.http import MediaIoBaseDownload

from cat import endpoint, check_permissions, AuthorizedInfo, AuthPermission, AuthResource, CheshireCat
from cat.exceptions import CustomNotFoundException
from cat.utils import log


class DriveIngestRequest(BaseModel):
    drive_id: str


class DriveIngestResponse(BaseModel):
    drive_id: str
    message: str
    info: str


def get_drive_service(cat) -> Resource:
    settings = cat.mad_hatter.get_plugin().load_settings()
    if not settings.get("service_account_json"):
        raise ValueError("Google Service Account JSON not configured in the settings of the plugin.")

    creds = service_account.Credentials.from_service_account_info(settings["service_account_json"])
    return build("drive", "v3", credentials=creds)


async def process_and_ingest_recursive(service: Resource, item_id: str, cat: CheshireCat):
    """Download a file e recursively surf through folders."""
    item = service.files().get(fileId=item_id, fields='id, name, mimeType').execute()  # noqa

    if item["mimeType"] == "application/vnd.google-apps.folder":
        log.info(f"Explore the Google Drive folder: {item['name']}")
        query = f"'{item_id}' in parents and trashed = false"
        results = service.files().list(q=query, fields="files(id, name, mimeType)").execute()  # noqa
        for f in results.get("files", []):
            await process_and_ingest_recursive(service, f["id"], cat)

        return

    # It is a file: download it
    is_google_doc = "application/vnd.google-apps" in item["mimeType"]
    filename = item["name"]

    try:
        if is_google_doc:
            request = service.files().export_media(fileId=item_id, mimeType="application/pdf")  # noqa
            filename += ".pdf"
        else:
            request = service.files().get_media(fileId=item_id)  # noqa

        suffix = os.path.splitext(filename)[1] or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            downloader = MediaIoBaseDownload(tmp_file, request)  # type: ignore
            done = False
            while not done:
                _, done = downloader.next_chunk()
            tmp_path = tmp_file.name

        log.info(f"File downloaded: {filename}. Starting the ingestion to the RabbitHole.")

        # Pattern Grinning Cat Core: ingest_file requires cat and file path as arguments
        await cat.rabbit_hole.ingest_file(cat, tmp_path, metadata={"google_drive_id": item_id})

        # Post-ingestion cleanup
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    except Exception as e:
        log.error(f"Error during the ingestion of the file {filename}: {e}")


async def background_drive_task(drive_id: str, cat: CheshireCat):
    """Wrapper for the async execution"""
    try:
        service = get_drive_service(cat)
        await process_and_ingest_recursive(service, drive_id, cat)
        log.info(f"Task Google Drive completed for ID: {drive_id}")
    except Exception as e:
        log.error(f"Error in Background Task for Google Drive ID {drive_id}: {e}")


@endpoint.post("/drive/ingest", response_model=DriveIngestResponse)
async def ingest_from_drive(
    payload: DriveIngestRequest,
    background_tasks: BackgroundTasks,
    info: AuthorizedInfo = check_permissions(AuthResource.UPLOAD, AuthPermission.WRITE),
) -> DriveIngestResponse:
    if not info.cheshire_cat:
        raise CustomNotFoundException("Cheshire Cat instance not found.")

    background_tasks.add_task(background_drive_task, payload.drive_id, info.cheshire_cat)

    return DriveIngestResponse(
        drive_id=payload.drive_id,
        message="Ingestion started for the Drive object.",
        info="The processing of resource(s) is happening in the background. Check logs for details."
    )
