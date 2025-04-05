import uuid
from typing import List  # Import List

from quart import Blueprint, current_app
from quart_auth import login_required  # Keep login_required, remove current_user
from quart_schema import validate_request, validate_response

from api.models.base import ErrorResponse
from api.models.rent_payment import RentPaymentCreateManual, RentPaymentResponse
from api.services.database import get_session
from api.services.exceptions import (
    AuthorizationException,
    InvalidOperationException,  # Although not used in this endpoint yet
    LeaseNotFoundException,
)
from api.services.payment_service import PaymentService
from api.utils.auth_helpers import get_current_user_object  # Import the helper

bp = Blueprint("payment_routes", __name__, url_prefix="/api/payments")


@bp.route("/record-manual", methods=["POST"])
@login_required
@validate_request(RentPaymentCreateManual)
@validate_response(RentPaymentResponse, status_code=201)
@validate_response(
    ErrorResponse, status_code=400, description="Invalid input or operation"
)
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
@validate_response(ErrorResponse, status_code=403, description="Forbidden")
@validate_response(ErrorResponse, status_code=404, description="Not Found")
async def record_manual_payment_route(data: RentPaymentCreateManual):
    """
    Records a manual rent payment against a lease.
    Requires authenticated user (landlord or admin).
    """
    try:
        user = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            payment_service = PaymentService(db_session)
            # Pass the authenticated user object to the service method
            new_payment_record = await payment_service.record_manual_payment(
                payment_data=data, recording_user=user
            )
            return new_payment_record, 201
    except LeaseNotFoundException as e:
        current_app.logger.warning(f"Record Manual Payment Error - Not Found: {e}")
        return ErrorResponse(message=str(e)), 404
    except (AuthorizationException, InvalidOperationException) as e:
        current_app.logger.warning(
            f"Record Manual Payment Error - Forbidden/Invalid: {e}"
        )
        status_code = 403 if isinstance(e, AuthorizationException) else 400
        return ErrorResponse(message=str(e)), status_code
    except Exception as e:
        current_app.logger.error(f"Error recording manual payment: {e}", exc_info=True)
        return ErrorResponse(
            message="An unexpected error occurred while recording the payment."
        ), 500


@bp.route("/leases/<uuid:lease_id>/payments", methods=["GET"])
@login_required
@validate_response(List[RentPaymentResponse])
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
@validate_response(ErrorResponse, status_code=403, description="Forbidden")
@validate_response(ErrorResponse, status_code=404, description="Not Found")
async def get_lease_payments_route(lease_id: uuid.UUID):
    """
    Get all rent payment records for a specific lease.
    Requires authenticated user who is the tenant, landlord, or admin.
    """
    try:
        user = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            payment_service = PaymentService(db_session)
            # Service method handles authorization check (tenant/landlord/admin)
            payments = await payment_service.get_payments_for_lease(
                lease_id=lease_id, requesting_user=user
            )
            return payments, 200
    except LeaseNotFoundException as e:
        current_app.logger.warning(f"Get Lease Payments Error - Not Found: {e}")
        return ErrorResponse(message=str(e)), 404
    except AuthorizationException as e:
        current_app.logger.warning(f"Get Lease Payments Error - Forbidden: {e}")
        return ErrorResponse(message=str(e)), 403
    except Exception as e:
        current_app.logger.error(f"Error fetching lease payments: {e}", exc_info=True)
        return ErrorResponse(
            message="An unexpected error occurred while fetching payments."
        ), 500


# --- Placeholder for other payment endpoints ---
# GET /leases/{lease_id}/payments
# GET /payments/{payment_id}
# POST /payments/initiate-mobile-money (Future)
