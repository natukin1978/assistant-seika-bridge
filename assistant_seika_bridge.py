import asyncio
import logging
import os
import sys

import global_value as g
from config_helper import read_config
from logging_setup import setup_app_logging

g.app_name = "assistant_seika_bridge"
g.base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
g.config = read_config()

# ロガーの設定
setup_app_logging(g.config["logLevel"], log_file_path=f"{g.app_name}.log")
logger = logging.getLogger(__name__)

from web_server_logic import start_web_server


async def main():
    await start_web_server()


if __name__ == "__main__":
    asyncio.run(main())
