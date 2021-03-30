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
import random
import string
from string import Template

from django.db import transaction
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from drf_yasg import openapi
from drf_yasg.utils import swagger_auto_schema
from jsonschema.exceptions import ValidationError as JSONSchemaValidationError
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.mixins import (
    CreateModelMixin,
    ListModelMixin,
    RetrieveModelMixin,
    UpdateModelMixin,
)
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from simple_email_confirmation.models import EmailAddress

from instance.models.deployment import DeploymentType
from instance.models.openedx_deployment import DeploymentState, OpenEdXDeployment
from instance.schemas.static_content_overrides import (
    DEFAULT_STATIC_CONTENT_OVERRIDES,
    fill_default_hero_text,
    static_content_overrides_schema_validate,
)
from instance.schemas.theming import DEFAULT_THEME, theme_schema_validate
from instance.utils import build_instance_config_diff
from opencraft.swagger import (
    VALIDATION_AND_AUTH_RESPONSES,
    VALIDATION_RESPONSE,
    viewset_swagger_helper,
)
from registration.api.v2.serializers import (
    AccountSerializer, ApplicationImageUploadSerializer, OpenEdXInstanceConfigSerializer,
    OpenEdXInstanceConfigUpdateSerializer, OpenEdXInstanceDeploymentCreateSerializer,
    OpenEdXInstanceDeploymentNotificationSerializer, OpenEdXInstanceDeploymentStatusSerializer,
    StaticContentOverridesSerializer, ThemeSchemaSerializer,
    ToggleStaticContentPagesSerializer,
    DisplayStaticContentPagesSerializer,
    PasswordChangeSerializer, UserDetailSerializer,
)
from registration.models import BetaTestApplication
from registration.utils import verify_user_emails
from userprofile.models import UserProfile

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
    extra_serializer_classes = {
        "password_change": PasswordChangeSerializer,
        "update_details": UserDetailSerializer,
    }

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

    def get_serializer_class(self):
        serializer_class = self.extra_serializer_classes.get(self.action)
        if serializer_class is None:
            serializer_class = super().get_serializer_class()

        return serializer_class

    @swagger_auto_schema(
        request_body=PasswordChangeSerializer,
        responses={**VALIDATION_RESPONSE, 200: PasswordChangeSerializer, },
    )
    @action(detail=True, methods=["patch"])
    def password_change(self, request, username=None):
        """
        Change the user password
        """
        user = request.user
        serializer = self.get_serializer(instance=user, data=request.data)
        serializer.is_valid(raise_exception=True)
        new_password = serializer.validated_data['user']['password']
        user.set_password(new_password)
        user.save()
        return Response({"ok": True})

    @swagger_auto_schema(
        request_body=UserDetailSerializer,
        responses={**VALIDATION_RESPONSE, 200: UserDetailSerializer, },
    )
    @action(detail=True, methods=["patch"])
    def update_details(self, request, username=None):
        """
        Get the user details from the request and update the profile accordingly
        """
        profile = self.get_object()
        serializer = self.get_serializer(instance=profile, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class NotificationsViewSet(GenericViewSet):
    """
    Notifications API.

    For now, can retrieve notifications based on Open edX Instance Deployments status.
    """

    serializer_class = OpenEdXInstanceDeploymentNotificationSerializer
    permission_classes = [IsAuthenticated]

    def get_application(self):
        """
        Get latest `BetaTestApplication` instance owned by current user.
        """

        user = self.request.user

        applications = BetaTestApplication.objects.select_related('instance')

        if user.is_staff:
            applications = applications.all()
        else:
            applications = applications.filter(user=self.request.user)

        return applications.latest('created')

    def limit_queryset(self, queryset):
        """
        Limits given queryset if ``limit`` query param passed.
        """

        notifications_limit = self.request.query_params.get('limit')
        if notifications_limit is not None:
            try:
                notifications_limit = int(notifications_limit)
            except ValueError:
                raise ParseError("Notifications limit must be integer.")

            if notifications_limit < 0:
                raise ParseError("Notifications limit can't be negative.")

            return queryset[:notifications_limit]

        return queryset

    def get_queryset(self, application=None): # pylint: disable=arguments-differ
        if application is None:
            application = self.get_application()

        instance = application.instance
        if instance is None:
            return OpenEdXDeployment.objects.none()

        queryset = OpenEdXDeployment.objects.filter(
            instance=instance.ref
        )

        return self.limit_queryset(queryset)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter(
                "limit",
                openapi.IN_QUERY,
                type=openapi.TYPE_INTEGER,
                description="How many notifications should be fetched.",
            )
        ]
    )
    def list(self, request, *args, **kwargs):
        """
        Returns Open edX deployments information in form of status notifications.

        If there is no deployments at all, this endpoint returns blank notification,
        that deployment is preparing.
        """

        application = self.get_application()
        deployments = self.get_queryset(application)

        undeployed_changes = build_instance_config_diff(application)

        notifications = []
        for deployment in deployments:
            deployment_status = deployment.status()
            notifications.append({
                "deployed_changes": deployment.changes or [],
                "status": deployment_status.name,
                "date": deployment.created,
            })

        if not notifications:
            notifications.append({
                "deployed_changes": [],
                "status": DeploymentState.preparing.name,
                "date": application.created,
            })

        # Configuration diff relates only to last created deployment, so if
        # last deployment is healthy and diff is not empty,
        # we manually change its status.
        last_notification = notifications[0]
        if last_notification['status'] == DeploymentState.healthy.name:
            undeployed_changes = build_instance_config_diff(application)
            if undeployed_changes:
                last_notification['status'] = DeploymentState.changes_pending

        return Response(
            status=status.HTTP_200_OK,
            data=OpenEdXInstanceDeploymentNotificationSerializer(
                notifications, many=True
            ).data
        )


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

    def create(self, request, *args, **kwargs):
        """
        Checks if user is creating account with external domain and fill subdomain slug.

        This check if `external_domain` is filled, if so, generate a valid subdomain slug
        and fill in the field before passing it to the serializer.

        Checks if public contact email is empty or not, if empty override it with user mail
        """
        external_domain = request.data.get('external_domain')
        if external_domain:
            # Create a valid slug with this format: `<domain-slug>-<random-hash>`
            # Hash is added to avoid name clashes when generating slug
            random_hash = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
            subdomain = f"{slugify(external_domain)[:30]}-{random_hash}"
            # Set request data
            self.request.data.update({
                "subdomain": subdomain
            })

        public_contact_email = request.data.get('public_contact_email')
        if not public_contact_email:
            self.request.data.update({
                "public_contact_email": request.user.email
            })

        # Perform create as usual
        return super(OpenEdXInstanceConfigViewSet, self).create(request, *args, **kwargs)

    def perform_create(self, serializer):
        """
        When a new instance is registered queue its public contact email for verification.
        """

        instance = serializer.save()
        # Deploy default theme for users that just registered
        instance.draft_theme_config = DEFAULT_THEME
        if not instance.draft_static_content_overrides:
            static_content_overrides = DEFAULT_STATIC_CONTENT_OVERRIDES.copy()
            static_content_overrides['homepage_overlay_html'] = Template(
                static_content_overrides['homepage_overlay_html']
            ).safe_substitute(
                instance_name=instance.instance_name
            )
            instance.draft_static_content_overrides = static_content_overrides
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
        TODO: Improve behavior consistency when returning. Instead of setting
        the default value when a required variable is sent empty, error out.
        And to allow reverting back to a default value, add support for a
        `default` keyword to enable the frontend to revert values to the default
        theme colors. Examples:
        PATCH: {"main-color": ""} should error out.
        PATCH" {"main-color": "default"} should revert to the default theme
        base color.
        """
        with transaction.atomic():
            application = BetaTestApplication.objects.select_for_update().get(id=pk)
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

            # Merges the current application theme draft with the values modified by
            # the user and performs validation.
            # If the key is empty (""), the user reverted the field to the default
            # value, and the key needs to be erased.
            merged_theme = {
                key: value for key, value in {
                    **application.draft_theme_config, **serializer.validated_data
                }.items() if value
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
                # multiple frontend changes to allow individual fields feedback.
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        "non_field_errors": "Schema validation failed."
                    }
                )

            application.draft_theme_config = safe_merged_theme
            application.save()

            return Response(status=status.HTTP_200_OK, data=application.draft_theme_config)

    @action(
        detail=True,
        methods=['post'],
        parser_classes=(MultiPartParser,),
        serializer_class=ApplicationImageUploadSerializer
    )
    def image(self, request, pk: str):
        """
        Endpoint for saving favicon or logo images

        Send a POST to action image/ with the file in the `logo` or `favicon`
        field to add or update it.
        """
        application = self.get_object()
        try:
            if 'favicon' in request.data:
                application.favicon = request.data['favicon']
                application.save()

            if 'logo' in request.data:
                application.logo = request.data['logo']
                application.save()

            if 'hero_cover_image' in request.data:
                application.hero_cover_image = request.data['hero_cover_image']
                application.save()

        except Exception as e:  # pylint: disable=broad-except
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data=dict(e)
            )

        return Response(
            status=status.HTTP_200_OK,
            data=ApplicationImageUploadSerializer(
                application,
                context={'request': request}
            ).data
        )

    @swagger_auto_schema(
        request_body=StaticContentOverridesSerializer,
        responses={**VALIDATION_RESPONSE, 200: StaticContentOverridesSerializer},
    )
    @action(detail=True, methods=["patch"])
    def static_content_overrides(self, request, pk=None):
        """
        Partial update for static content overrides configuration
        """
        with transaction.atomic():
            application = BetaTestApplication.objects.select_for_update().get(id=pk)
            serializer = StaticContentOverridesSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=400)

            if not application.draft_static_content_overrides:
                application.draft_static_content_overrides = DEFAULT_STATIC_CONTENT_OVERRIDES

            merged_values = {
                key: value for key, value in {
                    **application.draft_static_content_overrides, **serializer.validated_data
                }.items()}

            if 'homepage_overlay_html' not in merged_values:
                current_value = ''
            else:
                current_value = merged_values['homepage_overlay_html']

            merged_values['homepage_overlay_html'] = Template(
                fill_default_hero_text(
                    current_value
                )
            ).safe_substitute(instance_name=application.instance_name)

            try:
                static_content_overrides_schema_validate(merged_values)
            except JSONSchemaValidationError:
                return Response(
                    status=status.HTTP_400_BAD_REQUEST,
                    data={
                        'non_field_errors': "Schema validation failed."
                    }
                )
            application.draft_static_content_overrides = merged_values
            application.save()

            return Response(status=status.HTTP_200_OK, data=application.draft_static_content_overrides)

    @swagger_auto_schema(
        request_body=ToggleStaticContentPagesSerializer,
        responses={**VALIDATION_RESPONSE, 200: DisplayStaticContentPagesSerializer},
    )
    @action(detail=True, methods=["post"])
    def toggle_static_content_page(self, request, pk=None):
        """
        Enable/Disable static page.
        """
        application = BetaTestApplication.objects.get(id=pk)
        serializer = ToggleStaticContentPagesSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        page_name = serializer.data['page_name']
        if not application.configuration_display_static_pages:
            application.configuration_display_static_pages = {}

        application.configuration_display_static_pages[page_name] = serializer.data['enabled']
        application.save()
        return Response(
            status=status.HTTP_200_OK,
            data=application.configuration_display_static_pages
        )

    def list(self, request, *args, **kwargs):
        """
        Endpoint for getting the list of instances owned by the current user.

        If the user is staff, return a 400 error. This is used by the frontend to prevent
        staff users from accidentally accessing and updating other users' instances (see SE-2865).
        """
        if request.user.is_staff:
            return Response(
                status=status.HTTP_400_BAD_REQUEST,
                data={
                    'code': 'NOT_ACCESSIBLE_TO_STAFF',
                    'details': "Not allowed for staff users"
                }
            )
        return super(OpenEdXInstanceConfigViewSet, self).list(request, *args, **kwargs)

    def get_queryset(self):
        """
        Get `BetaTestApplication` instances owned by current user.
        For a regular user it should return a single object.
        """
        user: User = self.request.user
        if not user.is_authenticated:
            return BetaTestApplication.objects.none()
        elif user.is_staff:
            return BetaTestApplication.objects.all().select_related("instance")
        else:
            return BetaTestApplication.objects.filter(
                user=self.request.user
            ).select_related("instance")


class OpenEdxInstanceDeploymentViewSet(GenericViewSet):
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
        queryset = BetaTestApplication.objects.select_related("instance")

        if not user.is_authenticated:
            return queryset.none()
        elif user.is_staff:
            return queryset.all()
        else:
            return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == "create":
            return OpenEdXInstanceDeploymentCreateSerializer

        return OpenEdXInstanceDeploymentStatusSerializer

    @swagger_auto_schema(
        responses={**VALIDATION_AND_AUTH_RESPONSES, 200: openapi.Response("Changes committed"), },
        manual_parameters=[
            openapi.Parameter(
                "cancel_pending_deployments",
                openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description="Cancel any deployments which might have been pending, and start a new one.",
            ),
            openapi.Parameter(
                "force",
                openapi.IN_QUERY,
                type=openapi.TYPE_BOOLEAN,
                description="Force launching a new instance even if one is already in progress.",
            ),
            openapi.Parameter(
                "deployment_type",
                openapi.IN_QUERY,
                type=openapi.TYPE_STRING,
                enum=DeploymentType.names(),
                description="The type of deployment being initiated.",
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
        cancel_pending_deployments = request.query_params.get("cancel_pending_deployments", False)
        if self.request.user.is_superuser:
            default_deployment_type = DeploymentType.admin.name
        else:
            default_deployment_type = DeploymentType.user.name
        # Allow overriding trigger in case deployment is created by API in some other way.
        deployment_type = request.query_params.get("deployment_type", default_deployment_type)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance_config = self.commit_pre_flight(serializer, cancel_pending_deployments, force)

        instance_config.commit_changes_to_instance(
            deploy_on_commit=True,
            retry_attempts=settings.SELF_SERVICE_SPAWN_RETRY_ATTEMPTS,
            creator=self.request.user,
            deployment_type=deployment_type,
            cancel_pending_deployments=cancel_pending_deployments
        )

        return Response(status=status.HTTP_200_OK)

    def commit_pre_flight(self, serializer, cancel_pending_deployments, force):
        """
        Completes several pre-flight sanity checks and then returns an instance configuration for commit.
        """
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

        deployment = instance.get_latest_deployment()
        if deployment and deployment.status() == DeploymentState.preparing:
            raise ValidationError(
                'You must wait for your initial instance to finish building.', code='first-build-incomplete',
            )

        if not cancel_pending_deployments and not force and instance.get_provisioning_appservers().exists():
            raise ValidationError("Instance launch already in progress", code="in-progress")

        if not EmailAddress.objects.get(email=instance_config.public_contact_email).is_confirmed:
            raise ValidationError(
                "Updated public email needs to be confirmed.", code="email-unverified"
            )

        if not instance.successfully_provisioned:
            raise ValidationError(
                'You must wait for a successful deployment before attempting another one.',
                code='no-successful-deployment',
            )

        return instance_config

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
        undeployed_changes = build_instance_config_diff(application)
        deployed_changes = None
        deployment_type = None

        if (not instance or
                not instance.get_latest_deployment() or
                not instance.successfully_provisioned):
            # Set to preparing if no existing deployments or provisioned appservers found
            deployment_status = DeploymentState.preparing
        else:
            deployment = instance.get_latest_deployment()
            deployment_status = deployment.status()
            if deployment_status == DeploymentState.healthy and undeployed_changes:
                deployment_status = DeploymentState.changes_pending
            deployment_type = deployment.type
            deployed_changes = deployment.changes

        data = {
            'undeployed_changes': undeployed_changes,
            'deployed_changes': deployed_changes,
            'status': deployment_status.name,
            'deployment_type': deployment_type,
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
        deployment = instance.get_latest_deployment()

        if deployment.type != DeploymentType.user.name:
            return Response(
                status=status.HTTP_403_FORBIDDEN,
                data={
                    'details': "Can't cancel deployment not manually initiated by user."
                }
            )

        deployment.cancel_deployment()
        return Response(status=status.HTTP_204_NO_CONTENT)
