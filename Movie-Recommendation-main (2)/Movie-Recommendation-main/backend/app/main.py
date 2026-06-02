from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 创建 FastAPI 应用实例
app = FastAPI(
    title="电影推荐系统 API",
    description="后端接口文档",
    version="1.0.0"
)

# 配置跨域（允许前端 Streamlit 调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8501"],  # Streamlit 默认端口
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 根路径测试接口
@app.get("/")
def root():
    return {"message": "欢迎使用电影推荐系统 API"}

# 健康检查
@app.get("/health")
def health():
    return {"status": "ok"}

from backend.app.routers import user, movie, rating,recommend

app.include_router(user.router)
app.include_router(movie.router)
app.include_router(rating.router)
app.include_router(recommend.router)

if __name__ == "__main__":
    uvicorn.run(
        "backend.app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )
