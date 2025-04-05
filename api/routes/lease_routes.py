from typing import List  # Import List

from quart import Blueprint, current_app
from quart_auth import login_required  # Remove current_user
from quart_schema import validate_request, validate_response

from api.models.base import ErrorResponse  # For error responses
from api.models.lease import LeaseCreate, LeaseResponse
from api.services.database import get_session
from api.services.exceptions import (
    AuthorizationException,
    InvalidOperationException,
    PropertyNotFoundException,
    UserNotFoundException,
)
from api.services.lease_service import LeaseService
from api.utils.auth_helpers import get_current_user_object  # Import the helper

bp = Blueprint("lease_routes", __name__, url_prefix="/api/leases")


@bp.route("", methods=["POST"])
@login_required
@validate_request(LeaseCreate)
@validate_response(LeaseResponse, status_code=201)
@validate_response(
    ErrorResponse, status_code=400, description="Invalid input or operation"
)
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
@validate_response(ErrorResponse, status_code=403, description="Forbidden")
@validate_response(ErrorResponse, status_code=404, description="Not Found")
async def create_lease(data: LeaseCreate):
    """
    Create a new lease agreement.
    Requires authenticated user (landlord, agent, or admin).
    The landlord_id is automatically set to the logged-in user.
    """
    try:
        user = await get_current_user_object()  # Use the helper
        # Basic role check - ensure user is at least a standard USER.
        # More specific checks (is landlord/agent/admin for the property) are in the service.
        if not user:
            # This case should ideally be caught by @login_required, but added for safety
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            lease_service = LeaseService(db_session)
            # Pass the authenticated user object to the service method
            new_lease = await lease_service.create_lease(
                lease_data=data, landlord_user=user
            )
            return new_lease, 201
    except (PropertyNotFoundException, UserNotFoundException) as e:
        current_app.logger.warning(f"Create Lease Error - Not Found: {e}")
        return ErrorResponse(message=str(e)), 404
    except (AuthorizationException, InvalidOperationException) as e:
        current_app.logger.warning(f"Create Lease Error - Forbidden/Invalid: {e}")
        # Return 403 for Authorization, 400 for InvalidOperation
        status_code = 403 if isinstance(e, AuthorizationException) else 400
        return ErrorResponse(message=str(e)), status_code
    except Exception as e:
        current_app.logger.error(f"Error creating lease: {e}", exc_info=True)
        return ErrorResponse(
            message="An unexpected error occurred while creating the lease."
        ), 500


@bp.route("/my-landlord-leases", methods=["GET"])
@login_required
@validate_response(List[LeaseResponse])
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
async def get_my_landlord_leases():
    """
    Get all leases where the current user is the landlord.
    """
    try:
        user = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            lease_service = LeaseService(db_session)
            leases = await lease_service.get_leases_for_landlord(user.id, user)
            # LeaseResponse schema handles the conversion
            return leases, 200
    except AuthorizationException as e:
        # This shouldn't happen if the user is fetched correctly, but handle defensively
        current_app.logger.warning(f"Get My Landlord Leases Error - Forbidden: {e}")
        return ErrorResponse(message=str(e)), 403
    except Exception as e:
        current_app.logger.error(f"Error fetching landlord leases: {e}", exc_info=True)
        return ErrorResponse(
            message="An unexpected error occurred while fetching leases."
        ), 500


@bp.route("/my-tenant-leases", methods=["GET"])
@login_required
@validate_response(List[LeaseResponse])
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
async def get_my_tenant_leases():
    """
    Get all leases where the current user is the tenant.
    """
    try:
        user = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            lease_service = LeaseService(db_session)
            # Service method handles authorization check implicitly by fetching by tenant_id
            leases = await lease_service.get_leases_for_tenant(user.id, user)
            # LeaseResponse schema handles the conversion
            return leases, 200
    except AuthorizationException as e:
        # This shouldn't happen if the user is fetched correctly, but handle defensively
        current_app.logger.warning(f"Get My Tenant Leases Error - Forbidden: {e}")
        return ErrorResponse(message=str(e)), 403
    except Exception as e:
        current_app.logger.error(f"Error fetching tenant leases: {e}", exc_info=True)
        return ErrorResponse(
            message="An unexpected error occurred while fetching your leases."
        ), 500


# --- Placeholder for other lease endpoints ---
# GET /leases/{lease_id}
# PUT /leases/{lease_id}
# DELETE /leases/{lease_id}
# GET /properties/{property_id}/leases
# GET /users/{user_id}/leases/tenant
# GET /users/{user_id}/leases/landlord
