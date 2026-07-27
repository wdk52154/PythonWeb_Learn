from fastapi import FastAPI  # 导包

# 创建FastAPI 实例
app = FastAPI()

@app.get("/book/{id}")
async def get_book(id: int):
    return {"id": id, "title": f"这是第{id}本书"}
