# 新闻资讯项目：后端 CRUD 流程

本文只说明后端如何完成增删改查，不展开 Vue 页面实现。代码范围主要是：

```text
backend/
├── main.py                    # FastAPI 应用入口和路由注册
├── routes/                    # 接口层：参数、鉴权、业务流程、响应
├── schemas/                   # Pydantic 请求模型和响应模型
├── crud/                      # 数据库 CRUD 函数
├── models/                    # SQLAlchemy ORM 模型
├── config/db_config.py        # 异步数据库引擎、Session 和 get_db
├── utils/auth.py              # Token 鉴权
├── utils/response.py          # 成功响应封装
└── utils/exception*.py        # 全局异常处理
```

数据库使用 PostgreSQL，ORM 使用 SQLAlchemy 2.0 异步 API。

## 1. 后端整体调用链

```text
浏览器发送 HTTP 请求
  ↓
FastAPI 路由 routes/
  ↓
Query / Path / Pydantic Schema 校验参数
  ↓
Depends(get_db) 注入 AsyncSession
Depends(get_current_user) 验证登录态
  ↓
CRUD 函数 crud/
  ↓
SQLAlchemy ORM models/
  ↓
PostgreSQL
  ↓
success_response 或 HTTPException
  ↓
统一 JSON 响应
```

后端路由在 `main.py` 中注册：

```python
app.include_router(news.router)
app.include_router(users.router)
app.include_router(favorite.router)
app.include_router(history.router)
```

各路由通过 `prefix` 形成最终接口地址：

| 路由文件 | 前缀 | 主要业务 |
| --- | --- | --- |
| `routes/news.py` | `/api/news` | 分类、列表、详情 |
| `routes/users.py` | `/api/user` | 注册、登录、用户资料 |
| `routes/favorite.py` | `/api/favorite` | 收藏增删查 |
| `routes/history.py` | `/api/history` | 浏览历史增删查 |

## 2. 数据库 Session 和事务

数据库依赖定义在 `config/db_config.py`：

```python
async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
```

路由通过 `Depends(get_db)` 获得异步 Session：

```python
@router.get("/list")
async def get_list(db: AsyncSession = Depends(get_db)):
    return await some_crud_function(db)
```

常见数据库操作：

| 操作 | SQLAlchemy 写法 | 作用 |
| --- | --- | --- |
| 查询 | `select(Model).where(...)` | 读取记录 |
| 新增 | `db.add(obj)` | 将 ORM 对象加入 Session |
| 更新 | 修改 ORM 属性或使用 `update(Model)` | 修改记录 |
| 删除 | `delete(Model).where(...)` | 删除记录 |
| 提交 | `await db.commit()` | 提交事务 |
| 刷新 | `await db.refresh(obj)` | 读取数据库生成的 ID、时间等字段 |

当前项目的多个写操作在 CRUD 函数中显式 `commit`，`get_db` 在请求正常结束时还会再次提交；发生异常时由依赖执行回滚。

## 3. Schema：请求和响应的边界

路由不直接接收任意字典，而是使用 `schemas/` 中的 Pydantic 模型：

```python
class FavoriteAddRequest(BaseModel):
    news_id: int = Field(..., alias="newsId")
```

前端发送：

```json
{
  "newsId": 10
}
```

后端函数内使用：

```python
data.news_id
```

当前项目使用 alias 处理前端驼峰和 Python 下划线命名：

| 前端字段 | Python Schema 字段 | 业务 |
| --- | --- | --- |
| `newsId` | `news_id` | 收藏、历史 |
| `pageSize` | `page_size` | 分页 |
| `oldPassword` | `old_password` | 修改密码 |
| `newPassword` | `new_password` | 修改密码 |
| `isFavorite` | `is_favorite` | 收藏状态响应 |
| `hasMore` | `has_more` | 分页响应 |
| `favoriteTime` | `favorite_time` | 收藏记录 |
| `viewTime` | `view_time` | 历史记录 |

## 4. 统一成功响应和异常响应

成功响应使用 `utils/response.py`：

```python
def success_response(message: str = "success", data=None):
    return JSONResponse(content=jsonable_encoder({
        "code": 200,
        "message": message,
        "data": data
    }))
```

接口成功时：

```json
{
  "code": 200,
  "message": "操作成功",
  "data": {}
}
```

接口主动抛出的 `HTTPException`、数据库完整性错误、SQLAlchemy 错误和未捕获异常，统一由 `utils/exception.py` 处理，返回 `code / message / data`。

常见状态：

| 状态 | 场景 |
| --- | --- |
| `400` | 请求参数或唯一约束冲突 |
| `401` | Token 缺失、无效或过期 |
| `404` | 新闻、收藏或历史记录不存在 |
| `500` | 数据库或服务器内部错误 |

## 5. Create：后端新增数据

### 5.1 用户注册

接口：`POST /api/user/register`

路由：`routes/users.py:register`

