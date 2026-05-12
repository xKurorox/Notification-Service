import redis
import os
from dotenv import load_dotenv

load_dotenv()

redis_client = redis.Redis(host= os.getenv("REDIS_HOST"), port=6380, db=0, decode_responses=True)