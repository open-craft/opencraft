"""
Tasks user models
"""

#pylint: disable=no-init

from django.db import models
from django_extensions.db.models import TimeStampedModel

class Organization(TimeStampedModel):
    '''
    Organizations to which the users can belong, like companies
    '''
    name = models.CharField(max_length=100)

    class Meta:
        ordering = ('name',)

    def __str__(self):
        return self.name
