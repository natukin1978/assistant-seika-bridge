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


async def play_wav(response):
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
    wait = not g.config["voice"]["playAsync"]
    play_wav_from_memory(wav_bytes, sound_device_id, wait)


async def handle_common_logic(request, handle_response):
    url = request.url
    method = request.method
    headers = request.headers
    params = request.query
    logger.info(f"Request received: {method} {url}")

    target_base_url = g.config["assistantSeika"]["baseUrl"]
    target_url = target_base_url + str(url.path)
    logger.info(f"Target URL: {target_url}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method, target_url, headers=headers, params=params, timeout=10
            ) as response:
                logger.info(f"Response from target: {response.status}")
                return await handle_response(response)
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


async def handle_request_binary(request):
    async def handle_default_response(response):
        return aiohttp.web.Response(
            body=await response.read(),
            status=response.status,
            headers=response.headers,
        )

    return await handle_common_logic(request, handle_default_response)


async def handle_request_play_sound(request):
    async def handle_save2_response(response):
        await play_wav(response)
        return aiohttp.web.Response(status=200)

    return await handle_common_logic(request, handle_save2_response)


async def handle_request(request):
    async def handle_default_response(response):
        return aiohttp.web.Response(
            body=await response.text(),
            status=response.status,
            headers=response.headers,
        )

    return await handle_common_logic(request, handle_default_response)


async def start_web_server():
    app = aiohttp.web.Application()
    app.add_routes(
        [
            aiohttp.web.route("*", "/favicon.ico", handle_request_binary),
            aiohttp.web.route("*", "/SAVE2/{tail:.*}", handle_request_play_sound),
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
