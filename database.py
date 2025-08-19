from sqlalchemy import create_engine, Column, String, Text, DateTime, JSON
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime
import os

Base = declarative_base()

class TroubleshootingSession(Base):
    __tablename__ = 'sessions'
    
    id = Column(String, primary_key=True)
    app_name = Column(String(255), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    diagnostic_message = Column(Text)
    final_response = Column(JSON)

class DatabaseManager:
    def __init__(self):
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:root@localhost:5433/troubleshooting')
        self.engine = create_engine(database_url)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        Base.metadata.create_all(bind=self.engine)
    
    def save_session(self, session_id: str, app_name: str, diagnostic_message: str, final_response: dict):
        with self.SessionLocal() as db:
            session = TroubleshootingSession(
                id=session_id,
                app_name=app_name,
                diagnostic_message=diagnostic_message,
                final_response=final_response
            )
            db.add(session)
            db.commit()