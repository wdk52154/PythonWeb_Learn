from fastapi import FastAPI, Query, Depends  # 2 导入Depends

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "hello world"}


# 分页参数逻辑公用：新闻列表和用户列表
# 1 依赖项
async def common_parameters(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, le=60),
):
    return {"skip": skip, "limit": limit}


# 3 .声明依赖项 -> 依赖注入
@app.get("/news/news_list")
async def get_news_list(commons=Depends(common_parameters)):
    return commons


@app.get("/user/user_list")
async def get_user_list(comoons =Depends(common_parameters)):
    return comoons
