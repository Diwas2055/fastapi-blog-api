"""CRUD operations for database models."""
from typing import List, Optional

from slugify import slugify
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.auth import get_password_hash
from app.models import Article, Comment, Tag, User, article_tags
from app.schemas import (
    ArticleCreate,
    ArticleUpdate,
    CommentCreate,
    TagCreate,
    UserCreate,
    UserUpdate,
)


# ============== User CRUD ==============

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    """Create a new user in the database.

    Args:
        db: Database session for executing the query.
        user_in: User creation data including email, username, password,
            and optional full_name and bio.

    Returns:
        The newly created User model instance with generated ID.

    Raises:
        IntegrityError: If email or username already exists.

    Example:
        >>> user_data = UserCreate(email="user@example.com", username="john")
        >>> user = await create_user(db, user_data)
    """
    db_user = User(
        email=user_in.email,
        username=user_in.username,
        full_name=user_in.full_name,
        bio=user_in.bio,
        hashed_password=get_password_hash(user_in.password),
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Retrieve a user by their unique ID.

    Args:
        db: Database session for executing the query.
        user_id: The unique identifier of the user.

    Returns:
        User instance if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Retrieve a user by their email address.

    Args:
        db: Database session for executing the query.
        email: The email address to search for.

    Returns:
        User instance if found, None otherwise.
    """
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user(
    db: AsyncSession, user: User, user_in: UserUpdate
) -> User:
    """Update user information."""
    update_data = user_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(db: AsyncSession, user: User) -> None:
    """Delete a user."""
    await db.delete(user)
    await db.commit()


# ============== Article CRUD ==============

def generate_slug(title: str) -> str:
    """Generate URL-friendly slug from title."""
    return slugify(title, max_length=255)


async def get_or_create_tags(
    db: AsyncSession, tag_names: List[str]
) -> List[Tag]:
    """Get existing tags or create new ones."""
    if not tag_names:
        return []
    
    normalized_names = [name.lower().strip() for name in tag_names if name.strip()]
    
    # Get existing tags
    result = await db.execute(
        select(Tag).where(Tag.name.in_(normalized_names))
    )
    existing_tags = result.scalars().all()
    existing_names = {tag.name for tag in existing_tags}
    
    # Create new tags
    new_tags = []
    for name in normalized_names:
        if name not in existing_names:
            new_tag = Tag(name=name)
            db.add(new_tag)
            new_tags.append(new_tag)
    
    if new_tags:
        await db.commit()
        for tag in new_tags:
            await db.refresh(tag)
    
    return list(existing_tags) + new_tags


async def create_article(
    db: AsyncSession, article_in: ArticleCreate, author_id: int
) -> Article:
    """Create a new article."""
    # Generate unique slug
    base_slug = generate_slug(article_in.title)
    slug = base_slug
    counter = 1
    
    while await db.execute(
        select(Article).where(Article.slug == slug)
    ):
        existing = await db.scalar(
            select(Article).where(Article.slug == slug)
        )
        if not existing:
            break
        slug = f"{base_slug}-{counter}"
        counter += 1
    
    # Get or create tags
    tags = await get_or_create_tags(db, article_in.tag_list)
    
    db_article = Article(
        slug=slug,
        title=article_in.title,
        description=article_in.description,
        body=article_in.body,
        author_id=author_id,
        published=article_in.published,
    )
    db_article.tags = tags
    
    db.add(db_article)
    await db.commit()
    await db.refresh(db_article)
    return db_article


async def get_article_by_id(
    db: AsyncSession, article_id: int, load_relations: bool = True
) -> Optional[Article]:
    """Get article by ID with optional relationship loading."""
    query = select(Article).where(Article.id == article_id)
    if load_relations:
        query = query.options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.comments).selectinload(Comment.author),
        )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_article_by_slug(
    db: AsyncSession, slug: str, load_relations: bool = True
) -> Optional[Article]:
    """Get article by slug."""
    query = select(Article).where(Article.slug == slug)
    if load_relations:
        query = query.options(
            selectinload(Article.author),
            selectinload(Article.tags),
            selectinload(Article.comments).selectinload(Comment.author),
        )
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_articles(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 20,
    published_only: bool = True,
    author_id: Optional[int] = None,
    tag: Optional[str] = None,
) -> tuple[List[Article], int]:
    """Get articles with filtering and pagination."""
    query = select(Article)
    count_query = select(func.count(Article.id))
    
    # Apply filters
    if published_only:
        query = query.where(Article.published.is_(True))
        count_query = count_query.where(Article.published.is_(True))
    
    if author_id:
        query = query.where(Article.author_id == author_id)
        count_query = count_query.where(Article.author_id == author_id)
    
    if tag:
        query = query.join(article_tags).join(Tag).where(Tag.name == tag.lower())
        count_query = count_query.join(article_tags).join(Tag).where(Tag.name == tag.lower())
    
    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results with relationships
    query = query.options(
        selectinload(Article.author),
        selectinload(Article.tags),
    )
    query = query.order_by(Article.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    articles = list(result.scalars().all())
    
    return articles, total


async def update_article(
    db: AsyncSession, article: Article, article_in: ArticleUpdate
) -> Article:
    """Update an article."""
    update_data = article_in.model_dump(exclude_unset=True)
    
    # Handle tags separately
    if "tag_list" in update_data:
        tag_list = update_data.pop("tag_list")
        if tag_list is not None:
            article.tags = await get_or_create_tags(db, tag_list)
    
    # Update slug if title changed
    if "title" in update_data and update_data["title"] != article.title:
        base_slug = generate_slug(update_data["title"])
        slug = base_slug
        counter = 1
        
        while True:
            existing = await db.scalar(
                select(Article).where(Article.slug == slug, Article.id != article.id)
            )
            if not existing:
                break
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        article.slug = slug
    
    # Update other fields
    for field, value in update_data.items():
        setattr(article, field, value)
    
    await db.commit()
    await db.refresh(article)
    return article


async def delete_article(db: AsyncSession, article: Article) -> None:
    """Delete an article."""
    await db.delete(article)
    await db.commit()


async def increment_article_views(db: AsyncSession, article: Article) -> None:
    """Increment article view count."""
    article.views_count += 1
    await db.commit()


# ============== Comment CRUD ==============

async def create_comment(
    db: AsyncSession, comment_in: CommentCreate, article_id: int, author_id: int
) -> Comment:
    """Create a new comment."""
    db_comment = Comment(
        body=comment_in.body,
        article_id=article_id,
        author_id=author_id,
    )
    db.add(db_comment)
    await db.commit()
    await db.refresh(db_comment)
    return db_comment


async def get_comment_by_id(
    db: AsyncSession, comment_id: int
) -> Optional[Comment]:
    """Get comment by ID."""
    result = await db.execute(
        select(Comment)
        .where(Comment.id == comment_id)
        .options(selectinload(Comment.author))
    )
    return result.scalar_one_or_none()


async def get_comments_by_article(
    db: AsyncSession, article_id: int, skip: int = 0, limit: int = 20
) -> tuple[List[Comment], int]:
    """Get comments for an article."""
    count_result = await db.execute(
        select(func.count(Comment.id)).where(Comment.article_id == article_id)
    )
    total = count_result.scalar()
    
    result = await db.execute(
        select(Comment)
        .where(Comment.article_id == article_id)
        .options(selectinload(Comment.author))
        .order_by(Comment.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    comments = list(result.scalars().all())
    
    return comments, total


async def update_comment(
    db: AsyncSession, comment: Comment, body: str
) -> Comment:
    """Update a comment."""
    comment.body = body
    await db.commit()
    await db.refresh(comment)
    return comment


async def delete_comment(db: AsyncSession, comment: Comment) -> None:
    """Delete a comment."""
    await db.delete(comment)
    await db.commit()


# ============== Tag CRUD ==============

async def create_tag(db: AsyncSession, tag_in: TagCreate) -> Tag:
    """Create a new tag."""
    db_tag = Tag(name=tag_in.name.lower().strip())
    db.add(db_tag)
    await db.commit()
    await db.refresh(db_tag)
    return db_tag


async def get_tag_by_id(db: AsyncSession, tag_id: int) -> Optional[Tag]:
    """Get tag by ID."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tag_by_name(db: AsyncSession, name: str) -> Optional[Tag]:
    """Get tag by name."""
    result = await db.execute(
        select(Tag).where(Tag.name == name.lower().strip())
    )
    return result.scalar_one_or_none()


async def get_all_tags(db: AsyncSession) -> List[Tag]:
    """Get all tags."""
    result = await db.execute(select(Tag).order_by(Tag.name))
    return list(result.scalars().all())


async def get_popular_tags(db: AsyncSession, limit: int = 10) -> List[tuple]:
    """Get most popular tags by article count."""
    result = await db.execute(
        select(Tag.name, func.count(article_tags.c.article_id).label("article_count"))
        .join(article_tags)
        .group_by(Tag.id)
        .order_by(func.count(article_tags.c.article_id).desc())
        .limit(limit)
    )
    return list(result.all())


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    """Delete a tag."""
    await db.delete(tag)
    await db.commit()
