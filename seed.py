"""
Database seeding script.

Populates the database with realistic sample data for development and testing.
Creates one user per role and ~30 financial records spanning several months
to demonstrate filtering, aggregation, and trend features.

Usage:
    python seed.py

The script is idempotent — it checks for existing data before seeding
and will skip if the database already contains users.
"""

from app import create_app
from app.seed_data import seed_if_empty, DEFAULT_SEED_PASSWORD


def seed_database():
    """Populate the database with sample users and financial records."""
    app = create_app()

    with app.app_context():
        users_created, records_created = seed_if_empty()

        if users_created == 0 and records_created == 0:
            print("Database already contains data. Skipping seed.")
            return

        print("Seeding database...")
        print(f"  Created {users_created} users")
        print(f"  Created {records_created} financial records")
        print("\nSeed complete! You can now log in with:")
        print(f"  - admin@example.com / {DEFAULT_SEED_PASSWORD}")
        print(f"  - analyst@example.com / {DEFAULT_SEED_PASSWORD}")
        print(f"  - viewer@example.com / {DEFAULT_SEED_PASSWORD}")


if __name__ == "__main__":
    seed_database()
