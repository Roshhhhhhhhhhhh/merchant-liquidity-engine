from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings
from app.core.logging import logger

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False,
    future=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    from sqlalchemy import text
    from app.database.base import Base
    # import models to register them
    import app.models  # noqa
    logger.info("Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Safe lightweight schema migration for SQLite
    if settings.DATABASE_URL.startswith("sqlite"):
        with engine.connect() as conn:
            try:
                # Check existing columns in transactions table
                res = conn.execute(text("PRAGMA table_info(transactions)")).fetchall()
                existing_cols = {row[1] for row in res}
                new_columns = [
                    ("source", "VARCHAR(50) DEFAULT 'direct'"),
                    ("negotiation_id", "VARCHAR(50)"),
                    ("payment_order_id", "VARCHAR(50)"),
                    ("razorpay_payment_id", "VARCHAR(100)"),
                    ("razorpay_order_id", "VARCHAR(100)"),
                    ("paid_at", "DATETIME"),
                ]
                for col_name, col_type in new_columns:
                    if col_name not in existing_cols:
                        conn.execute(text(f"ALTER TABLE transactions ADD COLUMN {col_name} {col_type}"))
                conn.commit()
            except Exception as e:
                logger.warning(f"Schema migration note: {e}")

    logger.info("Database tables initialized successfully.")
