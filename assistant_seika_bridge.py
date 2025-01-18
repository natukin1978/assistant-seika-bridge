import asyncio
import logging

import global_value as g
from config_helper import readConfig
from web_server_logic import start_web_server

g.config = readConfig()

# ロガーの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    await start_web_server()


if __name__ == "__main__":
    asyncio.run(main())
