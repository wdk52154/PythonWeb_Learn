# PostgreSQL 从 0 到 1：给 React + FastAPI 开发者的数据库教程

> 适合你现在的背景：有前端 React 基础，学过 Python + FastAPI，但没有系统学过 PostgreSQL。
>
> 目标不是背 SQL 语法，而是建立一个后端开发者真正能用起来的数据库思维：会建表、会查询、会设计关系、会接 FastAPI、知道什么时候该加索引、知道哪里容易踩坑。

## 目录

1. [先建立数据库直觉](#1-先建立数据库直觉)
2. [安装和连接 PostgreSQL](#2-安装和连接-postgresql)
3. [psql 命令行入门](#3-psql-命令行入门)
4. [SQL 的四类操作](#4-sql-的四类操作)
5. [从一个任务管理 App 开始建库](#5-从一个任务管理-app-开始建库)
6. [PostgreSQL 常用数据类型](#6-postgresql-常用数据类型)
7. [增删改查：CRUD](#7-增删改查crud)
8. [条件查询、排序、分页](#8-条件查询排序分页)
9. [关系设计：一对多、多对多](#9-关系设计一对多多对多)
10. [JOIN：把多张表的数据拼起来](#10-join把多张表的数据拼起来)
11. [聚合查询：统计数据](#11-聚合查询统计数据)
12. [约束：让坏数据进不来](#12-约束让坏数据进不来)
13. [事务：要么都成功，要么都失败](#13-事务要么都成功要么都失败)
14. [索引：为什么查询会变快](#14-索引为什么查询会变快)
15. [视图、枚举、JSONB 和数组](#15-视图枚举jsonb-和数组)
16. [在 FastAPI 中连接 PostgreSQL](#16-在-fastapi-中连接-postgresql)
17. [迁移工具 Alembic 入门](#17-迁移工具-alembic-入门)
18. [常见错误和排查方式](#18-常见错误和排查方式)
19. [学习路线和练习题](#19-学习路线和练习题)

---

## 1. 先建立数据库直觉

如果你写过 React，你可能很熟悉这种数据：

```js
const task = {
  id: 1,
  title: "学习 PostgreSQL",
  done: false,
  userId: 3
}
```

在前端里，这是一个对象；在后端 API 里，它可能是 JSON；在 PostgreSQL 里，它通常会变成一张表里的一行：

| id | title | done | user_id |
|---:|---|---|---:|
| 1 | 学习 PostgreSQL | false | 3 |

你可以先把 PostgreSQL 理解成：

- 一个专门负责安全、稳定、快速存储数据的软件。
- 它比普通 JSON 文件强，因为它能处理并发、事务、索引、权限、约束和复杂查询。
- 它是关系型数据库，核心思维是：把业务对象拆成表，再用主键和外键描述对象之间的关系。

### 1.1 数据库里常见概念

| 概念 | 类比 | 说明 |
|---|---|---|
| PostgreSQL | 浏览器或 Node 运行时 | 一个数据库管理系统 |
| database | 一个项目的数据空间 | 比如 `shop_db`、`blog_db` |
| schema | database 里的命名空间 | 默认常用 `public` |
| table | Excel 的一张表 | 存同一类数据 |
| row | 一条记录 | 一个用户、一篇文章、一个订单 |
| column | 字段 | `name`、`email`、`created_at` |
| primary key | 唯一 ID | 一行数据的唯一身份 |
| foreign key | 关联 ID | 表与表之间的关系 |
| index | 目录 | 让查询更快 |
| transaction | 一组不可拆的操作 | 要么全部成功，要么全部失败 |

### 1.2 为什么后端项目需要数据库

拿一个任务管理 App 来说：

- React 负责展示任务列表、表单、按钮和状态变化。
- FastAPI 负责接收请求、校验参数、返回 JSON。
- PostgreSQL 负责长期保存用户、项目、任务、评论等数据。

典型数据流：

```text
React 页面
  -> fetch / axios 请求
FastAPI 路由
  -> 调用 service / crud 函数
PostgreSQL
  -> 返回查询结果
FastAPI
  -> 转成 JSON
React
  -> setState / 渲染列表
```

你学 PostgreSQL 的重点不是“数据库管理员那套全部学完”，而是先掌握后端开发最常用的能力。

---

## 2. 安装和连接 PostgreSQL

下面给你两种推荐方式。

### 2.1 推荐方式一：Docker 启动 PostgreSQL

如果你不想污染本机环境，用 Docker 最干净。

```bash
docker run --name pg-learn \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_DB=learn_pg \
  -p 5432:5432 \
  -d postgres
```

含义：

| 参数 | 说明 |
|---|---|
| `--name pg-learn` | 容器名字 |
| `POSTGRES_USER=postgres` | 默认用户名 |
| `POSTGRES_PASSWORD=postgres` | 默认密码 |
| `POSTGRES_DB=learn_pg` | 启动时创建的数据库 |
| `-p 5432:5432` | 把容器端口映射到本机 |
| `-d postgres` | 后台运行官方 PostgreSQL 镜像 |

连接：

```bash
docker exec -it pg-learn psql -U postgres -d learn_pg
```

停止：

```bash
docker stop pg-learn
```

再次启动：

```bash
docker start pg-learn
```

删除容器：

```bash
docker rm pg-learn
```

### 2.2 推荐方式二：macOS 使用 Homebrew

```bash
brew install postgresql
brew services start postgresql
```

连接默认数据库：

```bash
psql postgres
```

如果你的 Homebrew 安装了带版本号的公式，比如 `postgresql@16`、`postgresql@17`，启动命令可能是：

```bash
brew services start postgresql@17
```

具体版本以你本机 `brew info postgresql` 的输出为准。

### 2.3 图形化工具

你可以先用命令行 `psql`，因为它能逼你真正理解 SQL。等熟悉后再用图形化工具：

- DBeaver
- TablePlus
- pgAdmin
- DataGrip

---

## 3. psql 命令行入门

连接后，你会看到类似：

```text
learn_pg=#
```

常用命令：

| 命令 | 作用 |
|---|---|
| `\l` | 查看所有数据库 |
| `\c 数据库名` | 切换数据库 |
| `\dt` | 查看当前 schema 下的表 |
| `\d 表名` | 查看表结构 |
| `\du` | 查看用户和角色 |
| `\conninfo` | 查看当前连接信息 |
| `\q` | 退出 |

注意：

- SQL 语句一般要用分号 `;` 结尾。
- `\dt` 这种是 `psql` 自己的命令，不需要分号。
- SQL 关键字大小写都可以，但建议关键字大写、表名字段名小写。

示例：

```sql
SELECT 1;
SELECT now();
```

---

## 4. SQL 的四类操作

SQL 可以粗略分成几类：

| 分类 | 作用 | 常见语句 |
|---|---|---|
| DDL | 定义结构 | `CREATE`、`ALTER`、`DROP` |
| DML | 修改数据 | `INSERT`、`UPDATE`、`DELETE` |
| DQL | 查询数据 | `SELECT` |
| TCL | 控制事务 | `BEGIN`、`COMMIT`、`ROLLBACK` |

你作为 FastAPI 开发者，最常写的是：

- `CREATE TABLE`
- `INSERT`
- `SELECT`
- `UPDATE`
- `DELETE`
- `JOIN`
- `CREATE INDEX`

---

## 5. 从一个任务管理 App 开始建库

我们用一个小型任务管理 App 学 PostgreSQL。它有这些功能：

- 用户注册。
- 用户创建项目。
- 项目里创建任务。
- 任务可以设置状态、优先级、截止时间。
- 任务可以打标签。

### 5.1 创建数据库

进入 `psql` 后执行：

```sql
CREATE DATABASE task_app;
```

切换数据库：

```sql
\c task_app
```

### 5.2 创建用户表

```sql
CREATE TABLE users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

逐行解释：

| 字段 | 说明 |
|---|---|
| `id` | 主键，自增 |
| `username` | 用户名，不能为空，不能重复 |
| `email` | 邮箱，不能为空，不能重复 |
| `password_hash` | 密码哈希，不能存明文密码 |
| `is_active` | 是否启用 |
| `created_at` | 创建时间，带时区 |

为什么用 `BIGINT GENERATED ALWAYS AS IDENTITY`？

- 这是 PostgreSQL 推荐的现代自增写法。
- 老项目里你也会看到 `SERIAL`，能用，但新项目更推荐 identity。

### 5.3 创建项目表

```sql
CREATE TABLE projects (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

重点是这一行：

```sql
owner_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE
```

它表示：

- `projects.owner_id` 必须对应 `users.id`。
- 如果某个用户被删除，他拥有的项目也会被删除。

这就是外键。

### 5.4 创建任务表

```sql
CREATE TABLE tasks (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'todo',
  priority SMALLINT NOT NULL DEFAULT 2,
  due_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT tasks_status_check CHECK (status IN ('todo', 'doing', 'done')),
  CONSTRAINT tasks_priority_check CHECK (priority BETWEEN 1 AND 5)
);
```

这里出现了 `CHECK` 约束：

```sql
CHECK (status IN ('todo', 'doing', 'done'))
CHECK (priority BETWEEN 1 AND 5)
```

意思是：

- `status` 只能是 `todo`、`doing`、`done`。
- `priority` 只能是 1 到 5。

数据库不应该只是“存东西的仓库”，它还应该帮你挡住明显错误的数据。

---

## 6. PostgreSQL 常用数据类型

### 6.1 数字类型

| 类型 | 场景 |
|---|---|
| `SMALLINT` | 很小的整数，比如优先级 |
| `INTEGER` | 普通整数 |
| `BIGINT` | 大整数，常用于主键 |
| `NUMERIC(10, 2)` | 金额，精确小数 |
| `REAL` / `DOUBLE PRECISION` | 科学计算，不适合金额 |

金额不要用浮点数，应该用：

```sql
price NUMERIC(10, 2) NOT NULL
```

### 6.2 字符串类型

| 类型 | 场景 |
|---|---|
| `VARCHAR(n)` | 有明确最大长度 |
| `TEXT` | 长文本 |
| `CHAR(n)` | 固定长度，少用 |

实战建议：

- 用户名、邮箱、标题：用 `VARCHAR(n)`。
- 文章正文、任务描述：用 `TEXT`。

### 6.3 时间类型

| 类型 | 场景 |
|---|---|
| `DATE` | 日期，不含时间 |
| `TIME` | 时间，不含日期 |
| `TIMESTAMP` | 日期时间，不含时区 |
| `TIMESTAMPTZ` | 日期时间，带时区语义 |

后端项目一般优先用：

```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

原因：

- Web 应用常常有不同时区的用户。
- `TIMESTAMPTZ` 更适合存储真实时间点。

### 6.4 布尔类型

```sql
is_active BOOLEAN NOT NULL DEFAULT true
```

### 6.5 UUID

如果你不想让用户 ID 暴露为连续数字，可以用 UUID：

```sql
CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE api_keys (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id BIGINT NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 6.6 JSONB

PostgreSQL 支持 `JSONB`，适合存结构灵活的数据：

```sql
CREATE TABLE events (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  event_type TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

插入：

```sql
INSERT INTO events (event_type, payload)
VALUES (
  'task_created',
  '{"task_id": 1, "source": "web"}'
);
```

但注意：不要因为 JSONB 很方便，就把所有东西都塞进一个 JSON 字段。稳定、需要关联、需要频繁查询的字段，通常应该拆成正常列。

---

## 7. 增删改查：CRUD

### 7.1 插入数据

```sql
INSERT INTO users (username, email, password_hash)
VALUES ('alice', 'alice@example.com', 'hashed_password_1');

INSERT INTO users (username, email, password_hash)
VALUES ('bob', 'bob@example.com', 'hashed_password_2');
```

插入并返回新数据：

```sql
INSERT INTO users (username, email, password_hash)
VALUES ('carol', 'carol@example.com', 'hashed_password_3')
RETURNING id, username, email, created_at;
```

`RETURNING` 很适合配合 FastAPI 创建接口：

```text
POST /users
  -> INSERT
  -> RETURNING
  -> 返回新用户 JSON
```

插入项目：

```sql
INSERT INTO projects (owner_id, name, description)
VALUES
  (1, 'PostgreSQL 学习计划', '从 SQL 到 FastAPI 集成'),
  (1, 'React 项目重构', '优化组件结构'),
  (2, '个人博客', '写技术文章');
```

插入任务：

```sql
INSERT INTO tasks (project_id, title, description, status, priority, due_at)
VALUES
  (1, '安装 PostgreSQL', '用 Docker 或 Homebrew 安装', 'done', 2, now() + interval '1 day'),
  (1, '学习 SELECT', '掌握查询、过滤、排序', 'doing', 3, now() + interval '2 days'),
  (1, '接入 FastAPI', '使用 asyncpg 或 SQLAlchemy', 'todo', 4, now() + interval '5 days'),
  (2, '拆分组件', '把大组件拆成小组件', 'todo', 3, NULL),
  (3, '设计文章表', '包含标题、内容、作者、发布时间', 'todo', 2, NULL);
```

### 7.2 查询数据

查询所有用户：

```sql
SELECT * FROM users;
```

只查部分字段：

```sql
SELECT id, username, email FROM users;
```

给字段起别名：

```sql
SELECT username AS name, created_at AS joined_at
FROM users;
```

### 7.3 更新数据

```sql
UPDATE tasks
SET status = 'done',
    completed_at = now(),
    updated_at = now()
WHERE id = 2
RETURNING *;
```

一定要小心：没有 `WHERE` 的 `UPDATE` 会更新整张表。

```sql
UPDATE tasks
SET status = 'done';
```

上面这句会把所有任务都改成 done。真实项目里写更新和删除时，先写 `SELECT` 检查范围：

```sql
SELECT * FROM tasks WHERE id = 2;
```

确认后再写：

```sql
UPDATE tasks SET status = 'done' WHERE id = 2;
```

### 7.4 删除数据

```sql
DELETE FROM tasks
WHERE id = 5
RETURNING *;
```

同样，真实项目里删除前先查：

```sql
SELECT * FROM tasks WHERE id = 5;
```

---

## 8. 条件查询、排序、分页

### 8.1 WHERE 条件

```sql
SELECT *
FROM tasks
WHERE status = 'todo';
```

多个条件：

```sql
SELECT *
FROM tasks
WHERE status = 'todo'
  AND priority >= 3;
```

或条件：

```sql
SELECT *
FROM tasks
WHERE status = 'todo'
   OR status = 'doing';
```

更简洁：

```sql
SELECT *
FROM tasks
WHERE status IN ('todo', 'doing');
```

### 8.2 模糊搜索

大小写敏感：

```sql
SELECT *
FROM tasks
WHERE title LIKE '%SQL%';
```

大小写不敏感：

```sql
SELECT *
FROM tasks
WHERE title ILIKE '%sql%';
```

### 8.3 NULL 判断

错误写法：

```sql
SELECT * FROM tasks WHERE due_at = NULL;
```

正确写法：

```sql
SELECT * FROM tasks WHERE due_at IS NULL;
SELECT * FROM tasks WHERE due_at IS NOT NULL;
```

### 8.4 排序

```sql
SELECT *
FROM tasks
ORDER BY created_at DESC;
```

多个排序条件：

```sql
SELECT *
FROM tasks
ORDER BY priority DESC, created_at ASC;
```

### 8.5 分页

```sql
SELECT *
FROM tasks
ORDER BY created_at DESC
LIMIT 10 OFFSET 0;
```

第二页：

```sql
SELECT *
FROM tasks
ORDER BY created_at DESC
LIMIT 10 OFFSET 10;
```

这就是很多 REST API 的分页基础：

```text
GET /tasks?page=2&page_size=10
```

换算：

```python
offset = (page - 1) * page_size
```

---

## 9. 关系设计：一对多、多对多

关系型数据库的核心是关系。

### 9.1 一对多

一个用户可以有多个项目：

```text
users 1 ---- N projects
```

实现方式是在多的一方加外键：

```sql
owner_id BIGINT NOT NULL REFERENCES users(id)
```

一个项目可以有多个任务：

```text
projects 1 ---- N tasks
```

实现方式：

```sql
project_id BIGINT NOT NULL REFERENCES projects(id)
```

### 9.2 多对多

一个任务可以有多个标签，一个标签也可以属于多个任务：

```text
tasks N ---- N tags
```

关系型数据库不能直接存 N 对 N，通常要加一张中间表。

创建标签表：

```sql
CREATE TABLE tags (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  color VARCHAR(20) NOT NULL DEFAULT '#64748b'
);
```

创建任务标签中间表：

```sql
CREATE TABLE task_tags (
  task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  tag_id BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (task_id, tag_id)
);
```

插入标签：

```sql
INSERT INTO tags (name, color)
VALUES
  ('database', '#2563eb'),
  ('frontend', '#16a34a'),
  ('backend', '#9333ea');
```

给任务打标签：

```sql
INSERT INTO task_tags (task_id, tag_id)
VALUES
  (1, 1),
  (2, 1),
  (3, 1),
  (3, 3),
  (4, 2);
```

中间表的联合主键：

```sql
PRIMARY KEY (task_id, tag_id)
```

它可以防止同一个任务重复绑定同一个标签。

---

## 10. JOIN：把多张表的数据拼起来

前端经常希望拿到这样的 JSON：

```json
{
  "id": 1,
  "title": "安装 PostgreSQL",
  "status": "done",
  "project": {
    "id": 1,
    "name": "PostgreSQL 学习计划"
  },
  "owner": {
    "id": 1,
    "username": "alice"
  }
}
```

数据库里数据是分表存的，所以要用 `JOIN` 查出来。

### 10.1 INNER JOIN

查询任务和所属项目：

```sql
SELECT
  tasks.id,
  tasks.title,
  tasks.status,
  projects.name AS project_name
FROM tasks
INNER JOIN projects ON tasks.project_id = projects.id;
```

可以加表别名：

```sql
SELECT
  t.id,
  t.title,
  t.status,
  p.name AS project_name
FROM tasks AS t
INNER JOIN projects AS p ON t.project_id = p.id;
```

### 10.2 多表 JOIN

查询任务、项目、项目拥有者：

```sql
SELECT
  t.id AS task_id,
  t.title AS task_title,
  t.status,
  p.id AS project_id,
  p.name AS project_name,
  u.id AS owner_id,
  u.username AS owner_name
FROM tasks AS t
INNER JOIN projects AS p ON t.project_id = p.id
INNER JOIN users AS u ON p.owner_id = u.id
ORDER BY t.created_at DESC;
```

### 10.3 LEFT JOIN

`INNER JOIN` 只返回两边都匹配的数据。

`LEFT JOIN` 会保留左表，即使右表没有匹配数据。

查询所有任务以及标签：

```sql
SELECT
  t.id,
  t.title,
  tag.name AS tag_name
FROM tasks AS t
LEFT JOIN task_tags AS tt ON t.id = tt.task_id
LEFT JOIN tags AS tag ON tt.tag_id = tag.id
ORDER BY t.id;
```

如果某个任务没有标签，它也会出现，只是 `tag_name` 是 `NULL`。

### 10.4 把多行标签聚合成数组

```sql
SELECT
  t.id,
  t.title,
  array_agg(tag.name) FILTER (WHERE tag.name IS NOT NULL) AS tags
FROM tasks AS t
LEFT JOIN task_tags AS tt ON t.id = tt.task_id
LEFT JOIN tags AS tag ON tt.tag_id = tag.id
GROUP BY t.id, t.title
ORDER BY t.id;
```

结果更接近前端喜欢的结构：

| id | title | tags |
|---:|---|---|
| 1 | 安装 PostgreSQL | `{database}` |
| 3 | 接入 FastAPI | `{database,backend}` |

---

## 11. 聚合查询：统计数据

### 11.1 COUNT

统计任务数：

```sql
SELECT COUNT(*) FROM tasks;
```

按状态统计：

```sql
SELECT status, COUNT(*) AS task_count
FROM tasks
GROUP BY status;
```

### 11.2 GROUP BY

统计每个项目的任务数：

```sql
SELECT
  p.id,
  p.name,
  COUNT(t.id) AS task_count
FROM projects AS p
LEFT JOIN tasks AS t ON p.id = t.project_id
GROUP BY p.id, p.name
ORDER BY task_count DESC;
```

### 11.3 HAVING

`WHERE` 是分组前过滤，`HAVING` 是分组后过滤。

查询任务数大于 2 的项目：

```sql
SELECT
  p.id,
  p.name,
  COUNT(t.id) AS task_count
FROM projects AS p
LEFT JOIN tasks AS t ON p.id = t.project_id
GROUP BY p.id, p.name
HAVING COUNT(t.id) > 2;
```

### 11.4 常用统计函数

| 函数 | 作用 |
|---|---|
| `COUNT()` | 数量 |
| `SUM()` | 求和 |
| `AVG()` | 平均值 |
| `MIN()` | 最小值 |
| `MAX()` | 最大值 |

示例：

```sql
SELECT
  AVG(priority) AS avg_priority,
  MAX(priority) AS max_priority,
  MIN(priority) AS min_priority
FROM tasks;
```

---

## 12. 约束：让坏数据进不来

约束是数据库帮你守门。

### 12.1 NOT NULL

```sql
title VARCHAR(200) NOT NULL
```

表示标题不能是空值。

### 12.2 UNIQUE

```sql
email VARCHAR(255) NOT NULL UNIQUE
```

表示邮箱不能重复。

### 12.3 PRIMARY KEY

```sql
id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY
```

主键要求：

- 不能为 `NULL`。
- 不能重复。
- 能唯一定位一行。

### 12.4 FOREIGN KEY

```sql
project_id BIGINT NOT NULL REFERENCES projects(id)
```

外键要求：这个任务引用的项目必须真实存在。

### 12.5 CHECK

```sql
CONSTRAINT tasks_priority_check CHECK (priority BETWEEN 1 AND 5)
```

业务规则尽量不要只写在后端代码里。重要规则可以同时放在数据库约束里。

### 12.6 DEFAULT

```sql
created_at TIMESTAMPTZ NOT NULL DEFAULT now()
```

插入时不传这个字段，数据库会自动填当前时间。

---

## 13. 事务：要么都成功，要么都失败

假设你做一个“创建项目并创建默认任务”的接口：

1. 插入项目。
2. 插入默认任务。

如果第一步成功，第二步失败，就会留下一个没有默认任务的项目。事务可以解决这个问题。

```sql
BEGIN;

INSERT INTO projects (owner_id, name, description)
VALUES (1, '新项目', '事务示例')
RETURNING id;

INSERT INTO tasks (project_id, title)
VALUES (999999, '默认任务');

COMMIT;
```

如果第二步失败，你可以：

```sql
ROLLBACK;
```

事务的思想：

- `BEGIN` 开始事务。
- `COMMIT` 提交事务，真正保存。
- `ROLLBACK` 回滚事务，撤销这次事务里的修改。

### 13.1 ACID

事务常说 ACID：

| 字母 | 含义 | 白话 |
|---|---|---|
| A | Atomicity 原子性 | 要么都做，要么都不做 |
| C | Consistency 一致性 | 数据必须从一个合法状态到另一个合法状态 |
| I | Isolation 隔离性 | 并发操作之间不要互相弄乱 |
| D | Durability 持久性 | 提交后数据可靠保存 |

日常开发里，你最先需要记住的是原子性。

---

## 14. 索引：为什么查询会变快

没有索引时，数据库可能要从第一行扫到最后一行。

有索引时，数据库可以像查字典目录一样更快定位数据。

### 14.1 创建索引

任务列表经常按项目查：

```sql
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
```

任务经常按状态查：

```sql
CREATE INDEX idx_tasks_status ON tasks(status);
```

项目下任务列表经常按创建时间倒序：

```sql
CREATE INDEX idx_tasks_project_created_at
ON tasks(project_id, created_at DESC);
```

### 14.2 什么时候应该加索引

适合加索引：

- 经常出现在 `WHERE` 条件里的字段。
- 经常用于 `JOIN` 的外键字段。
- 经常用于 `ORDER BY` 的字段。
- 数据量较大，而且查询明显变慢。

不适合乱加索引：

- 表很小，没必要。
- 字段经常更新。
- 查询很少用。
- 区分度很低的字段单独建索引收益可能有限，比如只有 true/false 的布尔字段。

### 14.3 查看查询计划

```sql
EXPLAIN
SELECT *
FROM tasks
WHERE project_id = 1
ORDER BY created_at DESC
LIMIT 10;
```

如果想看实际执行耗时：

```sql
EXPLAIN ANALYZE
SELECT *
FROM tasks
WHERE project_id = 1
ORDER BY created_at DESC
LIMIT 10;
```

`EXPLAIN ANALYZE` 会真的执行 SQL。对 `UPDATE`、`DELETE` 慎用。

---

## 15. 视图、枚举、JSONB 和数组

这些不是第一天必须全掌握，但后面会常见。

### 15.1 视图 VIEW

视图可以把复杂查询包装成一个虚拟表。

```sql
CREATE VIEW task_detail_view AS
SELECT
  t.id AS task_id,
  t.title,
  t.status,
  t.priority,
  p.name AS project_name,
  u.username AS owner_name
FROM tasks AS t
JOIN projects AS p ON t.project_id = p.id
JOIN users AS u ON p.owner_id = u.id;
```

之后可以：

```sql
SELECT * FROM task_detail_view;
```

### 15.2 ENUM

你也可以用枚举限制状态：

```sql
CREATE TYPE task_status AS ENUM ('todo', 'doing', 'done');

CREATE TABLE enum_tasks (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title TEXT NOT NULL,
  status task_status NOT NULL DEFAULT 'todo'
);
```

枚举的好处是更严格，坏处是后续修改枚举值比普通字符串麻烦。初学阶段，用 `VARCHAR + CHECK` 更容易理解和维护。

### 15.3 JSONB 查询

```sql
SELECT *
FROM events
WHERE payload->>'source' = 'web';
```

解释：

- `payload->'source'` 返回 JSON 值。
- `payload->>'source'` 返回文本值。

给 JSONB 建索引：

```sql
CREATE INDEX idx_events_payload ON events USING GIN (payload);
```

### 15.4 数组

PostgreSQL 支持数组：

```sql
CREATE TABLE notes (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  title TEXT NOT NULL,
  keywords TEXT[] NOT NULL DEFAULT '{}'
);
```

插入：

```sql
INSERT INTO notes (title, keywords)
VALUES ('PostgreSQL 笔记', ARRAY['sql', 'database', 'backend']);
```

查询包含某个元素：

```sql
SELECT *
FROM notes
WHERE 'sql' = ANY(keywords);
```

数组适合简单列表；如果元素需要独立维护、查询、关联，应该拆成表。

---

## 16. 在 FastAPI 中连接 PostgreSQL

FastAPI 连接 PostgreSQL 常见路线有两种：

| 路线 | 适合情况 |
|---|---|
| `asyncpg` | 想直接写 SQL，轻量、清晰 |
| SQLAlchemy | 项目较大，想用 ORM 和迁移体系 |

初学建议：先用 `asyncpg` 直接写 SQL，把数据库理解透；再学 SQLAlchemy。

### 16.1 安装依赖

```bash
pip install fastapi uvicorn asyncpg python-dotenv
```

### 16.2 准备环境变量

创建 `.env`：

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/task_app
```

真实项目不要把 `.env` 提交到 Git。

### 16.3 FastAPI 示例

创建 `main.py`：

```python
import os
from contextlib import asynccontextmanager
from typing import Optional

import asyncpg
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

load_dotenv()


class TaskCreate(BaseModel):
    project_id: int
    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    priority: int = Field(default=2, ge=1, le=5)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[int] = Field(default=None, ge=1, le=5)


@asynccontextmanager
async def lifespan(app: FastAPI):
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise RuntimeError("DATABASE_URL is not set")

    app.state.pool = await asyncpg.create_pool(database_url)
    yield
    await app.state.pool.close()


app = FastAPI(lifespan=lifespan)


def task_to_dict(record):
    return {
        "id": record["id"],
        "project_id": record["project_id"],
        "title": record["title"],
        "description": record["description"],
        "status": record["status"],
        "priority": record["priority"],
        "due_at": record["due_at"],
        "completed_at": record["completed_at"],
        "created_at": record["created_at"],
        "updated_at": record["updated_at"],
    }


@app.get("/tasks")
async def list_tasks(project_id: int, limit: int = 20, offset: int = 0):
    sql = """
    SELECT *
    FROM tasks
    WHERE project_id = $1
    ORDER BY created_at DESC
    LIMIT $2 OFFSET $3
    """

    async with app.state.pool.acquire() as conn:
        rows = await conn.fetch(sql, project_id, limit, offset)

    return [task_to_dict(row) for row in rows]


@app.post("/tasks", status_code=201)
async def create_task(payload: TaskCreate):
    sql = """
    INSERT INTO tasks (project_id, title, description, priority)
    VALUES ($1, $2, $3, $4)
    RETURNING *
    """

    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            sql,
            payload.project_id,
            payload.title,
            payload.description,
            payload.priority,
        )

    return task_to_dict(row)


@app.patch("/tasks/{task_id}")
async def update_task(task_id: int, payload: TaskUpdate):
    sql = """
    UPDATE tasks
    SET
      title = COALESCE($2, title),
      description = COALESCE($3, description),
      status = COALESCE($4, status),
      priority = COALESCE($5, priority),
      updated_at = now(),
      completed_at = CASE
        WHEN $4 = 'done' THEN now()
        WHEN $4 IN ('todo', 'doing') THEN NULL
        ELSE completed_at
      END
    WHERE id = $1
    RETURNING *
    """

    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(
            sql,
            task_id,
            payload.title,
            payload.description,
            payload.status,
            payload.priority,
        )

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task_to_dict(row)


@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    sql = """
    DELETE FROM tasks
    WHERE id = $1
    RETURNING id
    """

    async with app.state.pool.acquire() as conn:
        row = await conn.fetchrow(sql, task_id)

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return {"deleted_id": row["id"]}
```

启动：

```bash
uvicorn main:app --reload
```

### 16.4 为什么 asyncpg 参数是 `$1`、`$2`

不要这样拼 SQL：

```python
sql = f"SELECT * FROM users WHERE email = '{email}'"
```

这很容易造成 SQL 注入。

应该用参数：

```python
row = await conn.fetchrow(
    "SELECT * FROM users WHERE email = $1",
    email,
)
```

`$1`、`$2` 是占位符，真实值由驱动安全传入。

### 16.5 连接池是什么

不要每次请求都新建一个数据库连接。

连接池的意思是：

- 应用启动时创建一批连接。
- 请求进来时借一个连接。
- 请求结束后归还连接。

```python
app.state.pool = await asyncpg.create_pool(database_url)
```

这对 Web 服务很重要。

---

## 17. 迁移工具 Alembic 入门

你刚开始可以手写 `CREATE TABLE`。但项目变大后，你需要记录数据库结构的变化。

比如：

- 第一天创建 `users` 表。
- 第二天给 `tasks` 增加 `archived_at` 字段。
- 第三天给 `users.email` 增加唯一约束。

这类变化叫 migration，也就是数据库迁移。

Python 项目常用 Alembic。

安装：

```bash
pip install alembic sqlalchemy psycopg
```

初始化：

```bash
alembic init migrations
```

生成迁移：

```bash
alembic revision -m "create users table"
```

执行迁移：

```bash
alembic upgrade head
```

回退一个版本：

```bash
alembic downgrade -1
```

初学建议：

- 先手写 SQL 学会数据库本身。
- 再学 SQLAlchemy model。
- 最后用 Alembic 管理结构变化。

---

## 18. 常见错误和排查方式

### 18.1 password authentication failed

含义：用户名或密码不对。

排查：

- 检查连接字符串里的用户名、密码。
- Docker 环境检查 `POSTGRES_PASSWORD`。
- 确认连接的是正确容器或本机服务。

### 18.2 database does not exist

含义：数据库不存在。

解决：

```sql
CREATE DATABASE task_app;
```

或者连接到已有数据库：

```bash
psql -U postgres -d postgres
```

### 18.3 relation does not exist

含义：表不存在，或 schema 不对。

排查：

```sql
\dt
SELECT current_schema();
```

### 18.4 duplicate key value violates unique constraint

含义：违反唯一约束。

比如邮箱重复：

```sql
INSERT INTO users (username, email, password_hash)
VALUES ('alice2', 'alice@example.com', 'x');
```

解决思路：

- 注册时先查邮箱是否存在。
- 或者直接插入，捕获数据库唯一约束错误。
- 对于接口，返回合适的 409 Conflict。

### 18.5 insert or update violates foreign key constraint

含义：外键引用的数据不存在。

比如创建任务时，`project_id = 999999`，但项目表里没有这个项目。

解决：

```sql
SELECT * FROM projects WHERE id = 999999;
```

### 18.6 column cannot be cast automatically

含义：修改字段类型时，数据库不知道怎么转换旧数据。

比如把文本转数字，旧数据里有 `"abc"`，那就无法转换。

解决方式通常是：

- 先清理旧数据。
- 再修改字段类型。
- 必要时写 `USING` 指定转换方式。

---

## 19. 学习路线和练习题

### 19.1 建议学习路线

第一阶段：SQL 基础

- 会 `CREATE TABLE`。
- 会 `INSERT`、`SELECT`、`UPDATE`、`DELETE`。
- 会 `WHERE`、`ORDER BY`、`LIMIT`、`OFFSET`。

第二阶段：关系建模

- 理解主键、外键。
- 能设计一对多。
- 能设计多对多。
- 会写 `JOIN`。

第三阶段：后端实战

- FastAPI 连接 PostgreSQL。
- 使用连接池。
- 使用参数化查询。
- 用 `RETURNING` 返回创建或更新后的数据。

第四阶段：工程化

- 学 SQLAlchemy。
- 学 Alembic。
- 学索引和查询计划。
- 学事务和并发问题。

### 19.2 必做练习

练习 1：博客系统建模

设计这些表：

- `users`
- `posts`
- `comments`
- `categories`
- `post_categories`

要求：

- 一个用户可以写多篇文章。
- 一篇文章可以有多条评论。
- 一篇文章可以属于多个分类。
- 分类名不能重复。

练习 2：写查询

写出 SQL：

- 查询某个用户的所有文章。
- 查询某篇文章下的所有评论，并按创建时间升序。
- 查询每个用户写了多少篇文章。
- 查询评论数最多的前 10 篇文章。
- 查询某个分类下的所有文章。

练习 3：接入 FastAPI

实现这些接口：

```text
GET    /posts
POST   /posts
GET    /posts/{post_id}
PATCH  /posts/{post_id}
DELETE /posts/{post_id}
POST   /posts/{post_id}/comments
GET    /posts/{post_id}/comments
```

### 19.3 你应该形成的数据库习惯

- 表名、字段名统一用小写蛇形命名，比如 `created_at`。
- 每张核心业务表都要有主键。
- 重要字段加 `NOT NULL`。
- 能唯一的字段加 `UNIQUE`，比如邮箱。
- 表之间的关系用外键表达。
- 创建和更新时间使用 `TIMESTAMPTZ`。
- 更新和删除前先用 `SELECT` 检查范围。
- 后端永远使用参数化查询，避免 SQL 注入。
- 不要一开始就把所有数据塞进 JSONB。
- 索引按真实查询场景添加，不要为了“看起来专业”乱加。

---

## 附录 A：完整建表 SQL

你可以直接复制下面这段，在一个空数据库里跑。

```sql
CREATE TABLE users (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  email VARCHAR(255) NOT NULL UNIQUE,
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT true,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE projects (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  owner_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(100) NOT NULL,
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE tasks (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  project_id BIGINT NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  title VARCHAR(200) NOT NULL,
  description TEXT,
  status VARCHAR(20) NOT NULL DEFAULT 'todo',
  priority SMALLINT NOT NULL DEFAULT 2,
  due_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT tasks_status_check CHECK (status IN ('todo', 'doing', 'done')),
  CONSTRAINT tasks_priority_check CHECK (priority BETWEEN 1 AND 5)
);

CREATE TABLE tags (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(50) NOT NULL UNIQUE,
  color VARCHAR(20) NOT NULL DEFAULT '#64748b'
);

CREATE TABLE task_tags (
  task_id BIGINT NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
  tag_id BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (task_id, tag_id)
);

CREATE INDEX idx_projects_owner_id ON projects(owner_id);
CREATE INDEX idx_tasks_project_id ON tasks(project_id);
CREATE INDEX idx_tasks_status ON tasks(status);
CREATE INDEX idx_tasks_project_created_at ON tasks(project_id, created_at DESC);
CREATE INDEX idx_task_tags_tag_id ON task_tags(tag_id);
```

---

## 附录 B：完整练习数据

```sql
INSERT INTO users (username, email, password_hash)
VALUES
  ('alice', 'alice@example.com', 'hashed_password_1'),
  ('bob', 'bob@example.com', 'hashed_password_2');

INSERT INTO projects (owner_id, name, description)
VALUES
  (1, 'PostgreSQL 学习计划', '从 SQL 到 FastAPI 集成'),
  (1, 'React 项目重构', '优化组件结构'),
  (2, '个人博客', '写技术文章');

INSERT INTO tasks (project_id, title, description, status, priority, due_at)
VALUES
  (1, '安装 PostgreSQL', '用 Docker 或 Homebrew 安装', 'done', 2, now() + interval '1 day'),
  (1, '学习 SELECT', '掌握查询、过滤、排序', 'doing', 3, now() + interval '2 days'),
  (1, '接入 FastAPI', '使用 asyncpg 或 SQLAlchemy', 'todo', 4, now() + interval '5 days'),
  (2, '拆分组件', '把大组件拆成小组件', 'todo', 3, NULL),
  (3, '设计文章表', '包含标题、内容、作者、发布时间', 'todo', 2, NULL);

INSERT INTO tags (name, color)
VALUES
  ('database', '#2563eb'),
  ('frontend', '#16a34a'),
  ('backend', '#9333ea');

INSERT INTO task_tags (task_id, tag_id)
VALUES
  (1, 1),
  (2, 1),
  (3, 1),
  (3, 3),
  (4, 2);
```

---

## 附录 C：常用 SQL 速查

```sql
-- 查全部
SELECT * FROM tasks;

-- 按条件查
SELECT * FROM tasks WHERE status = 'todo';

-- 排序
SELECT * FROM tasks ORDER BY created_at DESC;

-- 分页
SELECT * FROM tasks LIMIT 10 OFFSET 0;

-- 插入
INSERT INTO tasks (project_id, title)
VALUES (1, '新任务')
RETURNING *;

-- 更新
UPDATE tasks
SET status = 'done', updated_at = now()
WHERE id = 1
RETURNING *;

-- 删除
DELETE FROM tasks WHERE id = 1 RETURNING *;

-- 一对多 JOIN
SELECT t.title, p.name AS project_name
FROM tasks AS t
JOIN projects AS p ON t.project_id = p.id;

-- 多对多 JOIN
SELECT t.title, tag.name AS tag_name
FROM tasks AS t
JOIN task_tags AS tt ON t.id = tt.task_id
JOIN tags AS tag ON tt.tag_id = tag.id;

-- 分组统计
SELECT status, COUNT(*) AS count
FROM tasks
GROUP BY status;
```

---

## 最后一句

你真正学会 PostgreSQL 的标志不是“记住了多少语法”，而是看到一个功能需求时，能自然地想清楚：

- 这个业务对象应该拆成哪些表？
- 表之间是什么关系？
- 哪些字段必须唯一或不能为空？
- 哪些查询是前端页面最常用的？
- FastAPI 接口应该返回什么结构？
- 什么时候要事务？
- 慢查询是不是需要索引？

能回答这些问题，你就已经从“会写一点 SQL”进入了“能设计后端数据层”的阶段。
