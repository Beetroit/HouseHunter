class ServiceException(Exception):
    """Base class for service layer exceptions."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class UserNotFoundException(ServiceException):
    """Raised when a user is not found."""

    def __init__(self, message: str = "User not found", status_code: int = 404):
        super().__init__(message, status_code)


class EmailAlreadyExistsException(ServiceException):
    """Raised when trying to register with an existing email."""

    def __init__(
        self, message: str = "Email already exists", status_code: int = 409
    ):  # 409 Conflict
        super().__init__(message, status_code)


class InvalidCredentialsException(ServiceException):
    """Raised during login with incorrect credentials."""

    def __init__(
        self, message: str = "Invalid email or password", status_code: int = 401
    ):  # 401 Unauthorized
        super().__init__(message, status_code)


class PropertyNotFoundException(ServiceException):
    """Raised when a property is not found."""

    def __init__(self, message: str = "Property not found", status_code: int = 404):
        super().__init__(message, status_code)


class UnauthorizedException(ServiceException):
    """Raised when a user is not authorized to perform an action."""

    def __init__(
        self, message: str = "Unauthorized action", status_code: int = 403
    ):  # 403 Forbidden
        super().__init__(message, status_code)


class PaymentException(ServiceException):
    """Raised for payment processing errors."""

    def __init__(
        self, message: str = "Payment processing failed", status_code: int = 400
    ):
        super().__init__(message, status_code)


class ChatException(ServiceException):
    """Raised for chat-related errors."""

    def __init__(self, message: str = "Chat operation failed", status_code: int = 400):
        super().__init__(message, status_code)


class InvalidRequestException(ServiceException):
    """Raised for general invalid requests to the service layer."""

    def __init__(self, message: str = "Invalid request data", status_code: int = 400):
        super().__init__(message, status_code)


class StorageException(ServiceException):
    """Base exception for storage related errors."""

    def __init__(
        self, message: str = "Storage operation failed", status_code: int = 500
    ):  # Default to 500 for storage issues
        super().__init__(message, status_code)


class FileNotAllowedException(StorageException):
    """Raised when an uploaded file type is not allowed."""

    def __init__(
        self, message: str = "File type not allowed", status_code: int = 400
    ):  # 400 Bad Request for invalid file type
        super().__init__(message, status_code)


class ChatNotFoundException(ServiceException):
    """Raised when a chat session is not found."""

    def __init__(self, message: str = "Chat not found", status_code: int = 404):
        super().__init__(message, status_code)


class ReviewExistsException(ServiceException):
    """Raised when a user tries to review the same agent twice."""

    def __init__(
        self,
        message: str = "Review already submitted for this agent",
        status_code: int = 409,
    ):  # 409 Conflict
        super().__init__(message, status_code)


class FavoriteAlreadyExistsException(ServiceException):
    """Raised when trying to add a favorite that already exists."""

    def __init__(
        self, message: str = "Property already favorited", status_code: int = 409
    ):  # 409 Conflict
        super().__init__(message, status_code)


class FavoriteNotFoundException(ServiceException):
    """Raised when trying to remove a favorite that does not exist."""

    def __init__(
        self, message: str = "Favorite not found", status_code: int = 404
    ):  # 404 Not Found
        super().__init__(message, status_code)
