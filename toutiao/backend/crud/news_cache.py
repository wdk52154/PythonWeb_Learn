
from fastapi.encoders import jsonable_encoder
from cache.news_cache import get_cached_categories,set_cache_categories
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category



# 获取新闻分类 (旁路策略)
async def get_categories(db: AsyncSession, skip: int = 0, limit: int = 100):
    # 先尝试从缓存中获取数据
    cached_categories = await get_cached_categories()
    if cached_categories:
        return cached_categories

    stmt = select(Category).offset(skip).limit(limit)
    result = await db.execute(stmt)
    categories = result.scalars().all()  # ORM

    # 写入缓存
    if categories:
        categories = jsonable_encoder(categories)
        await set_cache_categories(categories)

    # 返回数据
    return categories