```text
接收 UserRequest(username, password)
  -> crud/users.py:get_user_by_username
  -> 用户已存在：抛出 400
  -> crud/users.py:create_user
  -> security.get_hash_password(password)
  -> 创建 User ORM 对象
  -> db.add() -> db.commit() -> db.refresh()
  -> crud/users.py:create_token
  -> 返回 token + userInfo
```

密码在写入 `user.password` 前会经过 bcrypt 哈希，数据库不保存明文密码。

### 5.2 添加收藏

接口：`POST /api/favorite/add`

请求体：

```json
{
  "newsId": 10
}
```

执行链：

```text
FavoriteAddRequest 校验 newsId
  -> get_current_user 获取当前 User
  -> favorite.add_news_favorite(db, user.id, data.news_id)
  -> Favorite(user_id=user.id, news_id=data.news_id)
  -> db.add(favorite)
  -> db.commit()
  -> db.refresh(favorite)
  -> success_response()
```

`favorite` 表对 `user_id + news_id` 设置唯一约束，同一用户不能重复添加同一篇新闻。

### 5.3 添加浏览历史

接口：`POST /api/history/add`

请求体：

```json
{
  "newsId": 10
}
```

历史记录不是简单的 INSERT。`crud/history.py:add_history` 先查询：

```text
按 user_id + news_id 查询 History
  -> 找到记录：更新 view_time（Update）
  -> 没找到记录：创建 History（Create）
  -> db.commit()
  -> db.refresh(history)
```

这样同一个用户重复浏览同一新闻时，列表中仍保留一条记录，但浏览时间变为最新时间。

## 6. Read：后端查询数据

### 6.1 查询新闻分类

接口：`GET /api/news/categories`

路由：`routes/news.py:get_categories`

```text
Depends(get_db) 注入 AsyncSession
  -> news_cache.get_categories(db, skip, limit)
  -> 必要时调用 crud/news.py:get_categories
  -> select(Category).offset(skip).limit(limit)
  -> 返回分类数组
```

### 6.2 查询新闻列表

接口：

```text
GET /api/news/list?categoryId=1&page=1&pageSize=10
```

路由先将分页参数转换成数据库偏移量：

```python
offset = (page - 1) * page_size
```

随后执行两次查询：

```text
crud/news.py:get_news_list
  -> SELECT News
  -> WHERE News.category_id = category_id
  -> OFFSET offset LIMIT page_size

crud/news.py:get_news_count
  -> SELECT COUNT(News.id)
  -> WHERE News.category_id = category_id
```

路由根据总量计算：

```python
has_more = (offset + len(news_list)) < total
```

最终返回：

```json
{
  "code": 200,
  "message": "获取新闻列表成功",
  "data": {
    "list": [],
    "total": 403,
    "hasMore": true
  }
}
```

### 6.3 查询新闻详情

接口：`GET /api/news/detail?id=10`

该接口包含查询、更新和组合响应三个步骤：

```text
news.get_news_detail(db, news_id)
  -> SELECT News WHERE News.id = news_id
  -> 不存在：404

news.increase_news_views(db, news_id)
  -> UPDATE News SET views = views + 1
  -> db.commit()

news.get_related_news(db, news_id, category_id)
  -> 查询同分类且排除当前新闻
  -> 按浏览量和发布时间倒序
  -> 最多返回 5 条
```

路由最后手动组装详情字段、相关推荐和统一响应。

### 6.4 查询收藏列表

接口：`GET /api/favorite/list?page=1&pageSize=10`

`crud/favorite.py:get_favorite_list` 同时查询：

```text
Favorite.created_at 总数
  -> 计算 total

News JOIN Favorite
  -> 按 Favorite.created_at DESC 排序
  -> OFFSET + LIMIT 分页
  -> 返回 News、favorite_time、favorite_id
```

路由将查询结果转换为 `FavoriteListResponse`，响应中同时包含新闻信息和收藏信息。

### 6.5 查询浏览历史

接口：`GET /api/history/list?page=1&pageSize=10`

`crud/history.py:get_history_list` 使用 `News JOIN History`：

```text
按当前 user.id 过滤
  -> 按 History.view_time DESC 排序
  -> 分页查询
  -> 转换为 HistoryNewsItemResponse
  -> 返回 list、total、hasMore
```

## 7. Update：后端更新数据

### 7.1 修改个人资料

接口：`PUT /api/user/update`

请求体：

```json
{
  "bio": "新的个人简介"
}
```

执行链：

```text
UserUpdateRequest 校验请求体
  -> get_current_user 获取当前用户
  -> users.update_user(db, user.username, user_data)
  -> user_data.model_dump(exclude_unset=True, exclude_none=True)
  -> UPDATE user SET bio = ...
  -> db.commit()
  -> 查询更新后的 User
  -> UserInfoResponse.model_validate(user)
  -> success_response()
```

`exclude_unset=True` 的作用是只更新请求中实际提交的字段，不修改没有传入的资料。

### 7.2 修改密码

