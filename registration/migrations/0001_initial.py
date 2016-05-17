# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators
import registration.models
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BetaTestApplication',
            fields=[
                ('id', models.AutoField(serialize=False, primary_key=True, verbose_name='ID', auto_created=True)),
                ('subdomain', models.CharField(validators=[django.core.validators.RegexValidator('^[\\w.-]+$', "Please include only letters, numbers, '_', '-' and '.'"), registration.models.validate_available_subdomain], help_text='The URL students will visit. In the future, you will also have the possibility to use your own domain name.\n\nExample: hogwarts.opencraft.hosting', error_messages={'unique': 'This domain is already taken.'}, verbose_name='domain name', unique=True, max_length=255)),
                ('instance_name', models.CharField(help_text='The name of your institution, company or project.\n\nExample: Hogwarts Online Learning', max_length=255)),
                ('public_contact_email', models.EmailField(help_text='The email your instance of Open edX will be using to send emails, and where your users should send their support requests.\n\nThis needs to be a valid email.', max_length=254)),
                ('project_description', models.TextField(verbose_name='your project', help_text='What are you going to use the instance for? What are your expectations?')),
                ('subscribe_to_updates', models.BooleanField(verbose_name='', default=False, help_text='I want OpenCraft to keep me updated about the progress of the beta test, and occasionally send me an email about it.')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], default='pending', max_length=255)),
                ('user', models.OneToOneField(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
