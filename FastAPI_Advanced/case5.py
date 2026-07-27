from fastapi import FastAPI, Depends  # 导入FastAPI类，用于创建Web应用实例
from decimal import Decimal  # 价格用Decimal精确表示
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
)  # 导入异步引擎工厂函数，用于创建数据库连接引擎
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
)  # DeclarativeBase:模型基类; Mapped:字段类型注解; mapped_column:定义表字段(列)
from datetime import datetime  # 时间字段用
from sqlalchemy import (
    DateTime,
    Numeric,
    String,
    select,
)  # 导入列类型：日期时间、定点数(金额用)、字符串

app = FastAPI()
ASYNC_DATABASS_URL = "postgresql+asyncpg://wangdekang@localhost:5432/fastapi_learn"

# 1 创建异步引擎
async_engine = create_async_engine(
    ASYNC_DATABASS_URL,
    echo=True,  # 可选,输出SQL日志
    pool_size=10,  # 设置连接池中保持的持久连接数
    max_overflow=20,  # 设置连接池允许创建的额外连接数
)


# 2 定义模型类：基类 + 表对应的模型类
# 基类：创建时间、更新时间；书籍表：id、书名、作者、价格、出版社
class Base(DeclarativeBase):
    # 公共字段：所有继承Base的模型类都会有这两列
    create_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, comment="创建时间"
    )
    update_time: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间"
    )


class Book(Base):
    __tablename__ = "book"  # 数据库里的表名

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="书籍ID"
    )
    bookname: Mapped[str] = mapped_column(String(255), comment="书名")
    author: Mapped[str] = mapped_column(String(255), comment="作者")
    price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), comment="价格"
    )  # 金额用Numeric/Decimal，float有精度误差
    publisher: Mapped[str] = mapped_column(String(255), comment="出版社")


# 3 建表：定义函数建表 -> FastAPI 启动的时候调用建表的函数
async def create_tables():
    # 获取异步引擎,创建事务  -  建表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)  # Base 模型类的元数据创建


@app.on_event("startup")
async def startup_event():
    await create_tables()


@app.get("/")
async def root():
    return {"message": "hello world"}


# 需求：查询功能的接口，查询图书 -> 依赖注入：创建依赖项获取数据库会话 + Depends 注入路由处理函数

# 创建会话工厂
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,  # 绑定数据库引擎
    class_=AsyncSession,  # 指定会话类
    expire_on_commit=False,  # 提交后会话不过期,不会重新查询数据库
)


# 依赖项
async def get_database():
    async with AsyncSessionLocal() as session:
        try:
            yield session  # 返回数据库会话给路由处理函数
            await session.commit()  # 提交事务
        except Exception:
            await session.rollback()  # 有异常,回滚
            raise
        finally:
            await session.close()  # 关闭会话


@app.get("/book/books")
async def get_book_list(db: AsyncSession = Depends(get_database)):
    # 查询
    # result = await db.execute(select(Book)) # 返回一个ORM对象
    # books = result.scalars().all()  # 获取所有数据
    # book = result.scalars().first() # 获取单条数据
    book = await db.get(Book, 1)      # 获取单条数据 -> 根据主键
    return book