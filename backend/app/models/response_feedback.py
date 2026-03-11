"""
Response feedback model - stores user feedback on bot responses.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func
from app.database import Base


class ResponseFeedback(Base):
    """
    User feedback on assistant responses.
    Used to analyze and improve the chatbot.
    """
    __tablename__ = "response_feedbacks"

    id = Column(Integer, primary_key=True, index=True)

    # Linked content
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)

    # Feedback
    rating = Column(String(20), nullable=False)  # 'positive' | 'negative'
    reason = Column(String(100), nullable=True)   # e.g. 'mevzuata_uygun_degil'
    comment = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    def __repr__(self) -> str:
        return f"<ResponseFeedback(id={self.id}, rating={self.rating}, reason={self.reason})>"
