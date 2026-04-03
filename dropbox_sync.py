"""Dropbox integration — sync local space_files folder with Dropbox."""

import os
from config import DROPBOX_ACCESS_TOKEN, FILES_DIR

try:
    import dropbox
    from dropbox.exceptions import ApiError
    DROPBOX_AVAILABLE = True
except ImportError:
    DROPBOX_AVAILABLE = False


def _get_client():
    if not DROPBOX_AVAILABLE:
        raise RuntimeError("dropbox package not installed")
    if not DROPBOX_ACCESS_TOKEN:
        raise RuntimeError("DROPBOX_ACCESS_TOKEN not set in config.py")
    return dropbox.Dropbox(DROPBOX_ACCESS_TOKEN)


def upload_file(local_path: str, dropbox_path: str = None) -> bool:
    """Upload a single local file to Dropbox.

    Args:
        local_path:    Full local path to file.
        dropbox_path:  Destination path in Dropbox (e.g. '/local_helper/file.txt').
                       Defaults to '/local_helper/<filename>'.
    """
    if not os.path.exists(local_path):
        return False
    if dropbox_path is None:
        filename = os.path.basename(local_path)
        dropbox_path = f"/local_helper/{filename}"
    try:
        dbx = _get_client()
        with open(local_path, "rb") as f:
            dbx.files_upload(f.read(), dropbox_path, mode=dropbox.files.WriteMode.overwrite)
        return True
    except Exception:
        return False


def sync_folder(local_folder: str = FILES_DIR, dropbox_folder: str = "/local_helper") -> dict:
    """Upload all files in local_folder to Dropbox.

    Returns:
        Dict with 'uploaded' and 'failed' lists.
    """
    result = {"uploaded": [], "failed": []}
    if not os.path.exists(local_folder):
        os.makedirs(local_folder, exist_ok=True)
    for fname in os.listdir(local_folder):
        local_path = os.path.join(local_folder, fname)
        if os.path.isfile(local_path):
            dropbox_path = f"{dropbox_folder}/{fname}"
            ok = upload_file(local_path, dropbox_path)
            (result["uploaded"] if ok else result["failed"]).append(fname)
    return result


def download_file(dropbox_path: str, local_path: str) -> bool:
    """Download a file from Dropbox to a local path."""
    try:
        dbx = _get_client()
        _, res = dbx.files_download(dropbox_path)
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        with open(local_path, "wb") as f:
            f.write(res.content)
        return True
    except Exception:
        return False
