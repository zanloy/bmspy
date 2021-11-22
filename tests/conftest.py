import copy
import pytest
from typing import List, Type

# External deps
from slack_sdk.models.blocks import Block

# Internal deps
from bmspy import HealthUpdate, Router
from bmspy import SlackBot as _SlackBot

# Fixture: slackbot
class SlackBot(_SlackBot):
    """Overwrite SlackBot to add functions for testing."""
    def __init__(self):
        self._messages = []
        super().__init__('testing', [])

    @property
    def messages(self) -> List[dict]:
        return self._messages

    def reset_messages(self):
        """Resets the mock message queue."""
        self._messages = []

    async def send_message(self, channel: str, text: str, blocks: List[Type[Block]] = ...):
        self._messages.append({'channel': channel, 'text': text, 'blocks': blocks})

@pytest.fixture
def slackbot():
    return SlackBot()

@pytest.fixture
def test_router(slackbot):
    return Router(slackbot = slackbot)

# Fixtures: hupdates
@pytest.fixture
def base_hupdate_dict():
    return  {
        'kind': 'Namespace',
        'name': 'testing',
        'namespace': '',
        'action': 'refresh',
        'healthy': 'Unknown',
        'errors': [],
        'warnings': [],
        'alerts': [],
    }

@pytest.fixture
def healthy_hupdate_dict(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['healthy'] = 'True'
    return subj

@pytest.fixture
def healthy_hupdate(healthy_hupdate_dict):
    return HealthUpdate(healthy_hupdate_dict)

@pytest.fixture
def unhealthy_hupdate_dict(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['healthy'] = 'False'
    subj['errors'] = ['Error #1']
    return subj

@pytest.fixture
def unhealthy_hupdate(unhealthy_hupdate_dict):
    return HealthUpdate(unhealthy_hupdate_dict)

@pytest.fixture
def warning_hupdate_dict(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['healthy'] = 'Warn'
    subj['warnings'] = ['Warning #1']
    return subj

@pytest.fixture
def warning_hupdate(warning_hupdate_dict):
    return HealthUpdate(warning_hupdate_dict)

@pytest.fixture
def alert_hupdate_dict(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['healthy'] = 'Alert'
    subj['alerts'] = ['Alert #1']
    return subj

@pytest.fixture
def alert_hupdate(alert_hupdate_dict):
    return HealthUpdate(alert_hupdate_dict)

@pytest.fixture
def unknown_hupdate_dict(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['healthy'] = 'Unknown'
    return subj

@pytest.fixture
def unknown_hupdate(unknown_hupdate_dict):
    return HealthUpdate(unknown_hupdate_dict)

@pytest.fixture
def tenant1_prod_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant1-prod'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant1', 'env': 'prod'}
    return HealthUpdate(subj)

@pytest.fixture
def tenant1_stage_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant1-stage'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant1', 'env': 'stage'}
    return HealthUpdate(subj)

@pytest.fixture
def tenant1_dev_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant1-dev'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant1', 'env': 'dev'}
    return HealthUpdate(subj)

@pytest.fixture
def tenant2_prod_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant2-prod'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant2', 'env': 'prod'}
    return HealthUpdate(subj)

@pytest.fixture
def tenant2_stage_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant2-stage'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant2', 'env': 'stage'}
    return HealthUpdate(subj)

@pytest.fixture
def tenant2_dev_ns(base_hupdate_dict):
    subj = copy.deepcopy(base_hupdate_dict)
    subj['name'] = 'tenant2-dev'
    subj['healthy'] = 'True'
    subj['tenant'] = {'name': 'tenant2', 'env': 'dev'}
    return HealthUpdate(subj)
