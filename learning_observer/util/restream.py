'''ReStream

Usage:
    restream.py [--url=<url>] [--extract-client] [--rate=<rate>] [--max-wait=<sec>] [--filelist] [--rename=auth.user_id] <filename>

Options
    --url=<url>       URL to connect [default: http://localhost:8888/]
    --extract-client  Parse JSON and extract unannoted client-side event
    --filelist        File is a list of files to play at once
    --rate=<rate>     Throttle events to: rate*timestamps
    --max-wait=<sec>  Maximum delay (if throttling)
    --rename=<field>  Rename students, randomly. If set, <field> must be auth.user_id.

Overview:
    * Restream logs from a file a web sockets server
    * Helpful for testing
    * Optional (todo): Capture server output
    * Optional (todo): Handle AJAX

The file list option starts streaming timestamps from the first
event. This is helpful for e.g. simulating 20 coglabs as one
session. It is not helpful for playing back what happened in one
class.

'''

import asyncio
import json
import random
import sys

import aiofiles
import aiohttp
import docopt
import names

print(docopt.docopt(__doc__))


async def restream(
        url,
        filename,
        rate,
        max_wait,
        extract_client,
        rename
):
    '''
    Simplest function in the world.

    Open up a session, then a socket, and then stream lines from the
    file to the socket.
    '''
    old_ts = None
    if rename is not None:
        new_id = "rst-{name}-{number}".format(
            name = names.get_first_name(),
            number = random.randint(1,1000)
        )

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(url) as web_socket:
            async with aiofiles.open(filename) as log_file:
                async for line in log_file:
                    if rate is not None:
                        new_ts = json.loads(line)["server"]["time"]
                        if old_ts is not None:
                            delay = (new_ts - old_ts) * rate
                            if max_wait is not None:
                                delay = min(delay, max_wait)
                            print(line)
                            print(delay)
                            await asyncio.sleep(delay)
                        old_ts = new_ts
                    if extract_client or rename:
                        json_line = json.loads(line)
                        if extract_client:
                            json_line = json_line['client']
                        print(json.dumps(json_line, indent=2))
                        if rename:
                            json_line['auth']['user_id'] = new_id
                        line = json.dumps(json_line)

                    await web_socket.send_str(line.strip())
        return True


async def run():
    '''
    Is there a way to clean up so we don't have an ever-expanding
    block indent?
    '''
    args = docopt.docopt(__doc__)
    print(args)
    if args["--filelist"]:
        filelist = [s.strip() for s in open(args['<filename>']).readlines()]
    else:
        filelist = [args['<filename>']]
    coroutines = [
        restream(
            url = args["--url"],
            filename = filename,
            rate = float(args["--rate"]),
            max_wait = args["--max-wait"],
            extract_client = args['--extract-client'],
            rename = args['--rename']
        ) for filename in filelist]
    await asyncio.gather(*coroutines)

try:
    asyncio.run(run())
except aiohttp.client_exceptions.ServerDisconnectedError:
    print("Could not connect to server")
    sys.exit(-1)
