"""算法工具函数：加载数据、计算余弦相似度、冷启动推荐。"""
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.app.models import Rating, Movie
from peewee import fn

# 全局缓存（启动后只加载一次）
_rating_matrix = None
_user_similarity = None
_item_similarity = None
_user_ids = None
_movie_ids = None


def load_data():
    """从数据库加载评分数据，构建评分矩阵，并计算用户/物品余弦相似度。"""
    global _rating_matrix, _user_similarity, _item_similarity, _user_ids, _movie_ids

    print("正在加载评分数据...")
    users = Rating.select(Rating.user_id).distinct()
    movies = Rating.select(Rating.movie_id).distinct()
    _user_ids = sorted(list(set([u.user_id for u in users])))
    _movie_ids = sorted(list(set([m.movie_id for m in movies])))

    data = []
    for user_id in _user_ids:
        row = {}
        ratings = Rating.select().where(Rating.user_id == user_id)
        for r in ratings:
            row[r.movie_id] = float(r.rating)
        data.append(row)

    _rating_matrix = pd.DataFrame(data, index=_user_ids, columns=_movie_ids).fillna(0).astype(float)

    if _rating_matrix.empty:
        _user_similarity = np.zeros((0, 0))
        _item_similarity = np.zeros((0, 0))
        print("暂无评分数据，已跳过相似度计算")
        return

    print("正在计算用户相似度矩阵（Cosine）...")
    _user_similarity = cosine_similarity(_rating_matrix.values)

    print("正在计算物品相似度矩阵（Cosine）...")
    _item_similarity = cosine_similarity(_rating_matrix.T.values)

    print(f"数据加载完成: {len(_user_ids)} 个用户, {len(_movie_ids)} 部电影")

def get_rating_matrix():
    """获取评分矩阵"""
    if _rating_matrix is None:
        load_data()
    return _rating_matrix, _user_ids, _movie_ids


def get_user_similarity():
    """获取用户相似度矩阵"""
    if _user_similarity is None:
        load_data()
    return _user_similarity, _user_ids


def get_item_similarity():
    """获取物品相似度矩阵"""
    if _item_similarity is None:
        load_data()
    return _item_similarity, _movie_ids


def cold_start_recommend(top_n: int = 10, exclude_movies: set = None) -> list:
    """冷启动推荐：返回评分次数最多的热门电影
    参数:
        top_n: 推荐数量
        exclude_movies: 需要排除的电影ID集合
    """
    if exclude_movies is None:
        exclude_movies = set()

    # 获取更多候选（top_n * 3），以提高排除后的命中率
    query = (Rating
             .select(Rating.movie_id, fn.COUNT(Rating.movie_id).alias('count'))
             .group_by(Rating.movie_id)
             .order_by(fn.COUNT(Rating.movie_id).desc())
             .limit(top_n * 5))  # 增加候选池

    result = []
    for row in query:
        if row.movie_id in exclude_movies:
            continue
        movie = Movie.get_or_none(Movie.id == row.movie_id)
        if movie:
            result.append({
                "movie_id": row.movie_id,
                "title": movie.title,
                "predicted_rating": None,
                "reason": "Popular movie recommendation (no rating data yet)"
            })
        if len(result) >= top_n:
            break

    # 如果仍不足，从电影表中随机或按ID补充（确保不重复）
    if len(result) < top_n:
        needed = top_n - len(result)
        default_movies = Movie.select().where(Movie.id.not_in(list(exclude_movies))).limit(needed * 3)
        for movie in default_movies:
            if movie.id in exclude_movies or any(r["movie_id"] == movie.id for r in result):
                continue
            result.append({
                "movie_id": movie.id,
                "title": movie.title,
                "predicted_rating": None,
                "reason": "Default recommendation"
            })
            if len(result) >= top_n:
                break

    return result[:top_n]


def refresh_data():
    """强制刷新数据缓存"""
    global _rating_matrix, _user_similarity, _item_similarity, _user_ids, _movie_ids
    _rating_matrix = None
    _user_similarity = None
    _item_similarity = None
    _user_ids = None
    _movie_ids = None
    load_data()
    print("数据缓存已刷新")
