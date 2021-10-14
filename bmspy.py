#!/usr/bin/env python3

import asyncio
import dotenv
import json
import logging
import os
import sys
import websockets
from bmspy import *
from collections import defaultdict
from pythonjsonlogger import jsonlogger
from typing import Dict, List, Literal, Tuple
from pprint import pprint

dotenv.load_dotenv()

# Helper methods (that should eventually be moved out into a lib)
def truncate(text: str, length: int=75) -> str:
    if len(text) > length:
        return text[:length-3] + '...'
    else:
        return text

class BMSConsumer:
    def __init__(self, url: str, slackbot: SlackBot) -> None:
        self.url = url
        self._slack = slackbot

    async def start(self):
        while True:
            try:
                async with websockets.connect(self.url, ping_interval=None) as websocket:
                    await self.consumer(websocket)
            except websockets.exceptions.ConnectionClosedError:
                continue
            else:
                break

    async def consumer(self, websocket: websockets.WebSocketClientProtocol) -> None:
        async for message in websocket:
            await self.process_msg(message)

    async def process_msg(self, message):
        json_payload = json.loads(message)
        # filter
        if json_payload['action'] == 'refresh':
            return
        if json_payload['kind'] not in ['namespace']:
            return
        kind = json_payload['kind']
        name = json_payload['name']
        if 'previous_healthy' in json_payload.keys():
            if json_payload['previous_healthy'].lower() == 'true':
                previous_healthy = 'HEALTHY'
            elif json_payload['previous_healthy'].lower() == 'false':
                previous_healthy = 'UNHEALTHY'
        else:
            previous_healthy = 'UNKNOWN'
        healthy = json_payload['healthy']
        channel = os.environ.get('BMSPY_ALERT_CHANNEL')
        print(f'Totes about to alert #{channel}...')
        await self._slack.send_message(f'#{channel}', f'{name} transitioned to {healthy} from {previous_healthy}.')
        print('How did it go?')

# Do work.
if __name__ == '__main__':
    # TODO: Setup argparse for these
    loglevel = logging.DEBUG
    sources = ["http://localhost:8080"]

    logHandler = logging.StreamHandler(stream=sys.stdout)
    formatter = jsonlogger.JsonFormatter('%(asctime)s %(name)s %(levelname)s %(message)s')
    logHandler.setFormatter(formatter)
    logging.basicConfig(handlers=[logHandler], level=loglevel)

    loop = asyncio.get_event_loop()
    try:
        # Start Slack bot
        logging.info('Initiating slack bot...')
        slackbot = SlackBot(os.environ.get('SLACK_BOT_TOKEN'), sources)
        loop.create_task(slackbot.start())
        logging.info('Slack bot initialized.')
        # Start BMS websocket consumer
        #logging.info('Initialing bms websocket consumer...')
        #bms = BMSConsumer('wss://bms-api.prod8.bip.va.gov/ws/ns', slackbot)
        #loop.create_task(bms.start())
        #logging.info('BMS websocket consumer initialized.')
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('Received keyboard interrupt signal. Closing down event loop and exiting...')
    finally:
        logging.info('Shutting down event loop and exiting...')
        loop.close()
        logging.info('Shutdown complete. Sayounara señoras y señores.')
