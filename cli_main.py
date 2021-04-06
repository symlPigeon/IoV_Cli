import asyncio
import traceback

from IoV_Handler.ws_event_handler import initialize_process
from ws_handler import ws_handler

url = r"wss://syml-gensokyo.cn:8888/ws_vehicle"


async def ws_cli_main():
    # ws_handler 初始化部分
    handler = ws_handler(url)
    initialize_process(handler)
    while True:
        try:
            print("socket start!")
            await handler.start()
        except ConnectionRefusedError as e:
            print(str(e))
            await asyncio.sleep(1)
        except Exception:
            traceback.print_exc()
            await asyncio.sleep(1)


asyncio.get_event_loop().run_until_complete(ws_cli_main())
