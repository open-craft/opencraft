from django.forms import Textarea
from django.core.serializers.json import DjangoJSONEncoder


class JSONWidget(Textarea):
    def render(self, name, value, attrs=None):
        if not isinstance(value, str):
            value = DjangoJSONEncoder().encode(value)
        return super(JSONWidget, self).render(name, value, attrs)
