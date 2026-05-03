"""Article management endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import get_current_active_user
from app.crud import (
    create_article,
    delete_article,
    get_article_by_id,
    get_article_by_slug,
    get_articles,
    increment_article_views,
    update_article,
)
from app.database import get_db
from app.models import User
from app.schemas import (
    ArticleCreate,
    ArticleInDB,
    ArticleListResponse,
    ArticleResponse,
    ArticleUpdate,
)

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("", response_model=ArticleListResponse)
async def list_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    tag: str = Query(None, description="Filter by tag"),
    author: int = Query(None, description="Filter by author ID"),
    published_only: bool = Query(True, description="Show only published articles"),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """List articles with optional filtering."""
    articles, total = await get_articles(
        db,
        skip=skip,
        limit=limit,
        published_only=published_only,
        author_id=author,
        tag=tag,
    )
    
    return ArticleListResponse(
        articles=[ArticleInDB.model_validate(a) for a in articles],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("", response_model=ArticleInDB, status_code=status.HTTP_201_CREATED)
async def create_new_article(
    article_in: ArticleCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleInDB:
    """Create a new article."""
    article = await create_article(db, article_in, current_user.id)
    return ArticleInDB.model_validate(article)


@router.get("/feed", response_model=ArticleListResponse)
async def get_feed(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleListResponse:
    """Get articles feed for current user."""
    # For now, return all published articles (can be customized later)
    articles, total = await get_articles(
        db, skip=skip, limit=limit, published_only=True
    )
    
    return ArticleListResponse(
        articles=[ArticleInDB.model_validate(a) for a in articles],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.get("/{slug}", response_model=ArticleResponse)
async def get_article(
    slug: str,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    """Get a single article by slug."""
    article = await get_article_by_slug(db, slug)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Increment view count
    await increment_article_views(db, article)
    
    return ArticleResponse.model_validate(article)


@router.put("/{slug}", response_model=ArticleInDB)
async def update_existing_article(
    slug: str,
    article_in: ArticleUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ArticleInDB:
    """Update an existing article."""
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Check ownership
    if article.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this article",
        )
    
    updated_article = await update_article(db, article, article_in)
    return ArticleInDB.model_validate(updated_article)


@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_article(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an article."""
    article = await get_article_by_slug(db, slug, load_relations=False)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    # Check ownership
    if article.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this article",
        )
    
    await delete_article(db, article)


@router.get("/by-id/{article_id}", response_model=ArticleResponse)
async def get_article_by_id_endpoint(
    article_id: int,
    db: AsyncSession = Depends(get_db),
) -> ArticleResponse:
    """Get a single article by ID."""
    article = await get_article_by_id(db, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found",
        )
    
    return ArticleResponse.model_validate(article)
