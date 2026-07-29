# News Headline 前后端启动文档

新闻资讯应用，前后端分离架构：

```
toutiao/
├── backend/                 # 后端：FastAPI + SQLAlchemy + PostgreSQL
└── news-headline-frontend/  # 前端：Vue 3 + Vite + Vant（移动端）
```

## 环境要求

| 软件 | 版本要求 |
| ---- | ---- |
| Python | 3.13（推荐用 uv 管理虚拟环境） |
| Node.js | 20.19+ 或 22.12+（Vite 7 要求） |
| PostgreSQL | 任意近期版本，本地 5432 端口 |
| Redis | 可选（缓存层规划中，当前代码未启用） |

## 一、启动后端

```bash
cd backend

# 1. 创建虚拟环境（已存在 .venv 则跳过）
uv venv --python 3.13

# 2. 安装依赖（清华源被限流时用阿里云源）
uv pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 3. 准备数据库（只需一次）
#    确保 PostgreSQL 已启动，然后创建数据库并导入表结构
createdb news_app
psql postgresql://wangdekang@localhost:5432/news_app -f db/database.sql

# 4. 启动服务
uv run uvicorn main:app --reload
```

- 接口地址：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs
- 数据库连接配置在 `config/db_conf.py`，按本机实际情况修改

如果不想用 uv，也可以激活已有环境后执行 `pip install -r requirements.txt`，再用 `uvicorn main:app --reload` 启动。

## 二、启动前端

```bash
cd news-headline-frontend

# 1. 安装依赖（只需一次）
npm install

# 2. 启动开发服务器
npm run dev
```

- 访问地址：http://localhost:5173
- 后端已配置 CORS 允许所有来源，前端直接请求 `http://localhost:8000` 即可联调

## 三、验证是否启动成功

1. 浏览器打开 http://localhost:8000/docs 能看到 Swagger 接口列表 → 后端 OK
2. 浏览器打开 http://localhost:5173 能看到新闻页面，分类/列表有数据 → 前端 + 联调 OK

## 四、常见问题

- **pip 安装报 `from versions: none`**：镜像源限流/封禁，换 `-i https://mirrors.aliyun.com/pypi/simple/` 或官方源
- **注册接口 500**：确认依赖版本为 `requirements.txt` 锁定版本（`bcrypt<5.0`，`sqlalchemy[asyncio]`），重新安装依赖并重启服务
- **改了代码不生效**：`--reload` 只监听启动时加载的代码；依赖变更或环境切换后需要手动重启 uvicorn
- **前端页面空白/请求失败**：先确认后端 8000 端口已启动，再看浏览器控制台 Network 面板的请求状态码
