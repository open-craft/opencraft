from swampdragon import route_handler
from swampdragon.route_handler import BaseRouter


class NotificationRouter(BaseRouter): #pylint: disable=abstract-method
    route_name = 'notifier'

    def get_subscription_channels(self, **kwargs):
        return ['notification', 'log']


route_handler.register(NotificationRouter)
