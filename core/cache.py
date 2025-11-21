import json
from typing import Any, Optional, Union

from pymemcache.client.base import Client

from core.config import settings


def json_serializer(key, value):
    if isinstance(value, str):
        return value, 1
    return json.dumps(value), 2


def json_deserializer(key, value, flags):
    if flags == 1:
        return value.decode("utf-8")
    if flags == 2:
        return json.loads(value.decode("utf-8"))
    raise Exception(f"Unknown serialization format: {flags}")


class MemcachedClient:
    def __init__(self):
        self.client = Client(
            (settings.MEMCACHED_HOST, settings.MEMCACHED_PORT),
            serializer=json_serializer,
            deserializer=json_deserializer,
            connect_timeout=1,
            timeout=1,
        )

    def get(self, key: str) -> Optional[Any]:
        try:
            return self.client.get(key)
        except Exception as e:
            # Log error in production
            print(f"Cache get failed: {e}")
            return None

    def set(self, key: str, value: Any, expire: int = settings.MEMCACHED_EXPIRATION):
        try:
            self.client.set(key, value, expire=expire)
        except Exception as e:
            print(f"Cache set failed: {e}")

    def delete(self, key: str):
        try:
            self.client.delete(key)
        except Exception as e:
            print(f"Cache delete failed: {e}")

    def flush_all(self):
        try:
            self.client.flush_all()
        except Exception as e:
            print(f"Cache flush failed: {e}")


cache = MemcachedClient()
