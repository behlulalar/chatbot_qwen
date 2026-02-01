"""
Chat log model - stores user queries and bot responses for analytics.
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, Float, JSON
from sqlalchemy.sql import func
from app.database import Base


class ChatLog(Base):
    """
    Model for storing chat interactions.
    
    Used for:
    - Analytics and metrics
    - Model performance comparison
    - User feedback tracking
    """
    __tablename__ = "chat_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Query and response
    user_query = Column(Text, nullable=False)
    bot_response = Column(Text, nullable=False)
    
    # Model information
    model_name = Column(String(100), index=True)
    
    # Retrieved sources (JSON array of document IDs and madde numbers)
    sources = Column(JSON)
    
    # Performance metrics
    response_time = Column(Float)  # in seconds
    token_count = Column(Integer)
    cost = Column(Float)  # in USD
    
    # Retrieval metrics
    retrieved_chunks = Column(Integer)
    relevance_score = Column(Float)
    
    # User feedback (optional)
    user_rating = Column(Integer)  # 1-5 stars
    user_feedback = Column(Text)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<ChatLog(id={self.id}, model='{self.model_name}', created_at='{self.created_at}')>"
