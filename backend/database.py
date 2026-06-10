from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base

DB_PATH = Path.home() / ".photo-manager" / "library.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def _migrate(conn):
    """Add columns that were introduced after initial release."""
    new_columns = [
        ("ai_provider",    "VARCHAR"),
        ("cloud_provider", "VARCHAR"),
    ]
    existing = {row[1] for row in conn.execute(text("PRAGMA table_info(photos)"))}
    for col, col_type in new_columns:
        if col not in existing:
            conn.execute(text(f"ALTER TABLE photos ADD COLUMN {col} {col_type}"))


def init_db():
    Base.metadata.create_all(bind=engine)
    with engine.connect() as conn:
        _migrate(conn)
        conn.commit()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
