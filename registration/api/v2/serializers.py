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
import logging
from typing import Dict

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.validators import RegexValidator
from django.utils import timezone
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from registration.api.v2 import constants
from registration.models import BetaTestApplication
from userprofile.models import UserProfile
from instance.schemas.theming import theme_schema_v1, ref

logger = logging.getLogger(__name__)


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

    def validate_accept_paid_support(self, value):
        """
        Ensure that no account exists that hasn't accepted the support terms.
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
            "accept_paid_support",
            "subscribe_to_updates",
        )
        extra_kwargs = {
            "accepted_privacy_policy": {"required": True},
            "accept_paid_support": {"required": True},
        }


# pylint: disable=abstract-method
class ThemeSchemaSerializerGenerator(serializers.Serializer):
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

        # Just using the new v1 schema for now, adding the v0 schema breaks
        # code generation because one variable is named main_color and other is
        # main-color and both get converted to mainColor in TS
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


class OpenEdXInstanceConfigSerializer(serializers.ModelSerializer):
    """
    Serializer with configuration details about the user's Open edX instance.
    """

    user = serializers.HiddenField(default=serializers.CurrentUserDefault())
    draft_theme_config = ThemeSchemaSerializerGenerator(read_only=True)

    def validate_user(self, value):
        """
        Prevent user from creating more than the allowed number of instances.

        Currently each user is allowed one Open edX instance.
        """
        if BetaTestApplication.objects.filter(user=value).exists():
            raise ValidationError("User has reached limit of allowed Open edX instances.")
        else:
            return value

    class Meta:
        model = BetaTestApplication
        fields = (
            "id",
            "user",
            "subdomain",
            "external_domain",
            "instance_name",
            "public_contact_email",
            "privacy_policy_url",
            "use_advanced_theme",
            "draft_theme_config",
        )


class OpenEdXInstanceConfigUpdateSerializer(OpenEdXInstanceConfigSerializer):
    """
    A version of OpenEdXInstanceConfigSerializer that excludes the 'id' field and makes
    all other fields optional. Used for editing existing items.
    """
    EXCLUDE_FIELDS = ("id",)

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
    status = serializers.ChoiceField(
        choices=constants.DEPLOYMENT_STATUS_CHOICES
    )
    undeployed_changes = serializers.IntegerField()


# pylint: disable=abstract-method
class OpenEdXInstanceDeploymentCreateSerializer(serializers.Serializer):
    """
    Serializer with configuration details about the user's Open edX instance.
    """
    id = serializers.IntegerField()
