import asyncio
import logging
import os
import sys

import global_value as g

g.app_name = "assistant_seika_bridge"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

from config_helper import read_config
from web_server_logic import start_web_server

g.config = read_config()
# ロガーの設定
logging.basicConfig(level=logging.INFO)


async def main():
    await start_web_server()


if __name__ == "__main__":
    asyncio.run(main())
