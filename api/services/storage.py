import abc
import os
import uuid
from typing import BinaryIO

import aiofiles
from azure.storage.blob.aio import BlobClient, BlobServiceClient
from quart import current_app
from werkzeug.utils import secure_filename

# Define allowed extensions (consider moving to config)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


class StorageException(Exception):
    """Base exception for storage errors."""

    pass


class FileNotAllowedException(StorageException):
    """Raised when file type is not allowed."""

    pass


class StorageInterface(abc.ABC):
    """Abstract base class for storage implementations."""

    @abc.abstractmethod
    async def save(self, file_storage, original_filename: str) -> tuple[str, str]:
        """
        Saves the file and returns a tuple of (public_url, internal_filename).
        'file_storage' is expected to be a file-like object (e.g., from request.files).
        'original_filename' is the filename provided by the client.
        """
        pass

    @abc.abstractmethod
    async def delete(self, filename: str) -> None:
        """Deletes the file identified by the internal filename."""
        pass

    @abc.abstractmethod
    def get_url(self, filename: str) -> str:
        """Gets the public URL for a stored file."""
        pass


class LocalStorage(StorageInterface):
    """Stores files on the local filesystem."""

    def __init__(self, upload_folder: str, base_url: str = "/uploads"):
        self.upload_folder = upload_folder
        self.base_url = base_url  # Base URL path for accessing uploaded files
        # Ensure upload folder exists
        os.makedirs(self.upload_folder, exist_ok=True)
        current_app.logger.info(
            f"LocalStorage initialized with folder: {self.upload_folder}"
        )

    async def save(self, file_storage, original_filename: str) -> tuple[str, str]:
        if not allowed_file(original_filename):
            raise FileNotAllowedException(f"File type not allowed: {original_filename}")

        # Generate a secure, unique filename
        _, ext = os.path.splitext(original_filename)
        filename = secure_filename(f"{uuid.uuid4()}{ext}")
        save_path = os.path.join(self.upload_folder, filename)

        try:
            # Use aiofiles for async file writing
            async with aiofiles.open(save_path, "wb") as afp:
                # Read chunks to avoid loading large files into memory
                while True:
                    chunk = await file_storage.read(8192)  # Read in 8KB chunks
                    if not chunk:
                        break
                    await afp.write(chunk)

            public_url = self.get_url(filename)
            current_app.logger.info(
                f"Saved file locally: {filename} (URL: {public_url})"
            )
            return public_url, filename
        except Exception as e:
            current_app.logger.error(
                f"Failed to save file locally {filename}: {e}", exc_info=True
            )
            # Attempt cleanup if save failed partially
            if os.path.exists(save_path):
                try:
                    os.remove(save_path)
                except Exception as cleanup_e:
                    current_app.logger.error(
                        f"Failed to cleanup partially saved file {save_path}: {cleanup_e}"
                    )
            raise StorageException(f"Failed to save file locally: {e}") from e

    async def delete(self, filename: str) -> None:
        try:
            file_path = os.path.join(self.upload_folder, filename)
            if os.path.exists(file_path):
                # Use aiofiles for async delete? os.remove is blocking but might be acceptable.
                # For true async, consider asyncio.to_thread or a dedicated async library if available.
                # Using os.remove for simplicity here.
                os.remove(file_path)
                current_app.logger.info(f"Deleted local file: {filename}")
            else:
                current_app.logger.warning(
                    f"Attempted to delete non-existent local file: {filename}"
                )
        except Exception as e:
            current_app.logger.error(
                f"Failed to delete local file {filename}: {e}", exc_info=True
            )
            raise StorageException(f"Failed to delete file locally: {e}") from e

    def get_url(self, filename: str) -> str:
        # Returns a relative URL path. Assumes Quart serves the /uploads directory.
        # Ensure app is configured to serve static files from UPLOAD_FOLDER under /uploads path.
        return f"{self.base_url}/{filename}"


