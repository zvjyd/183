from peewee import MySQLDatabase

db = MySQLDatabase(
    'movie_recommendation', # 数据库名
    user='root',
    password='zyh790201',
    host='localhost',
    port=3306
)

def get_db_connection():
    """返回数据库连接对象（用于需要原生连接的地方）"""
    return db.connection()