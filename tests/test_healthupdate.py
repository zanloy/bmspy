import copy
import pytest

from bmspy import HealthUpdate

test_params = [
    ('healthy_hupdate_dict', True, 'Healthy'),
    ('unhealthy_hupdate_dict', False, 'Unhealthy'),
    ('warning_hupdate_dict', True, 'Warning'),
    ('alert_hupdate_dict', True, 'Alert'),
    ('unknown_hupdate_dict', False, 'Unknown'),
]

@pytest.mark.parametrize('hupdate_dict,expected_healthy,expected_healthy_str', test_params)
def test_init(hupdate_dict, expected_healthy, expected_healthy_str, request):
    hupdate_dict = request.getfixturevalue(hupdate_dict)
    subj = HealthUpdate(hupdate_dict)

    assert subj.kind == hupdate_dict['kind']
    assert subj.name == hupdate_dict['name']
    assert subj.namespace == hupdate_dict['namespace']
    assert subj.healthy == expected_healthy
    assert subj.healthy_str == expected_healthy_str
    assert subj.errors == hupdate_dict['errors']
    assert subj.warnings == hupdate_dict['warnings']
    assert subj.alerts == hupdate_dict['alerts']

@pytest.mark.parametrize('field', ['healthy', 'kind', 'name'])
def test_init_validation(healthy_hupdate_dict, field):
    obj = copy.deepcopy(healthy_hupdate_dict)
    del(obj[field])
    with pytest.raises(KeyError) as e_info:
        HealthUpdate(obj)
