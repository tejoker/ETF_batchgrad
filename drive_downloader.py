"""
Google Drive CV downloader using a Service Account.

Required .env variables:
    GOOGLE_SERVICE_ACCOUNT_JSON=/path/to/service_account.json
    GOOGLE_DRIVE_FOLDER_ID=1AbCdEfGhIjKlMnOpQrStUvWxYz

Setup steps:
    1. Go to console.cloud.google.com, create a project, enable the Google Drive API.
    2. Create a Service Account (IAM & Admin > Service Accounts).
    3. Download the JSON key file and set GOOGLE_SERVICE_ACCOUNT_JSON to its path.
    4. Share the Drive folder with the service account's email address (Viewer role is enough).
    5. Set GOOGLE_DRIVE_FOLDER_ID to the folder ID from the folder's URL.
"""

import os
import io
from typing import List, Dict, Optional

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveDownloader:
    def __init__(self, credentials_json: str, folder_id: str):
        """
        Args:
            credentials_json: Path to the service account JSON key file.
            folder_id: Google Drive folder ID (from the folder's URL).
        """
        self.credentials_json = credentials_json
        self.folder_id = folder_id
        self.service = None

    def authenticate(self) -> None:
        """Authenticate using the service account and build the Drive API client."""
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_json, scopes=SCOPES
        )
        self.service = build("drive", "v3", credentials=credentials)
        print("[Drive] Authenticated successfully.")

    def list_files(self, mime_type: str = "application/pdf") -> List[Dict]:
        """
        List files in the configured folder.

        Args:
            mime_type: Filter by MIME type. Defaults to PDF only.

        Returns:
            List of dicts with keys: id, name, createdTime, size (if available).
        """
        if not self.service:
            raise RuntimeError("Call authenticate() before list_files().")

        query = f"'{self.folder_id}' in parents and mimeType='{mime_type}' and trashed=false"
        results = []
        page_token = None

        while True:
            response = self.service.files().list(
                q=query,
                fields="nextPageToken, files(id, name, createdTime, size)",
                pageToken=page_token,
                orderBy="createdTime desc"
            ).execute()

            results.extend(response.get("files", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return results

    def download_file(self, file_id: str, dest_path: str) -> str:
        """
        Download a Drive file to a local path.

        Args:
            file_id: Google Drive file ID.
            dest_path: Full local path to write the file.

        Returns:
            The dest_path on success.
        """
        if not self.service:
            raise RuntimeError("Call authenticate() before download_file().")

        os.makedirs(os.path.dirname(dest_path), exist_ok=True) if os.path.dirname(dest_path) else None

        request = self.service.files().get_media(fileId=file_id)
        buffer = io.BytesIO()
        downloader = MediaIoBaseDownload(buffer, request)

        done = False
        while not done:
            _, done = downloader.next_chunk()

        with open(dest_path, "wb") as f:
            f.write(buffer.getvalue())

        return dest_path

    def sync_folder(self, dest_dir: str) -> List[str]:
        """
        Download all PDFs from the configured Drive folder that are not already present locally.
        Idempotent: files already in dest_dir (matched by filename) are skipped.

        Args:
            dest_dir: Local directory to download files into.

        Returns:
            List of local paths of newly downloaded files.
        """
        if not self.service:
            self.authenticate()

        os.makedirs(dest_dir, exist_ok=True)
        existing = {f for f in os.listdir(dest_dir) if os.path.isfile(os.path.join(dest_dir, f))}

        remote_files = self.list_files()
        print(f"[Drive] Found {len(remote_files)} PDF(s) in folder.")

        downloaded = []
        for f in remote_files:
            name = f["name"]
            if name in existing:
                print(f"[Drive] Skipping {name} (already downloaded).")
                continue

            dest_path = os.path.join(dest_dir, name)
            print(f"[Drive] Downloading {name}...")
            try:
                self.download_file(f["id"], dest_path)
                downloaded.append(dest_path)
                print(f"[Drive] Saved to {dest_path}.")
            except Exception as e:
                print(f"[Drive] Error downloading {name}: {e}")

        print(f"[Drive] Sync complete. {len(downloaded)} new file(s) downloaded.")
        return downloaded


def get_downloader_from_env() -> Optional[DriveDownloader]:
    """
    Convenience factory that reads credentials from environment variables.
    Returns None if the required env vars are not set.
    """
    creds = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
    folder = os.environ.get("GOOGLE_DRIVE_FOLDER_ID", "")
    if not creds or not folder:
        return None
    return DriveDownloader(credentials_json=creds, folder_id=folder)
