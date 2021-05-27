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
Serializers for registration API.
"""
from typing import Dict

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from instance.models.deployment import DeploymentType
from instance.models.openedx_deployment import DeploymentState
from instance.schemas.static_content_overrides import static_content_overrides_v0_schema
from instance.schemas.theming import theme_schema_v1
from instance.schemas.utils import ref
from registration.models import (
    BetaTestApplication,
    DNSConfigState,
    validate_available_subdomain,
    validate_available_external_domain
)
from registration.tasks import verify_external_domain_configuration
from userprofile.models import UserProfile


class DataSerializer(serializers.Serializer):
    """
    Serializer for data that does not need to be persisted directly.
    Inherit from it to avoid needing to disable abstract-method warnings.
    """

    def create(self, validated_data):
        pass

    def update(self, instance, validated_data):
        pass


class GenericObjectSerializer(DataSerializer):
    """
    Serializer for any response that returns a JSON dict, without specifying
    the fields of that dict in detail.
    """

    def to_representation(self, instance):
        return instance

    def to_internal_value(self, data):
        return data

    class Meta:
        swagger_schema_fields = {
            "type": "object",
            "additionalProperties": True,
        }


class ApplicationImageUploadSerializer(DataSerializer):
    """
    Serializer for images to be uploaded for an application.
    """
    logo = serializers.ImageField(required=False, use_url=True)
    favicon = serializers.ImageField(required=False, use_url=True)
    hero_cover_image = serializers.ImageField(required=False, use_url=True)


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for User account information.
    """

    username = serializers.CharField(
        source="user.username",
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="This username is not available."),
            RegexValidator(
                r"^[\w.+-]+$",
                message="Usernames may contain only letters, numbers, and ./+/-/_ characters.",
            ),
        ],
        help_text=(
            "This would also be the username of the administrator account on the users's instances."
        ),
    )
    email = serializers.EmailField(
        source="user.email",
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is already registered with a different account.",
            ),
        ],
        required=True,
        help_text="This is also the account name, and where we will send important notices.",
    )
    password = serializers.CharField(
        source="user.password",
        required=True,
        write_only=True,
        style={"input_type": "password"},
        validators=[validate_password],
        help_text="A password for the OpenCraft account.",
    )

    def create(self, validated_data: Dict) -> UserProfile:
        """
        Create a new user profile and user instance from serialised data.
        """
        new_user = User.objects.create_user(**validated_data.pop("user"))
        new_user_profile = UserProfile.objects.create(**validated_data, user=new_user)
        return new_user_profile

    def _update_user_account(self, user: User, user_data: Dict):
        """
        Update user from validated data.
        """
        # Can't change username, so remove it if present
        user_data.pop("username", None)
        user_updated = False
        if "password" in user_data:
            user.set_password(user_data.pop("password"))
            user_updated = True
        if "email" in user_data:
            user.email = user_data.pop("email")
            user_updated = True
        if user_updated:
            user.save()

    def _update_user_profile(self, user_profile: UserProfile, profile_data: Dict):
        """
        Update user profile from validated data.
        """
        profile_updated = False
        for key, new_val in profile_data.items():
            current_val = getattr(user_profile, key)
            if new_val != current_val:
                setattr(user_profile, key, new_val)
                profile_updated = True
        if profile_updated:
            user_profile.save()

    def update(self, instance, validated_data):
        """
        Update existing user profile model and user.
        """
        self._update_user_account(instance.user, validated_data.pop("user", {}))
        self._update_user_profile(instance, validated_data)
        return instance

    def validate_accepted_privacy_policy(self, value):
        """
        Ensure that no account is created without a policy acceptance date.
        """
        if value is None:
            raise ValidationError("You must accept the privacy policy to register.")
        if (
                self.instance
                and self.instance.accepted_privacy_policy
                and value < self.instance.accepted_privacy_policy
        ):
            raise ValidationError(
                "New policy acceptance date cannot be earlier than previous acceptance date."
            )
        if value >= timezone.now() + timezone.timedelta(hours=1):
            raise ValidationError("Cannot accept policy for a future date.")
        return value

    def validate_accept_domain_condition(self, value):
        """
        Ensure that no account registers a domain without stating he/she has the rights
        to use that domain.
        """
        if not value:
            raise ValidationError("You must accept these terms to register.")
        return value

    class Meta:
        model = UserProfile
        fields = (
            "full_name",
            "username",
            "password",
            "email",
            "accepted_privacy_policy",
            "accept_domain_condition",
            "subscribe_to_updates",
        )
        extra_kwargs = {
            "accepted_privacy_policy": {"required": True},
            "accept_domain_condition": {"required": True},
        }


