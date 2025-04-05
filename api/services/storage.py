import abc
import os
import uuid
from typing import Optional, Tuple, Type

import rich
from azure.core.exceptions import ResourceExistsError, ResourceNotFoundError
from azure.storage.blob import PublicAccess
from azure.storage.blob.aio import BlobClient, BlobServiceClient, ContainerClient
from quart import current_app
from quart.datastructures import FileStorage
from werkzeug.utils import secure_filename

# Define allowed extensions (consider moving to config)
ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "gif",
    "webp",
    "pdf",
    "doc",
    "docx",
}  # Added document types


def allowed_file(filename: str) -> bool:
    """Check if the file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


# --- Custom Storage Exceptions ---


class StorageException(Exception):
    """Base exception for storage errors."""

    pass


class FileNotAllowedException(StorageException):
    """Raised when file type is not allowed."""

    pass


# Azure Specific Exceptions
class BlobStorageError(StorageException):
    """Base exception for Azure Blob Service errors."""

    pass


class BlobInitializationError(BlobStorageError):
    """Error during Azure client or container initialization."""

    pass


class BlobUploadError(BlobStorageError):
    """Error during Azure blob upload."""

    pass


class BlobDeleteError(BlobStorageError):
    """Error during Azure blob deletion (other than not found)."""

    pass


class BlobNotFoundError(BlobStorageError, FileNotFoundError):
    """Specific error for when an Azure blob is not found."""

    pass


# --- Storage Interface ---


class StorageInterface(abc.ABC):
    """
    Abstract base class for storage implementations.
    Implementations should support async context management (`async with`).
    """

    @abc.abstractmethod
    async def __aenter__(self) -> "StorageInterface":
        """Enter the runtime context related to this object."""
        pass

    @abc.abstractmethod
    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Type],
    ) -> Optional[bool]:
        """Exit the runtime context related to this object."""
        pass

    @abc.abstractmethod
    async def save(self, file_storage, original_filename: str) -> Tuple[str, str]:
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


# --- Local Storage Implementation ---


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

    async def __aenter__(self) -> "LocalStorage":
        """Enter context, no specific action needed for local storage."""
        current_app.logger.debug("Entering LocalStorage context.")
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Type],
    ) -> Optional[bool]:
        """Exit context, no specific cleanup needed for local storage."""
        current_app.logger.debug("Exiting LocalStorage context.")
        return None  # Propagate exceptions if any

    async def save(
        self, file_storage: FileStorage, original_filename: str
    ) -> Tuple[str, str]:
        if not allowed_file(original_filename):
            raise FileNotAllowedException(f"File type not allowed: {original_filename}")

        # Generate a secure, unique filename
        _, ext = os.path.splitext(original_filename)
        filename = secure_filename(f"{uuid.uuid4()}{ext}")
        save_path = os.path.join(self.upload_folder, filename)

        try:
            # Use the built-in async save method of quart.datastructures.FileStorage
            await file_storage.save(save_path)
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
                # Using os.remove for simplicity here. Consider asyncio.to_thread for true async.
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
        return f"{self.base_url}/{filename}"


# --- Azure Blob Storage Implementation ---


class AzureBlobStorage(StorageInterface):
    """Stores files in Azure Blob Storage using an async context manager."""

    def __init__(self, connection_string: str, container_name: str):
        if not connection_string:
            raise ValueError(
                "Azure connection string is required for AzureBlobStorage."
            )
        self.connection_string = connection_string
        self.container_name = container_name
        self.blob_service_client: Optional[BlobServiceClient] = None
        self.container_client: Optional[ContainerClient] = None
        current_app.logger.info(
            f"AzureBlobStorage instance created for container: {self.container_name}. Use 'async with' to initialize."
        )

    async def __aenter__(self) -> "AzureBlobStorage":
        """Initializes clients and container connection."""
        if self.blob_service_client:
            current_app.logger.warning(
                f"AzureBlobStorage context entered again for {self.container_name} without exiting previous."
            )
            return self

        current_app.logger.info(
            f"Entering AzureBlobStorage context for {self.container_name}..."
        )
        try:
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            self.container_client = await self._get_or_create_container()
            current_app.logger.info(
                f"AzureBlobStorage context entered and initialized for container: {self.container_name}"
            )
            return self
        except BlobInitializationError:
            raise
        except Exception as e:
            current_app.logger.error(
                f"Failed to initialize Azure Blob Storage client/container: {e}",
                exc_info=True,
            )
            # Ensure cleanup happens if partially initialized
            await self.__aexit__(type(e), e, e.__traceback__)
            raise BlobInitializationError(
                f"Failed to initialize Azure Blob Storage: {e}"
            ) from e

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[Type],
    ) -> Optional[bool]:
        """Closes clients and connections."""
        current_app.logger.info(
            f"Exiting AzureBlobStorage context for container: {self.container_name}."
        )
        closed_container = False
        closed_service = False

        if self.container_client:
            try:
                await self.container_client.close()
                closed_container = True
                current_app.logger.debug(
                    f"Closed Azure ContainerClient for {self.container_name}"
                )
            except Exception as e:
                current_app.logger.error(
                    f"Error closing Azure ContainerClient for {self.container_name}: {e}",
                    exc_info=True,
                )
            finally:
                self.container_client = None

        if self.blob_service_client:
            try:
                await self.blob_service_client.close()
                closed_service = True
                current_app.logger.debug("Closed Azure BlobServiceClient")
            except Exception as e:
                current_app.logger.error(
                    f"Error closing Azure BlobServiceClient: {e}", exc_info=True
                )
            finally:
                self.blob_service_client = None

        # Return None to propagate exceptions if any occurred within the 'with' block
        return None

    async def _get_or_create_container(self) -> ContainerClient:
        """Gets or creates the Azure container."""
        if not self.blob_service_client:
            raise BlobInitializationError(
                "BlobServiceClient not initialized before getting container."
            )

        container_client = self.blob_service_client.get_container_client(
            self.container_name
        )
        try:
            await container_client.create_container(public_access=PublicAccess.BLOB)
            current_app.logger.info(f"Created Azure container: {self.container_name}")
        except ResourceExistsError:
            current_app.logger.info(
                f"Using existing Azure container: {self.container_name}"
            )
        except Exception as e:
            current_app.logger.error(
                f"Failed to get or create Azure container '{self.container_name}': {e}",
                exc_info=True,
            )
            raise BlobInitializationError(
                f"Failed to get or create container '{self.container_name}': {e}"
            ) from e
        return container_client

    def _get_blob_client(self, blob_name: str) -> BlobClient:
        """Gets a BlobClient for a specific blob."""
        if not self.container_client:
            raise BlobInitializationError(
                "ContainerClient not initialized. Ensure 'async with' context is active."
            )
        return self.container_client.get_blob_client(blob_name)

    async def save(
        self, file_storage: FileStorage, original_filename: str
    ) -> Tuple[str, str]:
        if not self.container_client:  # Check if context is active
            raise BlobInitializationError(
                "Cannot save file, Azure storage context not active."
            )
        if not allowed_file(original_filename):
            raise FileNotAllowedException(f"File type not allowed: {original_filename}")

        _, ext = os.path.splitext(original_filename)
        filename = secure_filename(f"{uuid.uuid4()}{ext}")  # Unique name for blob

        try:
            blob_client = self._get_blob_client(filename)
            async with blob_client:
                file_data = file_storage.stream.read(-1)
                content_length = len(file_data)
                rich.print(len(file_data), content_length)
                await blob_client.upload_blob(
                    file_data, overwrite=True, length=content_length
                )

            public_url = self.get_url(filename)
            current_app.logger.info(
                f"Uploaded file to Azure: {filename} (URL: {public_url})"
            )
            return public_url, filename

        except Exception as e:
            current_app.logger.error(
                f"Failed to upload file '{original_filename}' to Azure blob '{filename}': {e}",
                exc_info=True,
            )
            raise BlobUploadError(
                f"Failed to upload file '{original_filename}' to Azure blob '{filename}': {e}"
            ) from e

    async def delete(self, filename: str) -> None:
        if not self.container_client:  # Check if context is active
            raise BlobInitializationError(
                "Cannot delete file, Azure storage context not active."
            )
        try:
            blob_client = self._get_blob_client(filename)
            async with blob_client:
                await blob_client.delete_blob(delete_snapshots="include")
            current_app.logger.info(f"Deleted blob from Azure: {filename}")
        except ResourceNotFoundError:
            current_app.logger.warning(
                f"Blob not found during delete attempt, skipping: {filename}"
            )
        except Exception as e:
            current_app.logger.error(
                f"Failed to delete blob {filename} from Azure: {e}", exc_info=True
            )
            raise BlobDeleteError(
                f"Failed to delete blob '{filename}' from Azure: {e}"
            ) from e

    def get_url(self, filename: str) -> str:
        if not self.blob_service_client:  # Check if context is active/initialized
            raise BlobInitializationError(
                "Cannot get URL, Azure storage context not active or initialized."
            )
        return f"{self.blob_service_client.url}{self.container_name}/{filename}"


# --- Storage Manager Factory ---


def get_storage_manager(config) -> StorageInterface:
    """
    Factory function to create the appropriate storage manager based on config.
    All returned storage managers should be used with 'async with'.
    """
    if config.AZURE_STORAGE_CONNECTION_STRING:
        current_app.logger.info(
            "Creating Azure Blob Storage manager (requires 'async with' usage)."
        )
        return AzureBlobStorage(
            connection_string=config.AZURE_STORAGE_CONNECTION_STRING,
            container_name=config.AZURE_STORAGE_CONTAINER_NAME,
        )
    else:
        current_app.logger.info(
            "Creating Local File Storage manager (requires 'async with' usage)."
        )
        upload_path = config.UPLOAD_FOLDER
        if not os.path.isabs(upload_path):
            upload_path = os.path.abspath(upload_path)

        return LocalStorage(upload_folder=upload_path, base_url=config.UPLOAD_URL_PATH)
