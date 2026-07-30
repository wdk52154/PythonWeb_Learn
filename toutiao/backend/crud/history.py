from datetime import datetime

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.history import History
from models.news import News


# 添加浏览历史：已浏览过则刷新浏览时间，没浏览过则新增记录
async def add_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    # 查询当前用户是否浏览过这条新闻
    query = select(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(query)
    history = result.scalar_one_or_none()

    if history:
        # 浏览过：更新浏览时间为当前时间
        history.view_time = datetime.now()
    else:
        # 没浏览过：用模型类创建一个 ORM 对象并加入会话
        history = History(user_id=user_id, news_id=news_id)
        db.add(history)

    # 提交事务：执行 INSERT 或 UPDATE
    await db.commit()
    # 刷新对象：从数据库读回最新数据（自增 id、view_time）
    await db.refresh(history)

    return history


# 获取浏览历史列表：某个用户的浏览历史 + 分页功能
async def get_history_list(
        db: AsyncSession,
        user_id: int,
        page: int = 1,
        page_size: int = 10
):
    # 总量
    count_query = select(func.count()).where(History.user_id == user_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # 获取历史列表 - 联表查询 join() + 浏览时间倒序 + 分页
    # [
    #   (新闻对象, 浏览时间, 历史id)
    # ]
    offset = (page - 1) * page_size
    query = (select(News, History.view_time.label("view_time"), History.id.label("history_id"))
             .join(History, History.news_id == News.id)
             .where(History.user_id == user_id)
             .order_by(History.view_time.desc())
             .offset(offset).limit(page_size)
             )
    result = await db.execute(query)
    rows = result.all()
    return rows, total


# 删除浏览历史：删除当前用户的某一条历史记录
async def delete_history(
        db: AsyncSession,
        user_id: int,
        news_id: int
):
    stmt = delete(History).where(
        History.user_id == user_id,
        History.news_id == news_id
    )
    result = await db.execute(stmt)

    await db.commit()
    # 返回是否删除成功（影响行数 > 0）
    return result.rowcount > 0


# 清空浏览历史：当前用户的所有历史记录
async def clear_history(
        db: AsyncSession,
        user_id: int
):
    stmt = delete(History).where(History.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()

    # 返回一个删除的数量
    return result.rowcount or 0
