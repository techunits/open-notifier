from aiohttp import web
from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import socketio
import json
import os

logger = settings.LOGGER

sio = socketio.AsyncServer(async_mode="aiohttp")
app = web.Application()
sio.attach(app)


@sio.event
async def connect(sid, environ):
    logger.info(f"New client socket connection: {sid}")


@sio.on("PING")
async def message(sid, data):
    logger.debug(f"Incoming Event({sid}): PING -> {data}")
    response = {"status": "OK", "sid": sid}
    logger.debug(f"Sending Event({sid}): PONG -> {response}")
    await sio.emit("PONG", response)


@sio.event
async def disconnect(sid):
    logger.info(f"Client socket disconnected: {sid}")


async def index(request):
    return web.Response(
        text=json.dumps({"status": "OK"}), content_type="application/json"
    )


async def socket_test(request):
    with open(
        os.path.join(settings.BASE_DIR, "notifier", "misc", "pages", "socket_demo.html")
    ) as fp:
        return web.Response(text=fp.read(), content_type="text/html")


app.router.add_get("/", index)
app.router.add_get("/demo", socket_test)


class Command(BaseCommand):
    def handle(self, *args, **options):
        asyncio.run(self.__run())

    def __run(self):
        web.run_app(app, host="0.0.0.0", port=3000)
