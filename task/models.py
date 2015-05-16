"""
Tasks app models
"""

#pylint: disable=no-init

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class Task(TimeStampedModel, TitleSlugDescriptionModel):
    '''
    A task requested by a client
    '''

    def __str__(self):
        return self.title
