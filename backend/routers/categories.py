# app/routers/categories.py

from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from typing import List
import logging

from ..database import get_db
from .. import models
from ..schemas import CategoryCreate, CategoryRead
from ..auth import get_current_active_user
from ..models import User

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Remove the trailing slash from the prefix
router = APIRouter(prefix="/categories", tags=["categories"])


@router.post("", response_model=CategoryRead)  # Handle POST without trailing slash
@router.post("/", response_model=CategoryRead)  # Handle POST with trailing slash
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    logger.info(f"Creating category for user {current_user.id}: {category.dict()}")
    # Check if category already exists for this user
    existing = (
        db.query(models.Category)
        .filter(
            models.Category.name == category.name,
            models.Category.user_id == current_user.id,
        )
        .first()
    )
    if existing:
        logger.warning(
            f"Category {category.name} already exists for user {current_user.id}"
        )
        raise HTTPException(status_code=400, detail="Category already exists")

    db_category = models.Category(
        name=category.name,
        transaction_type=category.transaction_type,
        user_id=current_user.id,
    )
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    logger.info(f"Category created: {db_category.id}")
    return db_category


@router.get("", response_model=List[CategoryRead])  # Handle GET without trailing slash
@router.get("/", response_model=List[CategoryRead])  # Handle GET with trailing slash
async def list_categories(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    logger.info("Received request to list categories")
    logger.debug(f"Request headers: {dict(request.headers)}")

    try:
        logger.info(f"Attempting to list categories for user {current_user.id}")
        categories = (
            db.query(models.Category)
            .filter(models.Category.user_id == current_user.id)
            .all()
        )
        logger.info(f"Found {len(categories)} categories")
        logger.debug(f"Categories: {[c.name for c in categories]}")
        return categories
    except Exception as e:
        logger.error(f"Error listing categories: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving categories"
        )
