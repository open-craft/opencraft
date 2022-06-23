# -*- coding: utf-8 -*-
#
# OpenCraft -- tools to aid developing and hosting free software projects
# Copyright (C) 2015-2022 OpenCraft <contact@opencraft.com>
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
Grove instance app model mixins - Payload
"""

# Classes #####################################################################


class AnsibleConfigurationShim:
    """
    Shim to parse the old ansible configuration settings and append settings to grove payload.

    This class is meant to be temporary, to help with the transition from the ansible based
    deployments to the new Grove based deployments.

    Going forward, configurations settings for all OCIM instances should be converted to new
    format compatible with Grove. This class would be redundant and can be removed when this is complete.

    Note: Grove/Tutor handles some type of configuration settings, such as hostnames, cache settings,
    celery/redis configuration, JWT settings, etc. through alternative channels. These settings have not been included
    in this shim, so as not to interefere with the Grove/Tutor setup. Therefore, those settings would have
    to be handled explicitly during transition from ansible-based setup to Grove.
    """

    GENERIC_ENV_CONFIG = {
        "EDXAPP_IDA_LOGOUT_URI_LIST": "IDA_LOGOUT_URI_LIST",
        "EDXAPP_CREDENTIALS_INTERNAL_SERVICE_URL": "CREDENTIALS_INTERNAL_SERVICE_URL",
        "EDXAPP_CREDENTIALS_PUBLIC_SERVICE_URL": "CREDENTIALS_PUBLIC_SERVICE_URL",
        "EDXAPP_ECOMMERCE_PUBLIC_URL_ROOT": "ECOMMERCE_PUBLIC_URL_ROOT",
        "EDXAPP_ECOMMERCE_API_URL": "ECOMMERCE_API_URL",
        "EDXAPP_BLOCKSTORE_PUBLIC_URL_ROOT": "BLOCKSTORE_PUBLIC_URL_ROOT",
        "EDXAPP_BLOCKSTORE_API_URL": "BLOCKSTORE_API_URL",
        "EDXAPP_LEARNER_PORTAL_URL_ROOT": "LEARNER_PORTAL_URL_ROOT",
        "EDX_PLATFORM_VERSION": "EDX_PLATFORM_REVISION",
        "EDXAPP_ENTERPRISE_API_URL": "ENTERPRISE_API_URL",
        "EDXAPP_COURSE_CATALOG_URL_ROOT": "COURSE_CATALOG_URL_ROOT",
        "EDXAPP_COURSE_CATALOG_API_URL": "COURSE_CATALOG_API_URL",
        "EDXAPP_COURSE_CATALOG_VISIBILITY_PERMISSION": "COURSE_CATALOG_VISIBILITY_PERMISSION",
        "EDXAPP_COURSE_ABOUT_VISIBILITY_PERMISSION": "COURSE_ABOUT_VISIBILITY_PERMISSION",
        "EDXAPP_DEFAULT_COURSE_VISIBILITY_IN_CATALOG": "DEFAULT_COURSE_VISIBILITY_IN_CATALOG",
        "EDXAPP_DEFAULT_MOBILE_AVAILABLE": "DEFAULT_MOBILE_AVAILABLE",
        "EDXAPP_FINANCIAL_REPORTS": "FINANCIAL_REPORTS",
        "EDXAPP_CORS_ORIGIN_WHITELIST": "CORS_ORIGIN_WHITELIST",
        "EDXAPP_CORS_ORIGIN_ALLOW_ALL": "CORS_ORIGIN_ALLOW_ALL",
        "EDXAPP_LOGIN_REDIRECT_WHITELIST": "LOGIN_REDIRECT_WHITELIST",
        "EDXAPP_CROSS_DOMAIN_CSRF_COOKIE_DOMAIN": "CROSS_DOMAIN_CSRF_COOKIE_DOMAIN",
        "EDXAPP_CROSS_DOMAIN_CSRF_COOKIE_NAME": "CROSS_DOMAIN_CSRF_COOKIE_NAME",
        "EDXAPP_CSRF_COOKIE_SECURE": "CSRF_COOKIE_SECURE",
        "EDXAPP_CSRF_TRUSTED_ORIGINS": "CSRF_TRUSTED_ORIGINS",
        "EDXAPP_VIDEO_UPLOAD_PIPELINE": "VIDEO_UPLOAD_PIPELINE",
        "EDXAPP_DEPRECATED_ADVANCED_COMPONENT_TYPES": "DEPRECATED_ADVANCED_COMPONENT_TYPES",
        "EDXAPP_XBLOCK_FS_STORAGE_BUCKET": "XBLOCK_FS_STORAGE_BUCKET",
        "EDXAPP_XBLOCK_FS_STORAGE_PREFIX": "XBLOCK_FS_STORAGE_PREFIX",
        "EDXAPP_ANALYTICS_DASHBOARD_URL": "ANALYTICS_DASHBOARD_URL",
        "EDXAPP_CELERY_BROKER_USE_SSL": "CELERY_BROKER_USE_SSL",
        "EDXAPP_CELERY_EVENT_QUEUE_TTL": "CELERY_EVENT_QUEUE_TTL",
        "EDXAPP_PAYMENT_SUPPORT_EMAIL": "PAYMENT_SUPPORT_EMAIL",
        "EDXAPP_ZENDESK_URL": "ZENDESK_URL",
        "EDXAPP_ZENDESK_CUSTOM_FIELDS": "ZENDESK_CUSTOM_FIELDS",
        "EDXAPP_COURSES_WITH_UNSAFE_CODE": "COURSES_WITH_UNSAFE_CODE",
        "EDXAPP_BULK_EMAIL_EMAILS_PER_TASK": "BULK_EMAIL_EMAILS_PER_TASK",
        "EDXAPP_MICROSITE_ROOT_DIR": "MICROSITE_ROOT_DIR",
        "EDXAPP_MICROSITE_CONFIGURATION": "MICROSITE_CONFIGURATION",
        "EDXAPP_DEFAULT_FILE_STORAGE": "DEFAULT_FILE_STORAGE",
        "EDXAPP_LMS_INTERNAL_ROOT_URL": "LMS_INTERNAL_ROOT_URL",
        "EDXAPP_PARTNER_SUPPORT_EMAIL": "PARTNER_SUPPORT_EMAIL",
        "EDXAPP_PLATFORM_DESCRIPTION": "PLATFORM_DESCRIPTION",
        "EDXAPP_ANALYTICS_DASHBOARD_NAME": "ANALYTICS_DASHBOARD_NAME",
        "EDXAPP_STUDIO_NAME": "STUDIO_NAME",
        "EDXAPP_STUDIO_SHORT_NAME": "STUDIO_SHORT_NAME",
        "EDXAPP_LOG_LEVEL": "LOCAL_LOGLEVEL",
        "EDXAPP_AWS_SES_REGION_NAME": "AWS_SES_REGION_NAME",
        "EDXAPP_AWS_SES_REGION_ENDPOINT": "AWS_SES_REGION_ENDPOINT",
        "EDXAPP_SYSLOG_SERVER": "SYSLOG_SERVER",
        "EDXAPP_LMS_ISSUER": "JWT_ISSUER",
        "EDXAPP_SYSTEM_WIDE_ROLE_CLASSES": "SYSTEM_WIDE_ROLE_CLASSES",
        "EDXAPP_ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS": "ENTERPRISE_MARKETING_FOOTER_QUERY_PARAMS",
        "EDXAPP_INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT": "INTEGRATED_CHANNELS_API_CHUNK_TRANSMISSION_LIMIT",
        "EDXAPP_FEEDBACK_SUBMISSION_EMAIL": "FEEDBACK_SUBMISSION_EMAIL",
        "EDXAPP_TIME_ZONE": "TIME_ZONE",
        "EDXAPP_LANGUAGE_COOKIE": "LANGUAGE_COOKIE",
        "EDXAPP_CERTIFICATE_TEMPLATE_LANGUAGES": "CERTIFICATE_TEMPLATE_LANGUAGES",
        "EDXAPP_MKTG_URL_LINK_MAP": "MKTG_URL_LINK_MAP",
        "EDXAPP_MKTG_URLS": "MKTG_URLS",
        "EDXAPP_SUPPORT_SITE_LINK": "SUPPORT_SITE_LINK",
        "EDXAPP_ID_VERIFICATION_SUPPORT_LINK": "ID_VERIFICATION_SUPPORT_LINK",
        "EDXAPP_ACTIVATION_EMAIL_SUPPORT_LINK": "ACTIVATION_EMAIL_SUPPORT_LINK",
        "EDXAPP_PASSWORD_RESET_SUPPORT_LINK": "PASSWORD_RESET_SUPPORT_LINK",
        "EDXAPP_CELERYBEAT_SCHEDULER": "CELERYBEAT_SCHEDULER",
        "EDXAPP_COMMENTS_SERVICE_URL": "COMMENTS_SERVICE_URL",
        "EDXAPP_SESSION_COOKIE_NAME": "SESSION_COOKIE_NAME",
        "EDXAPP_COMMENTS_SERVICE_KEY": "COMMENTS_SERVICE_KEY",
        "EDXAPP_TECH_SUPPORT_EMAIL": "TECH_SUPPORT_EMAIL",
        "EDXAPP_BUGS_EMAIL": "BUGS_EMAIL",
        "EDXAPP_DEFAULT_FROM_EMAIL": "DEFAULT_FROM_EMAIL",
        "EDXAPP_DEFAULT_FEEDBACK_EMAIL": "DEFAULT_FEEDBACK_EMAIL",
        "EDXAPP_DEFAULT_SERVER_EMAIL": "SERVER_EMAIL",
        "EDXAPP_BULK_EMAIL_DEFAULT_FROM_EMAIL": "BULK_EMAIL_DEFAULT_FROM_EMAIL",
        "EDXAPP_BULK_EMAIL_LOG_SENT_EMAILS": "BULK_EMAIL_LOG_SENT_EMAILS",
        "EDXAPP_CAS_SERVER_URL": "CAS_SERVER_URL",
        "EDXAPP_CAS_EXTRA_LOGIN_PARAMS": "CAS_EXTRA_LOGIN_PARAMS",
        "EDXAPP_CAS_ATTRIBUTE_CALLBACK": "CAS_ATTRIBUTE_CALLBACK",
        "EDXAPP_UNIVERSITY_EMAIL": "UNIVERSITY_EMAIL",
        "EDXAPP_PRESS_EMAIL": "PRESS_EMAIL",
        "EDXAPP_SOCIAL_MEDIA_FOOTER_URLS": "SOCIAL_MEDIA_FOOTER_URLS",
        "EDXAPP_MOBILE_STORE_URLS": "MOBILE_STORE_URLS",
        "EDXAPP_FOOTER_ORGANIZATION_IMAGE": "FOOTER_ORGANIZATION_IMAGE",
        "EDXAPP_ORA2_FILE_PREFIX": "ORA2_FILE_PREFIX",
        "EDXAPP_FILE_UPLOAD_STORAGE_BUCKET_NAME": "FILE_UPLOAD_STORAGE_BUCKET_NAME",
        "EDXAPP_FILE_UPLOAD_STORAGE_PREFIX": "FILE_UPLOAD_STORAGE_PREFIX",
        "EDXAPP_REGISTRATION_EXTRA_FIELDS": "REGISTRATION_EXTRA_FIELDS",
        "EDXAPP_XBLOCK_SETTINGS": "XBLOCK_SETTINGS",
        "EDXAPP_EDXMKTG_USER_INFO_COOKIE_NAME": "EDXMKTG_USER_INFO_COOKIE_NAME",
        "EDXAPP_VIDEO_IMAGE_MAX_AGE": "VIDEO_IMAGE_MAX_AGE",
        "EDXAPP_VIDEO_IMAGE_SETTINGS": "VIDEO_IMAGE_SETTINGS",
        "EDXAPP_VIDEO_TRANSCRIPTS_MAX_AGE": "VIDEO_TRANSCRIPTS_MAX_AGE",
        "EDXAPP_VIDEO_TRANSCRIPTS_SETTINGS": "VIDEO_TRANSCRIPTS_SETTINGS",
        "EDXAPP_BLOCK_STRUCTURES_SETTINGS": "BLOCK_STRUCTURES_SETTINGS",
        "EDXAPP_COMPREHENSIVE_THEME_LOCALE_PATHS": "COMPREHENSIVE_THEME_LOCALE_PATHS",
        "EDXAPP_PREPEND_LOCALE_PATHS": "PREPEND_LOCALE_PATHS",
        "EDXAPP_CUSTOM_RESOURCE_TEMPLATES_DIRECTORY": "CUSTOM_RESOURCE_TEMPLATES_DIRECTORY",
        "EDXAPP_DEFAULT_SITE_THEME": "DEFAULT_SITE_THEME",
        "EDXAPP_SESSION_SAVE_EVERY_REQUEST": "SESSION_SAVE_EVERY_REQUEST",
        "EDXAPP_SOCIAL_SHARING_SETTINGS": "SOCIAL_SHARING_SETTINGS",
        "EDXAPP_SESSION_COOKIE_SECURE": "SESSION_COOKIE_SECURE",
        "EDXAPP_AFFILIATE_COOKIE_NAME": "AFFILIATE_COOKIE_NAME",
        "EDXAPP_ELASTIC_SEARCH_CONFIG": "ELASTIC_SEARCH_CONFIG",
        "EDXAPP_PLATFORM_TWITTER_ACCOUNT": "PLATFORM_TWITTER_ACCOUNT",
        "EDXAPP_PLATFORM_FACEBOOK_ACCOUNT": "PLATFORM_FACEBOOK_ACCOUNT",
        "EDXAPP_HELP_TOKENS_BOOKS": "HELP_TOKENS_BOOKS",
        "EDXAPP_ICP_LICENSE": "ICP_LICENSE",
        "EDXAPP_ICP_LICENSE_INFO": "ICP_LICENSE_INFO",
        "EDXAPP_BASE_COOKIE_DOMAIN": "BASE_COOKIE_DOMAIN",
        "EDXAPP_POLICY_CHANGE_GRADES_ROUTING_KEY": "POLICY_CHANGE_GRADES_ROUTING_KEY",
        "EDXAPP_PROCTORING_SETTINGS": "PROCTORING_SETTINGS",
        "EDXAPP_EXTRA_MIDDLEWARE_CLASSES": "EXTRA_MIDDLEWARE_CLASSES",
        "EDXAPP_MAINTENANCE_BANNER_TEXT": "MAINTENANCE_BANNER_TEXT",
        "EDXAPP_RETIRED_USERNAME_PREFIX": "RETIRED_USERNAME_PREFIX",
        "EDXAPP_RETIRED_EMAIL_PREFIX": "RETIRED_EMAIL_PREFIX",
        "EDXAPP_RETIRED_EMAIL_DOMAIN": "RETIRED_EMAIL_DOMAIN",
        "EDXAPP_RETIRED_USER_SALTS": "RETIRED_USER_SALTS",
        "EDXAPP_RETIREMENT_SERVICE_USER_NAME": "RETIREMENT_SERVICE_WORKER_USERNAME",
        "EDXAPP_RETIREMENT_STATES": "RETIREMENT_STATES",
        "EDXAPP_USERNAME_REPLACEMENT_WORKER": "USERNAME_REPLACEMENT_WORKER",
        "EDXAPP_AUTH_PASSWORD_VALIDATORS": "AUTH_PASSWORD_VALIDATORS",
        "EDXAPP_PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG": "PASSWORD_POLICY_COMPLIANCE_ROLLOUT_CONFIG",
        "EDXAPP_DASHBOARD_COURSE_LIMIT": "DASHBOARD_COURSE_LIMIT",
        "EDXAPP_COMPLETION_AGGREGATOR_URL": "COMPLETION_AGGREGATOR_URL"
    }

    LMS_ENV_CONFIG = {
        "EDXAPP_OAUTH_ENFORCE_SECURE": "OAUTH_ENFORCE_SECURE",
        "EDXAPP_OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS": "OAUTH_EXPIRE_CONFIDENTIAL_CLIENT_DAYS",
        "EDXAPP_OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS": "OAUTH_EXPIRE_PUBLIC_CLIENT_DAYS",
        "EDXAPP_OAUTH_DELETE_EXPIRED": "OAUTH_DELETE_EXPIRED",
        "EDXAPP_PAID_COURSE_REGISTRATION_CURRENCY": "PAID_COURSE_REGISTRATION_CURRENCY",
        "EDXAPP_THIRD_PARTY_AUTH_BACKENDS": "THIRD_PARTY_AUTH_BACKENDS",
        "EDXAPP_GIT_REPO_DIR": "GIT_REPO_DIR",
        "EDXAPP_VIDEO_CDN_URLS": "VIDEO_CDN_URL",
        "EDXAPP_PDF_RECEIPT_TAX_ID": "PDF_RECEIPT_TAX_ID",
        "EDXAPP_PDF_RECEIPT_FOOTER_TEXT": "PDF_RECEIPT_FOOTER_TEXT",
        "EDXAPP_PDF_RECEIPT_DISCLAIMER_TEXT": "PDF_RECEIPT_DISCLAIMER_TEXT",
        "EDXAPP_PDF_RECEIPT_BILLING_ADDRESS": "PDF_RECEIPT_BILLING_ADDRESS",
        "EDXAPP_PDF_RECEIPT_TERMS_AND_CONDITIONS": "PDF_RECEIPT_TERMS_AND_CONDITIONS",
        "EDXAPP_PDF_RECEIPT_TAX_ID_LABEL": "PDF_RECEIPT_TAX_ID_LABEL",
        "EDXAPP_PDF_RECEIPT_COBRAND_LOGO_PATH": "PDF_RECEIPT_COBRAND_LOGO_PATH",
        "EDXAPP_PDF_RECEIPT_LOGO_PATH": "PDF_RECEIPT_LOGO_PATH",
        "EDXAPP_PROFILE_IMAGE_BACKEND": "PROFILE_IMAGE_BACKEND",
        "EDXAPP_PROFILE_IMAGE_MIN_BYTES": "PROFILE_IMAGE_MIN_BYTES",
        "EDXAPP_PROFILE_IMAGE_MAX_BYTES": "PROFILE_IMAGE_MAX_BYTES",
        "EDXAPP_PROFILE_IMAGE_SIZES_MAP": "PROFILE_IMAGE_SIZES_MAP",
        "EDXAPP_EDXNOTES_PUBLIC_API": "EDXNOTES_PUBLIC_API",
        "EDXAPP_EDXNOTES_INTERNAL_API": "EDXNOTES_INTERNAL_API",
        "EDXAPP_LTI_USER_EMAIL_DOMAIN": "LTI_USER_EMAIL_DOMAIN",
        "EDXAPP_LTI_AGGREGATE_SCORE_PASSBACK_DELAY": "LTI_AGGREGATE_SCORE_PASSBACK_DELAY",
        "EDXAPP_CREDIT_HELP_LINK_URL": "CREDIT_HELP_LINK_URL",
        "EDXAPP_MAILCHIMP_NEW_USER_LIST_ID": "MAILCHIMP_NEW_USER_LIST_ID",
        "EDXAPP_CONTACT_MAILING_ADDRESS": "CONTACT_MAILING_ADDRESS",
        "EDXAPP_API_ACCESS_MANAGER_EMAIL": "API_ACCESS_MANAGER_EMAIL",
        "EDXAPP_API_ACCESS_FROM_EMAIL": "API_ACCESS_FROM_EMAIL",
        "EDXAPP_API_DOCUMENTATION_URL": "API_DOCUMENTATION_URL",
        "EDXAPP_AUTH_DOCUMENTATION_URL": "AUTH_DOCUMENTATION_URL",
        "EDXAPP_RECALCULATE_GRADES_ROUTING_KEY": "RECALCULATE_GRADES_ROUTING_KEY",
        "EDXAPP_BULK_EMAIL_ROUTING_KEY_SMALL_JOBS": "BULK_EMAIL_ROUTING_KEY_SMALL_JOBS",
        "EDXAPP_LMS_CELERY_QUEUES": "CELERY_QUEUES",
        "EDXAPP_ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES": "ENTERPRISE_COURSE_ENROLLMENT_AUDIT_MODES",
        "EDXAPP_ENTERPRISE_CUSTOMER_SUCCESS_EMAIL": "ENTERPRISE_CUSTOMER_SUCCESS_EMAIL",
        "EDXAPP_ENTERPRISE_INTEGRATIONS_EMAIL": "ENTERPRISE_INTEGRATIONS_EMAIL",
        "EDXAPP_ENTERPRISE_ENROLLMENT_API_URL": "ENTERPRISE_ENROLLMENT_API_URL",
        "EDXAPP_ENTERPRISE_SUPPORT_URL": "ENTERPRISE_SUPPORT_URL",
        "EDXAPP_PARENTAL_CONSENT_AGE_LIMIT": "PARENTAL_CONSENT_AGE_LIMIT",
        "EDXAPP_ACE_ENABLED_CHANNELS": "ACE_ENABLED_CHANNELS",
        "EDXAPP_ACE_ENABLED_POLICIES": "ACE_ENABLED_POLICIES",
        "EDXAPP_ACE_CHANNEL_SAILTHRU_DEBUG": "ACE_CHANNEL_SAILTHRU_DEBUG",
        "EDXAPP_ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME": "ACE_CHANNEL_SAILTHRU_TEMPLATE_NAME",
        "EDXAPP_ACE_CHANNEL_DEFAULT_EMAIL": "ACE_CHANNEL_DEFAULT_EMAIL",
        "EDXAPP_ACE_CHANNEL_TRANSACTIONAL_EMAIL": "ACE_CHANNEL_TRANSACTIONAL_EMAIL",
        "EDXAPP_ORGANIZATIONS_AUTOCREATE": "ORGANIZATIONS_AUTOCREATE",
        "EDXAPP_ENTERPRISE_TAGLINE": "ENTERPRISE_TAGLINE",
        "EDXAPP_LMS_ANALYTICS_API_URL": "ANALYTICS_API_URL",
        "EDXAPP_GOOGLE_SITE_VERIFICATION_ID": "GOOGLE_SITE_VERIFICATION_ID",
        "EDXAPP_LMS_STATIC_URL_BASE": "STATIC_URL_BASE",
        "EDXAPP_X_FRAME_OPTIONS": "X_FRAME_OPTIONS",
        "EDXAPP_LMS_WRITABLE_GRADEBOOK_URL": "WRITABLE_GRADEBOOK_URL",
        "EDXAPP_PROFILE_MICROFRONTEND_URL": "PROFILE_MICROFRONTEND_URL",
        "EDXAPP_ORDER_HISTORY_MICROFRONTEND_URL": "ORDER_HISTORY_MICROFRONTEND_URL",
        "EDXAPP_PROGRAM_CERTIFICATES_ROUTING_KEY": "PROGRAM_CERTIFICATES_ROUTING_KEY",
        "EDXAPP_ACCOUNT_MICROFRONTEND_URL": "ACCOUNT_MICROFRONTEND_URL",
        "EDXAPP_DCS_SESSION_COOKIE_SAMESITE": "DCS_SESSION_COOKIE_SAMESITE",
        "EDXAPP_DCS_SESSION_COOKIE_SAMESITE_FORCE_ALL": "DCS_SESSION_COOKIE_SAMESITE_FORCE_ALL",
        "EDXAPP_PROGRAM_CONSOLE_MICROFRONTEND_URL": "PROGRAM_CONSOLE_MICROFRONTEND_URL",
        "EDXAPP_LEARNING_MICROFRONTEND_URL": "LEARNING_MICROFRONTEND_URL"
    }

    CMS_ENV_CONFIG = {
        "EDXAPP_GIT_REPO_EXPORT_DIR": "GIT_REPO_EXPORT_DIR",
        "EDXAPP_CMS_CELERY_QUEUES": "CELERY_QUEUES",
        "EDXAPP_IMPORT_EXPORT_BUCKET": "COURSE_IMPORT_EXPORT_BUCKET",
        "EDXAPP_CMS_STATIC_URL_BASE": "STATIC_URL_BASE",
        "EDXAPP_X_FRAME_OPTIONS": "X_FRAME_OPTIONS",
        "EDXAPP_COURSE_AUTHORING_MICROFRONTEND_URL": "COURSE_AUTHORING_MICROFRONTEND_URL"
    }

    COMMON_FEATURES = {
        "EDXAPP_AUTH_USE_OPENID_PROVIDER": "AUTH_USE_OPENID_PROVIDER",
        "EDXAPP_ENABLE_DISCUSSION_SERVICE": "ENABLE_DISCUSSION_SERVICE",
        "EDXAPP_ENABLE_MKTG_SITE": "ENABLE_MKTG_SITE",
        "EDXAPP_ENABLE_PUBLISHER": "ENABLE_PUBLISHER",
        "EDXAPP_ENABLE_AUTO_AUTH": "AUTOMATIC_AUTH_FOR_TESTING",
        "EDXAPP_ENABLE_BULK_ENROLLMENT_VIEW": "ENABLE_BULK_ENROLLMENT_VIEW",
        "EDXAPP_ENABLE_VIDEO_UPLOAD_PIPELINE": "ENABLE_VIDEO_UPLOAD_PIPELINE",
        "EDXAPP_ENABLE_DISCUSSION_HOME_PANEL": "ENABLE_DISCUSSION_HOME_PANEL",
        "EDXAPP_ENABLE_CORS_HEADERS": "ENABLE_CORS_HEADERS",
        "EDXAPP_ENABLE_CROSS_DOMAIN_CSRF_COOKIE": "ENABLE_CROSS_DOMAIN_CSRF_COOKIE",
        "EDXAPP_ENABLE_COUNTRY_ACCESS": "ENABLE_COUNTRY_ACCESS",
        "EDXAPP_ENABLE_EDXNOTES": "ENABLE_EDXNOTES",
        "EDXAPP_ENABLE_CREDIT_API": "ENABLE_CREDIT_API",
        "EDXAPP_ENABLE_CREDIT_ELIGIBILITY": "ENABLE_CREDIT_ELIGIBILITY",
        "EDXAPP_ENABLE_LTI_PROVIDER": "ENABLE_LTI_PROVIDER",
        "EDXAPP_ENABLE_SPECIAL_EXAMS": "ENABLE_SPECIAL_EXAMS",
        "EDXAPP_ENABLE_SYSADMIN_DASHBOARD": "ENABLE_SYSADMIN_DASHBOARD",
        "EDXAPP_CUSTOM_COURSES_EDX": "CUSTOM_COURSES_EDX",
        "EDXAPP_ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES": "ENABLE_READING_FROM_MULTIPLE_HISTORY_TABLES",
        "EDXAPP_SHOW_HEADER_LANGUAGE_SELECTOR": "SHOW_HEADER_LANGUAGE_SELECTOR",
        "EDXAPP_SHOW_FOOTER_LANGUAGE_SELECTOR": "SHOW_FOOTER_LANGUAGE_SELECTOR",
        "EDXAPP_ENABLE_ENROLLMENT_RESET": "ENABLE_ENROLLMENT_RESET",
        "EDXAPP_ENABLE_EXPORT_GIT": "ENABLE_EXPORT_GIT"
    }

    ENV_LMS = "ENV_LMS"
    ENV_CMS = "ENV_CMS"
    ENV_COMMON_FEATURES = "ENV_COMMON_FEATURES"

    CONFIG_MAP = (
        (GENERIC_ENV_CONFIG, [ENV_LMS, ENV_CMS]),
        (LMS_ENV_CONFIG, [ENV_LMS]),
        (CMS_ENV_CONFIG, [ENV_CMS]),
        (COMMON_FEATURES, [ENV_COMMON_FEATURES]),
    )

    EXTRA_CONFIG_MAP = {
        "EDXAPP_LMS_ENV_EXTRA": [ENV_LMS],
        "EDXAPP_CMS_ENV_EXTRA": [ENV_CMS],
        "EDXAPP_ENV_EXTRA": [ENV_LMS, ENV_CMS],
        "EDXAPP_FEATURES_EXTRA": [ENV_COMMON_FEATURES]
    }

    def parse_ansible_configuration(self, grove_env_configuration, configuration_extra_settings):
        """
        Parse old ansible configuration settings and build payload from Grove pipeline
        """
        for ansible_key, config_value in configuration_extra_settings.items():
            self._check_and_update_grove_config(grove_env_configuration, ansible_key, config_value)
        self._update_extra_config(grove_env_configuration, configuration_extra_settings)

    def _check_and_update_grove_config(self, grove_env_config, ansible_key, config_value):
        """
        Check if ansible config key is for LMS, CMS or both and append config to correct payload key(s).
        """
        for config_map in self.CONFIG_MAP:
            (ansible_key_map, grove_config_types) = config_map
            if ansible_key in ansible_key_map:
                grove_config_key = ansible_key_map.get(ansible_key)
                config = {grove_config_key: config_value}
                self._update_grove_config(grove_env_config, grove_config_types, config)
                return True
        return False

    def _update_extra_config(self, grove_env_config, configuration_extra_settings):
        """
        Append EXTRA configs as-is to correct payload key(s).
        """
        for extra_config_key in self.EXTRA_CONFIG_MAP:
            extra_config = configuration_extra_settings.get(extra_config_key, {})
            grove_config_types = self.EXTRA_CONFIG_MAP.get(extra_config_key)
            self._update_grove_config(grove_env_config, grove_config_types, extra_config)

    def _update_grove_config(self, grove_env_config, grove_config_types, config):
        """
        Append config to given payload key(s).
        """
        for grove_config_type in grove_config_types:
            grove_env_config.get(grove_config_type).update(config)
