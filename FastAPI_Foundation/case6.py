from fastapi import FastAPI  # 导包

# 创建FastAPI 实例
app = FastAPI()

@app.get('/')
async def root():
    return {"message":'Hello World'}