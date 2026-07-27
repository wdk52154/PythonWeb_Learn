from fastapi import FastAPI, Query  # 从fastapi库引入 FastAPI和Query 使用

# 创建FastAPI 实例
app = FastAPI()


# 需求：查询新闻 -> 分页 ，skip：跳过的记录数，limit：返回的记录数 10


@app.get("/news/news_list")
async def get_news_list(
    skip: int = Query(default=0, description="跳过的记录数", lt=100),
    limit: int = Query(default=10, description="返回的记录数"),
):
    return {"skip": skip, "limit": limit}
