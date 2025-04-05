from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from .property import (  # Import Property for relationship and simple response
        Property,
        PropertyResponseSimple,
    )
    from .user import (  # Import User for relationship and simple response
        User,
        UserResponseSimple,
    )


class MaintenanceRequestStatus(str, Enum):
    SUBMITTED = "SUBMITTED"  # Tenant submitted, awaiting landlord review
    IN_PROGRESS = "IN_PROGRESS"  # Landlord acknowledged, work underway
    RESOLVED = (
        "RESOLVED"  # Work completed, awaiting tenant confirmation (optional step)
    )
    CLOSED = "CLOSED"  # Issue resolved and confirmed by tenant/landlord, or cancelled
    CANCELLED = "CANCELLED"  # Request cancelled by tenant or landlord


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id"), nullable=False, index=True
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # User who submitted
    landlord_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )  # User responsible (owner/agent)

    title: Mapped[str] = mapped_column(
        String(200), nullable=False
    )  # Short title of the issue
    description: Mapped[str] = mapped_column(Text, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(
        String(512), nullable=True
    )  # Optional photo of the issue
    status: Mapped[MaintenanceRequestStatus] = mapped_column(
        SQLAlchemyEnum(MaintenanceRequestStatus),
        nullable=False,
        default=MaintenanceRequestStatus.SUBMITTED,
        index=True,
    )
    resolution_notes: Mapped[Optional[str]] = mapped_column(
        Text, nullable=True
    )  # Notes from landlord on resolution

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    closed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        back_populates="maintenance_requests"
    )  # Add back_populates later
    tenant: Mapped["User"] = relationship(
        foreign_keys=[tenant_id], back_populates="submitted_maintenance_requests"
    )  # Add back_populates later
    landlord: Mapped["User"] = relationship(
        foreign_keys=[landlord_id], back_populates="assigned_maintenance_requests"
    )  # Add back_populates later

    def to_dict(self):
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "tenant_id": str(self.tenant_id),
            "landlord_id": str(self.landlord_id),
            "title": self.title,
            "description": self.description,
            "photo_url": self.photo_url,
            "status": self.status.value,
            "resolution_notes": self.resolution_notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }


# --- Pydantic Schemas ---


class MaintenanceRequestBase(BaseModel):
    property_id: uuid.UUID  # Tenant needs to specify which property
    title: str = Field(..., min_length=5, max_length=200)
    description: str = Field(..., min_length=10)
    photo_url: Optional[str] = None  # Assume URL is provided after upload elsewhere


class MaintenanceRequestCreate(MaintenanceRequestBase):
    # tenant_id is inferred from logged-in user
    pass


class MaintenanceRequestUpdate(BaseModel):  # For landlord/admin updates
    status: Optional[MaintenanceRequestStatus] = None
    resolution_notes: Optional[str] = None


class MaintenanceRequestResponse(BaseModel):
    id: uuid.UUID
    property: PropertyResponseSimple  # Use simple response
    tenant: UserResponseSimple  # Use simple response
    landlord: UserResponseSimple  # Use simple response
    title: str
    description: str
    photo_url: Optional[str] = None
    status: MaintenanceRequestStatus
    resolution_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
