import asyncio

# Asyncio Locks for the in-memory counters. https://docs.python.org/3/library/asyncio-sync.html
hit_lock = asyncio.Lock()
miss_lock = asyncio.Lock()


class CachePerformance():
    """
    A class to track caching performance through cache hits and misses.
    """
    def __init__(self):
        # In-Memory Counters
        self.HIT_COUNT = 0
        self.MISS_COUNT = 0
        
    async def increment_hit_count(self, hits=1):
        """
        Increments the hit count by number of hits
        """
        async with hit_lock: #Acquires and releases the locks after finished.
            self.HIT_COUNT += hits
            print(f"Hit Count: {self.HIT_COUNT}")

    async def increment_miss_count(self, misses=1):
        """
        Increments the miss count by number of misses.
        """
        async with miss_lock: #Acquires and releases the locks after finished.
            self.MISS_COUNT += misses
            print(f"Miss Count: {self.MISS_COUNT}")