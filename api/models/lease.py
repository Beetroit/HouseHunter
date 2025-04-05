from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base
from models.property import (
    PropertyResponseSimple,
)
from models.user import (
    UserResponseSimple,
)

# fmt: off
if TYPE_CHECKING:
    from .property import Property
    from .user import User
# fmt: on


class LeaseStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    TERMINATED = "TERMINATED"
    PENDING = "PENDING"  # Added for leases not yet started or finalized


class Lease(Base):
    __tablename__ = "leases"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("properties.id"), nullable=False
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    landlord_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False
    )  # Often the property owner or agent

    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    rent_amount: Mapped[float] = mapped_column(Float, nullable=False)
    payment_day: Mapped[int] = mapped_column(
        nullable=False, default=1
    )  # Day of the month rent is due
    status: Mapped[LeaseStatus] = mapped_column(
        SQLAlchemyEnum(LeaseStatus), nullable=False, default=LeaseStatus.PENDING
    )
    document_url: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # URL to the signed lease document

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    property: Mapped["Property"] = relationship(
        back_populates="leases", foreign_keys=[property_id]
    )
    tenant: Mapped["User"] = relationship(
        foreign_keys=[tenant_id], back_populates="leases_as_tenant"
    )
    landlord: Mapped["User"] = relationship(
        foreign_keys=[landlord_id], back_populates="leases_as_landlord"
    )
    # rent_payments: Mapped[List["RentPayment"]] = relationship(back_populates="lease", cascade="all, delete-orphan") # Add when RentPayment model is created

    def to_dict(self):
        return {
            "id": str(self.id),
            "property_id": str(self.property_id),
            "tenant_id": str(self.tenant_id),
            "landlord_id": str(self.landlord_id),
            "start_date": self.start_date.isoformat(),
            "end_date": self.end_date.isoformat(),
            "rent_amount": self.rent_amount,
            "payment_day": self.payment_day,
            "status": self.status.value,
            "document_url": self.document_url,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class LeaseAgreementTemplate(Base):
    __tablename__ = "lease_agreement_templates"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )  # The template content (e.g., markdown, HTML)
    is_default: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "is_default": self.is_default,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            # Content excluded by default for brevity
        }


# --- Pydantic Schemas ---


class LeaseBase(BaseModel):
    property_id: uuid.UUID
    tenant_id: uuid.UUID
    # landlord_id will likely be inferred from the logged-in user or property owner
    start_date: date
    end_date: date
    rent_amount: float = Field(..., gt=0)
    payment_day: int = Field(..., ge=1, le=31)
    status: Optional[LeaseStatus] = LeaseStatus.PENDING
    document_url: Optional[str] = None


class LeaseCreate(LeaseBase):
    pass


class LeaseUpdate(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    rent_amount: Optional[float] = Field(None, gt=0)
    payment_day: Optional[int] = Field(None, ge=1, le=31)
    status: Optional[LeaseStatus] = None
    document_url: Optional[str] = None


class LeaseResponse(BaseModel):
    id: uuid.UUID
    property: PropertyResponseSimple  # Use the simple response model
    tenant: UserResponseSimple  # Use the simple response model
    landlord: UserResponseSimple  # Use the simple response model
    start_date: date
    end_date: date
    rent_amount: float
    payment_day: int
    status: LeaseStatus
    document_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class LeaseAgreementTemplateBase(BaseModel):
    name: str
    content: str
    is_default: Optional[bool] = False


class LeaseAgreementTemplateCreate(LeaseAgreementTemplateBase):
    pass


class LeaseAgreementTemplateUpdate(BaseModel):
    name: Optional[str] = None
    content: Optional[str] = None
    is_default: Optional[bool] = None


class LeaseAgreementTemplateResponse(BaseModel):
    id: uuid.UUID
    name: str
    is_default: bool
    created_at: datetime
    updated_at: datetime
    # Content excluded by default


class LeaseAgreementTemplateDetailResponse(LeaseAgreementTemplateResponse):
    content: str  # Include content for detail view
