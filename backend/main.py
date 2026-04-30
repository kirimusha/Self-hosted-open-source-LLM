from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import time
import shutil
from pathlib import Path

from database import engine, get_db, Base
from models import User
from crud import DatabaseOperations as db_ops
from rag_module import generate_wbs, get_rag
from llm_client import call_llm

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="WBS Generator API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class GenerateRequest(BaseModel):
    goal: str
    username: str = "anonymous"

class GenerateResponse(BaseModel):
    query_id: int
    wbs: str
    references: List[str]
    processing_time_seconds: float

class FeedbackRequest(BaseModel):
    query_id: int
    username: str
    score: int
    comment: Optional[str] = ""

@app.get("/")
async def root():
    return {"message": "WBS Generator API", "status": "running"}

@app.post("/generate", response_model=GenerateResponse)
async def generate_wbs_endpoint(request: GenerateRequest, db: Session = Depends(get_db)):
    start_time = time.time()
    
    user = db_ops.get_or_create_user(db, request.username)
    prompt, sources = await generate_wbs(request.goal)
    wbs_result = await call_llm(prompt)
    processing_time = time.time() - start_time
    
    query = db_ops.save_query(
        db=db,
        user_id=user.id,
        goal=request.goal,
        generated_wbs=wbs_result,
        references=sources,
        processing_time=processing_time
    )
    
    return GenerateResponse(
        query_id=query.id,
        wbs=wbs_result,
        references=sources,
        processing_time_seconds=processing_time
    )

@app.post("/feedback")
async def submit_feedback(request: FeedbackRequest, db: Session = Depends(get_db)):
    if request.score < 1 or request.score > 5:
        raise HTTPException(400, "Score must be 1-5")
    
    user = db_ops.get_or_create_user(db, request.username)
    feedback = db_ops.save_feedback(
        db=db,
        query_id=request.query_id,
        user_id=user.id,
        score=request.score,
        comment=request.comment or ""
    )
    
    return {"message": "Feedback saved", "feedback_id": feedback.id}

@app.post("/admin/upload-document")
async def upload_document(
    username: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    user = db_ops.get_or_create_user(db, username)
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    upload_dir = Path("/knowledge_base/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    doc = db_ops.save_document(
        db=db,
        filename=file.filename,
        file_path=str(file_path),
        file_type=file.filename.split('.')[-1],
        user_id=user.id
    )
    
    rag = get_rag()
    chunks_count = rag.index_document(str(file_path))
    db_ops.mark_document_indexed(db, doc.id)
    
    return {
        "message": "Document uploaded and indexed",
        "document_id": doc.id,
        "chunks_created": chunks_count
    }

@app.post("/admin/index-all")
async def index_all_documents(username: str, db: Session = Depends(get_db)):
    user = db_ops.get_or_create_user(db, username)
    if not user.is_admin:
        raise HTTPException(403, "Admin access required")
    
    rag = get_rag()
    results = rag.index_all_documents()
    
    return {"status": "completed", "indexed_documents": results}

@app.get("/stats")
async def get_statistics(db: Session = Depends(get_db)):
    stats = db_ops.get_statistics(db)
    stats["meets_requirement_percentile_95"] = stats["percentile_95_time_seconds"] <= 400
    stats["meets_requirement_positive_feedback"] = stats["positive_feedback_percentage"] >= 60
    return stats

@app.get("/health")
async def health_check():
    return {"status": "healthy"}