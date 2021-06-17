"""
Factories related to RabbitMQ.
"""
import factory
import factory.django as django_factory

from instance.models.rabbitmq_server import RabbitMQServer

class RabbitMQServerFactory(django_factory.DjangoModelFactory):
    """
    Factory for RabbitMQServer.
    """

    class Meta:
        model = RabbitMQServer

    name = factory.Sequence(lambda n: f"RabbitMQ {n}")
    admin_username = "admin"
    admin_password = "admin"
    instance_host = factory.Sequence(lambda n: f"rabbitmq-{n}.test")
    api_url = factory.LazyAttribute(lambda o: f"https://{o.instance_host}/api")
