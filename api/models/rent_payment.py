from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from pydantic import BaseModel, Field
from sqlalchemy import (
    Date,
    DateTime,
    Float,
    ForeignKey,
    String,
    func,
)
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from models.base import Base

if TYPE_CHECKING:
    from .lease import (
        Lease,  # Import Lease for relationship and LeaseResponse for schema
    )


class RentPaymentStatus(str, Enum):
    PENDING = "PENDING"  # Payment expected but not yet received/recorded
    PAID = "PAID"  # Payment received and recorded
    OVERDUE = "OVERDUE"  # Payment past due date
    PARTIAL = "PARTIAL"  # Partial payment received (optional complexity)
    CANCELLED = "CANCELLED"  # Payment record cancelled (e.g., lease terminated early)


class PaymentMethod(str, Enum):
    CASH = "CASH"
    BANK_TRANSFER = "BANK_TRANSFER"
    MOBILE_MONEY_MTN = "MOBILE_MONEY_MTN"
    MOBILE_MONEY_ORANGE = "MOBILE_MONEY_ORANGE"
    CARD = "CARD"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"  # Default if not specified


class RentPayment(Base):
    __tablename__ = "rent_payments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    lease_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("leases.id"), nullable=False, index=True
    )

    amount_due: Mapped[float] = mapped_column(Float, nullable=False)
    amount_paid: Mapped[Optional[float]] = mapped_column(
        Float, nullable=True
    )  # Nullable until paid
    due_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    payment_date: Mapped[Optional[date]] = mapped_column(
        Date, nullable=True
    )  # Date payment was recorded

    status: Mapped[RentPaymentStatus] = mapped_column(
        SQLAlchemyEnum(RentPaymentStatus),
        nullable=False,
        default=RentPaymentStatus.PENDING,
        index=True,
    )
    payment_method: Mapped[Optional[PaymentMethod]] = mapped_column(
        SQLAlchemyEnum(PaymentMethod), nullable=True, default=PaymentMethod.UNKNOWN
    )
    transaction_reference: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # e.g., Mobile Money Tx ID
    notes: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  # Internal notes for landlord

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    lease: Mapped["Lease"] = relationship(
        back_populates="rent_payments"
    )  # Add back_populates="rent_payments" to Lease model later

    def to_dict(self):
        return {
            "id": str(self.id),
            "lease_id": str(self.lease_id),
            "amount_due": self.amount_due,
            "amount_paid": self.amount_paid,
            "due_date": self.due_date.isoformat(),
            "payment_date": self.payment_date.isoformat()
            if self.payment_date
            else None,
            "status": self.status.value,
            "payment_method": self.payment_method.value
            if self.payment_method
            else None,
            "transaction_reference": self.transaction_reference,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


# --- Pydantic Schemas ---


class RentPaymentBase(BaseModel):
    lease_id: uuid.UUID
    amount_due: float = Field(..., gt=0)
    due_date: date


class RentPaymentCreateManual(BaseModel):  # For manually recording a payment
    lease_id: uuid.UUID  # Need to associate with a lease
    amount_paid: float = Field(..., gt=0)
    payment_date: date
    payment_method: Optional[PaymentMethod] = PaymentMethod.UNKNOWN
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    # We might need to link this to a specific RentPayment record (e.g., the PENDING one for that due date)
    # Or the service layer handles finding the right record to update. Let's assume service handles it.
    # Optional: Allow specifying the due_date it corresponds to if multiple are pending/overdue.
    corresponding_due_date: Optional[date] = None


class RentPaymentUpdate(BaseModel):  # For internal updates, e.g., marking as overdue
    status: Optional[RentPaymentStatus] = None
    amount_paid: Optional[float] = Field(None, gt=0)
    payment_date: Optional[date] = None
    payment_method: Optional[PaymentMethod] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None


class RentPaymentResponse(BaseModel):
    id: uuid.UUID
    lease_id: uuid.UUID
    amount_due: float
    amount_paid: Optional[float] = None
    due_date: date
    payment_date: Optional[date] = None
    status: RentPaymentStatus
    payment_method: Optional[PaymentMethod] = None
    transaction_reference: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    # Optionally include simplified Lease info?
    # lease: Optional[LeaseResponseSimple] = None # Requires LeaseResponseSimple definition
