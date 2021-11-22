import jmespath
from typing import List, Union
from .utils import get_or_die

class HealthUpdate(object):
    """An object representing a HealthUpdate from BMS."""

    def __init__(self, hupdate: dict):
        self._action = hupdate.get('action', '')
        self._alerts = hupdate.get('alerts', [])
        self._env = jmespath.search('tenant.env', hupdate)
        self._errors = hupdate.get('errors', [])
        self._healthy = get_or_die(hupdate, 'healthy')
        self._kind = get_or_die(hupdate, 'kind')
        self._name = get_or_die(hupdate, 'name')
        self._namespace = hupdate.get('namespace', '')
        self._tenant = jmespath.search('tenant.name', hupdate)
        self._warnings = hupdate.get('warnings', [])

        self._previous_healthy = hupdate.get('previous_healthy', None)

    @property
    def action(self) -> str:
        return self._action

    @property
    def alerts(self) -> List[str]:
        return self._alerts

    @property
    def env(self) -> str:
        return self._env

    @property
    def errors(self) -> List[str]:
        return self._errors

    def has_above(self, level: str) -> bool:
        result = {
            'error': self.has_errors,
            'warn': self.has_errors or self.has_warnings,
            'alert': self.has_errors or self.has_warnings or self.has_alerts,
        }.get(level, None)

        if result == None:
            raise ValueError("level must be 'error', 'warn', or 'alert'")

        return result

    @property
    def has_alerts(self) -> bool:
        return len(self._alerts) > 0

    @property
    def has_errors(self) -> bool:
        return len(self._errors) > 0

    @property
    def has_warnings(self) -> bool:
        return len(self._warnings) > 0

    @property
    def healthy(self) -> bool:
        healthy = self._healthy.lower()
        if healthy in ['true', 'warn', 'alert']:
            return True
        else:
            return False

    @property
    def healthy_raw(self) -> str:
        return self._healthy

    @property
    def healthy_str(self) -> str:
        return HealthUpdate.healthy_to_str(self._healthy)

    @property
    def kind(self) -> str:
        return self._kind

    @property
    def name(self) -> str:
        return self._name

    @property
    def namespace(self) -> str:
        return self._namespace

    @property
    def previous_healthy(self) -> Union[bool, None]:
        if self._previous_healthy == None:
            return None
        healthy = self._previous_healthy.lower()
        if healthy in ['true', 'warn', 'alert']:
            return True
        else:
            return False

    @property
    def previous_healthy_raw(self) -> Union[str, None]:
        return self._previous_healthy

    @previous_healthy_raw.setter
    def previous_healthy_raw(self, value: str) -> None:
        if isinstance(value, str):
            self._previous_healthy = value

    @property
    def previous_healthy_str(self) -> Union[str, None]:
        return HealthUpdate.healthy_to_str(self._previous_healthy)

    @property
    def tenant(self) -> str:
        return self._tenant

    @property
    def warnings(self) -> List[str]:
        return self._warnings

    def to_s(self) -> str:
        return f'[{self.kind}] {self.name} state: {self.healthy_str}'

    @staticmethod
    def healthy_to_str(healthy: str) -> str:
        """Because the API returns "True" if healthy,
        we want to translate that to something more
        readable by meat objects."""
        if healthy == None or not isinstance(healthy, str):
            return 'Unknown'

        healthy = healthy.lower()
        if healthy == 'true':
            return 'Healthy'
        elif healthy == 'false':
            return 'Unhealthy'
        elif healthy == 'warn':
            return 'Warning'
        elif healthy == 'alert':
            return 'Alert'
        else:
            return 'Unknown'