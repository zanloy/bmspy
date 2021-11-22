import pytest

from bmspy import Route

def test_init():
    # Init object
    channel = '#tenant'
    namespaces = ['tenant-prod', 'tenant-stage', 'tenant-dev']
    tenants = ['tenant']
    route = Route(channel, namespaces=namespaces, tenants=tenants)

    # Assert values
    assert isinstance(route, Route)
    assert route.channel == channel
    assert len(route.namespaces) == len(namespaces)
    assert len(route.tenants) == len(tenants)

def test_matchs_namespaces(tenant1_prod_ns, tenant1_stage_ns, tenant1_dev_ns, tenant2_prod_ns, tenant2_stage_ns, tenant2_dev_ns):
    # Init objects
    route = Route(channel='#tenant1', namespaces=['tenant1-prod', 'tenant1-stage'])

    # Assert matches
    assert route.matches(tenant1_prod_ns) == True
    assert route.matches(tenant1_stage_ns) == True
    assert route.matches(tenant1_dev_ns) == False
    assert route.matches(tenant2_prod_ns) == False
    assert route.matches(tenant2_stage_ns) == False
    assert route.matches(tenant2_dev_ns) == False

def test_matches_namespaces_regex(tenant1_prod_ns, tenant1_stage_ns, tenant1_dev_ns, tenant2_prod_ns, tenant2_stage_ns, tenant2_dev_ns):
    # Init
    route = Route(channel='#tenant1', namespaces=['/tenant1-(prod|stage)/'])

    # Assertions
    assert route.matches(tenant1_prod_ns) == True
    assert route.matches(tenant1_stage_ns) == True
    assert route.matches(tenant1_dev_ns) == False
    assert route.matches(tenant2_prod_ns) == False
    assert route.matches(tenant2_stage_ns) == False
    assert route.matches(tenant2_dev_ns) == False

def test_matchs_tenants(tenant1_prod_ns, tenant1_stage_ns, tenant1_dev_ns, tenant2_prod_ns, tenant2_stage_ns, tenant2_dev_ns):

    # Init objects
    route = Route(channel='#tenant1', tenants=['tenant1'])

    # Assert matches
    assert route.matches(tenant1_prod_ns) == True
    assert route.matches(tenant1_stage_ns) == True
    assert route.matches(tenant1_dev_ns) == True
    assert route.matches(tenant2_prod_ns) == False
    assert route.matches(tenant2_stage_ns) == False
    assert route.matches(tenant2_dev_ns) == False

def test_check():
    # Check using literal string
    assert Route.check('string', 'string') == True
    assert Route.check('string', 'notastring') == False
    # Check using basic wildcard (*-only)
    assert Route.check('tenant-*', 'tenant-prod') == True
    assert Route.check('tenant-*', 'trout-prod') == False
    assert Route.check('tenant-*-watch', 'tenant-prod-watch') == True
    assert Route.check('tenant-*-watch', 'trout-prod-watch') == False
    assert Route.check('*-prod', 'tenant-prod') == True
    assert Route.check('*-prod', 'tenant-preprod') == False
    # Check using regex
    assert Route.check('/tenant-(prod|stage)/', 'tenant-prod') == True
    assert Route.check('/tenant-(prod|stage)/', 'tenant-stage') == True
    assert Route.check('tenant-(prod|stage)/', 'tenant-dev') == False
