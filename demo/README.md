# Demo Data Generator

This folder contains scripts for generating dummy data for testing and demonstration purposes.

## generate_dummy_data.py

This script creates realistic dummy users and newsletter subscribers directly in the database.

### Features

- Creates 50 dummy users (2 superusers, 48 regular users)
- Creates 100 dummy newsletter subscribers
- Uses realistic names and email addresses
- All users have the same password for easy testing
- Subscribers have random companies and interests
- Mix of active/inactive users and subscribers

### Usage

1. Make sure your `.env` file has the correct `DATABASE_URL`
2. The dummy password is set in `.env` as `DUMMY_USER_PASSWORD` (default: `DemoPass123!`)
3. Run the script:

```bash
cd demo
uv run python generate_dummy_data.py
```

### Sample Data Created

**Users:**
- Email format: `firstname.lastname@pyfaststack.com`
- 2 superusers (first 2 users created)
- 90% active users, 10% inactive
- Random registration dates within the last year

**Subscribers:**
- Various email formats from different domains
- 85% active subscribers, 15% inactive
- 70% have company information
- 80% have interests selected
- Random subscription dates within the last 6 months

### Warning

⚠️ This script will DELETE all existing users and subscribers (except the admin user) before creating new dummy data. Always confirm before proceeding.

### Example Users

After running the script, you can login with any user using:
- Username: Check the console output for sample usernames
- Password: `DemoPass123!` (or whatever is set in `.env`)

The first two users created are superusers and can access admin functions.