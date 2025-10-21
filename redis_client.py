import redis

def get_redis_client():
    pool = redis.ConnectionPool.from_url("redis://localhost:6379/0", decode_responses=True)
    client = redis.Redis(connection_pool=pool)
    return client