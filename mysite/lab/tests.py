from django.test import TestCase
from cars.models import *
import utils

# python manage.py test
# Temporary test database, not affecting production.

class ServiceTaskMethodTests(TestCase):

    def _test_engine(self, compatible):
        def _new(dbmodel, **kwargs):
            return dbmodel.objects.create(**kwargs)
        def _new_name(dbmodel, **kwargs):
            return _new(dbmodel, name='Any', **kwargs)
        engine = _new_name(Engine)
        model = _new_name(Model, make=_new_name(Make), engine=engine)
        service = _new(Service, car=_new(Car, year=2000, owner=_new(Owner), model=model))
        task = _new_name(Task)
        if compatible:
            task.engines.add(engine)
        data = dict(service=service, task=task)
        error = utils.validate_engine(data)
        self.assertEqual(bool(error), not compatible)

    def test_engine_compatible(self):
        self._test_engine(True)

    def test_engine_incompatible(self):
        self._test_engine(False)

class CarMethodTests(TestCase):

    def test_other(self):
        car = Car()
        self.assertEqual(car.test_value(), True)
