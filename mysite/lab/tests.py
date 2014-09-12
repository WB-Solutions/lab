from django.test import TestCase
from .models import *
import utils

# python manage.py test
# Temporary test database, not affecting production.

class ForceVisitMethodTests(TestCase):

    def test_X(self):
        self.assertEqual(True, True)
