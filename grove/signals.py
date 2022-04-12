"""
Signals for Grove app to deploy new instances through signals.
"""

import logging
from grove.models.deployment import GroveDeployment
from grove.models.gitlabpipeline import GitlabPipeline

from django.db.models.signals import post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_save, sender=GroveDeployment)
def create_new_deployment_pipeline(sender, instance, created, **kwargs):
    """
    Create a new pipeline for deployment when the deployment object is created.
    """
    if not created:
        return

    new_pipeline = GitlabPipeline.objects.create(instance=instance.instance.instance.ref)
    instance.pipeline = new_pipeline
    instance.save()

    logger.info('Triggering deployment for %s!', len(instance.instance.name))
    instance.trigger_pipeline()
