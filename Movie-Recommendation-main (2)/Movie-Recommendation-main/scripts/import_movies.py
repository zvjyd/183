"""
MovieLens 100K 数据导入脚本。

导入 u.item 到 movie 表，导入 u.data 到 rating 表，保证推荐算法能从数据库读取评分数据。
"""

import argparse
import csv
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.database import db
from backend.app.models import Movie, Rating

# 类型编号到名称的映射（MovieLens 100k 的 19 个类型）
GENRE_MAP = {
    1: "unknown",
    2: "Action",
    3: "Adventure",
    4: "Animation",
    5: "Children's",
    6: "Comedy",
    7: "Crime",
    8: "Documentary",
    9: "Drama",
    10: "Fantasy",
    11: "Film-Noir",
    12: "Horror",
    13: "Musical",
    14: "Mystery",
    15: "Romance",
    16: "Sci-Fi",
    17: "Thriller",
    18: "War",
    19: "Western"
}


def parse_genres(genre_flags):
    """
    将类型标识（0/1列表）转换为类型名称字符串

    参数:
        genre_flags: 长度为19的列表，包含0或1

    返回:
        类型名称字符串，用 | 分隔，例如 "Animation|Comedy|Children's"
    """
    genres = []
    for i, flag in enumerate(genre_flags, start=1):
        if flag == '1' or flag == 1:
            genre_name = GENRE_MAP.get(i)
            if genre_name:
                genres.append(genre_name)
    return '|'.join(genres) if genres else 'unknown'


def import_movies(file_path):
    """
    导入电影数据到数据库

    参数:
        file_path: u.item 文件的路径
    """
    print(f"正在读取电影数据: {file_path}")

    db.connect(reuse_if_open=True)
    db.create_tables([Movie, Rating], safe=True)

    # 统计
    total = 0
    inserted = 0
    updated = 0

    with open(file_path, 'r', encoding='latin-1') as f:
        reader = csv.reader(f, delimiter='|')

        for row in reader:
            total += 1
            movie_id = int(row[0])
            title = row[1]
            # row[5] 到 row[23] 是19个类型标识（0或1）
            genre_flags = row[5:24]
            genres_str = parse_genres(genre_flags)

            # 插入或更新
            movie, created = Movie.get_or_create(
                id=movie_id,
                defaults={
                    'title': title,
                    'genres': genres_str
                }
            )

            if not created:
                # 如果已存在，更新 genres
                movie.title = title
                movie.genres = genres_str
                movie.save()
                updated += 1
            else:
                inserted += 1

            # 每100条打印一次进度
            if total % 100 == 0:
                print(f"已处理 {total} 条...")

    print(f"\n导入完成！")
    print(f"总处理: {total} 条")
    print(f"新增: {inserted} 条")
    print(f"更新: {updated} 条")

    return {"total": total, "inserted": inserted, "updated": updated}


def import_ratings(file_path):
    """
    导入 MovieLens 100K 评分数据到数据库。

    参数:
        file_path: u.data 文件路径
    """
    print(f"正在读取评分数据: {file_path}")

    db.connect(reuse_if_open=True)
    db.create_tables([Movie, Rating], safe=True)

    total = 0
    inserted = 0
    updated = 0

    with open(file_path, "r", encoding="latin-1") as f:
        reader = csv.reader(f, delimiter="\t")
        for row in reader:
            if len(row) < 3:
                continue

            total += 1
            user_id = int(row[0])
            movie_id = int(row[1])
            rating_value = float(row[2]) * 2.0  # MovieLens 1-5 转为系统 1-10 评分

            rating, created = Rating.get_or_create(
                user_id=user_id,
                movie_id=movie_id,
                defaults={"rating": rating_value}
            )

            if not created:
                rating.rating = rating_value
                rating.save()
                updated += 1
            else:
                inserted += 1

            if total % 10000 == 0:
                print(f"已处理 {total} 条评分...")

    print("\n评分导入完成！")
    print(f"总处理: {total} 条")
    print(f"新增: {inserted} 条")
    print(f"更新: {updated} 条")

    return {"total": total, "inserted": inserted, "updated": updated}


# 测试函数（可选）
def test_import():
    """测试导入结果"""
    db.connect(reuse_if_open=True)

    # 查看前5条数据
    print("\n=== 导入结果预览 ===")
    movies = Movie.select().limit(10)
    for movie in movies:
        print(f"ID: {movie.id}, 标题: {movie.title[:40]}, 类型: {movie.genres}")

    # 统计有类型的数据量和评分数据量
    with_genres = Movie.select().where(Movie.genres != 'unknown').count()
    total = Movie.select().count()
    rating_total = Rating.select().count()
    print(f"\n有类型标签的电影: {with_genres}/{total}")
    print(f"评分记录: {rating_total}")


def parse_args():
    default_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data",
        "ml-100k"
    )
    parser = argparse.ArgumentParser(description="Import MovieLens 100K movies and ratings.")
    parser.add_argument("--data-dir", default=default_dir, help="MovieLens 100K 解压目录")
    parser.add_argument("--movies", default=None, help="u.item 文件路径")
    parser.add_argument("--ratings", default=None, help="u.data 文件路径")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    movie_path = args.movies or os.path.join(args.data_dir, "u.item")
    rating_path = args.ratings or os.path.join(args.data_dir, "u.data")

    if not os.path.exists(movie_path):
        print(f"错误: 找不到电影文件 {movie_path}")
        sys.exit(1)
    if not os.path.exists(rating_path):
        print(f"错误: 找不到评分文件 {rating_path}")
        sys.exit(1)

    try:
        import_movies(movie_path)
        import_ratings(rating_path)
        test_import()
    finally:
        if not db.is_closed():
            db.close()
