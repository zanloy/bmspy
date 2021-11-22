import pytest

from bmspy import Route

@pytest.mark.asyncio
async def test_simple_ns(test_router, tenant1_prod_ns, tenant1_stage_ns, tenant1_dev_ns, tenant2_prod_ns, tenant2_stage_ns, tenant2_dev_ns):
    route = Route(channel = '#tenant1', namespaces = ['tenant1-prod', 'tenant1-stage'])
    test_router.add_route(route)
    await test_router.process_msg(tenant1_prod_ns)
    await test_router.process_msg(tenant1_stage_ns)
    await test_router.process_msg(tenant1_dev_ns)
    await test_router.process_msg(tenant2_prod_ns)
    await test_router.process_msg(tenant2_stage_ns)
    await test_router.process_msg(tenant2_dev_ns)
    messages = test_router.slackbot.messages

    # Assertions
    assert len(messages) == 2
    assert messages[0]['channel'] == '#tenant1'
    assert messages[1]['channel'] == '#tenant1'

@pytest.mark.asyncio
async def test_regex_ns(test_router, tenant1_prod_ns, tenant1_stage_ns, tenant1_dev_ns, tenant2_prod_ns, tenant2_stage_ns, tenant2_dev_ns):
    route = Route(channel = '#tenant1', namespaces = ['/tenant1-(prod|stage)/'])
    test_router.add_route(route)
    await test_router.process_msg(tenant1_prod_ns)
    await test_router.process_msg(tenant1_stage_ns)
    await test_router.process_msg(tenant1_dev_ns)
    await test_router.process_msg(tenant2_prod_ns)
    await test_router.process_msg(tenant2_stage_ns)
    await test_router.process_msg(tenant2_dev_ns)
    messages = test_router.slackbot.messages

    # Assertions
    assert len(messages) == 2
    assert messages[0]['channel'] == '#tenant1'
    assert messages[1]['channel'] == '#tenant1'
