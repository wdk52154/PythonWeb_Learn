from fastapi import APIRouter

# 创建APIRouter实例
# prefix 路由前缀（API 接口规范文档）
# tags 分组 标签
router = APIRouter(prefix="/api/news", tags=["news"])


@router.get("/categories")
async def get_categories():
    return {"message": "获取分类成功"}
 