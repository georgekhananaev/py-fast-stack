"""
Generate dummy users and subscribers for testing/demo purposes.

This script creates realistic test data directly in the database.
All users will have the same password defined in the .env file.
"""
import asyncio
import os
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal, engine
from app.models.subscription import Subscription
from app.models.user import User
# Import all models to ensure they're registered
from app.db.base import Base  # This imports all models

# Load environment variables
load_dotenv()

# Get dummy password from env or use default
DUMMY_USER_PASSWORD = os.getenv("DUMMY_USER_PASSWORD", "DemoPass123!")

# Sample data for realistic names and roles
FIRST_NAMES = [
    "Emma", "Liam", "Olivia", "Noah", "Ava", "Ethan", "Sophia", "Mason",
    "Isabella", "William", "Mia", "James", "Charlotte", "Benjamin", "Amelia",
    "Lucas", "Harper", "Henry", "Evelyn", "Alexander", "Abigail", "Michael",
    "Emily", "Elijah", "Elizabeth", "Daniel", "Sofia", "Matthew", "Avery",
    "Aiden", "Ella", "Joseph", "Madison", "Samuel", "Scarlett", "David",
    "Grace", "Carter", "Chloe", "Owen", "Victoria", "Wyatt", "Riley",
    "John", "Aria", "Jack", "Lily", "Luke", "Aurora", "Jayden", "Zoey"
]

LAST_NAMES = [
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Jackson", "Martin",
    "Lee", "Perez", "Thompson", "White", "Harris", "Sanchez", "Clark",
    "Ramirez", "Lewis", "Robinson", "Walker", "Young", "Allen", "King",
    "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores", "Green",
    "Adams", "Nelson", "Baker", "Hall", "Rivera", "Campbell", "Mitchell",
    "Carter", "Roberts", "Gomez", "Phillips", "Evans", "Turner", "Diaz"
]

DEPARTMENTS = [
    "Engineering", "Marketing", "Sales", "Product", "Design", "HR",
    "Finance", "Operations", "Customer Success", "Data Science",
    "Legal", "Business Development", "IT", "Research", "Support"
]

COMPANY_TYPES = ["Tech", "Solutions", "Systems", "Digital", "Labs", "Works", "Co", "Inc", "Group"]

INTERESTS = [
    "Product Updates", "Tutorials", "Best Practices", 
    "Community", "API Changes", "Security"
]


def generate_company_name():
    """Generate a realistic company name."""
    prefix = random.choice([
        "Tech", "Global", "Digital", "Smart", "Next", "Future", "Rapid",
        "Prime", "Core", "Swift", "Bright", "Clear", "Pure", "Edge"
    ])
    suffix = random.choice(COMPANY_TYPES)
    return f"{prefix} {suffix}"


def generate_username(first_name, last_name, index):
    """Generate a unique username."""
    options = [
        f"{first_name.lower()}.{last_name.lower()}",
        f"{first_name.lower()}{last_name.lower()}",
        f"{first_name[0].lower()}{last_name.lower()}",
        f"{first_name.lower()}{last_name[0].lower()}",
        f"{first_name.lower()}_{last_name.lower()}",
    ]
    base = random.choice(options)
    # Add number if needed for uniqueness
    return f"{base}{index if index > 0 else ''}"


async def clear_existing_data(db: AsyncSession):
    """Clear existing users and subscriptions (except the default admin and root)."""
    print("Clearing existing dummy data...")
    
    # Delete non-admin and non-root users
    users = await db.execute(
        select(User).where(
            (User.username != "admin") & (User.username != "root")
        )
    )
    for user in users.scalars():
        await db.delete(user)
    
    # Delete all subscriptions
    subscriptions = await db.execute(select(Subscription))
    for sub in subscriptions.scalars():
        await db.delete(sub)
    
    await db.commit()
    print("Existing data cleared.")


async def create_root_user(db: AsyncSession):
    """Create root superuser if it doesn't exist."""
    # Check if root user already exists
    existing_root = await db.execute(
        select(User).where(User.username == "root")
    )
    if existing_root.scalar_one_or_none():
        print("Root user already exists, skipping...")
        return
    
    print("Creating root superuser...")
    hashed_password = await get_password_hash(DUMMY_USER_PASSWORD)
    
    root_user = User(
        username="root",
        email="root@pyfaststack.com",
        full_name="Root Administrator",
        hashed_password=hashed_password,
        is_active=True,
        is_superuser=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(root_user)
    await db.commit()
    print(f"✓ Created root superuser (username: root, password: {DUMMY_USER_PASSWORD})")


async def create_dummy_users(db: AsyncSession, count: int = 50):
    """Create dummy users with realistic data."""
    print(f"\nCreating {count} dummy users...")
    
    hashed_password = await get_password_hash(DUMMY_USER_PASSWORD)
    created_users = []
    
    for i in range(count):
        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)
        username = generate_username(first_name, last_name, i)
        email = f"{username}@pyfaststack.com"
        
        # Determine user type
        is_superuser = i < 2  # First 2 users are superusers
        is_active = random.random() > 0.1  # 90% active users
        
        # Create random registration date within last year
        days_ago = random.randint(1, 365)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        user = User(
            username=username,
            email=email,
            full_name=f"{first_name} {last_name}",
            hashed_password=hashed_password,
            is_active=is_active,
            is_superuser=is_superuser,
            created_at=created_at,
            updated_at=created_at
        )
        
        db.add(user)
        created_users.append(user)
        
        if (i + 1) % 10 == 0:
            print(f"  Created {i + 1} users...")
    
    await db.commit()
    print(f"✓ Created {count} users successfully!")
    
    # Print some sample users
    print("\nSample users created:")
    print(f"  Superusers: {', '.join([u.username for u in created_users[:2]])}")
    print(f"  Regular users: {', '.join([u.username for u in created_users[2:5]])}")
    print(f"  All passwords: {DUMMY_USER_PASSWORD}")
    
    return created_users


