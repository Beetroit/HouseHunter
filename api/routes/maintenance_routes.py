from typing import List
import uuid  # Import List

from quart import Blueprint, current_app
from quart_auth import login_required
from quart_schema import validate_request, validate_response

from api.models.base import ErrorResponse
from api.models.maintenance_request import (
    MaintenanceRequestCreate,
    MaintenanceRequestResponse,
    MaintenanceRequestUpdate,  # Import MaintenanceRequestUpdate
)
from api.models.user import User
from api.services.database import get_session
from api.services.exceptions import (
    AuthorizationException,
    InvalidOperationException,
    MaintenanceRequestNotFoundException,  # Import MaintenanceRequestNotFoundException
    PropertyNotFoundException,
)
from api.services.maintenance_service import MaintenanceService
from api.utils.auth_helpers import get_current_user_object

bp = Blueprint("maintenance_routes", __name__, url_prefix="/api/maintenance")


@bp.route("/requests", methods=["POST"])
@login_required
@validate_request(MaintenanceRequestCreate)
@validate_response(MaintenanceRequestResponse, status_code=201)
@validate_response(
    ErrorResponse, status_code=400, description="Invalid input or operation"
)
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
@validate_response(ErrorResponse, status_code=403, description="Forbidden")
@validate_response(ErrorResponse, status_code=404, description="Not Found")
async def submit_maintenance_request(data: MaintenanceRequestCreate):
    """
    Submits a new maintenance request for a property.
    Requires authenticated user (tenant).
    """
    try:
        user: User = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        # Add check: Only users with 'user' role (tenants) can submit? Or allow agents too?
        # if user.role != UserRole.USER:
        #     return ErrorResponse(message="Only tenants can submit maintenance requests."), 403

        async with get_session() as db_session:
            maintenance_service = MaintenanceService(db_session)
            new_request = await maintenance_service.create_request(
                request_data=data, tenant_user=user
            )
            return new_request, 201
    except PropertyNotFoundException as e:
        current_app.logger.warning(f"Submit Maintenance Request Error - Not Found: {e}")
        return ErrorResponse(message=str(e)), 404
    except (AuthorizationException, InvalidOperationException) as e:
        current_app.logger.warning(
            f"Submit Maintenance Request Error - Forbidden/Invalid: {e}"
        )
        status_code = 403 if isinstance(e, AuthorizationException) else 400
        return ErrorResponse(message=str(e)), status_code
    except Exception as e:
        current_app.logger.error(
            f"Error submitting maintenance request: {e}", exc_info=True
        )
        return ErrorResponse(
            message="An unexpected error occurred while submitting the request."
        ), 500


@bp.route("/requests/my-submitted", methods=["GET"])
@login_required
@validate_response(List[MaintenanceRequestResponse])  # Use imported List
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
async def get_my_submitted_requests():
    """
    Get all maintenance requests submitted by the current user.
    """
    try:
        user: User = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            maintenance_service = MaintenanceService(db_session)
            requests = await maintenance_service.get_requests_submitted_by_tenant(user)
            return requests, 200
    except Exception as e:
        current_app.logger.error(
            f"Error fetching submitted maintenance requests: {e}", exc_info=True
        )
        return ErrorResponse(
            message="An unexpected error occurred while fetching your requests."
        ), 500


@bp.route("/requests/my-assigned", methods=["GET"])
@login_required
@validate_response(List[MaintenanceRequestResponse])
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
async def get_my_assigned_requests():
    """
    Get all maintenance requests assigned to the current user (landlord/agent).
    """
    try:
        user: User = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        # Add check: Ensure user is landlord/agent/admin?
        # if user.role not in [UserRole.AGENT, UserRole.ADMIN]: # Assuming owner is landlord
        #     return ErrorResponse(message="Only landlords/admins can view assigned requests."), 403

        async with get_session() as db_session:
            maintenance_service = MaintenanceService(db_session)
            requests = await maintenance_service.get_requests_assigned_to_landlord(user)
            return requests, 200
    except Exception as e:
        current_app.logger.error(
            f"Error fetching assigned maintenance requests: {e}", exc_info=True
        )


@bp.route("/requests/<uuid:request_id>", methods=["PUT"])
@login_required
@validate_request(MaintenanceRequestUpdate)
@validate_response(MaintenanceRequestResponse)
@validate_response(
    ErrorResponse, status_code=400, description="Invalid input or operation"
)
@validate_response(ErrorResponse, status_code=401, description="Unauthorized")
@validate_response(ErrorResponse, status_code=403, description="Forbidden")
@validate_response(ErrorResponse, status_code=404, description="Not Found")
async def update_maintenance_request_status(
    request_id: uuid.UUID, data: MaintenanceRequestUpdate
):
    """
    Updates the status or resolution notes of a maintenance request.
    Requires authenticated user (landlord/admin).
    """
    try:
        user = await get_current_user_object()
        if not user:
            return ErrorResponse(message="Authentication required."), 401

        async with get_session() as db_session:
            maintenance_service = MaintenanceService(db_session)
            updated_request = await maintenance_service.update_request_status(
                request_id=request_id, update_data=data, requesting_user=user
            )
            return updated_request, 200
    except MaintenanceRequestNotFoundException as e:
        current_app.logger.warning(f"Update Maintenance Request Error - Not Found: {e}")
        return ErrorResponse(message=str(e)), 404
    except (AuthorizationException, InvalidOperationException) as e:
        current_app.logger.warning(
            f"Update Maintenance Request Error - Forbidden/Invalid: {e}"
        )
        status_code = 403 if isinstance(e, AuthorizationException) else 400
        return ErrorResponse(message=str(e)), status_code
    except Exception as e:
        current_app.logger.error(
            f"Error updating maintenance request {request_id}: {e}", exc_info=True
        )
        return ErrorResponse(
            message="An unexpected error occurred while updating the request."
        ), 500


# --- Placeholder for other maintenance endpoints ---
# GET /requests/my-submitted
# GET /requests/my-assigned
# GET /requests/{request_id}
# PUT /requests/{request_id} (Update status/notes)
# GET /properties/{property_id}/requests (Landlord/Admin view)
