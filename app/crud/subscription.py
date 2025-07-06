from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.crud.base import CRUDBase
from app.models.subscription import Subscription
from app.schemas.subscription import SubscriptionCreate, SubscriptionUpdate


class CRUDSubscription(CRUDBase[Subscription, SubscriptionCreate, SubscriptionUpdate]):
    """CRUD operations for subscriptions."""

    async def get_by_email(self, db: AsyncSession, *, email: str) -> Optional[Subscription]:
        """Get subscription by email."""
        result = await db.execute(select(Subscription).where(Subscription.email == email))
        return result.scalar_one_or_none()

    async def get_active_subscriptions(self, db: AsyncSession, *, skip: int = 0, limit: int = 100) -> List[Subscription]:
        """Get all active subscriptions."""
        result = await db.execute(
            select(Subscription)
            .where(Subscription.is_active == True)
            .offset(skip)
            .limit(limit)
            .order_by(Subscription.created_at.desc())
        )
        return result.scalars().all()

    async def deactivate_subscription(self, db: AsyncSession, *, email: str) -> Optional[Subscription]:
        """Deactivate a subscription by email."""
        subscription = await self.get_by_email(db, email=email)
        if subscription:
            update_data = SubscriptionUpdate(is_active=False)
            return await self.update(db, db_obj=subscription, obj_in=update_data)
        return None


subscription = CRUDSubscription(Subscription)