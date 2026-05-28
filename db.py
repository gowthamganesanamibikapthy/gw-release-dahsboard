from datetime import datetime
from typing import List

from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine("sqlite:///deployments.db", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class DeploymentRecord(Base):
    __tablename__ = "deployments"

    id = Column(Integer, primary_key=True, index=True)
    environment = Column(String, index=True)
    product = Column(String, index=True)
    version = Column(String)
    branch = Column(String)
    status = Column(String)
    triggered_by = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

def init_db():
    Base.metadata.create_all(bind=engine)

def create_deployment(environment, product, version, branch, status, triggered_by):
    db = SessionLocal()
    try:
        rec = DeploymentRecord(
            environment=environment,
            product=product,
            version=version,
            branch=branch,
            status=status,
            triggered_by=triggered_by,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
    finally:
        db.close()

def list_deployments(limit=100) -> List[DeploymentRecord]:
    db = SessionLocal()
    try:
        return (
            db.query(DeploymentRecord)
            .order_by(DeploymentRecord.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
