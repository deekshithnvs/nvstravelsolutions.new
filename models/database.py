from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from core.config import settings

# Database URL from settings
DATABASE_URL = settings.DATABASE_URL

# Fix for Heroku/Render style Postgres URLs
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create engine (SQLite requires check_same_thread=False)
is_sqlite = DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)

# Enable WAL Mode for SQLite concurrency
from sqlalchemy import event
if is_sqlite:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    from models.user import User
    from models.vendor import Vendor
    from models.invoice import Invoice
    from models.session import Session  # Persistent sessions
    from models.audit import AuditLog
    from models.error_log import ErrorLog
    from models.message import Message
    from models.system_setting import SystemSetting
    Base.metadata.create_all(bind=engine)
