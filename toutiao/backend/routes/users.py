from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from schemas.users import UserRequest

from config.db_conf import get_db
from crud import users

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post("/register")
async def register(
    user_data: UserRequest, db: AsyncSession = Depends(get_db)
):  # 用户信息和db
    # 注册逻辑：验证用户是否存在 -> 创建用户 -> 生成Token -> 响应结果
    existing_user = await users.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="用户已存在")
    user = await users.create_user(db, user_data)
    return {
        "code": 200,
        "message": "注册成功",
        "data": {
            "token": "用户访问令牌",
            "userInfo": {
                "id": user.id,
                "username": user.username,
                "bio": user.bio,
                "avatar": user.avatar,
            },
        },
    }
