from fastapi import FastAPI, HTTPException

# 创建FastAPI 实例
app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Hello World"}


# 需求：按id查询新闻  -> 1-6
@app.get("/news/{id}")
async def get_name(id: int):
    id_list = [1, 2, 3, 4, 5, 6]
    if id not in id_list:
        raise HTTPException(status_code=404, detail="您查找的新闻不存在")
    return {"id": id}
