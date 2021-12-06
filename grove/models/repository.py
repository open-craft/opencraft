# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2021 OpenCraft <contact@opencraft.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.
"""
The Grove deployment model.
"""

import logging

from django.conf import settings
from django.db import models
from django_extensions.db.models import TimeStampedModel

from instance.logging import ModelLoggerAdapter

logger = logging.getLogger(__name__)


def get_default_repository() -> "GroveClusterRepository":
    """
    Return the default Grove cluster repository.

    If the default repository does not exist, create the repo, and return that.
    """

    repository, _ = GroveClusterRepository.objects.get_or_create(
        name=settings.GROVE_DEFAULT_REPOSITORY_NAME,
        project_id=settings.GROVE_DEFAULT_REPOSITORY_PROJECT_ID,
        unleash_instance_id=settings.GROVE_DEFAULT_REPOSITORY_UNLEASH_INSTANCE_ID,
        git_ref=settings.GROVE_DEFAULT_REPOSITORY_GIT_REF,
        trigger_token=settings.GROVE_DEFAULT_REPOSITORY_TRIGGER_TOKEN,
    )

    return repository


class GroveClusterRepository(TimeStampedModel):
    """
    GroveClusterRepository model stores the configuration of Grove projects.

    When a Grove project is managed by the Console Backend, the backend must
    know its project ID and trigger token to call the appropriate GitLab CI
    pipeline on deployment.
    """

    name = models.CharField(
        max_length=255,
        unique=True,
        help_text="Descriptive name of the repository. E.g. P&T clients."
    )
    project_id = models.PositiveIntegerField(
        unique=True,
        help_text="GitLab project ID of the repository."
    )
    unleash_instance_id = models.CharField(
        max_length=255,
        help_text="Instance ID of the unleash setup, obtained from GitLab.",
    )
    git_ref = models.CharField(
        max_length=255,
        help_text="Git branch or tag on the repository to use when triggering pipelines.",
    )
    trigger_token = models.CharField(
        max_length=255,
        help_text="GitLab token used to trigger pipeline builds."
    )

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Grove cluster repositories"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = ModelLoggerAdapter(logger, {'obj': self})

    def __str__(self):
        return f"{self.name} ({self.project_id})"
