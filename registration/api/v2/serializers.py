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
from django.contrib.auth.password_validation import (
    validate_password,
)
from django.core.validators import RegexValidator
from django.db.models import Model
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.validators import UniqueValidator

from registration.models import BetaTestApplication
from userprofile.models import UserProfile

logger = logging.getLogger(__name__)


class AccountSerializer(serializers.ModelSerializer):
    """
    Serializer for User account information.
    """
    username = serializers.CharField(
        source="user.username",
        required=True,
        validators=[
            UniqueValidator(queryset=User.objects.all(), message="That username is not available."),
            RegexValidator(r'^[\w.+-]+$', message=('Usernames may contain only letters, numbers, and '
                                                   './+/-/_ characters.'))
        ],
        help_text=('This would also be the username of the administrator '
                   'account on the users\'s instances.'),
    )
    email = serializers.EmailField(
        source="user.email",
        required=True,
        help_text='This is also the account name, and where we will send important notices.',
    )
    password = serializers.CharField(
        source="user.password",
        required=True,
        write_only=True,
        style={'input_type': 'password'},
        validators=[validate_password],
        help_text='A password for the OpenCraft account.',
    )

    def create(self, validated_data: Dict) -> UserProfile:
        """
        Create a new user profile and user instance from serialised data.
        """
        new_user = User.objects.create_user(**validated_data.pop('user'))
        new_user_profile = UserProfile.objects.create(**validated_data, user=new_user)
        return new_user_profile

    def __init__(self, *args, **kwargs):
        # When set this serializer removes fields that can't be updated.
        update_only = kwargs.pop('update_only', False)

        super(AccountSerializer, self).__init__(self, *args, **kwargs)

        if update_only:
            self.fields.pop('username', 'accept_paid_support')

    class Meta:
        model = UserProfile
        fields = (
            'full_name', 'username', 'password', 'email',
            'accepted_privacy_policy', 'accept_paid_support', 'subscribe_to_updates',
        )


class OpenEdxInstanceConfigSerializer(serializers.ModelSerializer):
    """
    Serializer with configuration details about the user's Open edX instance.
    """

    def __init__(self, *args, **kwargs):
        # When set this serializer removes fields that can't be updated.
        update_only = kwargs.pop('update_only', False)

        super(OpenEdxInstanceConfigSerializer, self).__init__(self, *args, **kwargs)

        if update_only:
            self.fields.pop('subdomain')

    class Meta:
        model = BetaTestApplication
        fields = (
            'subdomain', 'instance_name', 'public_contact_email',
            'project_description', 'privacy_policy_url',
            'use_advanced_theme', 'draft_theme_config',
        )


# pylint: disable=abstract-method
class ReadCreateRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """
    account = AccountSerializer()
    instance = OpenEdxInstanceConfigSerializer()

    def validate_account_data(self, account_data: Dict):
        """
        Validate uniqueness of username and email.
        """
        errors = {}
        if User.objects.filter(username=account_data.get('user', {}).get('username')).exists():
            errors.update({'username': "That username is not available."})
        if User.objects.filter(email=account_data.get('user', {}).get('email')).exists():
            errors.update({'email': "An account with that e-mail already exists."})
        if errors.keys():
            raise ValidationError(errors)

    def create(self, validated_data: Dict) -> Dict[str, Model]:
        """
        Set up a new user account, new user profile and an Open edX instance.
        """
        account_data = validated_data.pop('account')
        # Nested serializers don't work well with unique constraints when updating.
        # As such the unique constraints are enforced here only during creation.
        self.validate_account_data(account_data)
        instance_data = validated_data.pop('instance')
        new_user = User.objects.create(**account_data.pop('user'))
        new_user_profile = UserProfile.objects.create(**account_data, user=new_user)
        instance = BetaTestApplication.objects.create(**instance_data, user=new_user)
        return {
            'account': new_user_profile,
            'instance': instance,
        }


# pylint: disable=abstract-method
class UpdateOnlyRegistrationSerializer(serializers.Serializer):
    """
    Serializer for user registration.
    """
    account = AccountSerializer(update_only=True)
    instance = OpenEdxInstanceConfigSerializer(update_only=True)

    def validate_account_data(self, account_data: Dict[str, Dict]):
        """
        Validate uniqueness of the email.
        """
        if User.objects.filter(email=account_data.get('user', {}).get('email')).exists():
            raise ValidationError({'email': "An account with that e-mail already exists."})

    def _update_user_account(self, user: User, user_data: Dict):
        """
        Update user from validated data.
        """
        user_updated = False
        if 'password' in user_data:
            user.set_password(user_data.pop('password'))
            user_updated = True
        if 'email' in user_data:
            user.email = user_data.pop('email')
            user_updated = True
        if user_updated:
            user.save()

    def _update_instance(self, instance: BetaTestApplication, instance_data: Dict):
        """
        Update instance configuration from validated data.
        """
        instance_updated = False
        for key, val in instance_data.items():
            setattr(instance, key, val)
            instance_updated = True
        if instance_updated:
            instance.save()

    def _update_user_profile(self, user_profile: UserProfile, profile_data: Dict):
        """
        Update user profile from validated data.
        """
        profile_updated = False
        for key, val in profile_data.items():
            setattr(user_profile, key, val)
            profile_updated = True
        if profile_updated:
            user_profile.save()

    def update(self, instance: Dict, validated_data: Dict) -> Dict[str, Model]:
        """
        Update existing data for the user profile, and Open edX instance.
        """
        user_profile: UserProfile = instance['account']
        instance: BetaTestApplication = instance['instance']
        account_data = validated_data.pop('account')
        self._update_user_account(user_profile.user, account_data.pop('user'))
        self._update_user_profile(user_profile, account_data)
        self._update_instance(instance, validated_data.get('instance'))
        return {
            'account': user_profile,
            'instance': instance
        }
