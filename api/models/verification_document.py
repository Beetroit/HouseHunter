import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl
from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from models.property import Property
    from models.user import User


# --- Enums ---
class DocumentType(str, Enum):
    PROOF_OF_OWNERSHIP = "proof_of_ownership"
    LISTER_IDENTIFICATION = "lister_identification"
    OTHER = "other"


# --- SQLAlchemy Model ---
class VerificationDocument(Base):
    """Represents a document uploaded for property verification."""

    __tablename__ = "verification_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, index=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "properties.id", name="fk_verification_documents_property_id_properties"
        ),
        index=True,
        nullable=False,
    )
    uploader_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", name="fk_verification_documents_uploader_id_users"),
        index=True,
        nullable=False,
    )
    document_type: Mapped[DocumentType] = mapped_column(
        SQLAlchemyEnum(DocumentType), nullable=False, index=True
    )
    file_url: Mapped[str] = mapped_column(
        String(512), nullable=False
    )  # URL from storage
    filename: Mapped[str] = mapped_column(
        String(255), nullable=False
    )  # Filename in storage (for deletion/reference)
    description: Mapped[Optional[str]] = mapped_column(Text)  # Optional description
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        "Property", back_populates="verification_documents"
    )  # type: ignore[name-defined]
    uploader: Mapped["User"] = relationship(
        "User"
    )  # Basic relationship, no back_populates needed unless User tracks uploaded docs

    def __repr__(self):
        return f"<VerificationDocument(id={self.id}, property_id={self.property_id}, type='{self.document_type.value}')>"


# --- Pydantic Schemas ---


class VerificationDocumentBase(BaseModel):
    document_type: DocumentType = Field(..., example=DocumentType.PROOF_OF_OWNERSHIP)
    description: Optional[str] = Field(None, example="Title deed scan")


# No Create Request here, creation happens via file upload endpoint


class VerificationDocumentResponse(VerificationDocumentBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    property_id: uuid.UUID
    uploader_id: uuid.UUID
    file_url: HttpUrl  # Validate as URL
    filename: str
    uploaded_at: datetime
    # Consider adding uploader details if needed:
    # uploader: Optional[UserResponse] = None # Requires UserResponse import and relationship loading