class AzureBlobStorage(StorageInterface):
    """Stores files in Azure Blob Storage."""

    def __init__(self, connection_string: str, container_name: str):
        if not connection_string:
            raise ValueError(
                "Azure connection string is required for AzureBlobStorage."
            )
        self.connection_string = connection_string
        self.container_name = container_name
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            # Try to create container if it doesn't exist (optional, requires permissions)
            # asyncio.run(self._create_container_if_not_exists()) # Can't run async in init easily
            current_app.logger.info(
                f"AzureBlobStorage initialized for container: {self.container_name}"
            )
        except Exception as e:
            current_app.logger.error(
                f"Failed to initialize Azure BlobServiceClient: {e}", exc_info=True
            )
            raise StorageException(
                f"Failed to initialize Azure BlobServiceClient: {e}"
            ) from e

    # Helper to create container (call from startup if needed)
    # async def _create_container_if_not_exists(self):
    #     try:
    #         async with self.blob_service_client.get_container_client(self.container_name) as client:
    #             # Check if exists? API might not have simple check, create might fail if exists
    #             pass
    #         await self.blob_service_client.create_container(self.container_name)
    #         current_app.logger.info(f"Azure container '{self.container_name}' created or already exists.")
    #     except Exception as e:
    #         # Handle potential errors like container already exists, auth issues etc.
    #         current_app.logger.warning(f"Could not ensure Azure container '{self.container_name}' exists: {e}")

    async def save(self, file_storage, original_filename: str) -> tuple[str, str]:
        if not allowed_file(original_filename):
            raise FileNotAllowedException(f"File type not allowed: {original_filename}")

        _, ext = os.path.splitext(original_filename)
        filename = secure_filename(f"{uuid.uuid4()}{ext}")  # Unique name for blob

        try:
            # Get a client for the specific blob
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=filename
            )

            # Upload the stream directly
            # file_storage.read() needs to be awaitable if it's an async stream
            # Assuming file_storage is from Quart request.files, which might need chunked reading
            # For simplicity, assuming upload_blob can handle the stream type or we read it first.
            # Reading entire file into memory - BEWARE OF LARGE FILES!
            # A chunked upload approach is better for large files.
            # file_content = await file_storage.read()
            # await blob_client.upload_blob(file_content, overwrite=True)

            # More robust chunked reading:
            await blob_client.upload_blob(
                file_storage, overwrite=True, length=file_storage.content_length
            )  # Pass length if known

            public_url = self.get_url(filename)
            current_app.logger.info(
                f"Uploaded file to Azure: {filename} (URL: {public_url})"
            )
            return public_url, filename

        except Exception as e:
            current_app.logger.error(
                f"Failed to upload file to Azure {filename}: {e}", exc_info=True
            )
            raise StorageException(f"Failed to upload file to Azure: {e}") from e
        finally:
            # Ensure blob_client is closed if necessary (usually handled by context manager if used)
            # await blob_client.close() # If needed
            pass

    async def delete(self, filename: str) -> None:
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name, blob=filename
            )
            await blob_client.delete_blob(delete_snapshots="include")
            current_app.logger.info(f"Deleted blob from Azure: {filename}")
        except Exception as e:
            # Handle cases where blob doesn't exist gracefully?
            current_app.logger.error(
                f"Failed to delete blob {filename} from Azure: {e}", exc_info=True
            )
            raise StorageException(f"Failed to delete file from Azure: {e}") from e
        finally:
            # await blob_client.close() # If needed
            pass

    def get_url(self, filename: str) -> str:
        # Construct the public URL for the blob
        # Ensure container has public access enabled or use SAS tokens for private access
        return f"{self.blob_service_client.url}{self.container_name}/{filename}"


# --- Storage Manager Factory ---


def get_storage_manager(config) -> StorageInterface:
    """
    Factory function to create the appropriate storage manager based on config.
    """
    if config.AZURE_STORAGE_CONNECTION_STRING:
        current_app.logger.info("Using Azure Blob Storage for uploads.")
        return AzureBlobStorage(
            connection_string=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=config.AZURE_STORAGE_CONTAINER_NAME,
        )
    else:
        current_app.logger.info("Using Local File Storage for uploads.")
        # Ensure UPLOAD_FOLDER is absolute or relative to a known location
        upload_path = config.UPLOAD_FOLDER
        if not os.path.isabs(upload_path):
            # Assuming config.py is in 'api/', make path relative to project root or api/
            # This might need adjustment based on where hypercorn is run from.
            # Let's assume relative to api/ for now.
            api_dir = os.path.dirname(__file__)  # Directory of storage.py
            upload_path = os.path.abspath(os.path.join(api_dir, upload_path))

        return LocalStorage(upload_folder=upload_path)