# pylint: disable=abstract-method
class ThemeSchemaSerializer(serializers.Serializer):
    """
    Custom automatically generated serializer from the theme schemas.

    This is needed to make the Swagger code generator correctly generate the
    schema model in the frontend without requiring to duplicate the schema
    there.
    """

    def __init__(self, *args, **kwargs):
        """
        Start with empty serializer and add fields from both theme schemas
        """
        super().__init__(*args, **kwargs)

        # We're just going to use the v1 theme schema here since v0 is
        # getting deprecated soon
        theme_schema_combined = {
            **theme_schema_v1['properties']
        }
        for key, value in theme_schema_combined.items():
            field_type = None
            if key == 'version':
                field_type = serializers.IntegerField(required=False)
            elif value == ref('flag'):
                field_type = serializers.BooleanField(required=False)
            else:
                field_type = serializers.CharField(
                    max_length=7,
                    required=False,
                    allow_blank=True,
                    # TODO: Add a color validator here
                )
            self.fields[key] = field_type


class StaticContentOverridesSerializer(serializers.Serializer):
    """
    Custom automatically generated serializer from the static content overrides schema.

    This is needed to make the Swagger code generator correctly generate the schema model in the frontend
    without having to duplicate teh schema there.
    """

    def __init__(self, *args, **kwargs):
        """
        Add fields dynamically from the schema.
        """
        super().__init__(*args, **kwargs)
        static_content_overrides = {
            **static_content_overrides_v0_schema['properties']
        }

        for key, _ in static_content_overrides.items():
            if key == 'version':
                field_type = serializers.IntegerField(required=False)
            else:
                field_type = serializers.CharField(required=False, allow_blank=True)
            self.fields[key] = field_type


class ToggleStaticContentPagesSerializer(serializers.Serializer):
    """
    Serializer to enable/disable specific static page
    """
    page_name = serializers.CharField()
    enabled = serializers.BooleanField()


class DisplayStaticContentPagesSerializer(DataSerializer):
    """
    Serializer with configuration values for MKTG_URL_LINK_MAP
    """
    about = serializers.BooleanField()
    contact = serializers.BooleanField()
    donate = serializers.BooleanField()
    tos = serializers.BooleanField()
    honor = serializers.BooleanField()
    privacy = serializers.BooleanField()

    def to_representation(self, instance):
        return instance.static_content_display


