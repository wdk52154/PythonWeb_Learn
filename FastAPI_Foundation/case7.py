from fastapi import FastAPI 
from fastapi.responses import HTMLResponse

# 创建FastAPI 实例
app = FastAPI()

@app.get('/')
async def root():
    return {"message":'Hello World'}

# 接口 -> 响应 HTML 代码
@app.get(path='/html',response_class=HTMLResponse)
async def get_html():
    return "<h1>这是一级标题</h1>"