import redis
import time

client = redis.Redis()


def make_dash_req():
    for key in client.scan_iter():
        item = client.get(key)
        print(key)


while True:
    try:
        make_dash_req()
        time.sleep(5)
    except KeyboardInterrupt:
        print("quitting...")
        client.close()
        break

