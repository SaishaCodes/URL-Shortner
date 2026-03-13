import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
 
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/urldb")
 
engine = create_engine(DATABASE_URL)
 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
 
Base = declarative_base()
 
def init_db():
    from app.models import URL, Click  # noqa: F401 — ensures tables are registered
    Base.metadata.create_all(bind=engine)