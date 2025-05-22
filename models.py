from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel

# --- Database Setup ---
DATABASE_URL = "sqlite:///./feedback.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()


class Customer(Base):
    __tablename__ = "customers"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True)
    second_name = Column(String, index=True)
    last_name = Column(String, nullable=True)
    phone = Column(String, unique=True, index=True)

class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"))
    rating = Column(Integer, nullable=True)
    comments = Column(Text, nullable=True)
    
class PaymentPayload(BaseModel):
    TransID: str
    TransTime: str
    TransAmount: str
    BusinessShortCode: str
    BillRefNumber: str
    MSISDN: str
    FirstName: str
    MiddleName: str = ""
    LastName: str = ""


class FeedbackResponse(BaseModel):
    phone: str
    rating: int
    comments: str = None