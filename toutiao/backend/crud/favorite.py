from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.favorite import Favorite
from models.news import News


# 检查收藏状态：当前用户 是否 收藏了这一条新闻
async def is_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    query = select(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(query)
    # 是否有收藏记录
    return result.scalar_one_or_none() is not None


# 添加收藏
async def add_news_favorite(
        db: AsyncSession,  # 数据库会话（由路由层 Depends(get_db) 注入）
        user_id: int,      # 用户id
        news_id: int       # 新闻id
):
    # 用模型类创建一个 ORM 对象（此时只存在于内存，还没有进数据库）
    favorite = Favorite(user_id=user_id, news_id=news_id)
    # 把对象加入会话（标记为"待插入"状态，还没有真正执行 SQL）
    db.add(favorite)
    # 提交事务：把会话里待插入的数据写入数据库（执行 INSERT）
    await db.commit()
    # 刷新对象：从数据库读回最新数据（拿到自增 id、created_at 默认值）
    await db.refresh(favorite)

    # 返回完整对象给路由层（此时 id 等字段都有值了）
    return favorite


# 取消收藏
async def remove_news_favorite(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    stmt = delete(Favorite).where(
        Favorite.user_id == user_id,
        Favorite.news_id == news_id
    )
    result = await db.execute(stmt)

    await db.commit()
    return result.rowcount > 0



# 获取收藏列表：获取的是某个用户的收藏列表 + 分页功能
async def get_favorite_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总量 + 收藏的新闻列表
    count_query = select(func.count()).where(Favorite.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取收藏列表 - 联表查询 join() + 收藏时间排序 + 分页
    # select(查询主体模型类, 字段别名).join(联合查询的模型类, 联合查询的条件).where().order_by().offset().limit()
    # 别名： Favorite.created_at.label("favorite_time")
    offset = (page - 1) * page_size
    # [
    #   (新闻对象, 收藏时间, 收藏id)
    # ]
    query = (select(News, Favorite.created_at.label("favorite_time"), Favorite.id.label("favorite_id"))
             .join(Favorite, Favorite.news_id == News.id)
             .where(Favorite.user_id == user_id)
             .order_by(Favorite.created_at.desc())
             .offset(offset).limit(page_size)
             )
    result = await db.execute(query)
    rows = result.all()
    return rows, total
