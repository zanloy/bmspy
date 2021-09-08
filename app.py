#!/usr/bin/env python3

import asyncio
import dotenv
import http
import json
import logging
import os
import re
import requests
import slack_bolt.async_app
import sys
import urllib.parse
import websockets
from collections import defaultdict
from typing import Dict, List, Literal, Tuple
from pprint import pprint
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

dotenv.load_dotenv()

# Helper methods (that should eventually be moved out into a lib)
def truncate(text: str, length: int=75) -> str:
    if len(text) > length:
        return text[:length-3] + '...'
    else:
        return text

class SlackBot:
    HEALTHY = ('healthy', ':white_check_mark:')
    UNHEALTHY = ('unhealthy', ':x:')
    WARNING = ('warning', ':warning:')

    def __init__(self, token: str) -> None:
        self._app = slack_bolt.async_app.AsyncApp(token=token)
        self.token = token
        # Setup handlers
        self._app.action('health')(self.action_health)
        self._app.event('app_mention')(self.handle_mention)

    async def start(self) -> None:
        handler = AsyncSocketModeHandler(self._app)
        await handler.start_async()

    async def action_health(self, ack, payload, say, logger):
        await ack()
        namespace = payload['selected_option']['value']
        resp = requests.get(f'https://bms-api.prod8.bip.va.gov/ns/{namespace}', verify=False)
        if resp.status_code == http.HTTPStatus.NOT_FOUND:
            await say(f':octagonal_sign: Could not find {namespace}.')
        elif resp.status_code == http.HTTPStatus.OK:
            obj = resp.json()
            text, blocks = self.build_health_blocks(obj)
            await say(text, blocks)
        else:
            await say(f':o: Error when trying to query {namespace}; Received HTTP status: {resp.status_code}.')
        logger.info(payload)

    async def cmd_health(self, text, say) -> None:
        """Handles the `health` command.
        
        text may be 0-2 "tokens".
        Case #1: No tokens. text=''. Will return a overall summary of all namespaces.
        Case #2: 1 token. text='mynamespace'. Will return the health of that namespace.
        Case #3: 2 tokens. text='deployment mynamespace/mydeployment. Will return the health of mydeployment from mynamespace.
        """
        token_count = len(text.split())
        if token_count == 0:
            resp = requests.get('https://bms-api.prod8.bip.va.gov/health/namespaces', verify=False)
            resp.raise_for_status()
            objs = resp.json()
            text, blocks = self.build_overview_blocks(objs)
            await say(text, blocks)
        elif token_count == 1:
            (namespace, text) = self.next_token(text)
            # Check for wildcards
            if '*' in namespace:
                namespace_regex = re.compile(namespace.replace('*', '.*'))
                blocks = [
                    {
                        'type': 'header',
                        'text': {
                            'type': 'plain_text',
                            'text': f'Health for {namespace}:',
                        },
                    },
                    { 'type': 'divider', },
                ]
                for ns in self.get_all_namespaces():
                    if namespace_regex.fullmatch(ns):
                        obj = await self.fetch_namespace(ns)
                        _, subblocks = self.build_health_blocks(obj, include_header=False, include_link=False)
                        blocks.extend(subblocks)
                await say(f'Results for {namespace}.', blocks)
            else:
                self.say_health(namespace, say)

    async def cmd_help(self, text, say) -> None:
        """Returns a help message, duh?"""
        (token, text) = self.next_token(text)
        if token == '':
            await say("I do one thing, and I try to do it well. Just @mention me with 'health %namespace%' or just 'health'.")

    async def cmd_status(self, text, say) -> None:
        await self.cmd_health(text, say)

    async def fetch_namespace(self, namespace) -> Dict[str, str]:
        resp = requests.get(f'https://bms-api.prod8.bip.va.gov/ns/{namespace}', verify=False)
        if resp.status_code == http.HTTPStatus.NOT_FOUND:
            raise Exception(f':octagonal_sign: Could not find {namespace}.')
        elif resp.status_code == http.HTTPStatus.OK:
            return resp.json()
        else:
            raise Exception(f':o: Error when trying to query {namespace}; Received HTTP status: {resp.status_code}.')

    def get_all_namespaces(self) -> List[str]:
        resp = requests.get('https://bms-api.prod8.bip.va.gov/health/namespaces', verify=False)
        resp.raise_for_status()
        objs = resp.json()
        namespaces = [ns['name'] for ns in objs]
        return namespaces

    async def handle_mention(self, event, say) -> None:
        (cmd, text) = self.next_token(event['text'])
        try:
            method = getattr(self, f'cmd_{cmd}')
        except AttributeError:
            await say(f'{cmd}: Unknown Command.')
            return
        await method(text, say)

    async def say_health(self, namespace, say) -> None:
        try:
            result = await self.fetch_namespace(namespace)
            text, blocks = self.build_health_blocks(result)
            await say(text, blocks)
        except Exception:
            say('There was an error while fetching the health of {namespace}. Check logs for details.')

    async def send_message(self, channel: str, text: str):
        await self._app.client.chat_postMessage(
            channel=channel,
            text=text,
        )

    def translate_healthy(self, healthy: str) -> Tuple[str, str]:
        """Because the API returns "True" if healthy,
        we want to translate that to something more 
        readable by meat objects."""
        healthy = healthy.lower()
        if healthy == 'true':
            return SlackBot.HEALTHY
        elif healthy == 'false':
            return SlackBot.UNHEALTHY
        elif healthy == 'warn':
            return SlackBot.WARNING
        else:
            return (healthy, ':question:')

    def build_overview_blocks(self, objs: Dict) -> Tuple[str, List[Dict]]:
        collection = defaultdict(lambda: [])
        for ns in objs:
            healthy, _ = self.translate_healthy(ns['healthy'])
            collection[healthy].append(ns)
        healthy_count = len(collection['healthy'])
        statuses = []
        if healthy_count:
            statuses.append(f'healthy({healthy_count})')
        if len(collection['unhealthy']):
            statuses.append(f"unhealthy({len(collection['unhealthy'])})")
        if len(collection['warn']):
            statuses.append(f"warning({len(collection['warn'])})")
        text = f"Overall health: {', '.join(statuses)}"
        blocks = []
        blocks.append({
            'type': 'header',
            'text': {
                'type': 'plain_text',
                'text': f':medical_symbol: {text}',
            },
        })
        if len(collection['unhealthy']):
            blocks.append({'type':'divider'})
            namespaces: List[str] = []
            for ns in collection['unhealthy']:
                try:
                    errors = len(ns['errors'])
                except KeyError:
                    errors = 0
                try:
                    warnings = len(ns['warnings'])
                except KeyError:
                    warnings = 0
                namespaces.append(f"*{ns['name']}*: {errors} errors, {warnings} warnings.")
            select_block = {
                'type': 'static_select',
                'placeholder': {
                    'type': 'plain_text',
                    'text': 'More details...',
                },
                'options': [{'text': {'type':'plain_text','text':ns['name']},'value':ns['name']} for ns in collection['unhealthy']],
                'action_id': 'health',
            }
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': os.linesep.join(namespaces)
                },
                'accessory': select_block,
            })
        # Why did I put this in a Dict and then never use it? Because one day I'll be smart enough to move all these functions out to a library.
        open_in_bms =  {
            'accessory': {
                'type': 'button',
                'text': {
                    'type': 'plain_text',
                    'text': 'Open in BMS',
                },
                'value': 'open_in_bms',
                'url': 'https://bms.prod8.bip.va.gov/dashboard',
                'action_id': 'button-action',
            }
        }
        blocks.append({
            'type': 'section',
            'text': {
                'type': 'mrkdwn',
                'text': '<https://bms.prod8.bip.va.gov/dashboard|BMS Dashboard>',
            },
        })
        unhealthy_namespaces = [ns['name'] for ns in collection['unhealthy']]
        text += f". Unhealthy namespaces: {', '.join(unhealthy_namespaces)}."
        return text, blocks

    def build_health_blocks(self, obj: Dict, include_header=True, include_link=True) -> Tuple[str, List[Dict]]:
        status, icon = self.translate_healthy(obj['healthy'])
        try:
            kind = f"[{obj['kind']}] "
        except KeyError:
            kind = ''
        try:
            name = obj['name']
        except KeyError:
            name = 'UNKNOWN'
        text = f'{kind}{name} status: {status}.'
        blocks = []
        if include_header:
            blocks.append({
                'type': 'header',
                'text': {
                    'type': 'plain_text',
                    'text': f'{icon} {kind}{name} status: {status}',
                }
            })
        else:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'{icon} {kind}*{name}*: {status}',
                }
            })
        if 'warnings' in obj.keys() or 'errors' in obj.keys():
            blocks.append({'type':'divider'})
            if 'errors' in obj.keys():
                error_lines: List[str] = []
                for error in obj['errors']:
                    error_lines.append(f':small_red_triangle: {error}')
                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '\n'.join(error_lines)
                    }
                })
            if 'warnings' in obj.keys():
                warning_lines: List[str] = []
                for warning in obj['warnings']:
                    warning_lines.append(f':small_orange_diamond: {warning}')
                blocks.append({
                    'type': 'section',
                    'text': {
                        'type': 'mrkdwn',
                        'text': '\n'.join(warning_lines)
                    }
                })
        if include_link:
            blocks.append({
                'type': 'section',
                'text': {
                    'type': 'mrkdwn',
                    'text': f'<https://bms.prod8.bip.va.gov/ns/{name}|Open in BMS>',
                },
            })
        return text, blocks

    def next_token(self, text: str):
        tokens = text.split(' ', maxsplit=1)
        while len(tokens) < 2:
            tokens.append('')
        token, text = tokens[0], tokens[1]
        if token.startswith('<') or token in ['of']:
            return self.next_token(text)
        return (token, text)

