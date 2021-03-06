import asyncio
import re
from typing import List, Type, Union

from .builder import Builder
from .health_update import HealthUpdate
from .slack_bot import SlackBot

class Route:
    def __init__(self, channel: str, namespaces: List[str]=[], tenants: List[str]=[]) -> None:
        # Init
        self._namespaces = []
        self._tenants = []

        # Assignment
        self.channel = channel
        self.namespaces = namespaces
        self.tenants = tenants

    @property
    def channel(self) -> str:
        return self._channel

    @channel.setter
    def channel(self, value: str) -> None:
        if not value.startswith('#'):
            value = '#' + value
        self._channel = value

    def matches(self, hupdate: HealthUpdate) -> bool:
        for tenant in self._tenants:
            if tenant.match(hupdate.tenant):
                return True
        for namespace in self._namespaces:
            if namespace.match(hupdate.name):
                return True
        return False

    @property
    def namespaces(self) -> List[str]:
        return self._namespaces

    @namespaces.setter
    def namespaces(self, values: Union[List[str],None]) -> None:
        if values:
            self._namespaces = list(map(self._parse_pattern, values))
        else:
            self._namespaces = []

    @property
    def tenants(self) -> List[str]:
        return self._tenants

    @tenants.setter
    def tenants(self, values: Union[List[str],None]) -> None:
        if values:
            self._tenants = list(map(self._parse_pattern, values))
        else:
            self._tenants = []

    def _parse_pattern(self, pattern: str) -> re.Pattern:
        if pattern[0] == '/' and pattern[-1:] == '/':
            pattern = pattern[1:-1]
        else:
            if '*' in pattern:
                pattern = pattern.replace('*', '.*')
        return re.compile(pattern)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            if self._channel == other.channel and self._namespaces == other.namespaces and self._tenants == other.tenants:
                return True
            else:
                return False
        else:
            return False

    @staticmethod
    def check(pattern: str, string: str) -> bool:
        # Check if pattern is regex
        if pattern[0] == '/' and pattern[-1:] == '/':
            pattern = pattern[1:-1]
        else:
            if '*' in pattern:
                pattern = pattern.replace('*', '.*')

        return bool(re.match(pattern, string))

class Router:
    """A Router is setup with a SlackBot for output and a set of Routes. As
    HealthUpdates are passed into the Router, they are parsed to see if they
    match and Routes. When a match occurs, a Slack message is built and sent
    to the appropriate channel/thread.

    The Router is in charge of maintaining the list of Routes. This
    functionality is handed off to redis on the backend. The reason for this
    is that it allows us to set a TTL on ephemeral routes.

    Ephemeral routes are generated by SlackBot commands to allow for temporary
    Routes in channels/threads.

    Routes are defined in the 'routes' key of the config file. These are the
    only Routes that are permanent and have no TTL.

    An example route in settings.yaml:
    routes:
      - channel: testing
        namespaces:
          - 'testing-prod'
          - 'testing-stage'
        tenants:
          - 'tenant1'
          - 'tenant2'"""

    def __init__(self, slackbot: Type[SlackBot], routes: List[dict] = []) -> None:
        # Init
        self._routes = []

        # Assignment
        self._slackbot = slackbot
        for route in routes:
            self.add_route(route)

    def add_route(self, route: Union[dict, Route]) -> None:
        if isinstance(route, dict) == False and isinstance(route, Route) == False:
            raise ValueError('route must be an instance of dict or Route')

        if isinstance(route, dict):
            channel = route.get('channel', None)
            if channel == None:
                raise KeyError('channel cannot be None')
            namespaces = route.get('namespaces', None)
            tenants = route.get('tenants', None)
            if namespaces == None and tenants == None:
                raise KeyError('must include either a list of namespaces or tenants')

            # Create the Route
            route = Route(channel, namespaces, tenants)

        self._routes.append(route)

    def add_routes(self, routes: Union[List[dict], List[Route]]) -> None:
        for route in routes:
            self.add_route(route)

    def has_route(self, route: Route) -> bool:
        for r in self._routes:
            if r == route:
                return True
        return False

    async def process_msg(self, hupdate: HealthUpdate) -> None:
        blocks = Builder.transition_msg(hupdate)
        text = blocks[0].text.text

        pending = []
        for route in self._routes:
            if route.matches(hupdate):
                pending.append(asyncio.create_task(self._slackbot.send_message(channel = route.channel, text = text, blocks = blocks)))

        if pending:
            group = asyncio.gather(*pending, return_exceptions = True)
            await group

    def __len__(self) -> bool:
        return len(self._routes)

    @property
    def routes(self) -> List[Route]:
        return self._routes

    @property
    def slackbot(self) -> SlackBot:
        return self._slackbot
