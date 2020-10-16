from unittest import TestCase
import ddt

from instance.models.mixins.utilities import SensitiveDataFilter


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
    )
    @ddt.unpack
    def test_filter_plain_text(self, data, expected):
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
            [{"username": "test", "password": ["topsecret"]}],
            [{"username": "test", "password": ["topsecret"]}]  # topsecret is not matching any plain text pattern
        ),
        (
            [{"data": {"password": "topsecret"}}],
            [{"data": {"password": SensitiveDataFilter.FILTERED_TEXT}}],
        ),
        (
            [{"data": {"password": ["topsecret"]}}],
            [{"data": {"password": ["topsecret"]}}],  # topsecret is not matching any plain text pattern
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
    )
    @ddt.unpack
    def test_filter_list_data(self, data, expected):
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
    )
    @ddt.unpack
    def test_filter_dict_data(self, data, expected):
        with SensitiveDataFilter(data) as filtered_data:
            self.assertDictEqual(filtered_data, expected)
