"""
Feedback API endpoints
POST: public (any user can submit feedback from chat)
GET list / GET {id}: admin only
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field

from app.database import get_db
from app.models import ResponseFeedback
from app.core.deps import get_current_admin
from app.utils.logger import setup_logger

logger = setup_logger("api_feedback", "./logs/api_feedback.log")

router = APIRouter(prefix="/feedback", tags=["feedback"])


# --- Schemas ---
class FeedbackCreate(BaseModel):
    question: str = Field(..., min_length=1)
    answer: str = Field(...)
    rating: str = Field(..., pattern="^(positive|negative)$")
    reason: Optional[str] = Field(None, max_length=100)
    comment: Optional[str] = Field(None, max_length=2000)


class FeedbackItem(BaseModel):
    id: int
    question: str
    answer: str
    rating: str
    reason: Optional[str]
    comment: Optional[str]
    created_at: str

    class Config:
        from_attributes = True


class FeedbackListResponse(BaseModel):
    total: int
    items: list[FeedbackItem]


# --- Endpoints ---
@router.post("/", status_code=201)
def create_feedback(data: FeedbackCreate, db: Session = Depends(get_db)):
    """Save user feedback for a bot response."""
    try:
        fb = ResponseFeedback(
            question=data.question,
            answer=data.answer,
            rating=data.rating,
            reason=data.reason,
            comment=data.comment,
        )
        db.add(fb)
        db.commit()
        db.refresh(fb)
        logger.info(f"Feedback saved: id={fb.id}, rating={data.rating}, reason={data.reason}")
        return {"id": fb.id, "status": "saved"}
    except Exception as e:
        logger.error(f"Error saving feedback: {e}", exc_info=True)
        db.rollback()
        raise


@router.get("/", response_model=FeedbackListResponse)
def list_feedbacks(
    rating: Optional[str] = Query(None, pattern="^(positive|negative)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin),
):
    """List feedbacks with optional filter by rating."""
    query = db.query(ResponseFeedback)
    if rating:
        query = query.filter(ResponseFeedback.rating == rating)
    total = query.count()
    rows = query.order_by(ResponseFeedback.created_at.desc()).offset(skip).limit(limit).all()
    items = [
        FeedbackItem(
            id=r.id,
            question=r.question[:200] + ("..." if len(r.question) > 200 else ""),
            answer=r.answer[:200] + ("..." if len(r.answer) > 200 else ""),
            rating=r.rating,
            reason=r.reason,
            comment=r.comment,
            created_at=r.created_at.isoformat() if r.created_at else "",
        )
        for r in rows
    ]
    return FeedbackListResponse(total=total, items=items)


@router.get("/{feedback_id}")
def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    _admin: str = Depends(get_current_admin),
):
    """Get full feedback details (question + answer) for admin panel."""
    fb = db.query(ResponseFeedback).filter(ResponseFeedback.id == feedback_id).first()
    if not fb:
        raise HTTPException(status_code=404, detail="Feedback not found")
    return {
        "id": fb.id,
        "question": fb.question,
        "answer": fb.answer,
        "rating": fb.rating,
        "reason": fb.reason,
        "comment": fb.comment,
        "created_at": fb.created_at.isoformat() if fb.created_at else "",
    }
