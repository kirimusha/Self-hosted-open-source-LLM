from sqlalchemy.orm import Session
from sqlalchemy import func
import models
from datetime import datetime
from typing import List, Optional

class DatabaseOperations:
    
    @staticmethod
    def get_or_create_user(db: Session, username: str, email: str = None, company: str = None):
        user = db.query(models.User).filter(models.User.username == username).first()
        if not user:
            user = models.User(
                username=username,
                email=email or username,
                company=company or ""
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return user
    
    @staticmethod
    def save_query(db: Session, user_id: int, goal: str, generated_wbs: str, 
                   references: List[str], processing_time: float):
        query = models.QueryHistory(
            user_id=user_id,
            goal=goal,
            generated_wbs=generated_wbs,
            references=references,
            processing_time=processing_time,
            status="done"
        )
        db.add(query)
        db.commit()
        db.refresh(query)
        return query
    
    @staticmethod
    def save_feedback(db: Session, query_id: int, user_id: int, score: int, comment: str = ""):
        feedback = models.Feedback(
            query_id=query_id,
            user_id=user_id,
            score=score,
            comment=comment
        )
        db.add(feedback)
        db.commit()
        return feedback
    
    @staticmethod
    def save_document(db: Session, filename: str, file_path: str, file_type: str, user_id: int):
        doc = models.Document(
            filename=filename,
            file_path=file_path,
            file_type=file_type,
            uploaded_by=user_id,
            is_indexed=False
        )
        db.add(doc)
        db.commit()
        db.refresh(doc)
        return doc
    
    @staticmethod
    def mark_document_indexed(db: Session, doc_id: int):
        doc = db.query(models.Document).filter(models.Document.id == doc_id).first()
        if doc:
            doc.is_indexed = True
            db.commit()
    
    @staticmethod
    def get_statistics(db: Session):
        total_queries = db.query(models.QueryHistory).count()
        
        # 95th percentile
        times = [q.processing_time for q in db.query(models.QueryHistory.processing_time).all() if q.processing_time]
        percentile_95 = sorted(times)[int(len(times) * 0.95)] if times else 0
        
        # Average feedback
        avg_score = db.query(func.avg(models.Feedback.score)).scalar() or 0
        
        # Positive feedback rate (score >= 4)
        total_feedbacks = db.query(models.Feedback).count()
        positive_feedbacks = db.query(models.Feedback).filter(models.Feedback.score >= 4).count()
        positive_rate = (positive_feedbacks / total_feedbacks * 100) if total_feedbacks > 0 else 0
        
        return {
            "total_queries": total_queries,
            "percentile_95_time_seconds": percentile_95,
            "average_feedback_score": float(avg_score),
            "positive_feedback_percentage": positive_rate
        }