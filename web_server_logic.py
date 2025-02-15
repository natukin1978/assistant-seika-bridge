import asyncio
import logging
import re
import traceback

import aiohttp.web

import global_value as g
from sound_helper import get_sound_device, play_wav_from_memory

logger = logging.getLogger(__name__)


def get_sound_device_name_from_cid(cid: int) -> str:
    try:
        voice_maps = g.config["voice"]["maps"]
        for voice_map in voice_maps:
            pattern = voice_map["cid"]
            if re.fullmatch(pattern, cid):
                return voice_map["soundDeviceName"]
        return ""
    except:
        return ""


async def play_wav(request, response):
    response.raise_for_status()
    if response.content_type != "audio/wav":
        raise ValueError(f"Content-Type is not audio/wav: {response.content_type}")

    wav_bytes = bytearray()
    async for chunk in response.content.iter_chunked(65535):
        wav_bytes.extend(chunk)

    # 再生するデバイスIDを得る
    paths = response.url.parts
    cid = paths[2]
    sound_device_name = get_sound_device_name_from_cid(cid)
    if not sound_device_name:
        sound_device_name = g.config["voice"]["soundDeviceName"]
    sound_device_id, _ = get_sound_device(sound_device_name)
    paths = request.url.parts
    cmd = paths[1]
    wait = {
        "PLAY2": True,
        "PLAYASYNC2": False,
    }[cmd]
    play_wav_from_memory(wav_bytes, sound_device_id, wait)


async def handle_common_logic(request, handle_response, replace_cmd=None):
    url = request.url
    method = request.method
    headers = request.headers
    params = request.query
    logger.info(f"Request received: {method} {url}")

    target_base_url = g.config["assistantSeika"]["baseUrl"]
    url_path = str(url.path)
    if replace_cmd:
        url_path = re.sub(r"/.*?/", f"/{replace_cmd}/", url_path, 1)
    target_url = target_base_url + url_path
    logger.info(f"Target URL: {target_url}")

    try:
        data = await request.read()
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method,
                target_url,
                headers=headers,
                params=params,
                data=data,
                timeout=10,
            ) as response:
                logger.info(f"Response from target: {response.status}")
                return await handle_response(request, response)
    except aiohttp.ClientError as e:
        logger.error(f"Error forwarding request: {e}")
        traceback.print_exc()
        return aiohttp.web.Response(text=str(e), status=500)
    except asyncio.TimeoutError:
        logger.error("Request to target timed out.")
        return aiohttp.web.Response(text="Request to target timed out.", status=504)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        traceback.print_exc()
        return aiohttp.web.Response(text="An unexpected error occurred.", status=500)


async def handle_request_play_sound(request):
    async def handle_save2_response(request, response):
        await play_wav(request, response)
        return aiohttp.web.Response(status=200)

    return await handle_common_logic(request, handle_save2_response, "SAVE2")


async def handle_request(request):
    async def handle_default_response(request, response):
        if next(filter(lambda v: v in response.content_type, ["json", "text"]), None):
            response_result = await response.text()
        else:
            response_result = await response.read()
        return aiohttp.web.Response(
            body=response_result,
            status=response.status,
        )

    return await handle_common_logic(request, handle_default_response)


async def start_web_server():
    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.route("*", "/PLAYASYNC2/{tail:.*}", handle_request_play_sound),
            aiohttp.web.route("*", "/PLAY2/{tail:.*}", handle_request_play_sound),
            aiohttp.web.route("*", "/{tail:.*}", handle_request),
        ]
    )

    port = g.config["server"]["port"]
    runner = aiohttp.web.AppRunner(app)
    await runner.setup()
    site = aiohttp.web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

    logger.info(f"Serving on http://0.0.0.0:{port}")

    try:
        await asyncio.Future()
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()
