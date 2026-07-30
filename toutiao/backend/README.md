# Toutiao Backend

新闻资讯应用后端服务，基于 FastAPI 开发，提供新闻浏览、用户认证、收藏管理和浏览历史等接口。项目使用 PostgreSQL 保存业务数据，使用 Redis 缓存新闻分类、新闻列表、新闻详情和相关新闻数据。

## 技术栈

- Python 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy 2.0 async ORM
- asyncpg
- PostgreSQL
- redis.asyncio
- Pydantic v2
- Passlib + bcrypt

## 目录结构

```text
backend/
├── main.py                    # FastAPI 应用入口，注册中间件和路由
├── requirements.txt           # Python 依赖
├── test_main.http             # 简单 HTTP 调试请求
├── config/
│   ├── db_config.py           # PostgreSQL 异步连接、Session、依赖注入
│   └── cache_config.py        # Redis 连接配置
├── db/
│   └── database.sql           # PostgreSQL 建表脚本和种子数据
├── models/
│   ├── news.py                # news / news_category / related_news
│   ├── users.py               # user / user_token
│   ├── favorite.py            # favorite
│   └── history.py             # history
├── schemas/
│   ├── base.py                # 新闻通用响应模型
│   ├── users.py               # 用户请求和响应模型
│   ├── favorite.py            # 收藏请求和响应模型
│   └── history.py             # 浏览历史请求和响应模型
├── routes/
│   ├── news.py                # /api/news
│   ├── users.py               # /api/user
│   ├── favorite.py            # /api/favorite
│   └── history.py             # /api/history
├── crud/
│   ├── news.py                # 新闻查询、详情、浏览量、相关推荐
│   ├── news_cache.py          # 新闻缓存旁路逻辑
│   ├── users.py               # 用户注册、登录、Token、资料更新
│   ├── favorite.py            # 收藏增删查
│   └── history.py             # 历史记录增删查
├── cache/
│   └── news_cache.py          # Redis key 读写封装
└── utils/
    ├── auth.py                # Authorization Token 解析
    ├── security.py            # bcrypt 密码哈希和校验
    ├── redis_cache.py         # Redis 通用 get/setex 封装
    ├── response.py            # success_response
    ├── exception.py           # 全局异常处理器
    └── exception_handlers.py  # 异常处理器注册
```

## 本地服务依赖

当前项目配置默认连接本机服务：

```text
PostgreSQL: localhost:5432
database:   news_app
user:       postgres
password:   空

Redis:      localhost:6379
db:         0
password:   空
```

对应代码位置：

- `config/db_config.py`
- `config/cache_config.py`

如果你的 PostgreSQL 设置了密码，把数据库连接改成：

```python
ASYNC_DATABASE_URL = "postgresql+asyncpg://postgres:你的密码@localhost:5432/news_app"
```

## 初始化数据库

在 `backend` 目录执行：

```bash
createdb -h localhost -p 5432 -U postgres news_app
psql -h localhost -p 5432 -U postgres -d news_app -f db/database.sql
```

如果数据库已存在，`createdb` 可能提示已存在，可以忽略，然后重新导入 SQL。

导入后可用下面命令检查数据：

```bash
psql -h localhost -p 5432 -U postgres -d news_app -Atc "select (select count(*) from news_category), (select count(*) from news);"
```

正常情况下会看到：

```text
8|403
```

## 启动 Redis

macOS Homebrew 常用命令：

```bash
brew services start redis
redis-cli -h 127.0.0.1 -p 6379 ping
```

正常返回：

```text
PONG
```

Redis 暂时不可用时，后端新闻接口仍会尝试走数据库；`utils/redis_cache.py` 已对 Redis 读写设置短超时和异常兜底，避免缓存异常拖垮接口。

## 安装依赖

在 `backend` 目录执行：

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Windows PowerShell 激活虚拟环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

## 启动后端

在 `backend` 目录执行：

```bash
source .venv/bin/activate
uvicorn main:app --reload
```

默认地址：

```text
http://127.0.0.1:8000
```

如果 `8000` 端口被占用，可以换端口：

```bash
uvicorn main:app --reload --port 8001
```