async def create_dummy_subscribers(db: AsyncSession, count: int = 100):
    """Create dummy newsletter subscribers."""
    print(f"\nCreating {count} dummy subscribers...")
    
    created_subscribers = []
    used_emails = set()
    
    for i in range(count):
        # Generate unique email
        while True:
            first_name = random.choice(FIRST_NAMES)
            last_name = random.choice(LAST_NAMES)
            company = generate_company_name()
            
            # Various email formats
            email_formats = [
                f"{first_name.lower()}.{last_name.lower()}@{company.lower().replace(' ', '')}.com",
                f"{first_name.lower()}@{company.lower().replace(' ', '')}.com",
                f"{first_name[0].lower()}{last_name.lower()}@{company.lower().replace(' ', '')}.com",
                f"{first_name.lower()}{random.randint(1, 99)}@pyfaststack.com",
            ]
            email = random.choice(email_formats)
            
            if email not in used_emails:
                used_emails.add(email)
                break
        
        # Random subscription date within last 6 months
        days_ago = random.randint(1, 180)
        created_at = datetime.utcnow() - timedelta(days=days_ago)
        
        # 85% active subscribers
        is_active = random.random() > 0.15
        
        # Random interests
        num_interests = random.randint(1, 4)
        selected_interests = random.sample(INTERESTS, num_interests)
        interests_str = ", ".join(selected_interests)
        
        subscriber = Subscription(
            email=email,
            name=f"{first_name} {last_name}",
            company=company if random.random() > 0.3 else None,  # 70% have company
            interests=interests_str if random.random() > 0.2 else None,  # 80% have interests
            is_active=is_active,
            created_at=created_at,
            updated_at=created_at
        )
        
        db.add(subscriber)
        created_subscribers.append(subscriber)
        
        if (i + 1) % 20 == 0:
            print(f"  Created {i + 1} subscribers...")
    
    await db.commit()
    print(f"✓ Created {count} subscribers successfully!")
    
    # Print statistics
    active_count = sum(1 for s in created_subscribers if s.is_active)
    with_company = sum(1 for s in created_subscribers if s.company)
    with_interests = sum(1 for s in created_subscribers if s.interests)
    
    print(f"\nSubscriber statistics:")
    print(f"  Total: {count}")
    print(f"  Active: {active_count} ({active_count/count*100:.1f}%)")
    print(f"  With company: {with_company} ({with_company/count*100:.1f}%)")
    print(f"  With interests: {with_interests} ({with_interests/count*100:.1f}%)")


async def init_database():
    """Initialize database tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✓ Database tables initialized.")


async def main():
    """Main function to generate all dummy data."""
    print("=" * 60)
    print("PyFastStack Dummy Data Generator")
    print("=" * 60)
    print(f"Database URL: {os.getenv('DATABASE_URL', 'Not set!')}")
    print(f"Dummy Password: {DUMMY_USER_PASSWORD}")
    print("=" * 60)
    
    # Initialize database tables
    await init_database()
    
    # Check for --force flag to skip confirmation
    if "--force" not in sys.argv:
        # Ask for confirmation
        try:
            response = input("\nThis will DELETE existing users/subscribers (except admin). Continue? (y/N): ")
            if response.lower() != 'y':
                print("Cancelled.")
                return
        except EOFError:
            print("\nNo input available. Use --force flag to skip confirmation.")
            return
    else:
        print("\n--force flag detected, skipping confirmation.")
    
    async with AsyncSessionLocal() as db:
        try:
            # Clear existing data
            await clear_existing_data(db)
            
            # Create root user
            await create_root_user(db)
            
            # Create dummy data
            await create_dummy_users(db, count=50)
            await create_dummy_subscribers(db, count=100)
            
            print("\n" + "=" * 60)
            print("✓ Dummy data generation completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            await db.rollback()
            raise


if __name__ == "__main__":
    asyncio.run(main())