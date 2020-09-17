# Generated by Django 2.2.12 on 2020-09-17 11:45

import django.core.validators
from django.db import migrations, models
import registration.models


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0017_betatestapplication_hero_cover_image'),
    ]

    operations = [
        migrations.AlterField(
            model_name='betatestapplication',
            name='subdomain',
            field=models.CharField(error_messages={'blacklisted': 'This domain name is not publicly available.', 'unique': 'This domain is already taken.'}, help_text='The URL students will visit. In the future, you will also have the possibility to use your own domain name.\n\nExample: hogwarts.plebia.net', max_length=255, unique=True, validators=[django.core.validators.MinLengthValidator(3, 'The subdomain name must at least have 3 characters.'), django.core.validators.MaxLengthValidator(63, 'The subdomain name can have at most have 63 characters.'), django.core.validators.RegexValidator('^[a-z0-9]([a-z0-9\\-]+[a-z0-9])?$', 'Please choose a name of at least 3 characters, using lower-case letters, numbers, and hyphens. Cannot start or end with a hyphen.'), registration.models.validate_available_subdomain], verbose_name='domain name'),
        ),
    ]
