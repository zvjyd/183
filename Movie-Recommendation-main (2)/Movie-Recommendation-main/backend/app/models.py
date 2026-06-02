from peewee import *
from datetime import datetime
from .database import db

# 定义基础模型
class BaseModel(Model):
    class Meta:
        database = db

# 用户模型
class User(BaseModel):
    id = AutoField()                  # 自增主键
    username = CharField(max_length=50, unique=True)
    password = CharField(max_length=100)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'user'

# 电影模型
class Movie(BaseModel):
    id = IntegerField(primary_key=True)
    title = CharField(max_length=200)
    genres = CharField(max_length=200, null=True)

    class Meta:
        table_name = 'movie'

# 评分模型
class Rating(BaseModel):
    id = AutoField()
    user_id = IntegerField()
    movie_id = IntegerField()
    rating = DecimalField(max_digits=3, decimal_places=1)
    created_at = DateTimeField(default=datetime.now)

    class Meta:
        table_name = 'rating'
        indexes = (
            (('user_id', 'movie_id'), True),   # 联合唯一索引，保证一个用户对一部电影只能有一个评分，防止重复数据
        )