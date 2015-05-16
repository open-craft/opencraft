"""
Tasks app models
"""

#pylint: disable=no-init

from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

class Task(TimeStampedModel, TitleSlugDescriptionModel):
    pass