class BMSConsumer:
    def __init__(self, base_url: str, slackbot: SlackBot) -> None:
        self.base_url = base_url
        self._slack = slackbot

    async def start(self):
        url = urllib.parse.urljoin(self.base_url, '/health/ws')
        async with websockets.connect(url) as websocket:
            await self.consumer(websocket)

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
        await self._slack.send_message('#general', f'[{kind}] {name} changed to {healthy} from {previous_healthy}.')
        pprint(message)

# Do work.
if __name__ == '__main__':
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    loop = asyncio.get_event_loop()
    try:
        # Start Slack bot
        logging.info('Initiating slack bot...')
        slackbot = SlackBot(os.environ.get('SLACK_BOT_TOKEN'))
        loop.create_task(slackbot.start())
        logging.info('Slack bot initialized.')
        # Start BMS websocket consumer
        logging.info('Initialing bms websocket consumer...')
        bms = BMSConsumer('wss://bms-api.prod8.bip.va.gov/', slackbot)
        loop.create_task(bms.start())
        logging.info('BMS websocket consumer initialized.')
        loop.run_forever()
    except KeyboardInterrupt:
        logging.info('Received keyboard interrupt signal. Closing down event loop and exiting...')
    finally:
        logging.info('Shutting down event loop and exiting...')
        loop.close()
        logging.info('Shutdown complete. Sayounara señoras y señores.')
