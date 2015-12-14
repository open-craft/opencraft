"""Utilities to run the OpenCraft IM tests."""

import os
import unittest

from django.test.runner import DiscoverRunner


def shard(index):
    """Mark a test method as running only on a particular shard when running tests in parallel.

    This decorator sets an attribute on the function that is read by our customised test loader.
    Undecorated tests always run in shard 0.
    """
    def decorator(function):
        """The actual decorator."""
        function.shard = index
        return function
    return decorator


class ShardedTestLoader(unittest.TestLoader):
    """Load only the tests belonging to a particular shard.

    The constructor takes the arguments `node_index` and `node_total`, indicating the zero-based
    index of the current node and the total number of nodes.  Only tests that fulfil the condition

        test_shard % node_total == node_index

    are run, where test_shard is the shard a particular test is marked to run in.  Unannotated
    tests run in shard 0.
    """

    def __init__(self, node_index, node_total):
        super().__init__()
        self.node_index = node_index
        self.node_total = node_total

    def getTestCaseNames(self, test_case_class):  # nopep8
        """Only return the test cases that are supposed to run on the current shard."""
        method_names = super().getTestCaseNames(test_case_class)
        filtered_method_names = []
        for method_name in method_names:
            method = getattr(test_case_class, method_name)
            test_shard = getattr(method, 'shard', 0)
            if test_shard % self.node_total == self.node_index:
                filtered_method_names.append(method_name)
        return filtered_method_names


class CircleCIParallelTestRunner(DiscoverRunner):
    """Customization of Django's test runner for running tests in parallel on CircleCI.

    This test runner retrieves CircleCI node information from the environment and uses
    `ShardedTestLoader` to only run the tests meant for the current shard.
    """

    def __init__(self, *args, **kwargs):
        node_index = os.getenv('CIRCLE_NODE_INDEX')
        node_total = os.getenv('CIRCLE_NODE_TOTAL')
        if node_index is not None and node_total is not None:
            self.test_loader = ShardedTestLoader(int(node_index), int(node_total))
        super().__init__(*args, **kwargs)
