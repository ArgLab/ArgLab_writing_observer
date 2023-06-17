import asyncio 
from writing_observer.caching_performance import increment_hit_count, increment_miss_count, HIT_COUNT, MISS_COUNT

# entry point
async def main():
    print(f"Initial Hit Count: {HIT_COUNT}")
    number_of_coroutines = 10
    # create many concurrent coroutines
    coros = [increment_hit_count() for i in range(number_of_coroutines)]
    # execute and wait for tasks to complete
    await asyncio.gather(*coros)
    print(HIT_COUNT)

asyncio.run(main())