import redis
import uuid
import os
from datetime import datetime

ht = os.getenv("REDIS_HOST")
pt = int(os.getenv("REDIS_PORT"))
passw = os.getenv("REDIS_PASS")
# Initialize Redis connection
r = redis.Redis(
    host=ht,
    port=pt,
    decode_responses=True,
    username="default",
    password=passw,
)

def init_db():
    # No need to create tables in Redis
    pass

def get_user_results():
    results = []
    for key in r.scan_iter("user_result:*"):
        result = r.hgetall(key)
        results.append((
            result["user_id"],
            result["tg_id"],
            result["test"],
            result["score"],
            result["datetime"]
        ))
    return results

def get_user_tokens():
    tokens = []
    for key in r.scan_iter("user_token:*"):
        tokens.append((key.split(":")[1], r.get(key)))
    return tokens

def get_user_state(telegram_id):
    return r.get(f"user_state:{telegram_id}")

def set_user_state(user_id, state):
    r.set(f"user_state:{user_id}", state)

def generate_tokens(n):
    num = len(list(r.scan_iter("user_token:*")))
    for i in range(num, n + num):
        token = str(uuid.uuid4())
        r.set(f"user_token:{i}", token)

def add_tokens(last, n):
    for i in range(last + 1, last + n + 1):
        token = str(uuid.uuid4())
        r.set(f"user_token:{i}", token)

def get_user_id(user_token):
    for key in r.scan_iter("user_token:*"):
        if r.get(key) == user_token:
            return key.split(":")[1]
    return None

def setup_user_session(telegram_id, user_id):
    r.set(f"user_session:{telegram_id}", user_id)

def get_user_session_info(telegram_id):
    return r.get(f"user_session:{telegram_id}")

def add_result(user_id, telegram_id, test, score):
    result_id = str(uuid.uuid4())
    r.hmset(f"user_result:{result_id}", {
        "user_id": user_id,
        "tg_id": telegram_id,
        "test": test,
        "score": score,
        "datetime": str(datetime.now())
    })
