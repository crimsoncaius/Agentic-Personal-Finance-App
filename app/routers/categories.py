# app/routers/categories.py

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from ..database import SessionLocal, engine
from .. import models
from ..schemas import CategoryCreate, CategoryRead

router = APIRouter(
    prefix="/categories",
    tags=["categories"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=CategoryRead)
def create_category(category: CategoryCreate, db: Session = Depends(get_db)):
    # Check if category already exists
    existing = db.query(models.Category).filter(models.Category.name == category.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    db_category = models.Category(
        name=category.name,
        transaction_type=category.transaction_type
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/", response_model=List[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all() 