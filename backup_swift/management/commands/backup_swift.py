from django.core.management.base import BaseCommand, CommandError

from backup_swift.tasks import do_backup_swift


class Command(BaseCommand):

    def handle(self, *args, **options):
        do_backup_swift()
