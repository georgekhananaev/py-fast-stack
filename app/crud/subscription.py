
from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.base import CRUDBase
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    """CRUD operations for subscriptions."""

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Subscription | None:
        """Get subscription by email."""
        result = await db.execute(select(Subscription).where(Subscription.email == email))
        return result.scalar_one_or_none()

    async def get_active_subscriptions(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> list[Subscription]:
        """Get all active subscriptions."""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Subscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def deactivate_subscription(self, db: AsyncSession, *, email: str) -> Subscription | None:
        """Deactivate a subscription by email."""
        subscription = await self.get_by_email(db, email=email)
        if subscription:
            update_data = SubscriptionUpdate(is_active=False)
            return await self.update(db, db_obj=subscription, obj_in=update_data)
        return None

    async def get_multi_with_pagination(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 10,
        search: str | None = None,
        sort_by: str = "id",
        sort_order: str = "asc"
    ) -> tuple[list[Subscription], int]:
        """Get subscriptions with pagination, search, and sorting."""
        query = select(Subscription)

        # Add search filter if provided
        if search:
            search_filter = or_(
                Subscription.email.ilike(f"%{search}%"),
                Subscription.name.ilike(f"%{search}%"),
                Subscription.company.ilike(f"%{search}%")
            )
            query = query.where(search_filter)

        # Add sorting
        if sort_order == "desc":
            order_column = desc(getattr(Subscription, sort_by))
        else:
            order_column = asc(getattr(Subscription, sort_by))

        query = query.order_by(order_column)

        # Get total count
        count_query = select(func.count()).select_from(Subscription)
        if search:
            count_query = count_query.where(search_filter)

        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # Get paginated results
        query = query.offset(skip).limit(limit)
        result = await db.execute(query)
        subscriptions = list(result.scalars().all())

        return subscriptions, total


subscription = CRUDSubscription(Subscription)
