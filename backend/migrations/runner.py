"""Database migration runner for executing SQL migrations."""

import asyncio
import logging
import os
from pathlib import Path

import asyncpg

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).parent


async def get_applied_migrations(conn: asyncpg.Connection) -> set[str]:
    """Get the set of already applied migrations."""
    # Create migrations tracking table if it doesn't exist
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS _migrations (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) UNIQUE NOT NULL,
            applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
        )
    """)

    rows = await conn.fetch("SELECT name FROM _migrations")
    return {row["name"] for row in rows}


async def apply_migration(conn: asyncpg.Connection, migration_file: Path) -> None:
    """Apply a single migration file."""
    migration_name = migration_file.name
    logger.info(f"Applying migration: {migration_name}")

    sql = migration_file.read_text()

    async with conn.transaction():
        await conn.execute(sql)
        await conn.execute(
            "INSERT INTO _migrations (name) VALUES ($1)",
            migration_name,
        )

    logger.info(f"Successfully applied: {migration_name}")


async def run_migrations(database_url: str) -> None:
    """Run all pending migrations."""
    # Convert SQLAlchemy URL to asyncpg format
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(dsn)

    try:
        applied = await get_applied_migrations(conn)

        # Get all SQL migration files sorted by name
        migration_files = sorted(MIGRATIONS_DIR.glob("*.sql"))

        pending = [f for f in migration_files if f.name not in applied]

        if not pending:
            logger.info("No pending migrations")
            return

        logger.info(f"Found {len(pending)} pending migration(s)")

        for migration_file in pending:
            await apply_migration(conn, migration_file)

        logger.info("All migrations completed successfully")

    finally:
        await conn.close()


async def rollback_migration(database_url: str, migration_name: str) -> None:
    """Remove a migration from the tracking table (manual rollback required)."""
    dsn = database_url.replace("postgresql+asyncpg://", "postgresql://")

    conn = await asyncpg.connect(dsn)

    try:
        result = await conn.execute(
            "DELETE FROM _migrations WHERE name = $1",
            migration_name,
        )
        logger.info(f"Removed migration record: {migration_name}")
        logger.warning("Note: You must manually reverse the schema changes")

    finally:
        await conn.close()


def main():
    """CLI entry point for running migrations."""
    import argparse

    parser = argparse.ArgumentParser(description="Database migration runner")
    parser.add_argument(
        "--database-url",
        default=os.getenv("DATABASE_URL"),
        help="Database URL (or set DATABASE_URL env var)",
    )
    parser.add_argument(
        "--rollback",
        metavar="MIGRATION_NAME",
        help="Remove a migration from tracking (manual schema rollback required)",
    )

    args = parser.parse_args()

    if not args.database_url:
        logger.error("DATABASE_URL not provided")
        return 1

    if args.rollback:
        asyncio.run(rollback_migration(args.database_url, args.rollback))
    else:
        asyncio.run(run_migrations(args.database_url))

    return 0


if __name__ == "__main__":
    exit(main())
