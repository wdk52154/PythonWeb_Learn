from fastapi import APIRouter, Depends
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


# 接口实现流程 
# 1 模块化路由 -> API接口规范文档
# 2 定义模型类 -> 数据库表(数据库设计文档)
# 3 在 crud 文件夹里面创建文件，封装操作数据库的方法
# 4 在路由处理函数里面调用 crud 封装好的方法，响应结果
