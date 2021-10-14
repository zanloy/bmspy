from typing import List
from .utils import get_or_die

class HealthUpdate:
    """An object representing a HealthUpdate from BMS."""

    def __init__(self, hupdate: dict):
        self._healthy = get_or_die(hupdate, 'healthy')
        self._errors = hupdate.get('errors', [])
        self._warnings = hupdate.get('warnings', [])
        self._alerts = hupdate.get('alerts', [])
        self._kind = get_or_die(hupdate, 'kind')
        self._name = get_or_die(hupdate, 'name')
        self._namespace = hupdate.get('namespace', '')

    @property
    def alerts(self) -> List[str]:
        return self._alerts

    @property
    def errors(self) -> List[str]:
        return self._errors

    @property
    def healthy(self) -> bool:
        healthy = self._healthy.lower()
        if healthy in ['true', 'warn', 'alert']:
            return True
        else:
            return False

    @property
    def healthy_str(self) -> str:
        """Because the API returns "True" if healthy,
        we want to translate that to something more
        readable by meat objects."""
        healthy = self._healthy.lower()
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
    def warnings(self) -> List[str]:
        return self._warnings

    def to_s(self) -> str:
        return f'[{self.kind}] {self.name} state: {self.healthy_str}'
