import asyncio
import logging
import os
import sys

import global_value as g
from config_helper import readConfig
from web_server_logic import start_web_server


async def main():
    await start_web_server()


if __name__ == "__main__":
    os.chdir(os.path.dirname(os.path.abspath(sys.argv[0])))
    g.config = readConfig()
    # ロガーの設定
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
