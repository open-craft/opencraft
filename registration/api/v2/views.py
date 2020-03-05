# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2019 OpenCraft <xavier@opencraft.com>
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
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
"""
Registration api views for API v2
"""
import logging

from django.conf import settings
from django.contrib.auth.models import User
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.generics import CreateAPIView, RetrieveDestroyAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from simple_email_confirmation.models import EmailAddress

from opencraft.swagger import (
    VALIDATION_AND_AUTH_RESPONSES,
    VALIDATION_RESPONSE,
    viewset_swagger_helper,
)
from registration.api.v2 import constants
from registration.api.v2.serializers import (
    AccountSerializer,
    OpenEdXInstanceConfigSerializer,
    OpenEdXInstanceConfigUpdateSerializer,
    OpenEdXInstanceDeploymentStatusSerializer,
    OpenEdXInstanceDeploymentCreateSerializer,
    ThemeSchemaSerializer,
)
from registration.models import BetaTestApplication
from registration.utils import verify_user_emails
from userprofile.models import UserProfile
from instance.schemas.theming import theme_schema_validate, DEFAULT_THEME


logger = logging.getLogger(__name__)


@viewset_swagger_helper(
    create="Create new user registration",
    list="Get current user registration data",
    update="Update current user registration data",
    partial_update="Update current user registration data",
    public_actions=["create"],
)
class AccountViewSet(CreateModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet):
    """
    User account management API.

    This API can be used to register users, and to access user registration
    information for the current user.
    """

    serializer_class = AccountSerializer
    lookup_field = "user__username"
    lookup_url_kwarg = "username"
    lookup_value_regex = "[^/]+"

    def perform_update(self, serializer):
        """
        When a new user registers, initiate email verification.
        """
        instance = serializer.save()
        verify_user_emails(instance.user, instance.user.email)

    def perform_create(self, serializer):
        """
        If a user updates their profile, initiate email verification in case their
        email has changed.
        """
        instance = serializer.save()
        verify_user_emails(instance.user, instance.user.email)

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "create":
            # Allow any user to create an account, but limit other actions to logged-in users.
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Get user profile objects restricted to the current user.
        Should be only one for regular users.
        """
        user: User = self.request.user
        if not user.is_authenticated:
            return UserProfile.objects.none()
        elif user.is_staff:
            return UserProfile.objects.all()
        else:
            return UserProfile.objects.filter(user=self.request.user)


@viewset_swagger_helper(
    list="Get all instances owned by user",
    create="Create new user instance.",
    retrieve="Get an instance owned by user",
    update="Update instance owned by user",
    partial_update="Update instance owned by user",
)
class OpenEdXInstanceConfigViewSet(
        CreateModelMixin, RetrieveModelMixin, UpdateModelMixin, ListModelMixin, GenericViewSet,
):
    """
    Open edX Instance Configuration API.

    This API can be used to manage the configuration for Open edX instances
    owned by clients.
    """

    serializer_class = OpenEdXInstanceConfigSerializer

    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        if self.action == "validate":
            # Allow validating instance configuration without an account
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    @swagger_auto_schema(
        responses={**VALIDATION_RESPONSE, 200: openapi.Response("Validation Successful"), },
        security=[],
    )
    @action(detail=False, methods=["post"])
    def validate(self, request):
        """
        Validate instance configuration

        This action is publicly accessible and allows any user to validate an instance
        configuration. It is useful when signing up.
        """
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        return Response(status=status.HTTP_200_OK)

    def perform_create(self, serializer):
        """
        When a new instance is registered queue its public contact email for verification.
        """
        instance = serializer.save()
        # Deploy default theme for users that just registered
        instance.draft_theme_config = DEFAULT_THEME
        instance.save()
        # Send verification emails
        verify_user_emails(instance.user, instance.public_contact_email)

    def perform_update(self, serializer):
        """
        If an instance has been changed, requests user to verify their new email
        if it has changed.
        """
        instance = serializer.save()
        verify_user_emails(instance.user, instance.public_contact_email)

    @swagger_auto_schema(request_body=OpenEdXInstanceConfigUpdateSerializer)
    def partial_update(self, request, *args, **kwargs):
        return super(OpenEdXInstanceConfigViewSet, self).partial_update(request, *args, **kwargs)

    @swagger_auto_schema(
        request_body=ThemeSchemaSerializer,
        responses={**VALIDATION_RESPONSE, 200: ThemeSchemaSerializer, },
    )
    @action(detail=True, methods=["patch"])
    def theme_config(self, request, pk=None):
        """
        Partial update for theme configuration

        This is a custom handler to partially update theme fields.
        """
        application = self.get_object()
        if not application.draft_theme_config:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "non_field_errors": "V1 theme isn't set up yet."
                }
            )

        # Sanitize inputs
        serializer = ThemeSchemaSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        # Merges the current aplication theme draft with the values modified by
        # the user and performs validation.
        # If the key is empty (""), the user reverted the field to the default
        # value, and the key needs to be erased.
        merged_theme = {
            key: value for key, value in {
                **application.draft_theme_config, **serializer.validated_data
            }.items() if value != ""
        }

        # To make sure the required values are always available, merge dict with
        # default values dictionary.
        safe_merged_theme = {
            **DEFAULT_THEME,
            **merged_theme
        }

        # TODO: Needs additional validation/filling up if button customization
        # is enabled to prevent the validation schema from failing

        # Perform validation, handle error if failed, and return updated
        # theme_config if succeeds.
        try:
            theme_schema_validate(safe_merged_theme)
        except JSONSchemaValidationError:
            # TODO: improve schema error feedback. Needs to be done along with
            # multiple fronend changes to allow individual fields feedback.
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    "non_field_errors": "Schema validation failed."
                }
            )

        application.draft_theme_config = safe_merged_theme
        application.save()

        return Response(status=status.HTTP_200_OK, data=application.draft_theme_config)

    def get_queryset(self):
        """
        Get `BetaTestApplication` instances owned by current user.
        For a regular user it should return a single object.
        """
        user: User = self.request.user
        if not user.is_authenticated:
            return BetaTestApplication.objects.none()
        elif user.is_staff:
            return BetaTestApplication.objects.all()
        else:
            return BetaTestApplication.objects.filter(user=self.request.user)


class OpenEdxInstanceDeploymentViewSet(CreateAPIView, RetrieveDestroyAPIView, GenericViewSet):
    """
    Open edX Instance Deployment API.

    This API can be used to manage the configuration for Open edX instances
    owned by clients.
    """
    serializer_class = OpenEdXInstanceDeploymentStatusSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Get `BetaTestApplication` instances owned by current user.
        For a regular user it should return a single object (for now).
        """
        user: User = self.request.user
        if not user.is_authenticated:
            return BetaTestApplication.objects.none()
        elif user.is_staff:
            return BetaTestApplication.objects.all()
        else:
            return BetaTestApplication.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OpenEdXInstanceDeploymentCreateSerializer

        return OpenEdXInstanceDeploymentStatusSerializer

    @swagger_auto_schema(
        responses={**VALIDATION_AND_AUTH_RESPONSES, 200: openapi.Response("Changes committed"), },
        manual_parameters=[
            openapi.Parameter(
                "force",
                openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description="Force launching a new instance even if one is already in progress.",
            )
        ],
    )
    def create(self, request, *args, **kwargs):
        """
        Commit configuration changes to instance and launch new AppServer.

        This API call will copy over any changes made to the instance config to
        the actual instance used to launch AppServers and launch a new AppServer
        with the applied changes.

        It checks if an AppServer is already being provisioned and in that
        case prevents a new one from being launched unless forced.
        """
        force = request.query_params.get("force", False)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            instance_config = BetaTestApplication.objects.get(id=serializer.data['id'])
        except BetaTestApplication.DoesNotExist:
            raise ValidationError(
                "The specified instance was not found.", code="instance-not-found",
            )

        instance = instance_config.instance
        if instance is None:
            # For a new user an instance will not exist until they've verified their email.
            raise ValidationError(
                "Must verify email before launching an instance", code="email-unverified",
            )

        if not force and instance.get_provisioning_appservers().exists():
            raise ValidationError("Instance launch already in progress", code="in-progress")

        if not EmailAddress.objects.get(email=instance_config.public_contact_email).is_confirmed:
            raise ValidationError(
                "Updated public email needs to be confirmed.", code="email-unverified"
            )

        instance_config.commit_changes_to_instance(
            spawn_on_commit=True,
            retry_attempts=settings.SELF_SERVICE_SPAWN_RETRY_ATTEMPTS,
        )

        return Response(status=status.HTTP_200_OK)

    def list(self, request, *args, **kwargs):
        """
        List method not allowed.
        """
        return Response(status=status.HTTP_405_METHOD_NOT_ALLOWED)

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieves the deployment status for a given betatest instance.

        This API will check for provisioning appservers or changes in settings
        that need to be deployed and return a status code to the frontend.
        """
        application = self.get_object()
        instance = application.instance
        deployment_status = constants.NO_STATUS

        # Get latest active appserver
        if not instance or not instance.get_active_appservers().exists():
            deployment_status = constants.PREPARING_INSTANCE
            num_changes = 0
        else:
            deployment_status = constants.UP_TO_DATE

            # Get number of undeployed changes
            num_changes = sum((
                application.instance_name != instance.name,
                application.privacy_policy_url != instance.privacy_policy_url,
                application.public_contact_email != instance.email,
                application.use_advanced_theme and application.draft_theme_config != instance.theme_config,
            ))

            if num_changes != 0:
                deployment_status = constants.PENDING_CHANGES

            # Check if there's any ongoing provisioning
            provisioning_appservers = instance.get_provisioning_appservers()
            if provisioning_appservers:
                # TODO: Differentiate between user deployments and OpenCraft deployments
                deployment_status = constants.DEPLOYING

        data = {
            'undeployed_changes': num_changes,
            'status': deployment_status,
        }

        return Response(
            status=status.HTTP_200_OK,
            data=OpenEdXInstanceDeploymentStatusSerializer(data).data
        )

    def destroy(self, request, *args, **kwargs):
        """
        Stops all current redeployments.

        This allows the user to cancel an ongoing deployment, note that this can
        can cancel both user-triggered deployments and OpenCraft triggered
        deployments.
        """
        application = self.get_object()
        instance = application.instance

        if not instance.get_active_appservers().exists():
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'details': "Can't cancel deployment while server is being prepared."
                }
            )
        # TODO: Prevent appservers provisioned by staff/redeployments to be cancelled

        provisioning_appservers = instance.get_provisioning_appservers()
        for appserver in provisioning_appservers:
            appserver.terminate_vm()

        return Response(status=status.HTTP_204_NO_CONTENT)
