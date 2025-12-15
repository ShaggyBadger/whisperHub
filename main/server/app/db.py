import sqlalchemy as sa
from sqlalchemy.orm import declarative_base, sessionmaker
from pathlib import Path
import sys
from alembic import command
from alembic.config import Config
from datetime import datetime, timezone

from . import models

# Build the path to the database file within the 'main' directory
db_path = Path(__file__).parent.parent / "whisperhub.db"

Base = declarative_base()
engine = sa.create_engine(f"sqlite:///{db_path}")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class DbManagement:
    """
    A class for managing the database. Provides a simple
    command-line interface to apply migrations, generate new
    migration scripts, and other DB tasks.
    """
    def __init__(self):
        self.options = {
            "1": self.initialize_database,
            "2": self.make_migrations,
            "3": self.run_migrations,
            "q": self.quit_program
        }
        self.menu()

    def menu(self):
        while True:
            print("\n***\nDatabase Management Menu:")
            for key, func in self.options.items():
                print(f"{key}: {func.__name__}")
            choice = input("Choose an option: ").strip()
            action = self.options.get(choice)
            if action:
                action()
            else:
                print("Invalid choice. Please try again.\n***\n")

    def get_alembic_config(self):
        """Load the Alembic config."""
        from pathlib import Path
        config_path = Path(__file__).parent / "alembic.ini"
        return Config(str(config_path))

    def initialize_database(self):
        """Apply all existing migrations (safe to run multiple times)."""
        print("Applying existing migrations...")
        alembic_cfg = self.get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        print("Database initialized or updated to latest schema!")

    def make_migrations(self):
        """Generate a new migration script from model changes."""
        alembic_cfg = self.get_alembic_config()
        msg = input("Enter a message for this migration: ").strip()
        if msg:
            command.revision(alembic_cfg, message=msg, autogenerate=True)
            print(f"Migration '{msg}' created!")
        else:
            print("No message provided. Migration cancelled.")

    def run_migrations(self):
        """Apply pending migrations."""
        print("Applying migrations...")
        alembic_cfg = self.get_alembic_config()
        command.upgrade(alembic_cfg, "head")
        print("Migrations applied successfully!")

    def quit_program(self):
        print("Exiting database management.")
        sys.exit()

if __name__ == "__main__":
    DbManagement()
