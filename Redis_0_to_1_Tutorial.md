# Redis 从 0 到 1：给 React + FastAPI + PostgreSQL/ORM 开发者的深入浅出教程

> 适合你现在的背景：有一年半 React 基础，学过 Python + FastAPI，已经接触过 PostgreSQL 和 ORM，但没有系统学过 Redis。
>
> 这份教程的目标不是让你背完 Redis 所有命令，而是让你真正知道：Redis 在一个 Web 项目里解决什么问题，什么时候该用，什么时候不该用，如何和 FastAPI、PostgreSQL、ORM 配合起来。

## 目录

1. [先建立 Redis 的直觉](#1-先建立-redis-的直觉)
2. [Redis 和 PostgreSQL 的区别](#2-redis-和-postgresql-的区别)
3. [安装和连接 Redis](#3-安装和连接-redis)
4. [redis-cli 入门](#4-redis-cli-入门)
5. [Redis 的 key 设计](#5-redis-的-key-设计)
6. [String：最常用的数据类型](#6-string最常用的数据类型)
7. [过期时间 TTL：Redis 的灵魂能力之一](#7-过期时间-ttlredis-的灵魂能力之一)
8. [Hash：存对象字段](#8-hash存对象字段)
9. [List：队列和时间线](#9-list队列和时间线)
10. [Set：去重集合](#10-set去重集合)
11. [Sorted Set：排行榜和权重排序](#11-sorted-set排行榜和权重排序)
12. [Bitmap、HyperLogLog、Stream 简介](#12-bitmaphyperloglogstream-简介)
13. [Redis 在后端项目里的典型用途](#13-redis-在后端项目里的典型用途)
14. [缓存设计：从最简单到能上线](#14-缓存设计从最简单到能上线)
15. [缓存问题：穿透、击穿、雪崩、脏数据](#15-缓存问题穿透击穿雪崩脏数据)
16. [FastAPI 连接 Redis](#16-fastapi-连接-redis)
17. [实战一：缓存 PostgreSQL/ORM 查询结果](#17-实战一缓存-postgresqlorm-查询结果)
18. [实战二：登录验证码和短信验证码](#18-实战二登录验证码和短信验证码)
19. [实战三：接口限流](#19-实战三接口限流)
20. [实战四：排行榜](#20-实战四排行榜)
21. [实战五：简单任务队列](#21-实战五简单任务队列)
22. [事务、Lua 和分布式锁](#22-事务lua-和分布式锁)
23. [持久化、内存淘汰和生产配置](#23-持久化内存淘汰和生产配置)
24. [监控、排查和常见错误](#24-监控排查和常见错误)
25. [学习路线和练习题](#25-学习路线和练习题)

---

## 1. 先建立 Redis 的直觉

你已经学过 PostgreSQL，可以先这么理解：

- PostgreSQL 是主数据库，负责可靠保存业务数据。
- Redis 是内存数据结构服务器，负责快、临时、计数、排队、缓存、限流。

Redis 不是“另一个 ORM 数据库”。它更像一个速度极快的后端工具箱。

在 React + FastAPI + PostgreSQL 项目里，常见链路是：

```text
React
  -> FastAPI
    -> 先查 Redis 缓存
      -> 命中：直接返回
      -> 未命中：查 PostgreSQL / ORM
         -> 写入 Redis
         -> 返回给前端
```

或者：

```text
用户请求 FastAPI
  -> Redis 记录这个 IP 一分钟请求了多少次
  -> 超过阈值：拒绝请求
  -> 没超过：继续处理
```

Redis 里的数据一般是这样的：

```text
key                         value
user:1:profile              {"id":1,"name":"alice"}
post:hot:list               [12, 35, 8, 19]
login:code:13800138000      826391
rate_limit:ip:127.0.0.1     27
article:views               sorted set
```

### 1.1 Redis 的核心特点

| 特点 | 说明 |
|---|---|
| 快 | 数据主要在内存里，读写非常快 |
| 数据结构丰富 | String、Hash、List、Set、Sorted Set 等 |
| 支持过期时间 | 很适合验证码、缓存、临时 token |
| 原子操作 | `INCR`、`SET NX` 等命令天然适合计数和锁 |
| 可持久化 | 可以把内存数据保存到磁盘，但它不是传统主库 |
| 单线程执行命令 | 避免很多并发锁问题，但慢命令会阻塞 |

### 1.2 Redis 最适合解决什么问题

| 场景 | 为什么适合 Redis |
|---|---|
| 缓存热门数据 | 读内存比查数据库快 |
| 验证码 | 天然需要几分钟后过期 |
| 登录 session | 可以设置过期时间 |
| 接口限流 | `INCR + EXPIRE` 很方便 |
| 计数器 | 浏览量、点赞数、下载次数 |
| 排行榜 | Sorted Set 天然适合 |
| 去重 | Set 天然适合 |
| 简单队列 | List / Stream 可做任务队列 |
| 分布式锁 | `SET key value NX EX seconds` |

### 1.3 Redis 不适合什么

不要把 Redis 当成 PostgreSQL 的替代品。

Redis 不适合：

- 存核心业务的唯一真相，比如订单、支付、用户资料主数据。
- 做复杂关系查询，比如多表 JOIN。
- 存超大对象，比如大图片、大文件、大段二进制。
- 不加限制地缓存所有东西。
- 用一个 Redis 实例承担所有业务，没有 key 规划、没有过期策略。

一句话：

```text
PostgreSQL 负责正确和可靠。
Redis 负责快速和临时。
```

---

## 2. Redis 和 PostgreSQL 的区别

你已经学过 PostgreSQL，所以这一章很重要。

| 对比 | PostgreSQL | Redis |
|---|---|---|
| 数据模型 | 表、行、列、关系 | key-value + 多种数据结构 |
| 主要存储 | 磁盘为主，内存缓存 | 内存为主，可落盘 |
| 查询能力 | SQL、JOIN、事务、聚合 | 通过 key 和数据结构命令访问 |
| 典型用途 | 主业务数据库 | 缓存、计数、限流、队列 |
| 数据可靠性 | 强 | 可配置，但通常不作为唯一主库 |
| 速度 | 已经很快 | 更快，尤其是简单读写 |
| ORM 支持 | SQLAlchemy、Tortoise 等 | 通常不用 ORM，直接命令操作 |

### 2.1 一个用户资料查询的例子

PostgreSQL 里：

```sql
SELECT id, username, avatar_url, bio
FROM users
WHERE id = 1;
```

Redis 里可能是：

```text
GET user:1:profile
```

返回一个 JSON 字符串：

```json
{"id":1,"username":"alice","avatar_url":"/a.png","bio":"hello"}
```

也可能用 Hash：

```text
HGETALL user:1:profile
```

得到：

```text
id          1
username    alice
avatar_url  /a.png
bio         hello
```

### 2.2 Redis 和 ORM 的关系

ORM 管 PostgreSQL 这类关系型数据库：

```python
user = await session.get(User, user_id)
```

Redis 通常不需要 ORM，而是直接通过客户端命令操作：

```python
cached = await redis.get(f"user:{user_id}:profile")
```

它们常常配合：

```python
async def get_user_profile(user_id: int):
    cache_key = f"user:{user_id}:profile"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    user = await db.get(User, user_id)
    data = user_to_dict(user)

    await redis.set(cache_key, json.dumps(data), ex=300)
    return data
```

---

## 3. 安装和连接 Redis

推荐两种方式：Docker 或 Homebrew。

### 3.1 使用 Docker 启动 Redis

```bash
docker run --name redis-learn \
  -p 6379:6379 \
  -d redis
```

连接：

```bash
docker exec -it redis-learn redis-cli
```

测试：

```text
PING
```

如果返回：

```text
PONG
```

说明连接成功。

停止容器：

```bash
docker stop redis-learn
```

再次启动：

```bash
docker start redis-learn
```

删除容器：

```bash
docker rm redis-learn
```

### 3.2 使用 Homebrew 安装

macOS 可以：

```bash
brew install redis
brew services start redis
```

连接：

```bash
redis-cli
```

测试：

```text
PING
```

### 3.3 Redis 默认端口

Redis 默认端口是：

```text
6379
```

本地连接地址通常是：

```text
redis://localhost:6379/0
```

最后的 `/0` 表示 Redis 的第 0 个逻辑数据库。

---

## 4. redis-cli 入门

进入 `redis-cli` 后，可以直接执行命令。

### 4.1 最小体验

```text
SET name alice
GET name
DEL name
GET name
```

你会看到：

```text
OK
"alice"
(integer) 1
(nil)
```

### 4.2 常用管理命令

| 命令 | 作用 |
|---|---|
| `PING` | 测试连接 |
| `SELECT 0` | 切换逻辑数据库 |
| `DBSIZE` | 当前数据库 key 数量 |
| `KEYS pattern` | 查找 key，学习环境可用，生产慎用 |
| `SCAN` | 渐进式扫描 key，生产更安全 |
| `TYPE key` | 查看 key 的类型 |
| `EXISTS key` | 判断 key 是否存在 |
| `DEL key` | 删除 key |
| `EXPIRE key seconds` | 设置过期秒数 |
| `TTL key` | 查看剩余过期时间 |
| `FLUSHDB` | 清空当前数据库，危险 |
| `FLUSHALL` | 清空所有数据库，极危险 |

### 4.3 为什么生产环境少用 KEYS

```text
KEYS user:*
```

这个命令会一次性扫描所有 key。数据量小时没问题，数据量大时可能阻塞 Redis。

更推荐：

```text
SCAN 0 MATCH user:* COUNT 100
```

`SCAN` 是分批扫描，不会一次性把 Redis 卡住。

---

## 5. Redis 的 key 设计

Redis 没有 SQL 表结构，所以 key 设计非常重要。

### 5.1 推荐命名风格

用冒号分隔层级：

```text
业务:实体:id:属性
```

示例：

```text
user:1:profile
user:1:settings
post:100:detail
post:100:comments
login:code:13800138000
rate_limit:ip:127.0.0.1
task:queue:email
rank:article:views
```

### 5.2 key 命名要表达清楚

不推荐：

```text
u1
p100
abc
```

推荐：

```text
user:1:profile
post:100:detail
```

Redis 很快，但人不是。key 命名清楚，后期排查会舒服很多。

### 5.3 key 不要太长

可以有可读性，但不要塞一大段 JSON 或长 URL。

如果必须基于复杂参数缓存，可以把参数做 hash：

```text
search:posts:sha256_abcd1234
```

### 5.4 给业务加前缀

如果一个 Redis 实例被多个环境或项目共用，可以加前缀：

```text
dev:task_app:user:1:profile
prod:task_app:user:1:profile
```

但更推荐不同环境使用不同 Redis 实例或不同数据库配置。

---

## 6. String：最常用的数据类型

Redis String 不是只能存字符串，它可以存：

- 普通文本。
- JSON 字符串。
- 数字计数。
- token。
- 验证码。

### 6.1 基本命令

```text
SET name alice
GET name
DEL name
```

设置多个：

```text
MSET user:1:name alice user:2:name bob
MGET user:1:name user:2:name
```

### 6.2 存 JSON

```text
SET user:1:profile '{"id":1,"username":"alice","role":"admin"}'
GET user:1:profile
```

后端拿到后再 `json.loads`。

### 6.3 计数器

```text
SET article:100:views 0
INCR article:100:views
INCR article:100:views
GET article:100:views
```

增加指定数量：

```text
INCRBY article:100:views 10
```

减少：

```text
DECR article:100:views
DECRBY article:100:views 5
```

### 6.4 SET 的常用参数

```text
SET login:code:13800138000 826391 EX 300
```

含义：设置验证码，300 秒后过期。

```text
SET lock:order:100 abc123 NX EX 10
```

含义：

- `NX`：key 不存在时才设置成功。
- `EX 10`：10 秒后自动过期。

这是分布式锁的基础。

### 6.5 GETSET 和 SET GET

新版本 Redis 支持 `SET ... GET`：

```text
SET counter 1
SET counter 2 GET
```

它会设置新值，同时返回旧值。

初学阶段知道即可，日常最常用还是 `GET`、`SET`、`INCR`。

---

## 7. 过期时间 TTL：Redis 的灵魂能力之一

Redis 很适合临时数据，因为 key 可以自动过期。

### 7.1 设置过期时间

```text
SET verify:code:13800138000 826391 EX 300
```

或者：

```text
SET verify:code:13800138000 826391
EXPIRE verify:code:13800138000 300
```

### 7.2 查看剩余时间

```text
TTL verify:code:13800138000
```

返回：

| 返回值 | 含义 |
|---:|---|
| 正整数 | 剩余秒数 |
| `-1` | key 存在，但没有过期时间 |
| `-2` | key 不存在 |

### 7.3 删除过期时间

```text
PERSIST verify:code:13800138000
```

### 7.4 毫秒级过期

```text
SET temp:value hello PX 1500
```

表示 1500 毫秒后过期。

### 7.5 为什么缓存一定要设置过期时间

如果缓存永不过期：

- 数据更新后，用户可能一直看到旧数据。
- Redis 内存会越来越大。
- 业务 bug 更难排查。

实战建议：

- 用户资料缓存：5 到 30 分钟。
- 首页热门内容：30 秒到 5 分钟。
- 验证码：3 到 10 分钟。
- 限流 key：按窗口设置，比如 60 秒。
- 分布式锁：必须设置短过期时间。

---

## 8. Hash：存对象字段

Hash 很像一个小对象：

```text
user:1:profile
  username -> alice
  email    -> alice@example.com
  role     -> admin
```

### 8.1 基本命令

```text
HSET user:1:profile username alice email alice@example.com role admin
HGET user:1:profile username
HMGET user:1:profile username email
HGETALL user:1:profile
```

删除字段：

```text
HDEL user:1:profile role
```

判断字段是否存在：

```text
HEXISTS user:1:profile email
```

### 8.2 Hash 适合什么

适合：

- 字段比较稳定的小对象。
- 只想更新某个字段，而不是整个 JSON。
- 用户设置、商品简要信息、配置项。

例如：

```text
HSET product:100 stock 50 price 199.00 title keyboard
HINCRBY product:100 stock -1
```

### 8.3 Hash 和 JSON String 怎么选

| 方式 | 优点 | 缺点 |
|---|---|---|
| JSON String | 和 FastAPI 返回结构接近，序列化简单 | 修改单个字段要整体读写 |
| Hash | 可以单独读写字段 | 嵌套结构不方便 |

实战建议：

- 接口响应缓存：优先 JSON String。
- 简单对象字段缓存：可以用 Hash。

---

## 9. List：队列和时间线

List 是有顺序的列表，可以从左边或右边插入、弹出。

### 9.1 基本命令

左侧插入：

```text
LPUSH tasks a
LPUSH tasks b
LPUSH tasks c
```

查看范围：

```text
LRANGE tasks 0 -1
```

右侧弹出：

```text
RPOP tasks
```

右侧插入：

```text
RPUSH tasks d
```

左侧弹出：

```text
LPOP tasks
```

### 9.2 队列

生产者往左边推：

```text
LPUSH queue:email '{"to":"a@example.com","template":"welcome"}'
```

消费者从右边取：

```text
RPOP queue:email
```

这样就是先进先出队列。

### 9.3 阻塞弹出

普通 `RPOP` 如果没有数据，会立刻返回空。

`BRPOP` 可以等待：

```text
BRPOP queue:email 5
```

表示最多等 5 秒。

### 9.4 List 适合什么

适合：

- 简单任务队列。
- 最新消息列表。
- 最近访问记录。

不适合：

- 复杂可靠任务系统。
- 需要确认、重试、死信队列的任务。

如果任务系统变复杂，可以考虑：

- Celery + Redis/RabbitMQ。
- RQ。
- Dramatiq。
- Redis Stream。

---

## 10. Set：去重集合

Set 是无序、自动去重的集合。

### 10.1 基本命令

```text
SADD post:100:liked_users 1
SADD post:100:liked_users 2
SADD post:100:liked_users 1
SMEMBERS post:100:liked_users
SCARD post:100:liked_users
SISMEMBER post:100:liked_users 1
SREM post:100:liked_users 1
```

解释：

| 命令 | 作用 |
|---|---|
| `SADD` | 添加成员 |
| `SMEMBERS` | 查看所有成员 |
| `SCARD` | 成员数量 |
| `SISMEMBER` | 判断是否存在 |
| `SREM` | 删除成员 |

### 10.2 集合运算

用户 1 关注的人：

```text
SADD user:1:following 2 3 4
```

用户 2 关注的人：

```text
SADD user:2:following 3 4 5
```

交集：

```text
SINTER user:1:following user:2:following
```

并集：

```text
SUNION user:1:following user:2:following
```

差集：

```text
SDIFF user:1:following user:2:following
```

### 10.3 Set 适合什么

适合：

- 点赞用户去重。
- 用户签到。
- 黑名单。
- 权限集合。
- 共同关注、共同好友。
- 防止重复提交。

---

## 11. Sorted Set：排行榜和权重排序

Sorted Set，也叫 ZSet，是 Redis 里非常实用的数据结构。

它的每个成员都有一个分数：

```text
member -> score
```

### 11.1 基本命令

```text
ZADD rank:article:views 100 article:1
ZADD rank:article:views 300 article:2
ZADD rank:article:views 200 article:3
```

从低到高：

```text
ZRANGE rank:article:views 0 -1 WITHSCORES
```

从高到低：

```text
ZREVRANGE rank:article:views 0 -1 WITHSCORES
```

增加分数：

```text
ZINCRBY rank:article:views 1 article:1
```

查排名：

```text
ZREVRANK rank:article:views article:1
```

查分数：

```text
ZSCORE rank:article:views article:1
```

### 11.2 排行榜

文章浏览排行榜：

```text
ZINCRBY rank:article:views 1 article:100
ZREVRANGE rank:article:views 0 9 WITHSCORES
```

用户积分排行榜：

```text
ZADD rank:user:points 1500 user:1
ZADD rank:user:points 800 user:2
ZADD rank:user:points 2300 user:3
ZREVRANGE rank:user:points 0 9 WITHSCORES
```

### 11.3 Sorted Set 适合什么

适合：

- 排行榜。
- 热门文章。
- 延迟队列。
- 根据权重取前 N 个。
- 按时间戳排序的任务。

---

## 12. Bitmap、HyperLogLog、Stream 简介

这些可以先有印象，不用第一天吃透。

### 12.1 Bitmap

Bitmap 适合记录大量 true/false 状态。

例如用户签到：

```text
SETBIT signin:2026-07 user_id 1
GETBIT signin:2026-07 user_id
BITCOUNT signin:2026-07
```

实际命令里 `user_id` 要替换成数字偏移量，比如 10001。

适合：

- 签到。
- 活跃状态。
- 是否看过某内容。

### 12.2 HyperLogLog

HyperLogLog 用来估算去重数量，占用内存很小。

比如统计网站 UV：

```text
PFADD uv:2026-07-28 user:1
PFADD uv:2026-07-28 user:2
PFADD uv:2026-07-28 user:1
PFCOUNT uv:2026-07-28
```

注意：它是估算，不是精确值。

适合：

- 大规模 UV 统计。
- 对精确度要求不极端的去重计数。

### 12.3 Stream

Stream 是 Redis 的消息流结构，比 List 更适合消息队列。

```text
XADD stream:orders * order_id 100 user_id 1
XREAD COUNT 10 STREAMS stream:orders 0
```

它支持：

- 消息 ID。
- 消费者组。
- 确认机制。
- 读取历史消息。

初学阶段，如果只是做简单后台任务，可以先理解 List；以后需要更可靠的消息系统，再深入 Stream 或专业消息队列。

---

## 13. Redis 在后端项目里的典型用途

### 13.1 缓存

最常见：

```text
GET /posts/100
  -> 查 Redis: post:100:detail
  -> 有：直接返回
  -> 没有：查 PostgreSQL
  -> 写 Redis，设置 5 分钟过期
  -> 返回
```

### 13.2 验证码

```text
SET login:code:13800138000 826391 EX 300
```

5 分钟后自动失效。

### 13.3 登录 session

```text
SET session:token:abc123 user:1 EX 86400
```

一天后自动过期。

### 13.4 限流

```text
INCR rate_limit:ip:127.0.0.1
EXPIRE rate_limit:ip:127.0.0.1 60
```

一分钟内请求次数超过阈值就拒绝。

### 13.5 点赞去重

```text
SADD post:100:liked_users 1
SISMEMBER post:100:liked_users 1
SCARD post:100:liked_users
```

### 13.6 排行榜

```text
ZINCRBY rank:post:hot 1 post:100
ZREVRANGE rank:post:hot 0 9 WITHSCORES
```

### 13.7 简单异步任务

```text
LPUSH queue:email '{"to":"alice@example.com","type":"welcome"}'
BRPOP queue:email 0
```

---

## 14. 缓存设计：从最简单到能上线

缓存是 Redis 最常见用途，也是最容易写出坑的地方。

### 14.1 Cache Aside 模式

这是 Web 后端最常用的缓存模式。

读取：

```text
1. 先查 Redis
2. 命中就返回
3. 未命中就查 PostgreSQL
4. 把结果写入 Redis
5. 返回结果
```

伪代码：

```python
async def get_post(post_id: int):
    cache_key = f"post:{post_id}:detail"

    cached = await redis.get(cache_key)
    if cached:
        return json.loads(cached)

    post = await db.get(Post, post_id)
    if post is None:
        return None

    data = post_to_dict(post)
    await redis.set(cache_key, json.dumps(data), ex=300)
    return data
```

更新：

```text
1. 先更新 PostgreSQL
2. 删除 Redis 缓存
3. 下次读取时重新查数据库并回填缓存
```

伪代码：

```python
async def update_post(post_id: int, payload: dict):
    post = await update_post_in_db(post_id, payload)
    await redis.delete(f"post:{post_id}:detail")
    return post
```

### 14.2 为什么更新后通常是删除缓存，而不是更新缓存

因为删除更简单、更不容易出错。

如果你更新缓存，需要保证：

- 数据库更新成功。
- 缓存更新成功。
- 缓存格式和查询返回格式完全一致。
- 并发情况下不会被旧数据覆盖。

删除缓存的思路是：

```text
旧缓存删掉，下次读的时候重新生成。
```

### 14.3 什么数据适合缓存

适合缓存：

- 读取频繁。
- 更新不太频繁。
- 查询成本较高。
- 允许短时间不是最新。

比如：

- 热门文章。
- 用户公开资料。
- 首页推荐列表。
- 商品分类树。
- 统计结果。

不适合缓存：

- 更新极频繁且必须实时准确的数据。
- 一次性读取的数据。
- 体积极大、访问很少的数据。
- 权限复杂且容易泄露的数据。

### 14.4 缓存时间怎么定

没有万能值，但可以这样想：

| 数据 | 建议过期时间 |
|---|---|
| 验证码 | 3 到 10 分钟 |
| 用户资料 | 5 到 30 分钟 |
| 首页热门列表 | 30 秒到 5 分钟 |
| 商品分类 | 10 分钟到数小时 |
| 临时 token | 按业务安全要求 |
| 限流 key | 和限流窗口一致 |

---

## 15. 缓存问题：穿透、击穿、雪崩、脏数据

这些概念听起来吓人，其实都是“缓存没按预期帮你挡住数据库压力”。

### 15.1 缓存穿透

含义：请求的数据根本不存在，Redis 没有，PostgreSQL 也没有。

比如有人一直请求：

```text
GET /posts/999999999
```

每次：

```text
Redis miss -> 查 PostgreSQL -> 查不到 -> 不缓存 -> 下次还查 PostgreSQL
```

解决：缓存空值。

```python
if post is None:
    await redis.set(cache_key, "null", ex=60)
    return None
```

读取时：

```python
cached = await redis.get(cache_key)
if cached == "null":
    return None
```

也可以加参数校验、布隆过滤器，但初学先记住“缓存空值”。

### 15.2 缓存击穿

含义：某个热点 key 突然过期，大量请求同时打到数据库。

例子：

```text
post:100:detail 是热门文章
它刚好过期
1000 个请求同时进来
大家都发现 Redis 没有
大家都去查 PostgreSQL
```

解决思路：

- 热点 key 设置更长过期时间。
- 提前刷新缓存。
- 加互斥锁，只有一个请求回源数据库，其他请求等待或返回旧值。

### 15.3 缓存雪崩

含义：大量 key 在同一时间过期，导致数据库瞬间压力暴涨。

解决：过期时间加随机抖动。

```python
ttl = 300 + random.randint(0, 60)
await redis.set(cache_key, json.dumps(data), ex=ttl)
```

这样不会所有缓存同一秒失效。

### 15.4 缓存脏数据

含义：数据库已经更新，但 Redis 里还是旧数据。

常见原因：

- 更新数据库后忘了删缓存。
- 删缓存失败。
- 并发读写导致旧数据回填。

初学项目可以采用：

```text
更新数据库成功后，立即删除相关缓存。
```

更复杂的系统会用：

- 消息队列异步删缓存。
- 延迟双删。
- 版本号。
- 更严格的数据一致性设计。

### 15.5 一句话总结

| 问题 | 白话 | 基础解决 |
|---|---|---|
| 穿透 | 查不存在的数据，缓存挡不住 | 缓存空值 |
| 击穿 | 单个热点 key 过期 | 加锁、延长 TTL、预热 |
| 雪崩 | 大量 key 同时过期 | TTL 加随机值 |
| 脏数据 | 缓存和数据库不一致 | 更新 DB 后删缓存 |

---

## 16. FastAPI 连接 Redis

Python 推荐使用 `redis` 官方客户端，它支持 asyncio。

### 16.1 安装

```bash
pip install redis fastapi uvicorn python-dotenv
```

如果你已有 FastAPI 项目，只需要：

```bash
pip install redis python-dotenv
```

### 16.2 环境变量

`.env`：

```env
REDIS_URL=redis://localhost:6379/0
```

### 16.3 最小 FastAPI 示例

```python
import os
from contextlib import asynccontextmanager

import redis.asyncio as redis
from dotenv import load_dotenv
from fastapi import FastAPI

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    app.state.redis = redis.from_url(redis_url, decode_responses=True)

    await app.state.redis.ping()
    yield

    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)


@app.get("/ping-redis")
async def ping_redis():
    pong = await app.state.redis.ping()
    return {"redis": pong}
```

启动：

```bash
uvicorn main:app --reload
```

访问：

```text
GET http://127.0.0.1:8000/ping-redis
```

返回：

```json
{"redis": true}
```

### 16.4 decode_responses=True 是什么

默认情况下，Redis Python 客户端返回 bytes：

```python
b"alice"
```

设置：

```python
decode_responses=True
```

它会自动解码成字符串：

```python
"alice"
```

对于初学项目更方便。

### 16.5 依赖注入写法

可以封装成依赖：

```python
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Request


def get_redis(request: Request) -> redis.Redis:
    return request.app.state.redis


RedisDep = Annotated[redis.Redis, Depends(get_redis)]
```

路由里使用：

```python
@app.get("/cache-demo")
async def cache_demo(r: RedisDep):
    await r.set("demo:name", "alice", ex=60)
    value = await r.get("demo:name")
    return {"value": value}
```

---

## 17. 实战一：缓存 PostgreSQL/ORM 查询结果

假设你已经有 SQLAlchemy ORM：

```python
class Post(Base):
    __tablename__ = "posts"

    id = mapped_column(BigInteger, primary_key=True)
    title = mapped_column(String(200), nullable=False)
    content = mapped_column(Text, nullable=False)
    author_id = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at = mapped_column(DateTime(timezone=True), server_default=func.now())
```

现在你要做：

```text
GET /posts/{post_id}
```

### 17.1 不加缓存的版本

```python
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession


async def get_post_detail(db: AsyncSession, post_id: int):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_id,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }
```

### 17.2 加 Redis 缓存

```python
import json
import random

from fastapi import HTTPException
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


def post_cache_key(post_id: int) -> str:
    return f"post:{post_id}:detail"


def post_to_dict(post: Post) -> dict:
    return {
        "id": post.id,
        "title": post.title,
        "content": post.content,
        "author_id": post.author_id,
        "created_at": post.created_at.isoformat(),
        "updated_at": post.updated_at.isoformat(),
    }


async def get_post_detail(db: AsyncSession, r: Redis, post_id: int):
    cache_key = post_cache_key(post_id)

    cached = await r.get(cache_key)
    if cached == "null":
        raise HTTPException(status_code=404, detail="Post not found")
    if cached:
        return json.loads(cached)

    post = await db.get(Post, post_id)
    if post is None:
        await r.set(cache_key, "null", ex=60)
        raise HTTPException(status_code=404, detail="Post not found")

    data = post_to_dict(post)
    ttl = 300 + random.randint(0, 60)
    await r.set(cache_key, json.dumps(data, ensure_ascii=False), ex=ttl)

    return data
```

这里做了几件事：

- 先查 Redis。
- 命中则直接返回。
- 查不到再查 PostgreSQL。
- 查不到文章时缓存 `"null"`，防止缓存穿透。
- 正常数据缓存 5 到 6 分钟，减少雪崩风险。

### 17.3 更新文章时删除缓存

```python
async def update_post(db: AsyncSession, r: Redis, post_id: int, payload: dict):
    post = await db.get(Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    for field, value in payload.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)

    await r.delete(post_cache_key(post_id))

    return post_to_dict(post)
```

### 17.4 列表缓存

列表接口也可以缓存：

```text
GET /posts?page=1&page_size=20
```

key 可以设计成：

```text
posts:list:page:1:size:20
```

如果还有搜索条件：

```text
posts:list:q:python:page:1:size:20
```

复杂条件可以把参数排序后做 hash：

```python
import hashlib
import json


def make_query_cache_key(prefix: str, params: dict) -> str:
    raw = json.dumps(params, sort_keys=True, ensure_ascii=False)
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"
```

### 17.5 列表缓存失效

如果文章新增、删除、修改，相关列表缓存都可能失效。

简单做法：

```text
列表缓存 TTL 设置短一点，比如 30 秒到 2 分钟。
详情缓存更新时精准删除。
```

不要一开始就追求完美缓存一致性。先让业务正确，再优化热点路径。

---

## 18. 实战二：登录验证码和短信验证码

验证码是 Redis 入门最好的实战之一。

需求：

- 用户输入手机号或邮箱。
- 后端生成 6 位验证码。
- Redis 保存 5 分钟。
- 用户提交验证码。
- 验证成功后删除验证码。

### 18.1 生成验证码

```python
import random


def generate_code() -> str:
    return f"{random.randint(0, 999999):06d}"
```

### 18.2 保存验证码

```python
from redis.asyncio import Redis


async def save_login_code(r: Redis, phone: str, code: str):
    key = f"login:code:{phone}"
    await r.set(key, code, ex=300)
```

### 18.3 校验验证码

```python
from fastapi import HTTPException
from redis.asyncio import Redis


async def verify_login_code(r: Redis, phone: str, code: str):
    key = f"login:code:{phone}"
    saved_code = await r.get(key)

    if saved_code is None:
        raise HTTPException(status_code=400, detail="Code expired")

    if saved_code != code:
        raise HTTPException(status_code=400, detail="Invalid code")

    await r.delete(key)
    return True
```

### 18.4 防止频繁发送

再加一个发送间隔 key：

```python
async def can_send_code(r: Redis, phone: str) -> bool:
    key = f"login:code:cooldown:{phone}"

    ok = await r.set(key, "1", nx=True, ex=60)
    return ok is True
```

解释：

- `nx=True` 表示只有 key 不存在时才设置成功。
- 设置成功说明可以发。
- 设置失败说明 60 秒内已经发过。

### 18.5 限制错误次数

```python
async def check_code_attempts(r: Redis, phone: str):
    key = f"login:code:attempts:{phone}"
    attempts = await r.incr(key)

    if attempts == 1:
        await r.expire(key, 300)

    if attempts > 5:
        raise HTTPException(status_code=429, detail="Too many attempts")
```

完整校验时：

```python
async def verify_login_code_with_limit(r: Redis, phone: str, code: str):
    await check_code_attempts(r, phone)

    key = f"login:code:{phone}"
    saved_code = await r.get(key)

    if saved_code is None:
        raise HTTPException(status_code=400, detail="Code expired")

    if saved_code != code:
        raise HTTPException(status_code=400, detail="Invalid code")

    await r.delete(key)
    await r.delete(f"login:code:attempts:{phone}")
    return True
```

---

## 19. 实战三：接口限流

限流就是限制某个用户或 IP 在一段时间内的请求次数。

比如：

```text
同一个 IP 每 60 秒最多请求 100 次
```

### 19.1 固定窗口限流

最简单版本：

```python
from fastapi import HTTPException, Request
from redis.asyncio import Redis


async def rate_limit_by_ip(r: Redis, request: Request):
    client_ip = request.client.host if request.client else "unknown"
    key = f"rate_limit:ip:{client_ip}"

    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)

    if count > 100:
        ttl = await r.ttl(key)
        raise HTTPException(
            status_code=429,
            detail=f"Too many requests. Try again in {ttl} seconds.",
        )
```

路由中使用：

```python
@app.get("/posts")
async def list_posts(request: Request, r: RedisDep):
    await rate_limit_by_ip(r, request)
    return {"items": []}
```

### 19.2 固定窗口的问题

固定窗口有边界问题：

```text
第 59 秒请求 100 次
第 60 秒窗口重置
又请求 100 次
短时间内实际通过 200 次
```

很多小项目可以接受。更严格时可以用滑动窗口、令牌桶、漏桶。

### 19.3 按用户限流

登录后可以按用户 ID 限流：

```python
async def rate_limit_by_user(r: Redis, user_id: int):
    key = f"rate_limit:user:{user_id}"

    count = await r.incr(key)
    if count == 1:
        await r.expire(key, 60)

    if count > 300:
        raise HTTPException(status_code=429, detail="Too many requests")
```

### 19.4 更安全的 Lua 限流

上面的 `INCR` 和 `EXPIRE` 是两条命令。极端情况下，`INCR` 成功后服务崩了，可能没来得及设置过期时间。

Lua 脚本可以把逻辑变成原子操作：

```python
RATE_LIMIT_SCRIPT = """
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return current
"""


async def rate_limit_with_lua(r: Redis, key: str, seconds: int, limit: int):
    current = await r.eval(RATE_LIMIT_SCRIPT, 1, key, seconds)
    if int(current) > limit:
        raise HTTPException(status_code=429, detail="Too many requests")
```

初学阶段可以先用简单版本，知道 Lua 能解决原子性问题即可。

---

## 20. 实战四：排行榜

假设你做一个博客或内容社区，需要文章热度榜。

### 20.1 记录浏览量

```python
async def increase_post_views(r: Redis, post_id: int):
    await r.zincrby("rank:post:views", 1, f"post:{post_id}")
```

### 20.2 查询 Top 10

```python
async def get_top_posts(r: Redis):
    items = await r.zrevrange("rank:post:views", 0, 9, withscores=True)

    return [
        {
            "post_id": int(member.split(":")[1]),
            "views": int(score),
        }
        for member, score in items
    ]
```

### 20.3 返回完整文章信息

排行榜只保存 ID 和分数，文章标题、作者等信息还是在 PostgreSQL。

流程：

```text
1. Redis 取 top post ids
2. PostgreSQL 查询这些文章
3. 按 Redis 排名顺序组装返回
```

伪代码：

```python
async def get_top_post_details(db: AsyncSession, r: Redis):
    ranked = await get_top_posts(r)
    post_ids = [item["post_id"] for item in ranked]

    if not post_ids:
        return []

    result = await db.execute(select(Post).where(Post.id.in_(post_ids)))
    posts = result.scalars().all()
    post_map = {post.id: post for post in posts}

    return [
        {
            "id": post_id,
            "title": post_map[post_id].title,
            "views": item["views"],
        }
        for item in ranked
        for post_id in [item["post_id"]]
        if post_id in post_map
    ]
```

### 20.4 定期落库

浏览量如果只在 Redis，Redis 数据丢了就麻烦。

更稳妥：

```text
每次浏览：Redis 计数
定时任务：把 Redis 增量同步到 PostgreSQL
```

例如：

```text
post:views:delta
  post:100 -> 32
  post:101 -> 8
```

定时任务每分钟读一次，然后：

```sql
UPDATE posts
SET view_count = view_count + :delta
WHERE id = :post_id;
```

---

## 21. 实战五：简单任务队列

有些操作不适合在接口里同步做：

- 发送邮件。
- 生成报表。
- 图片压缩。
- 调用慢的第三方接口。

请求里只需要把任务放进队列，然后快速返回。

### 21.1 生产任务

```python
import json
from redis.asyncio import Redis


async def enqueue_email(r: Redis, to: str, template: str):
    job = {
        "to": to,
        "template": template,
    }
    await r.lpush("queue:email", json.dumps(job, ensure_ascii=False))
```

路由：

```python
@app.post("/send-welcome-email")
async def send_welcome_email(r: RedisDep):
    await enqueue_email(r, "alice@example.com", "welcome")
    return {"queued": True}
```

### 21.2 消费任务

单独写一个 worker：

```python
import asyncio
import json
import os

import redis.asyncio as redis
from dotenv import load_dotenv

load_dotenv()


async def send_email(to: str, template: str):
    print(f"send email to={to}, template={template}")


async def main():
    r = redis.from_url(
        os.getenv("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True,
    )

    while True:
        item = await r.brpop("queue:email", timeout=0)
        _, raw_job = item
        job = json.loads(raw_job)
        await send_email(job["to"], job["template"])


if __name__ == "__main__":
    asyncio.run(main())
```

### 21.3 这个简单队列的问题

上面版本适合学习，但不是完整可靠任务系统。

问题：

- worker 取出任务后崩溃，任务可能丢失。
- 没有重试次数。
- 没有失败队列。
- 没有任务状态。
- 没有并发控制。

生产项目更推荐：

- Celery。
- RQ。
- Dramatiq。
- Arq。
- Redis Stream。
- RabbitMQ / Kafka 这类专业消息系统。

你现在先学 List 队列，理解“请求快速返回，耗时任务异步处理”的思想就很好。

---

## 22. 事务、Lua 和分布式锁

Redis 里有些操作需要原子性。

### 22.1 Redis 事务 MULTI/EXEC

```text
MULTI
INCR article:100:views
EXPIRE article:100:views 3600
EXEC
```

Redis 事务和 PostgreSQL 事务不完全一样。

PostgreSQL 事务更像：

```text
中间失败可以回滚，保证数据一致性。
```

Redis 的 `MULTI/EXEC` 更像：

```text
把多个命令排队，然后一次性按顺序执行。
```

### 22.2 Lua 脚本

Lua 可以把一段逻辑放到 Redis 里原子执行。

限流脚本：

```text
local current = redis.call("INCR", KEYS[1])
if current == 1 then
  redis.call("EXPIRE", KEYS[1], ARGV[1])
end
return current
```

Python 调用：

```python
current = await r.eval(script, 1, "rate_limit:ip:127.0.0.1", 60)
```

### 22.3 分布式锁是什么

假设你部署了 4 个 FastAPI 进程。

某个任务只能同时被一个进程执行，比如：

- 同步库存。
- 生成日报。
- 处理某个订单。

这时可以用 Redis 锁。

### 22.4 最小分布式锁

```python
import uuid
from redis.asyncio import Redis


async def acquire_lock(r: Redis, key: str, ttl: int = 10) -> str | None:
    token = str(uuid.uuid4())
    ok = await r.set(key, token, nx=True, ex=ttl)
    if ok:
        return token
    return None
```

释放锁要确保只释放自己的锁：

```python
UNLOCK_SCRIPT = """
if redis.call("GET", KEYS[1]) == ARGV[1] then
  return redis.call("DEL", KEYS[1])
else
  return 0
end
"""


async def release_lock(r: Redis, key: str, token: str):
    await r.eval(UNLOCK_SCRIPT, 1, key, token)
```

使用：

```python
token = await acquire_lock(r, "lock:daily-report", ttl=30)
if token is None:
    return {"message": "Another worker is running"}

try:
    await generate_report()
finally:
    await release_lock(r, "lock:daily-report", token)
```

### 22.5 分布式锁注意事项

- 必须设置过期时间，避免死锁。
- value 要用随机 token，释放时确认是自己的锁。
- 任务执行时间不能随便超过锁过期时间。
- 强一致场景不要轻率依赖简单 Redis 锁。

---

## 23. 持久化、内存淘汰和生产配置

Redis 是内存数据库，但支持持久化。

### 23.1 RDB

RDB 是快照持久化。

可以理解为：

```text
每隔一段时间，把 Redis 当前数据保存成一个快照文件。
```

优点：

- 文件紧凑。
- 恢复速度较快。

缺点：

- 两次快照之间的数据可能丢失。

### 23.2 AOF

AOF 是追加日志。

可以理解为：

```text
把每次写命令记录下来，重启时重新执行。
```

优点：

- 数据丢失更少。

缺点：

- 文件可能更大。
- 恢复可能更慢。

### 23.3 Redis 能不能当主数据库

大多数 Web 项目里，不建议把 Redis 当唯一主数据库。

更常见：

```text
PostgreSQL：保存最终业务数据
Redis：缓存、临时状态、计数、队列、限流
```

### 23.4 内存淘汰策略

Redis 内存满了怎么办？由 `maxmemory-policy` 决定。

常见策略：

| 策略 | 含义 |
|---|---|
| `noeviction` | 不淘汰，写入报错 |
| `allkeys-lru` | 所有 key 中淘汰最近最少使用 |
| `volatile-lru` | 只从设置了过期时间的 key 里淘汰 LRU |
| `allkeys-random` | 所有 key 中随机淘汰 |
| `volatile-random` | 只从有过期时间的 key 里随机淘汰 |
| `volatile-ttl` | 优先淘汰快过期的 key |

缓存型 Redis 常见选择：

```text
allkeys-lru
```

但如果 Redis 里有不能丢的临时业务状态，就要谨慎规划，最好拆实例。

### 23.5 生产环境基本建议

- 设置密码或内网访问控制。
- 不要暴露 Redis 到公网。
- 设置合理 `maxmemory`。
- 缓存 key 尽量设置 TTL。
- 监控内存、连接数、慢命令。
- 重要数据不要只放 Redis。
- 开发、测试、生产使用不同 Redis。

---

## 24. 监控、排查和常见错误

### 24.1 查看 Redis 信息

```text
INFO
```

常看：

- `used_memory_human`
- `connected_clients`
- `total_commands_processed`
- `keyspace_hits`
- `keyspace_misses`
- `evicted_keys`
- `expired_keys`

### 24.2 查看慢命令

```text
SLOWLOG GET 10
```

### 24.3 查看 key 类型

```text
TYPE user:1:profile
```

如果你对一个 String 执行 Hash 命令，会报错：

```text
WRONGTYPE Operation against a key holding the wrong kind of value
```

### 24.4 连接被拒绝

错误类似：

```text
Connection refused
```

排查：

- Redis 服务是否启动。
- 端口是否是 6379。
- Docker 是否映射端口。
- `REDIS_URL` 是否正确。

### 24.5 密码错误

错误类似：

```text
NOAUTH Authentication required
```

或：

```text
WRONGPASS invalid username-password pair
```

连接字符串带密码：

```env
REDIS_URL=redis://:your_password@localhost:6379/0
```

### 24.6 key 明明设置了却查不到

排查：

- 是否连到了不同逻辑数据库，比如 `/0` 和 `/1`。
- key 是否已经过期。
- key 名是否拼错。
- 项目前缀是否不一致。

命令：

```text
TTL your:key
EXISTS your:key
SELECT 0
SELECT 1
```

### 24.7 内存越来越大

排查：

- 有没有缓存 key 没设置 TTL。
- 有没有大 key。
- 列表、集合、排行榜是否一直增长。
- 是否把大量接口响应无限缓存。

查大 key 可以用：

```bash
redis-cli --bigkeys
```

生产环境使用前要了解影响，避免在高峰期排查。

---

## 25. 学习路线和练习题

### 25.1 建议学习路线

第一阶段：基本命令

- `GET`、`SET`、`DEL`。
- `EXPIRE`、`TTL`。
- `INCR`、`DECR`。
- `HSET`、`HGETALL`。
- `LPUSH`、`BRPOP`。
- `SADD`、`SISMEMBER`。
- `ZADD`、`ZREVRANGE`。

第二阶段：后端实战

- FastAPI 连接 Redis。
- 给 ORM 查询加缓存。
- 写验证码。
- 写接口限流。
- 写浏览量计数。
- 写排行榜。

第三阶段：缓存设计

- Cache Aside。
- 缓存空值。
- TTL 随机抖动。
- 更新数据库后删除缓存。
- 热点数据预热。

第四阶段：工程化

- Redis 持久化。
- 内存淘汰策略。
- 慢命令排查。
- Lua 原子操作。
- 分布式锁。
- Redis Stream 或任务队列框架。

### 25.2 必做练习一：验证码

实现接口：

```text
POST /auth/send-code
POST /auth/login-by-code
```

要求：

- 验证码 6 位数字。
- 5 分钟过期。
- 60 秒内不能重复发送。
- 输错超过 5 次锁定 5 分钟。
- 验证成功后删除验证码和错误次数。

### 25.3 必做练习二：文章详情缓存

已有 PostgreSQL 表：

```text
posts(id, title, content, author_id, created_at, updated_at)
```

实现：

```text
GET /posts/{post_id}
PATCH /posts/{post_id}
DELETE /posts/{post_id}
```

要求：

- 查询详情先查 Redis。
- Redis miss 后查 PostgreSQL。
- 不存在的文章缓存空值 60 秒。
- 正常文章缓存 5 到 6 分钟。
- 更新和删除文章后删除详情缓存。

### 25.4 必做练习三：限流

实现：

```text
同一个 IP 每分钟最多访问 /posts 100 次
登录用户每分钟最多点赞 30 次
```

要求：

- 使用 Redis `INCR`。
- 第一次请求设置 `EXPIRE`。
- 超过限制返回 HTTP 429。
- 返回剩余 TTL。

### 25.5 必做练习四：排行榜

实现：

```text
POST /posts/{post_id}/view
GET /posts/rankings/views
```

要求：

- 每次浏览用 `ZINCRBY` 增加分数。
- 排行榜用 `ZREVRANGE` 取前 10。
- 返回文章 ID、标题、浏览量。
- 标题从 PostgreSQL 查询。

### 25.6 必做练习五：简单任务队列

实现：

```text
POST /emails/welcome
```

要求：

- 接口只负责把任务写入 Redis List。
- 单独 worker 使用 `BRPOP` 消费。
- worker 打印任务内容即可。

---

## 附录 A：Redis 常用命令速查

### Key

```text
EXISTS key
DEL key
TYPE key
EXPIRE key 60
TTL key
SCAN 0 MATCH user:* COUNT 100
```

### String

```text
SET name alice
GET name
SET code 826391 EX 300
SET lock:demo token NX EX 10
INCR counter
INCRBY counter 10
DECR counter
```

### Hash

```text
HSET user:1 username alice email alice@example.com
HGET user:1 username
HMGET user:1 username email
HGETALL user:1
HDEL user:1 email
```

### List

```text
LPUSH queue:email job1
RPOP queue:email
BRPOP queue:email 0
LRANGE queue:email 0 -1
LLEN queue:email
```

### Set

```text
SADD post:1:likes user:1
SISMEMBER post:1:likes user:1
SCARD post:1:likes
SMEMBERS post:1:likes
SREM post:1:likes user:1
SINTER set:a set:b
SUNION set:a set:b
SDIFF set:a set:b
```

### Sorted Set

```text
ZADD rank:posts 100 post:1
ZINCRBY rank:posts 1 post:1
ZREVRANGE rank:posts 0 9 WITHSCORES
ZSCORE rank:posts post:1
ZREVRANK rank:posts post:1
ZREM rank:posts post:1
```

---

## 附录 B：FastAPI Redis 工具模块示例

可以在项目里建一个 `redis_client.py`：

```python
import os
from typing import Annotated

import redis.asyncio as redis
from fastapi import Depends, Request


def create_redis_client() -> redis.Redis:
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    return redis.from_url(redis_url, decode_responses=True)


def get_redis(request: Request) -> redis.Redis:
    return request.app.state.redis


RedisDep = Annotated[redis.Redis, Depends(get_redis)]
```

在 `main.py`：

```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from redis_client import create_redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = create_redis_client()
    await app.state.redis.ping()
    yield
    await app.state.redis.aclose()


app = FastAPI(lifespan=lifespan)
```

在路由里：

```python
from fastapi import APIRouter

from redis_client import RedisDep

router = APIRouter()


@router.get("/demo")
async def demo(r: RedisDep):
    await r.set("demo:hello", "world", ex=60)
    return {"value": await r.get("demo:hello")}
```

---

## 附录 C：Redis 学习心法

学 Redis 最重要的不是命令数量，而是知道每种数据结构对应什么业务直觉：

| 数据结构 | 业务直觉 |
|---|---|
| String | 一个值、JSON、验证码、计数器 |
| Hash | 一个对象的多个字段 |
| List | 简单队列、最新列表 |
| Set | 去重、是否存在、集合关系 |
| Sorted Set | 排行榜、按分数排序 |
| Bitmap | 大量 true/false |
| HyperLogLog | 大规模去重计数估算 |
| Stream | 更可靠的消息流 |

最后记住这条主线：

```text
PostgreSQL 是事实来源。
ORM 是你和 PostgreSQL 打交道的 Python 层。
Redis 是加速器、临时状态管理器和高并发小工具箱。
```

当你能自然判断“这个功能该查 PostgreSQL，还是该先查 Redis，还是两个都要”，你就不再只是会写 Redis 命令，而是开始具备后端系统设计的感觉了。
