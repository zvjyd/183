from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..models import User

router = APIRouter(prefix="/api/user", tags=["用户"])


# 带校验的请求体
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=50, description="用户名，不能为空")
    password: str = Field(..., min_length=1, max_length=100, description="密码，不能为空")


class UserLogin(BaseModel):
    username: str = Field(..., min_length=1, description="用户名，不能为空")
    password: str = Field(..., min_length=1, description="密码，不能为空")


# 注册
@router.post("/register")
def register(user: UserCreate):
    # Pydantic 已经校验了用户名和密码不为空，这里不需要再写 if

    # 检查用户名是否已存在
    if User.select().where(User.username == user.username).exists():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 创建新用户
    new_user = User.create(username=user.username, password=user.password)
    return {"code": 200, "user_id": new_user.id, "message": "注册成功"}


# 登录
@router.post("/login")
def login(user: UserLogin):
    # Pydantic 已经校验了不为空
    try:
        db_user = User.get(User.username == user.username, User.password == user.password)
        return {"code": 200, "user_id": db_user.id, "username": db_user.username}
    except User.DoesNotExist:
        raise HTTPException(status_code=401, detail="用户名或密码错误")