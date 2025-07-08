from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_current_active_superuser
from app.crud import subscription as crud_subscription
from app.schemas.subscription import Subscription, SubscriptionCreate
from app.models.user import User
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/subscribe", response_model=Subscription, status_code=status.HTTP_201_CREATED)
async def subscribe_to_newsletter(
    subscription_in: SubscriptionCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Subscribe to newsletter - Public endpoint.
    
    Allows anyone to subscribe to the newsletter.
    If email already exists but is inactive, it will be reactivated.
    
    Authentication required: NO
    Token type: None
    
    Args:
        subscription_in: SubscriptionCreate with email, name, company, interests
        
    Returns:
        Created/Updated Subscription object
        
    Raises:
        400: Email is already subscribed to our newsletter
        500: An error occurred while processing your subscription
    """
    try:
        # Check if email already exists
        existing_subscription = await crud_subscription.subscription.get_by_email(
            db, email=subscription_in.email
        )
        
        if existing_subscription:
            if existing_subscription.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email is already subscribed to our newsletter"
                )
            else:
                # Reactivate existing subscription
                from app.schemas.subscription import SubscriptionUpdate
                update_data = SubscriptionUpdate(
                    name=subscription_in.name,
                    company=subscription_in.company,
                    interests=subscription_in.interests,
                    is_active=True
                )
                subscription = await crud_subscription.subscription.update(
                    db, db_obj=existing_subscription, obj_in=update_data
                )
                logger.info(f"Reactivated subscription for email: {subscription_in.email}")
                return subscription
        
        # Create new subscription
        subscription = await crud_subscription.subscription.create(db, obj_in=subscription_in)
        logger.info(f"New subscription created for email: {subscription_in.email}")
        return subscription
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating subscription: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your subscription"
        )


@router.delete("/unsubscribe/{email}")
async def unsubscribe_from_newsletter(
    email: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Unsubscribe from newsletter - Public endpoint.
    
    Allows anyone to unsubscribe from the newsletter using their email.
    
    Authentication required: NO
    Token type: None
    
    Args:
        email: The email address to unsubscribe
        
    Returns:
        Success message
        
    Raises:
        404: Email not found in our subscription list
        500: An error occurred while processing your unsubscription
    """
    try:
        subscription = await crud_subscription.subscription.deactivate_subscription(db, email=email)
        
        if not subscription:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Email not found in our subscription list"
            )
        
        logger.info(f"Unsubscribed email: {email}")
        return {"detail": "Successfully unsubscribed from newsletter"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unsubscribing: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while processing your unsubscription"
        )


@router.get("/subscriptions", response_model=List[Subscription])
async def get_active_subscriptions(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_active_superuser),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active subscriptions - Protected endpoint (Admin only).
    
    Returns a list of all active newsletter subscriptions.
    
    Authentication required: YES
    Token type: Bearer token (in Authorization header)
    Access level: SUPERUSER ONLY
    
    Args:
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (max 100)
        
    Returns:
        List of Subscription objects
        
    Raises:
        401: Not authenticated
        403: Not a superuser
        500: An error occurred while fetching subscriptions
    """
    try:
        subscriptions = await crud_subscription.subscription.get_active_subscriptions(
            db, skip=skip, limit=limit
        )
        return subscriptions
    except Exception as e:
        logger.error(f"Error fetching subscriptions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while fetching subscriptions"
        )