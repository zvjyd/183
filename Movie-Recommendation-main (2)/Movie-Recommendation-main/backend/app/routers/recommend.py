from fastapi import APIRouter, Query, HTTPException
from algorithm.utils import refresh_data
from backend.app.models import Rating
from algorithm.user_based import recommend as user_recommend
from algorithm.item_based import recommend as item_recommend

router = APIRouter(prefix="/api/recommend", tags=["推荐"])


@router.get("")
def get_recommendations(
        user_id: int,
        algorithm: str = Query("user", pattern="^(user|item)$"),
        top_n: int = Query(10, ge=1, le=50)
):
    """
    获取推荐列表

    参数:
        user_id: 用户ID
        algorithm: 算法类型，user 或 item
        top_n: 返回推荐数量，默认10，最大50
    """
    # 1. 获取用户已有的评分
    ratings = Rating.select().where(Rating.user_id == user_id)
    user_ratings = {r.movie_id: float(r.rating) for r in ratings}

    # 2. 根据算法类型调用不同的推荐函数
    if algorithm == "user":
        recommendations = user_recommend(user_id, top_n)
    else:
        recommendations = item_recommend(user_ratings, top_n)

    return {"code": 200, "recommendations": recommendations}

@router.post("/refresh")
def refresh_cache():
    """手动刷新算法缓存（当有新评分时调用）"""
    refresh_data()
    return {"code": 200, "message": "缓存已刷新"}