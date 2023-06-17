import asyncio

# In-Memory Counters
HIT_COUNT = 0
MISS_COUNT = 0

# Asyncio Locks for the in-memory counters. https://docs.python.org/3/library/asyncio-sync.html
hit_lock = asyncio.Lock()
miss_lock = asyncio.Lock()

async def increment_hit_count():
    """
    Increments the hit count by 1
    """
    global HIT_COUNT
    async with hit_lock: #Acquires and releases the locks after finished.
        HIT_COUNT += 1
    print(HIT_COUNT)

async def increment_miss_count():
    """
    Increments the miss count by 1
    """
    global MISS_COUNT
    async with miss_lock: #Acquires and releases the locks after finished.
        MISS_COUNT += 1
