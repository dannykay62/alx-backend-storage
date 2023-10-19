#!/usr/bin/env python3
"""
    Create a Cache class. In the __init__ method, store an instance of the
    Redis client as a private variable named _redis (using redis.Redis()) and
    flush the instance using flushdb.
    Create a store method that takes a data argument and returns a string. The
    method should generate a random key (e.g. using uuid), store the input
    data in Redis using the random key and return the key.
    Type-annotate store correctly. Remember that data can be a str, bytes,
    int or float.
"""
from typing import Union, Callable, Optional, Any
import redis
import uuid
from functools import wraps


def call_history(method: callable) -> callable:
    """store the history of inputs and outputs for a function"""
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"

    @wraps(method)
    def wrapper(self, *args, **kwds):
        """wrapped function"""
        self._redis.rpush(inputs, str(args))
        data = method(self, *args, **kwds)
        self._redis.rpush(outputs, str(data))
        return data
    return wrapper

def count_calls(method: callable) -> callable:
    """counting the number of times methods of Cache class were called"""
    key = method.__qualname__

    @wraps(method)
    def wrapper(self, *args, **kwds):
        """functions that are wrapped"""
        self._redis.incr(key)
        return method(self, *args, **kwds)
    return wrapper

class Cache:
    """Cache class"""   
    def __init__(self) -> None:
        """
            store an instance of the Redis client as a private variable
            named _redis (using redis.Redis()) and flush the instance using flushdb.
        """
        self.redis = redis.Redis()
        self._redis.flushdb()

        @call_history
        @count_calls
        def store(self, data: Union[str, bytes, int, float]) -> str:
            """ generate a random key (e.g. using uuid), store the input data in
        Redis using the random key and return the key """
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self, key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float]:
        """ take a key string argument and an optional Callable argument named
            fn. This callable will be used to convert the data back to the
            desired format """
        data = self._redis.get(key)
        if fn:
            return fn(data)
        return data

    def get_str(self, key: str) -> str:
        """ automatically parametrize Cache.get to str """
        data = self._redis.get(key)
        return data.decode("utf-8")

    def get_int(self, key: str) -> int:
        """ automatically parametrize Cache.get to int """
        data = self._redis.get(key)
        try:
            data = int(value.decode("utf-8"))
        except Exception:
            data = 0
        return data


def replay(method: Callable):
    """ display the history of calls of a particular function """
    key = method.__qualname__
    inputs = key + ":inputs"
    outputs = key + ":outputs"
    redis = method.__self__._redis
    count = redis.get(key).decode("utf-8")
    print("{} was called {} times:".format(key, count))
    inputList = redis.lrange(inputs, 0, -1)
    outputList = redis.lrange(outputs, 0, -1)
    redis_zipped = list(zip(inputList, outputList))
    for a, b in redis_zipped:
        attr, data = a.decode("utf-8"), b.decode("utf-8")
        print("{}(*{}) -> {}".for
