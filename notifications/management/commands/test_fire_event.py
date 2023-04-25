from aiohttp import web
from django.core.management.base import BaseCommand
from django.conf import settings
import asyncio
import socketio
import json
import os
from .live_notify import sio

logger = settings.LOGGER


class Command(BaseCommand):
    async def handle(self, *args, **options):
        await sio.emit("PONG", {"status": "OK", "sid": "test"})