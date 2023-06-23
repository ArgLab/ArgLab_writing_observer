import asyncio 
from writing_observer.caching_performance import CachePerformance

# entry point
async def main():
    cache_performance = CachePerformance()
    number_of_coroutines = 10
    # create many concurrent coroutines
    coros = [cache_performance.increment_hit_count(2) for i in range(number_of_coroutines)]
    # execute and wait for tasks to complete
    await asyncio.gather(*coros)

asyncio.run(main())