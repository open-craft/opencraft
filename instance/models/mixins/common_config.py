"""
Instance app model mixins - Common Configuration
"""

# Imports #####################################################################

from django.db import models
from django.conf import settings


# Classes #####################################################################

class ConfigMixinBase(models.Model):
    """
    Returns common configuration variables.

    Can be used by configuration management tools like Ansible to be turned into YML and used by a Playbook.
    """

    class Meta:
        abstract = True

    def _get_common_configuration_variables(self):
        """
        Retrieve all common configuration variables.
        """
        return {
            **self._get_prometheus_variables(),
            **self._get_consul_variables(),
            **self._get_filebeat_variables(),
        }

    def _get_prometheus_variables(self):  # pylint: disable=no-self-use
        """Get all Prometheus-related ansible variables."""
        return {
            'NODE_EXPORTER_PASSWORD': settings.NODE_EXPORTER_PASSWORD
        }

    def _get_consul_variables(self):  # pylint: disable=no-self-use
        """Get all Consul-related ansible variables."""
        return {
            'consul_encrypt': settings.CONSUL_ENCRYPT,
            'consul_servers': settings.CONSUL_SERVERS,
        }

    def _get_filebeat_variables(self):  # pylint: disable=no-self-use
        """Get all Filebeat-related ansible variables."""
        return {
            'filebeat_logstash_hosts': settings.FILEBEAT_LOGSTASH_HOSTS,
            'filebeat_ca_cert': settings.FILEBEAT_CA_CERT,
            'filebeat_cert': settings.FILEBEAT_CERT,
            'filebeat_key': settings.FILEBEAT_KEY,
            'filebeat_common_prospector_fields': settings.FILEBEAT_COMMON_PROSPECTOR_FIELDS,
        }
