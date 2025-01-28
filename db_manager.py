import redis
import uuid
from datetime import datetime

# Initialize Redis connection
r = redis.Redis(
    host='redis-18982.c289.us-west-1-2.ec2.redns.redis-cloud.com',
    port=18982,
    decode_responses=True,
    username="default",
    password="n7zAhUSuxuHM6iZP65UOcdjndmjIHC4m",
)

def init_db():
    # No need to create tables in Redis
    pass

def get_user_results():
    results = []
    for key in r.scan_iter("user_result:*"):
        results.append(r.hgetall(key))
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
    r.flushdb()
    for i in range(1, n + 1):
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

def add_result(user_id, test, score):
    result_id = str(uuid.uuid4())
    r.hmset(f"user_result:{result_id}", {"user_id": user_id, "test": test, "score": score, "datetime": str(datetime.now())})
