"""
Factories related to RabbitMQ.
"""
import factory
import factory.django as django_factory

from instance.models.redis_server import RedisServer


class RedisServerFactory(django_factory.DjangoModelFactory):
    """
    Factory for RabbitMQServer.
    """

    class Meta:
        model = RedisServer

    name = factory.Sequence(lambda n: f"Redis {n}")
    admin_username = "admin"
    admin_password = "admin"

    instance_host = factory.Sequence(lambda n: f"redis-{n}.test")
    instance_port = 6379
    instance_db = 0

    use_ssl_connections = False
