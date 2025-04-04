import uuid
from math import ceil
from typing import List, Optional, Tuple

from models.review import CreateReviewRequest, Review
from models.user import User, UserRole
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from services.exceptions import (
    InvalidRequestException,
    ReviewExistsException,
    ServiceException,
    UserNotFoundException,
)
from services.user_service import UserService


class ReviewService:
    """Service layer for review-related operations."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_service = UserService(session)  # For fetching user details

    async def create_review(
        self, reviewer: User, agent_id: uuid.UUID, data: CreateReviewRequest
    ) -> Review:
        """Creates a review for an agent."""

        # 1. Validate Agent ID corresponds to an existing AGENT user
        agent = await self.user_service.get_user_by_id(agent_id)
        if not agent:
            raise UserNotFoundException(f"Agent with ID {agent_id} not found.")
        if agent.role != UserRole.AGENT:
            raise InvalidRequestException(f"User {agent_id} is not an Agent.")

        # 2. Validate reviewer is not the agent
        if reviewer.id == agent_id:
            raise InvalidRequestException("Users cannot review themselves.")

        # 3. Create Review object (DB constraint handles uniqueness)
        new_review = Review(
            reviewer_id=reviewer.id,
            agent_id=agent_id,
            rating=data.rating,
            comment=data.comment,
        )
        self.session.add(new_review)

        try:
            await self.session.flush()
            # Refresh to get DB defaults like ID and created_at
            await self.session.refresh(new_review)
            # Eager load reviewer for the response
            await self.session.refresh(new_review, attribute_names=["reviewer"])
            return new_review
        except IntegrityError as e:
            await self.session.rollback()
            # Check if it's the unique constraint violation
            if "uq_review_per_agent" in str(e.orig):
                raise ReviewExistsException(
                    f"User {reviewer.id} has already reviewed agent {agent_id}."
                )
            else:
                # Handle other potential integrity errors
                raise ServiceException(f"Database integrity error: {e}") from e
        except Exception as e:
            await self.session.rollback()
            raise ServiceException(f"Could not create review: {e}") from e

    async def get_reviews_for_agent(
        self, agent_id: uuid.UUID, page: int = 1, per_page: int = 10
    ) -> Tuple[List[Review], int, int]:
        """Fetches paginated reviews for a specific agent."""

        offset = (page - 1) * per_page
        base_query = (
            select(Review)
            .where(Review.agent_id == agent_id)
            .options(selectinload(Review.reviewer))  # Eager load reviewer
        )

        # Query for total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await self.session.execute(count_query)
        total_items = total_result.scalar_one()
        total_pages = ceil(total_items / per_page) if per_page > 0 else 0

        # Query for paginated items
        items_query = (
            base_query.order_by(Review.created_at.desc()).offset(offset).limit(per_page)
        )
        items_result = await self.session.execute(items_query)
        items = list(items_result.scalars().all())

        return items, total_items, total_pages

    async def calculate_average_rating(self, agent_id: uuid.UUID) -> Optional[float]:
        """Calculates the average rating for a specific agent."""
        stmt = select(func.avg(Review.rating)).where(Review.agent_id == agent_id)
        result = await self.session.execute(stmt)
        average = result.scalar_one_or_none()
        return average  # Returns None if no reviews exist
