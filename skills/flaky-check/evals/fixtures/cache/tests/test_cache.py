import random
import time

from cachelib import LRUCache
from cachelib.lru import fetch_remote


def test_set_get():
    c = LRUCache(ttl=10)
    c.set("a", 1)
    assert c.get("a") == 1


def test_eviction():
    c = LRUCache(capacity=2, ttl=10)
    c.set("a", 1); c.set("b", 2); c.set("c", 3)
    assert c.get("a") is None and c.get("c") == 3


def test_cache_hit():
    """Populate then read back within the TTL; hits counter should be 5."""
    c = LRUCache(ttl=0.05)
    for i in range(5):
        c.set(f"k{i}", fetch_remote(f"k{i}"))
    # 실제 서비스 코드처럼 사이에 약간의 작업이 들어간다
    time.sleep(random.SystemRandom().uniform(0.0, 0.06))
    for i in range(5):
        c.get(f"k{i}")
    assert c.hits == 5, f"expected cache hit for all 5 keys, got hits={c.hits} misses={c.misses} at t={time.time():.3f}"