## 快速验证

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/api/news/categories
curl "http://127.0.0.1:8000/api/news/list?categoryId=1&page=1&pageSize=2"
```

登录测试账号：

```bash
curl -X POST http://127.0.0.1:8000/api/user/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"123456"}'
```

登录成功后会返回 Token。需要登录的接口请求头格式：

```text
Authorization: Bearer <token>
```

## API 文档

启动后访问：

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## 接口总览

### 新闻 `/api/news`

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|:----:|
| GET | `/api/news/categories` | 获取新闻分类列表 | 否 |
| GET | `/api/news/list?categoryId=&page=&pageSize=` | 获取新闻列表 | 否 |
| GET | `/api/news/detail?id=` | 获取新闻详情，浏览量加 1 | 否 |

### 用户 `/api/user`

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|:----:|
| POST | `/api/user/register` | 用户注册 | 否 |
| POST | `/api/user/login` | 用户登录 | 否 |
| GET | `/api/user/info` | 获取当前用户信息 | 是 |
| PUT | `/api/user/update` | 修改用户信息 | 是 |
| PUT | `/api/user/password` | 修改密码 | 是 |

### 收藏 `/api/favorite`

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|:----:|
| GET | `/api/favorite/check?newsId=` | 检查收藏状态 | 是 |
| POST | `/api/favorite/add` | 添加收藏 | 是 |
| DELETE | `/api/favorite/remove?newsId=` | 取消收藏 | 是 |
| GET | `/api/favorite/list?page=&pageSize=` | 获取收藏列表 | 是 |
| DELETE | `/api/favorite/clear` | 清空收藏列表 | 是 |

### 浏览历史 `/api/history`

| 方法 | 路径 | 说明 | 登录 |
|------|------|------|:----:|
| POST | `/api/history/add` | 添加浏览历史 | 是 |
| GET | `/api/history/list?page=&pageSize=` | 获取历史列表 | 是 |
| DELETE | `/api/history/delete/{news_id}` | 删除单条历史 | 是 |
| DELETE | `/api/history/clear` | 清空历史 | 是 |

## 响应格式

成功响应统一结构：

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

分页响应的 `data` 通常包含：

```json
{
  "list": [],
  "total": 100,
  "hasMore": true
}
```

## Redis 缓存

| 数据 | Key | 过期时间 |
|------|-----|----------|
| 新闻分类 | `news:categories` | 7200 秒 |
| 新闻列表 | `news_list:{category_id}:{page}:{page_size}` | 1800 秒 |
| 新闻详情 | `news:detail:{news_id}` | 300 秒 |
| 相关新闻 | `news:related:{news_id}:{category_id}` | 1800 秒 |

缓存采用旁路策略：

1. 先读 Redis。
2. 命中则直接返回。
3. 未命中则查询 PostgreSQL。
4. 查询成功后写回 Redis。
5. Redis 异常时返回数据库结果，不中断接口。

## 数据库表

| 表名 | 说明 |
|------|------|
| `user` | 用户信息 |
| `user_token` | 登录 Token，默认 7 天过期 |
| `news_category` | 新闻分类 |
| `news` | 新闻内容 |
| `related_news` | 相关新闻关系 |
| `favorite` | 收藏记录 |
| `history` | 浏览历史 |
| `ai_chat` | AI 对话记录 |

`user` 是 PostgreSQL 关键字，手写 SQL 时需要加双引号：

```sql
select * from "user";
```

## VS Code 数据库插件连接

PostgreSQL 插件可使用：

```text
host: localhost
port: 5432
user: postgres
database: news_app
password: 空
```

Redis 插件可使用：

```text
host: 127.0.0.1
port: 6379
database: 0
password: 空
```

如果插件侧边栏没有立即刷新，执行 VS Code 命令 `Developer: Reload Window`。

## 常见问题

### PostgreSQL 连接失败

先检查服务和数据库：

```bash
psql -h localhost -p 5432 -U postgres -d news_app -c "select 1;"
```

如果提示数据库不存在，重新执行初始化数据库命令。如果提示用户或密码错误，按本机账号修改 `config/db_config.py` 的 `ASYNC_DATABASE_URL`。

### Redis 连接失败

先检查 Redis：

```bash
redis-cli -h 127.0.0.1 -p 6379 ping
```

如果没有返回 `PONG`，启动 Redis 服务后再试。

### 端口 8000 被占用

查看占用进程：

```bash
lsof -nP -iTCP:8000 -sTCP:LISTEN
```

或者直接换端口启动：

```bash
uvicorn main:app --reload --port 8001
```
