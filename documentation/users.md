Creating users
--------------

### Superusers

In order to login to the development server locally you will need to create a
superuser by running:

    make manage createsuperuser

Once created, you will be able to login with the username and password you set
up.

Superusers can manage all instances and use all APIs.

### Instance Manager users

Instance manager users can manage instances and use the API, but are not permitted in the Admin area.
They are limited to manage instances of their own organization.

To create an instance manager user:

    make shell

    In [1]: from django.contrib.auth.models import User, Permission
    In [2]: from django.contrib.contenttypes.models import ContentType
    In [3]: content_type = ContentType.objects.get_for_model(InstanceReference)
    In [4]: permission = Permission.objects.get(content_type=content_type, codename='manage_own')
    In [5]: user = User.objects.create(username='instance_manager', password='password')
    In [6]: user.user_permissions.add(permission)
    In [7]: user.save()

And set `Organization` and `UserProfile` to the right values.

### Staff users

Staff users cannot manage instances or use the API, but are permitted in the
Admin area.

To create a staff user:

    make shell

    In [1]: from django.contrib.auth.models import User
    In [2]: user = User.objects.create(username='staff_user', password='password')
    In [3]: user.is_staff = True
    In [4]: user.save()
