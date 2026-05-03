"""Tag management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_active_user, get_current_superuser
from app.crud import (
    create_tag,
    delete_tag,
    get_all_tags,
    get_popular_tags,
    get_tag_by_name,
)
from app.database import get_db
from app.models import User
from app.schemas import TagCreate, TagInDB

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagInDB])
async def list_tags(
    db: AsyncSession = Depends(get_db),
) -> list[TagInDB]:
    """List all tags."""
    tags = await get_all_tags(db)
    return [TagInDB.model_validate(t) for t in tags]


@router.get("/popular")
async def get_popular_tags_endpoint(
    limit: int = 10,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """Get most popular tags by article count."""
    popular = await get_popular_tags(db, limit=limit)
    return [{"name": name, "article_count": count} for name, count in popular]


@router.post("", response_model=TagInDB, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_in: TagCreate,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> TagInDB:
    """Create a new tag (superuser only)."""
    # Check if tag already exists
    existing = await get_tag_by_name(db, tag_in.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag already exists",
        )
    
    tag = await create_tag(db, tag_in)
    return TagInDB.model_validate(tag)


@router.delete("/{tag_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_name: str,
    current_user: User = Depends(get_current_superuser),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a tag (superuser only)."""
    tag = await get_tag_by_name(db, tag_name)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    
    await delete_tag(db, tag)
