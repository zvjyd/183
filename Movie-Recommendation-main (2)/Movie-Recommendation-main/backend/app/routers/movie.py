from fastapi import APIRouter, HTTPException, Query
from ..models import Movie, Rating

router = APIRouter(prefix="/api/movies", tags=["电影"])


@router.get("")
def get_movies(
        page: int = Query(1, ge=1),
        size: int = Query(50, ge=1, le=100),
        keyword: str = None,
        user_id: int = Query(None, ge=1)
):
    # 构建基础查询
    query = Movie.select()
    if keyword:
        query = query.where(Movie.title.contains(keyword))

    # 获取总数（在排序前）
    total = query.count()

    # 如果提供了user_id，则进行已评分优先排序
    if user_id:
        # 使用LEFT JOIN获取用户的评分信息
        # 子查询：获取用户已评分的电影ID
        user_ratings = Rating.select(Rating.movie_id).where(Rating.user_id == user_id)
        
        # 主查询：使用CASE WHEN进行排序，已评分的排在前面
        query = (query
                 .order_by(
                     Movie.id.not_in(user_ratings).asc(),  # 已评分的优先（False=0排在前面）
                     Movie.id.asc()  # 同状态按ID排序
                 ))
    
    # 分页
    movies = query.paginate(page, size)

    # 构建返回数据，标记已评分状态
    movies_data = []
    for m in movies:
        movie_dict = {
            "id": m.id, 
            "title": m.title, 
            "genres": m.genres
        }
        movies_data.append(movie_dict)

    return {
        "movies": movies_data,
        "total": total,
        "page": page,
        "size": size
    }


@router.get("/{movie_id}")
def get_movie(movie_id: int):
    try:
        movie = Movie.get_by_id(movie_id)
        return {"id": movie.id, "title": movie.title, "genres": movie.genres}
    except Movie.DoesNotExist:
        raise HTTPException(status_code=404, detail="电影不存在")