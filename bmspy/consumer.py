# StdLib
import asyncio
import json
import logging
from typing import Dict
import urllib.error
from urllib.parse import urlparse
import websockets

# Internal deps
from .builder import Builder
from .health_update import HealthUpdate
from .router import Router
from .slack_bot import SlackBot

class BMSConsumer:
    """Creates a websocket to BMS and monitors HealthUpdates to alert SlackBot."""
    def __init__(self, url: str, slackbot: SlackBot, router: Router, wait: int=1, max_wait: int=60) -> None:
        # Validate
        try:
            urlparse(url)
        except urllib.error.URLError as e:
            raise ValueError('failed to parse url') from e
        if slackbot == None:
            raise ValueError('slackbot cannot be None')
        if router == None or isinstance(router, Router) == False:
            raise ValueError('invalid router')
        if wait > max_wait:
            raise ValueError(f'wait "{ wait }" cannot be greater than max_wait "{ max_wait }"')

        self._url = url
        self._slack = slackbot
        self._router = router
        self._wait = wait
        self._max_wait = max_wait

        self._cache: Dict[str, HealthUpdate] = {}

    async def start(self):
        wait = self._wait
        while True:
            try:
                async with websockets.connect(self._url, ping_interval=None) as websocket:
                    await self.populate_cache()
                    wait = self._wait
                    await self.consumer(websocket)
            except (websockets.exceptions.ConnectionClosedError, ConnectionError) as e:
                logging.error(e, f"connection error contacting bms-api, waiting { wait } seconds to retry")
                await asyncio.sleep(wait)
                wait = wait * 2
                if wait > self._max_wait:
                    wait = self._max_wait
                continue

    async def consumer(self, websocket: websockets.WebSocketClientProtocol) -> None:
        async for message in websocket:
            await self.process_msg(message)

    async def populate_cache(self) -> None:
        """Check remote source and populate current 'healthy' values."""
        # TODO: We should be doing this work instead of relying on functionality in SlackBot for it.
        values = await self._slack.fetch_all_namespaces()
        for v in values:
            self._cache[v.name] = v

    async def process_msg(self, message) -> None:
        payload = json.loads(message)
        hupdate = HealthUpdate(payload)

        # Check cache to see if new state
        if hupdate.name in self._cache.keys():
            hupdate.previous_healthy_raw = self._cache[hupdate.name].healthy_raw

        # Update cache
        self._cache[hupdate.name] = hupdate

        if hupdate.healthy_str != hupdate.previous_healthy_str:
            await self._router.process_msg(hupdate)
