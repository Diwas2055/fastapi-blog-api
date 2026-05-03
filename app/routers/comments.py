"""Comment management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_active_user
from app.crud import (
    create_comment,
    delete_comment,
    get_article_by_slug,
    get_comment_by_id,
    get_comments_by_article,
    update_comment,
)
from app.database import get_db
from app.models import User
from app.schemas import CommentCreate, CommentInDB, CommentUpdate

router = APIRouter(prefix="/articles/{slug}/comments", tags=["comments"])


@router.get("", response_model=list[CommentInDB])
async def list_comments(
    slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[CommentInDB]:
    """List comments for an article."""
    # Get article
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    comments, _ = await get_comments_by_article(db, article.id, skip=skip, limit=limit)
    return [CommentInDB.model_validate(c) for c in comments]


@router.post("", response_model=CommentInDB, status_code=status.HTTP_201_CREATED)
async def add_comment(
    slug: str,
    comment_in: CommentCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentInDB:
    """Add a comment to an article."""
    # Get article
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    comment = await create_comment(db, comment_in, article.id, current_user.id)
    
    # Reload with author relationship
    comment = await get_comment_by_id(db, comment.id)
    return CommentInDB.model_validate(comment)


@router.put("/{comment_id}", response_model=CommentInDB)
async def update_existing_comment(
    slug: str,
    comment_id: int,
    comment_in: CommentUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> CommentInDB:
    """Update an existing comment."""
    # Verify article exists
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Get comment
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.article_id != article.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    # Check ownership
    if comment.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this comment",
        )
    
    updated_comment = await update_comment(db, comment, comment_in.body)
    return CommentInDB.model_validate(updated_comment)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_comment(
    slug: str,
    comment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a comment."""
    # Verify article exists
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Get comment
    comment = await get_comment_by_id(db, comment_id)
    if not comment or comment.article_id != article.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Comment not found",
        )
    
    # Check ownership (comment author or article author or superuser)
    if (
        comment.author_id != current_user.id
        and article.author_id != current_user.id
        and not current_user.is_superuser
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this comment",
        )
    
    await delete_comment(db, comment)
