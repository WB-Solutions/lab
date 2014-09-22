from django.core.management.base import BaseCommand, CommandError
from lab.models import *

# https://docs.djangoproject.com/en/1.6/howto/custom-management-commands/

class Command(BaseCommand):
    args = 'none'
    help = 'setup_db'

    def handle(self, *args, **kwargs):
        if User.objects.exists():
            msg = 'Error: db already setup.'
        else:
            User.objects.create_superuser('admin@admin.com', 'admin')
            msg = 'Success'
        self.stdout.write(msg)
