from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import datetime

DATABASE_URL = "sqlite:///./agent_memory.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class ProjectRecord(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    goal = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class EventRecord(Base):
    __tablename__ = "events"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer)
    event_type = Column(String) # PLAN_GENERATED, TASK_START, TASK_COMPLETED, FAILED
    task_id = Column(String, nullable=True)
    data = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(bind=engine)

class DBManager:
    def __init__(self):
        self.db = SessionLocal()

    def create_project(self, name, goal):
        project = ProjectRecord(name=name, goal=goal)
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project.id

    def log_event(self, project_id, event_type, task_id=None, data=None):
        event = EventRecord(
            project_id=project_id,
            event_type=event_type,
            task_id=task_id,
            data=data
        )
        self.db.add(event)
        self.db.commit()

    def get_history(self, project_id):
        return self.db.query(EventRecord).filter(EventRecord.project_id == project_id).order_by(EventRecord.timestamp).all()