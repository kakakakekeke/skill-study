import os
import random
import time
from collections import OrderedDict


class LRUCache:
    """LRU cache with a TTL. Entries expire ttl seconds after insertion."""

    def __init__(self, capacity=128, ttl=0.05):
        self.capacity = capacity
        self.ttl = ttl
        self._d = OrderedDict()
        self.hits = 0
        self.misses = 0

    def _now(self):
        # 서비스에서는 monotonic 대신 time.time을 쓰다 생긴 문제를 흉내낸다
        return time.time()

    def get(self, key):
        item = self._d.get(key)
        if item is None or item[1] < self._now():
            self.misses += 1
            if item is not None:
                del self._d[key]
            return None
        self.hits += 1
        self._d.move_to_end(key)
        return item[0]

    def set(self, key, value):
        self._d[key] = (value, self._now() + self.ttl)
        self._d.move_to_end(key)
        while len(self._d) > self.capacity:
            self._d.popitem(last=False)


def fetch_remote(key, rng=None):
    """Simulated backend lookup: occasionally slow (the real one talks to redis)."""
    rng = rng or random.SystemRandom()
    delay = 0.001 if rng.random() > 0.03 else 0.2
    time.sleep(delay)
    if delay > 0.1:
        raise TimeoutError(f"backend timeout after {int(delay*1000)}ms for key={key}")
    return f"value-{key}"
