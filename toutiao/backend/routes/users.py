from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserRequest

from config.db_conf import get_db

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register")
async def register(
    user_data: UserRequest, db: AsyncSession = Depends(get_db)
):  # 用户信息和db
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": "用户访问令牌",
            "userInfo": {
                "id": 1,
                "username": user_data.username,
                "bio": "这个人很懒，什么都没留下",
                "avatar": "https://fastly.jsdelivr.net/npm/@vant/assets/cat.jpeg",
            },
        },
    }
