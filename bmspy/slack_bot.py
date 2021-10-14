# StdLib
from collections import defaultdict
import http
import os
from pprint import pprint
import re
import requests
from typing import Dict, List, Literal, Tuple
from urllib.parse import urljoin

from slack_sdk.models.blocks.basic_components import PlainTextObject
# Internal Deps
from .builder import Builder
from .health_update import HealthUpdate
# External Deps
from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp
from slack_sdk.models.blocks import Block, DividerBlock, HeaderBlock

class SlackBot:
    HEALTHY = ('healthy', ':white_check_mark:')
    UNHEALTHY = ('unhealthy', ':x:')
    WARNING = ('warning', ':warning:')

    NAMESPACE_URI = '/ns/{namespace}'

    def __init__(self, token: str, sources: List[str]) -> None:
        self._app = AsyncApp(token=token)
        self.token = token
        self._sources = sources
        # Setup handlers
        self._app.action('health')(self.action_health)
        self._app.event('app_mention')(self.handle_mention)

    async def start(self) -> None:
        handler = AsyncSocketModeHandler(self._app)
        await handler.start_async()

    async def action_health(self, ack, action, say):
        await ack()
        await self.say_health(action['selected_option']['value'], say)

    async def cmd_health(self, event, text, say) -> None:
        """Handles the `health` command.

        text may be 0-2 "tokens".
        Case #1: No tokens. text=''. Will return a overall summary of all namespaces.
        Case #2: 1 token. text='mynamespace'. Will return the health of that namespace.
        Case #3: 2 tokens. text='deployment mynamespace/mydeployment. Will return the health of mydeployment from mynamespace.
        """
        token_count = len(text.split())
        if token_count == 0:
            namespaces = await self.fetch_all_namespaces()
            blocks = Builder.health_overview(namespaces)
            text = blocks[0].text.text
            await say(text, blocks, thread_ts=event.get('thread_ts', None))
        elif token_count == 1:
            (namespace, text) = self.next_token(text)
            # Check for wildcards
            if '*' in namespace:
                namespace_regex = re.compile(namespace.replace('*', '.*'))
                blocks: List[Block] = []
                blocks.append(
                    HeaderBlock(
                        text=PlainTextObject(
                            text=f'Health results for "{namespace}":'
                        )
                    )
                )
                blocks.append(DividerBlock())
                for ns in await self.fetch_all_namespaces():
                    if namespace_regex.fullmatch(ns.name):
                        blocks.extend(Builder.health(ns))
                await say(f'Health results for "{namespace}".', blocks)
            else:
                await self.say_health(namespace, say, event)

    async def cmd_help(self, text, say) -> None:
        """Returns a help message, duh?"""
        (token, text) = self.next_token(text)
        if token == '':
            await say("I do one thing, and I try to do it well. Just @mention me with 'health %namespace%' or just 'health'.")

    async def cmd_status(self, text, say) -> None:
        await self.cmd_health(text, say)

    def commands(self) -> List[str]:
        command_list = [func[len('cmd_'):] for func in dir(self) if callable(getattr(self, func)) and func.startswith('cmd_')]
        return command_list

    async def fetch_namespace(self, namespace) -> HealthUpdate:
        url = urljoin(self._sources[0], self.NAMESPACE_URI.format(namespace=namespace))
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        return HealthUpdate(resp.json())

    async def fetch_all_namespaces(self) -> List[HealthUpdate]:
        url = urljoin(self._sources[0], self.NAMESPACE_URI.format(namespace=''))
        resp = requests.get(url, verify=False)
        resp.raise_for_status()
        objs = resp.json()
        return [HealthUpdate(ns) for ns in objs]

    async def handle_mention(self, event, say) -> None:
        (cmd, text) = self.next_token(event['text'])
        try:
            method = getattr(self, f'cmd_{cmd}')
        except AttributeError:
            await say(f'{cmd}: Unknown Command.')
            return
        await method(event, text, say)

    async def say_health(self, namespace, say, payload=None) -> None:
        try:
            result = await self.fetch_namespace(namespace)
            blocks = Builder.health(result, details=True)
            # Reply in thread if applicable
            if payload and payload.get('thread_ts', None):
                await say(result.to_s(), blocks, thread_ts=payload['thread_ts'])
            else:
                await say(result.to_s(), blocks)
        except Exception:
            await say(f'There was an error while fetching the health of {namespace}. Check logs for details.')
            #raise

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