接口：`PUT /api/user/password`

执行链：

```text
UserChangePasswordRequest 校验 oldPassword、newPassword
  -> get_current_user 获取当前用户
  -> verify_password(old_password, user.password)
  -> 校验失败：返回修改失败
  -> get_hash_password(new_password)
  -> 更新 user.password
  -> db.add(user) -> db.commit() -> db.refresh(user)
  -> success_response()
```

旧密码只用于验证，新密码经过哈希后才写入数据库。

### 7.3 更新新闻浏览量

新闻浏览量的更新由详情接口内部触发，不对前端单独暴露 PUT 接口：

```python
stmt = update(News).where(
    News.id == news_id
).values(
    views=News.views + 1
)
result = await db.execute(stmt)
await db.commit()
```

使用 `News.views + 1` 由数据库执行自增，避免先读取旧值再写回时产生覆盖。

### 7.4 更新浏览历史时间

用户再次浏览同一新闻时，`add_history` 查到已有 `History` 对象后执行：

```python
history.view_time = datetime.now()
await db.commit()
```

该接口对外是 `POST /api/history/add`，但内部根据数据是否存在分别完成 Create 或 Update。

## 8. Delete：后端删除数据

### 8.1 删除单条收藏

接口：`DELETE /api/favorite/remove?newsId=10`

```text
Query 获取 newsId
  -> get_current_user 获取 user.id
  -> DELETE Favorite
  -> WHERE user_id = 当前用户 AND news_id = 参数
  -> db.commit()
  -> 检查 result.rowcount
  -> 0 行：404
  -> 成功：返回 success_response()
```

删除条件必须同时包含当前用户和新闻 ID，不能只根据新闻 ID 删除。

### 8.2 清空收藏

接口：`DELETE /api/favorite/clear`

```text
get_current_user
  -> DELETE FROM favorite WHERE user_id = 当前用户
  -> db.commit()
  -> 返回删除数量
```

### 8.3 删除单条历史

接口：`DELETE /api/history/delete/{news_id}`

```text
Path 获取 news_id
  -> get_current_user 获取 user.id
  -> DELETE History
  -> WHERE user_id = 当前用户 AND news_id = 参数
  -> db.commit()
  -> 没有命中：404
  -> 成功：success_response()
```

### 8.4 清空历史

接口：`DELETE /api/history/clear`

```text
get_current_user
  -> DELETE FROM history WHERE user_id = 当前用户
  -> db.commit()
  -> success_response(message="清空成功")
```

## 9. Token 鉴权流程

收藏、历史和用户资料接口都通过 `Depends(get_current_user)` 鉴权：

```text
请求头 Authorization
  -> utils/auth.py:get_current_user
  -> 去掉 "Bearer " 前缀
  -> crud/users.py:get_user_by_token
  -> 查询 user_token
  -> 判断 Token 是否存在和过期
  -> 查询 user
  -> 将 User 注入路由
```

后端不能使用前端请求体中的 `userId` 作为权限依据，应始终使用鉴权依赖返回的 `user.id`。

## 10. 新增后端 CRUD 模块的步骤

以新增评论模块为例：

1. 在 `db/database.sql` 设计 `comment` 表、外键、索引和约束。
2. 在 `models/` 创建 SQLAlchemy ORM 模型。
3. 在 `schemas/` 创建新增、修改和响应模型。
4. 在 `crud/` 创建 `create_comment`、`get_comment_list`、`update_comment`、`delete_comment`。
5. 在 `routes/` 创建 `APIRouter`，使用 `Query`、`Path`、Pydantic Schema 和 `Depends`。
6. 在路由中调用 CRUD 函数，不在路由里直接写 SQL。
7. 使用 `success_response` 统一成功返回；业务错误主动抛 `HTTPException`。
8. 在 `main.py` 中 `include_router` 注册新路由。
9. 启动服务后通过 `/docs` 或 `test_main.http` 验证请求、响应和错误场景。

推荐保持以下结构：

```text
请求
  -> routes：参数校验、鉴权、流程编排
  -> schemas：请求和响应数据结构
  -> crud：数据库读写
  -> models：表结构映射
  -> PostgreSQL
  -> response / exception：统一返回
```

## 11. 后端联调注意项

- 私有接口必须使用 `Depends(get_current_user)`，并用当前用户 ID 过滤数据。
- 新增、更新、删除操作需要明确事务提交和异常回滚行为。
- 列表接口应同时返回 `list`、`total` 和 `hasMore`，方便前端分页。
- 前端驼峰字段通过 Schema alias 映射到 Python 下划线字段。
- 对唯一约束、外键约束和不存在资源，要返回明确的业务错误。
- 当前 `crud/users.py:update_user` 最后写成了 `return update_user`，应修正为 `return updated_user`。
- 新闻列表直接返回 ORM 对象时，时间字段命名需要和前端统一；当前存在 `publish_time`、`publishedTime`、`publishTime` 不一致的问题。
