"""
User-based 协同过滤算法
"""
import numpy as np
from .utils import get_rating_matrix, get_user_similarity, cold_start_recommend
from backend.app.models import Movie, Rating


def recommend(user_id: int, top_n: int = 10) -> list:
    """
    基于用户的协同过滤推荐

    参数:
        user_id: 用户ID
        top_n: 推荐数量

    返回:
        list: [{"movie_id": 1, "title": "电影名", "predicted_rating": 4.8, "reason": "..."}, ...]
    """
    user_ratings_db = Rating.select().where(Rating.user_id == user_id)
    rated_movies_db = set([r.movie_id for r in user_ratings_db])

    # 1. 获取数据
    rating_matrix, user_ids, movie_ids = get_rating_matrix()
    user_similarity, _ = get_user_similarity()

    if rating_matrix.empty or not user_ids or not movie_ids:
        return cold_start_recommend(top_n, exclude_movies=rated_movies_db)

    # 2. 检查用户是否存在
    if user_id not in user_ids:
        return cold_start_recommend(top_n, exclude_movies=rated_movies_db)

    # 3. 获取用户索引
    user_idx = user_ids.index(user_id)

    # 4. 获取该用户与其他所有用户的相似度
    similarities = user_similarity[user_idx]

    # 5. 找到最相似的 K 个用户（K=20）
    K = min(20, len(user_ids) - 1)
    if K <= 0:
        return cold_start_recommend(top_n)

    similar_users_idx = [
        idx for idx in np.argsort(similarities)[::-1]
        if idx != user_idx and similarities[idx] > 0
    ][:K]
    if not similar_users_idx:
        return cold_start_recommend(top_n, exclude_movies=rated_movies_db)

    # 6. 获取当前用户已评分的电影（双重保障：从数据库和矩阵都获取）
    # 从评分矩阵获取
    user_rated_mask = rating_matrix.iloc[user_idx] > 0
    rated_movies_matrix = set(rating_matrix.columns[user_rated_mask].tolist())
    
    # 合并两个集合（取并集）
    rated_movies = rated_movies_db.union(rated_movies_matrix)

    # 7. 计算每个未评分电影的预测评分
    predictions = {}

    for movie_idx, movie_id in enumerate(movie_ids):
        # 过滤已评分的电影
        if movie_id in rated_movies:
            continue

        total_sim = 0
        weighted_rating = 0

        for sim_user_idx in similar_users_idx:
            sim = float(similarities[sim_user_idx])
            rating = rating_matrix.iloc[sim_user_idx, movie_idx]

            if sim > 0 and rating > 0:
                total_sim += sim
                weighted_rating += sim * rating

        if total_sim > 0:
            predictions[movie_id] = weighted_rating / total_sim

    # 8. 如果没有预测结果，返回热门推荐
    if not predictions:
        return cold_start_recommend(top_n, exclude_movies=rated_movies)

        # 9. 按预测评分排序，取 Top N
    sorted_predictions = sorted(predictions.items(), key=lambda x: x[1], reverse=True)

    # 如果预测数量不足，补充热门电影（排除已评分的）
    fallback_movie_ids = set()
    if len(sorted_predictions) < top_n:
        # 从热门推荐中获取更多候选（请求 top_n*2 个，再过滤）
        hot_candidates = cold_start_recommend(top_n * 2, exclude_movies=rated_movies)
        for hot_movie in hot_candidates:
            movie_id = hot_movie["movie_id"]
            if movie_id not in predictions and movie_id not in rated_movies:
                # 给一个临时评分（比预测的最低分略低，保证排在最后）
                temp_score = min(predictions.values()) - 1.0 if predictions else 0.0
                sorted_predictions.append((movie_id, temp_score))
                fallback_movie_ids.add(movie_id)
            if len(sorted_predictions) >= top_n:
                break
        # 重新排序（补充的热门电影排在后面）
        sorted_predictions.sort(key=lambda x: x[1], reverse=True)

    sorted_predictions = sorted_predictions[:top_n]

    # 10. 构建返回结果（确保没有重复）
    result = []
    seen_movie_ids = set()
    
    for movie_id, pred_rating in sorted_predictions:
        # 去重检查
        if movie_id in seen_movie_ids:
            continue
        seen_movie_ids.add(movie_id)
        
        # 再次确认不是已评分的电影
        if movie_id in rated_movies:
            continue
            
        movie = Movie.get_or_none(Movie.id == movie_id)
        if movie_id in fallback_movie_ids:
            predicted_rating = None
            reason = "Popular movie recommendation used to fill the result list"
        else:
            predicted_rating = float(min(max(round(float(pred_rating), 1), 1.0), 10.0))
            reason = "Other users with similar tastes also liked this movie"

        result.append({
            "movie_id": int(movie_id),
            "title": movie.title if movie else "Unknown",
            "predicted_rating": predicted_rating,
            "reason": reason
        })

    return result
