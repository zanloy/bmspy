import copy
import unittest

#from .bmspy.objects import ObjectBase
from bmspy import *

base_ns = {
    'health': {
        'healthy': 'Unknown',
        'errors': [],
        'warnings': [],
        'alerts': [],
    },
    'kind': 'Namespace',
    'metadata': {
        'annotations': {
            'test.bmspy.io/anno1': 'value1',
        },
        'labels': {
            'test.bmspy.io/label1': 'value1',
        },
        'name': 'testing',
        'namespace': '',
    },
}

healthy_ns = copy.deepcopy(base_ns)
healthy_ns['health']['healthy'] = 'True'

unhealthy_ns = copy.deepcopy(base_ns)
unhealthy_ns['health']['healthy'] = 'False'
unhealthy_ns['health']['errors'] = ['Error #1']

warn_ns = copy.deepcopy(base_ns)
warn_ns['health']['healthy'] = 'Warn'
warn_ns['health']['warnings'] = ['Warning #1']

alert_ns = copy.deepcopy(base_ns)
alert_ns['health']['healthy'] = 'Alert'
alert_ns['health']['alerts'] = ['Alert #1']

unknown_ns = copy.deepcopy(base_ns)
unknown_ns['health']['healthy'] = 'Unknown'

class TestObjectBase(unittest.TestCase):
    def assertValues(self, subj: HealthUpdate, expected: dict):
        # annotations
        self.assertDictEqual(subj.annotations, expected['metadata']['annotations'])
        # labels
        self.assertDictEqual(subj.labels, expected['metadata']['labels'])
        # kind
        self.assertEqual(subj.kind, expected['kind'])
        # name
        self.assertEqual(subj.name, expected['metadata']['name'])
        # namespace
        self.assertEqual(subj.namespace, expected['metadata']['namespace'])

    def test_with_healthy_ns(self):
        subj = HealthUpdate(healthy_ns)
        self.assertValues(subj, healthy_ns)
        # healthy
        self.assertTrue(subj.healthy)
        # healthy_str
        self.assertEqual(subj.healthy_str, 'Healthy')

    def test_with_unhealthy_ns(self):
        subj = HealthUpdate(unhealthy_ns)
        self.assertValues(subj, unhealthy_ns)
        # healthy
        self.assertFalse(subj.healthy)
        # healthy_str
        self.assertEqual(subj.healthy_str, 'Unhealthy')
        # errors
        self.assertListEqual(subj.errors, unhealthy_ns['health']['errors'])
        # warnings
        self.assertListEqual(subj.warnings, unhealthy_ns['health']['warnings'])
        # alerts
        self.assertListEqual(subj.alerts, unhealthy_ns['health']['alerts'])

    def test_with_warn_ns(self):
        subj = HealthUpdate(warn_ns)
        self.assertValues(subj, warn_ns)
        # healthy
        self.assertTrue(subj.healthy)
        # healthy_str
        self.assertEqual(subj.healthy_str, 'Warning')
        # errors
        self.assertListEqual(subj.errors, warn_ns['health']['errors'])
        # warnings
        self.assertListEqual(subj.warnings, warn_ns['health']['warnings'])
        # alerts
        self.assertListEqual(subj.alerts, warn_ns['health']['alerts'])

    def test_with_alert_ns(self):
        subj = HealthUpdate(alert_ns)
        self.assertValues(subj, alert_ns)
        # healthy
        self.assertTrue(subj.healthy)
        # healthy_str
        self.assertEqual(subj.healthy_str, 'Alert')
        # errors
        self.assertListEqual(subj.errors, alert_ns['health']['errors'])
        # warnings
        self.assertListEqual(subj.warnings, alert_ns['health']['warnings'])
        # alerts
        self.assertListEqual(subj.alerts, alert_ns['health']['alerts'])

    def test_with_unknown_ns(self):
        subj = HealthUpdate(unknown_ns)
        self.assertValues(subj, unknown_ns)
        # healthy
        self.assertFalse(subj.healthy)
        # healthy_str
        self.assertEqual(subj.healthy_str, 'Unknown')

    def test_with_missing_health(self):
        obj = copy.deepcopy(healthy_ns)
        del(obj['health'])
        with self.assertRaises(KeyError):
            HealthUpdate(obj)

    def test_with_missing_kind(self):
        obj = copy.deepcopy(healthy_ns)
        del(obj['kind'])
        with self.assertRaises(KeyError):
            HealthUpdate(obj)

    def test_with_missing_metadata(self):
        obj = copy.deepcopy(healthy_ns)
        del(obj['metadata'])
        with self.assertRaises(KeyError):
            HealthUpdate(obj)

if __name__ == '__main__':
    unittest.main()
