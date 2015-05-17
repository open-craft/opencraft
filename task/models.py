"""
Tasks app models
"""
#pylint: disable=no-init


# Imports #####################################################################

from django.db import models
from django_extensions.db.models import TimeStampedModel, TitleSlugDescriptionModel

from user.models import Organization


# Models ######################################################################

class Project(TimeStampedModel, TitleSlugDescriptionModel):
    '''
    Client project
    '''
    organization = models.ForeignKey(Organization)

    def __str__(self):
        return self.title

class Task(TimeStampedModel, TitleSlugDescriptionModel):
    '''
    Task requested by a client
    '''
    project = models.ForeignKey(Project)

    def __str__(self):
        return self.title
