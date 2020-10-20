"""
Test model mixin utilities.
"""

import json
from unittest import TestCase

import ddt
from django.test.utils import override_settings

from instance.models.mixins.utilities import SensitiveDataFilter, get_ansible_failure_log_entry
from instance.tests.models.factories.openedx_instance import OpenEdXInstanceFactory
from instance.tests.models.factories.openedx_appserver import make_test_appserver


@ddt.ddt
class SensitiveDataFilterTestCase(TestCase):
    """
    Test sensitive data filtering context manager.
    """

    @ddt.data([
        list(),
        ["nothing", "to", "filter", "here"],
        ["nothing", {"to": {"filter", "here"}}],
        ["nothing", {"to": {"filter": ["here"]}}],
        ["nothing", ["to", ["filter", ["here"]]]],
        dict(),
        {"nothing": "to", "filter": "here"},
        {"nothing": {"to": {"filter": "here"}}},
        {"nothing": {"to": ["filter", ["here"]]}},
        {"nothing": {"to": {"filter": ["here"]}}},
        {"nothing": ["to", {"filter": "here"}]},
        {"nothing": ["to", {"filter": ["here"]}]},
        "",
        "nothing to filter here",
    ])
    def test_nothing_to_filter(self, data):
        """
        Test nothing is sensitive in the given data.
        """
        with SensitiveDataFilter(data) as filtered_data:
            self.assertEqual(data, filtered_data)

    @ddt.data(
        ("username:password", SensitiveDataFilter.FILTERED_TEXT),
        ("api-abc", SensitiveDataFilter.FILTERED_TEXT),
        ("api_abc", SensitiveDataFilter.FILTERED_TEXT),
        ("token-abc", SensitiveDataFilter.FILTERED_TEXT),
        ("token_abc", SensitiveDataFilter.FILTERED_TEXT),
        ("key-abc", SensitiveDataFilter.FILTERED_TEXT),
        ("key_abc", SensitiveDataFilter.FILTERED_TEXT),
        ("KeY_AbC_d", SensitiveDataFilter.FILTERED_TEXT),
        ("UPPERCASE_KEY", SensitiveDataFilter.FILTERED_TEXT),
    )
    @ddt.unpack
    def test_filter_plain_text(self, data, expected):
        """
        Test filtering for plain text data.
        """
        with SensitiveDataFilter(data) as filtered_data:
            self.assertEqual(filtered_data, expected)

    @ddt.data(
        (
            ["username:password"],
            [SensitiveDataFilter.FILTERED_TEXT]
        ),
        (
            [{"username": "test", "password": "topsecret"}],
            [{"username": "test", "password": SensitiveDataFilter.FILTERED_TEXT}]
        ),
        (
            [{"username": "test", "password": ["this won't be filtered"]}],
            [{"username": "test", "password": ["this won't be filtered"]}]  # not matching any plain text pattern
        ),
        (
            [{"data": {"password": "topsecret"}}],
            [{"data": {"password": SensitiveDataFilter.FILTERED_TEXT}}],
        ),
        (
            [{"data": {"password": ["this won't be filtered"]}}],
            [{"data": {"password": ["this won't be filtered"]}}],  # not matching any plain text pattern
        ),
        (
            [{"data": {"password": ["api-abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["api_abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["token-abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["token_abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["key-abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["key_abc"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
        (
            [{"data": {"password": ["user:pass", "some:pattern"]}}],
            [{"data": {"password": [SensitiveDataFilter.FILTERED_TEXT, SensitiveDataFilter.FILTERED_TEXT]}}],
        ),
    )
    @ddt.unpack
    def test_filter_list_data(self, data, expected):
        """
        Test filtering for list data.
        """
        with SensitiveDataFilter(data) as filtered_data:
            self.assertListEqual(filtered_data, expected)

    @ddt.data(
        (
            {"password": "topsecret"},
            {"password": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"nested": {"password": "topsecret"}},
            {"nested": {"password": SensitiveDataFilter.FILTERED_TEXT}},
        ),
        (
            {"nested": {"list": ["of", {"some": [{"password": "topsecret"}]}]}},
            {"nested": {"list": ["of", {"some": [{"password": SensitiveDataFilter.FILTERED_TEXT}]}]}},
        ),
        (
            {"api-abc": "topsecret"},
            {"api-abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"api_abc": "topsecret"},
            {"api_abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"token-abc": "topsecret"},
            {"token-abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"token_abc": "topsecret"},
            {"token_abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"key-abc": "topsecret"},
            {"key-abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"key_abc": "topsecret"},
            {"key_abc": SensitiveDataFilter.FILTERED_TEXT}
        ),
        (
            {"not_problematic": "topsecret"},
            {"not_problematic": SensitiveDataFilter.FILTERED_TEXT}
        ),
        # Complex data which is like an ansible output. Although most of the data is
        # filtered out, that's the behaviour what is expected. In case of a real ansible
        # output, the error lines will verbose and not contain that much text to filter out.
        (
            {
                "changed": False,
                "cmd": "/usr/bin/git checkout --force 1821396aee788eabe2ec4cb00f60879a3fde7d01",
                "msg": "Failed to checkout 1821396aee788eabe2ec4cb00f60879a3fde7d01",
                "rc": 128,
                "stderr": "fatal: tree: tree\npassword: abc\nmyuser:mypa$$word\naPiKey=123\nnot matching line",
                "stderr_lines": [
                    "fatal: reference is not a tree: tree",
                    "password: abc",
                    "myuser:mypa$$word",
                    "aPiKey=123",
                    "not matching line"
                ],
                "stdout": "",
                "stdout_lines": []
            },
            {
                "changed": False,
                "cmd": "/usr/bin/git checkout --force 1821396aee788eabe2ec4cb00f60879a3fde7d01",
                "msg": "Failed to checkout 1821396aee788eabe2ec4cb00f60879a3fde7d01",
                "rc": 128,
                # the following line is filtered completely, which is not an issue, since the error lines will
                # be listed line-by-line below; there is no better/safer way to keep the sensitive data in safe
                "stderr": SensitiveDataFilter.FILTERED_TEXT,
                "stderr_lines": [
                    SensitiveDataFilter.FILTERED_TEXT,
                    SensitiveDataFilter.FILTERED_TEXT,
                    SensitiveDataFilter.FILTERED_TEXT,
                    SensitiveDataFilter.FILTERED_TEXT,
                    "not matching line",
                ],
                "stdout": "",
                "stdout_lines": []
            },
        )
    )
    @ddt.unpack
    def test_filter_dict_data(self, data, expected):
        """
        Test filtering for dictionaries for various values and nested dictionaries.
        """
        self.maxDiff = None
        with SensitiveDataFilter(data) as filtered_data:
            self.assertDictEqual(filtered_data, expected)


class AnsibleLogExtractTestCase(TestCase):
    """
    Test extracting relevant failure ansible log entry from appserver logs.
    """

    def setUp(self):
        self.instance = OpenEdXInstanceFactory(name='test instance')
        self.appserver = make_test_appserver(
            instance=self.instance.appserver_set.first()
        )

    def test_no_entries_found(self):
        """
        Test when no log entries found, we return default values, so processing
        result can continue.
        """
        self.appserver.logger.info('Usual log message')
        self.appserver.logger.warning('A warning message')
        self.appserver.logger.error("Some error happened, but that's not Ansible related")
        self.appserver.logger.error("Other error message happened")

        task_name, log_entry = get_ansible_failure_log_entry(self.appserver.log_entries_queryset)

        self.assertEqual(task_name, "")
        self.assertDictEqual(log_entry, dict())

    def test_entry_found_without_task_name(self):
        """
        Test when entry found without task, the entry returned, but task name remains
        empty. This behaviour is expected, since the value is in the log entry not in the
        ansible task name.
        """
        expected_log_entry = {"changed": False, "other": True, "std_out": []}

        self.appserver.logger.info('Usual log message')
        self.appserver.logger.warning('A warning message')

        self.appserver.logger.info('fatal: [1.2.3.4]: FAILED! => {}'.format(
            json.dumps(expected_log_entry)
        ))

        self.appserver.logger.error("Some error happened, but that's not Ansible related")
        self.appserver.logger.error("Other error message happened")

        task_name, log_entry = get_ansible_failure_log_entry(self.appserver.log_entries_queryset)

        self.assertEqual(task_name, "")
        self.assertDictEqual(log_entry, expected_log_entry)

    def test_entry_and_task_name_found(self):
        """
        Test if we find both log entry and the belonging ansible task name, we return both.
        """
        expected_task_name = "task name"
        expected_log_entry = {"changed": False, "other": True, "std_out": []}

        self.appserver.logger.info('Usual log message')
        self.appserver.logger.warning('A warning message')

        self.appserver.logger.info(f'TASK [{expected_task_name}]')
        self.appserver.logger.info(f'fatal: [1.2.3.4]: FAILED! => {json.dumps(expected_log_entry)}')

        self.appserver.logger.error("Some error happened, but that's not Ansible related")
        self.appserver.logger.error("Other error message happened")

        task_name, log_entry = get_ansible_failure_log_entry(self.appserver.log_entries_queryset)

        self.assertEqual(task_name, expected_task_name)
        self.assertDictEqual(log_entry, expected_log_entry)

    @override_settings(LOG_LIMIT=2)
    def test_entry_and_task_name_not_found_within_the_log_limit(self):
        """
        Test that the log entries don't contain information past the cutoff point even if those
        entries might have matched otherwise, and it would result in the log being empty.
        """
        self.appserver.logger.info('TASK [task name]')
        self.appserver.logger.info('fatal: [1.2.3.4]: FAILED! => {"changed": true}')

        self.appserver.logger.error("Some error happened, but that's not Ansible related")
        self.appserver.logger.error("Other error message happened")

        task_name, log_entry = get_ansible_failure_log_entry(self.appserver.log_entries_queryset)

        self.assertEqual(task_name, "")
        self.assertDictEqual(log_entry, dict())
