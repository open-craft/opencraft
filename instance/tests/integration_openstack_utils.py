import os
import time
import unittest

from instance import openstack_utils
from instance.tests.base import TestCase

def skip_unless_auth_url_is_set():
    if 'OPENSTACK_REGION' not in os.environ:
        unittest.skip('no OPENSTACK_REGION environment variable')
    return lambda func: func

@skip_unless_auth_url_is_set()
class OpenStackIntegrationTestCase(TestCase):
    """Tests for OpenStack."""

    def setUp(self):
        self.c = openstack_utils.OpenStackClient(os.environ['OPENSTACK_REGION'])
        self.prefix = str(int(time.time()))
        self.known = self.prefix + '-ocim-xenial-16.04-unmodified'
        self.c.image2url = {
            self.known:
            'https://cloud-images.ubuntu.com/xenial/current/xenial-server-cloudimg-amd64-disk1.img',
        }

    def tearDown(self):
        if self.c.image_exists(self.known):
            self.c.openstack('image', 'delete', self.known)
        for f in os.listdir():
            if f.startswith(self.prefix):
                os.remove(f)
    
    def test_image_create(self):
        self.c.image_create(self.known)
        self.assertTrue(self.c.image_exists(self.known))