class OpenEdXInstanceConfigSerializer(serializers.ModelSerializer):
    """
    Serializer with configuration details about the user's Open edX instance.

    Make sure to prefetch the instance data when using this serializer to
    avoid a high query count in LIST operations.
    """
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    # Theme and static overrides serializers
    draft_theme_config = ThemeSchemaSerializer(read_only=True)
    draft_static_content_overrides = StaticContentOverridesSerializer(read_only=True)

    static_pages_enabled = serializers.SerializerMethodField()

    # LMS and Studio URLs (if the instance is provisioned)
    lms_url = serializers.SerializerMethodField()
    studio_url = serializers.SerializerMethodField()

    public_contact_email = serializers.EmailField(required=False)
    is_email_verified = serializers.BooleanField(source='email_addresses_verified', read_only=True)

    def get_static_pages_enabled(self, obj):
        """
        Returns config with enabled static pages.

        default - all pages enabled
        """
        config = obj.configuration_display_static_pages
        if not config:
            return obj.default_configuration_display_static_pages()
        return config

    def get_lms_url(self, obj):
        """
        Returns instance LMS url if available
        """
        if obj.instance:
            return obj.instance.url
        return ""

    def get_studio_url(self, obj):
        """
        Returns instance Studio url if available
        """
        if obj.instance:
            return obj.instance.studio_url
        return ""

    def validate_user(self, value):
        """
        Prevent user from creating more than the allowed number of instances.

        Currently each user is allowed one Open edX instance.
        """
        if BetaTestApplication.objects.filter(user=value).exists():
            raise ValidationError("User has reached limit of allowed Open edX instances.")
        return value

    def validate_subdomain(self, value):
        """
        Prevent users from registering with a subdomain which is in use.
        """
        is_new_instance = self.instance is None
        is_changed = not is_new_instance and self.instance.subdomain != self.initial_data.get("subdomain")

        if is_new_instance or is_changed:
            validate_available_subdomain(value)

        return value

    def validate_external_domain(self, value):
        """
        Prevent users from registering with an external domain which was or currently in use.
        """
        initial_domain = self.initial_data.get("external_domain")
        is_new_instance = self.instance is None
        is_changed = not is_new_instance and self.instance.external_domain != initial_domain

        if (is_new_instance or is_changed) and initial_domain is not None:
            validate_available_external_domain(value)

        return value

    def save(self, **kwargs):
        """
        Override the save method to update the dns_configuration_state
        if external_domain is present.
        Also, trigger a dns config verification if there is a new external_domain.
        """
        is_new_instance = self.instance is None
        is_external_domain_present = self.validated_data.get("external_domain") is not None
        is_changed = not is_new_instance and self.instance.external_domain != self.validated_data.get("external_domain")
        # If we have a new external_domain, set the dns_configuration_state to pending
        if (is_new_instance and is_external_domain_present) or is_changed:
            self.validated_data.update({
                "dns_configuration_state": DNSConfigState.pending.name
            })

        instance = super().save(**kwargs)
        # Schedule a dns config verification after saving because there won't be an
        # instance in case of create().
        if (is_new_instance and is_external_domain_present) or is_changed:
            verify_external_domain_configuration.schedule(
                args=(self.instance.pk,),
                delay=60
            )
        return instance

    class Meta:
        model = BetaTestApplication
        fields = (
            "id",
            "user",
            "lms_url",
            "studio_url",
            "subdomain",
            "external_domain",
            "instance_name",
            "public_contact_email",
            "privacy_policy_url",
            "use_advanced_theme",
            "draft_theme_config",
            "logo",
            "favicon",
            "hero_cover_image",
            "draft_static_content_overrides",
            "static_pages_enabled",
            "is_email_verified",
            "dns_configuration_state"
        )
        read_only_fields = [
            "logo",
            "favicon",
            "lms_url",
            "studio_url",
            "dns_configuration_state"
        ]


class OpenEdXInstanceConfigUpdateSerializer(OpenEdXInstanceConfigSerializer):
    """
    A version of OpenEdXInstanceConfigSerializer that excludes non-updatable fields and makes
    all other fields optional. Used for editing existing items.
    """
    EXCLUDE_FIELDS = ("id", "is_email_verified")

    def __init__(self, *args, **kwargs):
        """ Override fields """
        super().__init__(*args, **kwargs)
        for field_name in self.EXCLUDE_FIELDS:
            self.fields.pop(field_name)
        # Mark all fields as optional:
        for field in self.fields.values():
            field.required = False


# pylint: disable=abstract-method
class OpenEdXInstanceDeploymentStatusSerializer(serializers.Serializer):
    """
    Serializer with configuration details about the user's Open edX instance.
    """
    status = serializers.ChoiceField(choices=DeploymentState.choices())
    undeployed_changes = serializers.JSONField()
    deployed_changes = serializers.JSONField()
    deployment_type = serializers.ChoiceField(choices=DeploymentType.choices())


# pylint: disable=abstract-method
class OpenEdXInstanceDeploymentNotificationSerializer(serializers.Serializer):
    """
    Simplistic serializer with status and changes for certain Open edX instance.
    """
    status = serializers.ChoiceField(choices=DeploymentState.choices())
    deployed_changes = serializers.JSONField()
    date = serializers.DateTimeField()


# pylint: disable=abstract-method
class OpenEdXInstanceDeploymentCreateSerializer(serializers.Serializer):
    """
    Serializer with configuration details about the user's Open edX instance.
    """
    id = serializers.IntegerField()
