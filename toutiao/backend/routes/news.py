from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_conf import get_db
from crud import news

# 创建APIRouter实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/categories")
async def get_categories(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
):
    # 先获取数据库里面新闻分类数据 -> 先定义模型类 -> 封装查询数据的方法
    categories = await news.get_categories(db, skip, limit)
    return {"code": 200, "message": "获取新闻分类成功", "data": categories}


@router.get("/list")
async def get_news_list(
    category_id: int = Query(default=..., alias="categoryId"),
    page: int = 1,
    page_size: int = Query(default=10, alias="pageSize", le=100),
    db: AsyncSession = Depends(get_db),
):
    # 思路: 处理分页规则 -> 查询新闻列表 -> 计算总量 -> 计算是否还有更多
    offset = (page - 1) * page_size
    news_list = await news.get_news_list(db, category_id, offset, page_size)
    total = await news.get_news_count(db, category_id)
    has_more = (offset + len(news_list)) < total  # (跳过的 + 当前列表里面的数量) < 总量
    return {
        "code": 200,
        "message": "获取新闻列表成功",
        "data": {"list": news_list, "total": total, "hasMore": has_more},
    }


# 接口实现流程
# 1 模块化路由 -> API接口规范文档
# 2 定义模型类 -> 数据库表(数据库设计文档)
# 3 在 crud 文件夹里面创建文件，封装操作数据库的方法
# 4 在路由处理函数里面调用 crud 封装好的方法，响应结果
