# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2018 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Tests for the nomad_client module.
"""

import json
from unittest.mock import patch

import requests

from instance import nomad_client
from instance.tests.base import TestCase


class TestNomadClient(TestCase):
    """Tests for the NomadClient class."""

    def setUp(self):
        self.jobspec = {
            "ID": "job-1",
            "TaskGroups": [
                {"Name": "group-1", "Count": 2},
                {"Name": "group-2", "Count": 3},
            ]
        }
        self.job = nomad_client.NomadJob(self.jobspec)

    # I tried to use the "responses" module to mock requests, but it doesn't seem to be able to
    # verify the certificate parameters, and doesn't really provide advantages for this particular
    # use case.
    @patch("requests.request")
    def test_run(self, mock_request):
        """Test that the run() method makes the correct REST request."""
        self.job.run()
        mock_request.assert_called_once_with(
            "post",
            "https://nomad.example.com:4646/v1/jobs",
            verify="path/to/ca.pem",
            cert=("path/to/cert.pem", "path/to/key.pem"),
            timeout=15,
            json={"Job": self.jobspec},
        )

    @patch("requests.request")
    def test_stop(self, mock_request):
        """Test that the stop() method makes the correct REST request."""
        self.job.stop()
        mock_request.assert_called_once_with(
            "delete",
            "https://nomad.example.com:4646/v1/job/job-1",
            verify="path/to/ca.pem",
            cert=("path/to/cert.pem", "path/to/key.pem"),
            timeout=15,
        )

    def fake_summary_response(self, status_code, summary):  # pylint: disable=no-self-use
        """Return a Response object wrapping a job summary as returned by the Nomad API."""
        response = requests.Response()
        response.status_code = status_code
        response.encoding = "utf-8"
        for group in summary.values():
            for key in ["Complete", "Failed", "Lost", "Queued", "Running", "Starting"]:
                group.setdefault(key, 0)
        response_json = {
            "JobID": "job-1",
            "Namespace": "default",
            "Summary": summary,
        }
        response._content = json.dumps(response_json).encode()
        return response

    def verify_all_running(self, mock_request, summary, expected):
        """Helper function to test the all_running() method."""
        mock_request.return_value = self.fake_summary_response(200, summary)
        self.assertEqual(self.job.all_running(), expected)
        mock_request.assert_called_once_with(
            "get",
            "https://nomad.example.com:4646/v1/job/job-1/summary",
            verify="path/to/ca.pem",
            cert=("path/to/cert.pem", "path/to/key.pem"),
            timeout=15,
        )

    @patch("requests.request")
    def test_all_running_true(self, mock_request):
        """Ensure that all_running() returns True if the right number of instances is running."""
        summary = {
            "group-1": {"Running": 2},
            "group-2": {"Running": 3},
        }
        self.verify_all_running(mock_request, summary, True)

    @patch("requests.request")
    def test_all_running_false(self, mock_request):
        """Ensure that all_running() returns False if not all tasks have started."""
        summary = {
            "group-1": {"Running": 2},
            "group-2": {"Running": 2, "Starting": 1},
        }
        self.verify_all_running(mock_request, summary, False)

    @patch("requests.request")
    def test_all_running_no_job(self, mock_request):
        """Ensure that all_running() returns False if the job does not exist on Nomad."""
        mock_request.return_value = self.fake_summary_response(404, {})
        self.assertFalse(self.job.all_running())
