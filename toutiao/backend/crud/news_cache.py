
from fastapi.encoders import jsonable_encoder
from cache.news_cache import get_cached_categories,set_cache_categories
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from models.news import Category 
from cache.news_cache import get_cache_news_list,set_cache_news_list
from models.news import News
from schemas.base import NewsItemBase

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


# 获取新闻列表
async def get_news_list(
        db: AsyncSession,
        category_id: int,
        skip: int = 0,
        limit: int = 10
):
    # 先尝试从缓存获取新闻列表
    # 跳过的数量skip = (页码 - 1) * 每页数量 -> 页码 = 跳过的数量 // 每页数量 + 1
    # await get_cache_news_list(分类id, 页码, 每页数量)

    page = skip // limit + 1
    cached_list = await get_cache_news_list(category_id, page, limit)  # 缓存数据 json
    if cached_list:
        # return cached_list  # 要的是 ORM
        return [News(**item) for item in cached_list]

    # 查询的是指定分类下的所有新闻
    stmt = select(News).where(News.category_id == category_id).offset(skip).limit(limit)
    result = await db.execute(stmt)
    news_list = result.scalars().all()

    # 写入缓存
    if news_list:
        # 先把 ORM 数据 转换 字典才能写入缓存
        # ORM 转成 Pydantic，再转为 字典
        # by_alias=False 不适用别名，保存 Python 风格，因为 Redis 数据是给后端用的
        news_data = [
            NewsItemBase.model_validate(item).model_dump(mode="json", by_alias=False)
            for item in news_list
        ]
        await set_cache_news_list(category_id, page, limit, news_data)

    return news_list