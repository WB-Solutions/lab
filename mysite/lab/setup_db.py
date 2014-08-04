from lab.models import *

import utils
dbmodels = utils.db_models()

def setup():

    return 'PENDING SETUP !!'

    """
    if Engine.objects.first():
        return 'Canceled, already setup.'

    def _new(dbmodel, **kwargs):
        return dbmodel.objects.create(**kwargs)

    owners = [ _new(Owner, name=name)
        for name in [ 'Steven Hines', 'Carlos Galindo', 'Vanessa Mar' ] ]

    engine_names = [ 'Diesel', 'Electric', 'Gasoline', 'Hybrid' ]
    engines = dict([ (name, _new(Engine, name=name)) for name in engine_names ])

    def _task(name, includes=None, excludes=None):
        task = _new(Task, name=name)
        if not includes:
            includes = engine_names
        if excludes:
            includes = [ each for each in includes if each not in excludes ]
        included = [ eng for key, eng in engines.items() if key in includes ]
        task.engines.add(*included)

    for name in engine_names:
        _task('%s engine maintenance' % name, includes=name)
    _task('Oil change', excludes=['Electric'])
    for name in [ 'Tire balancing', 'Tire rotation', 'Brake fluid', 'Car wash', 'Air filter' ]:
        _task(name)

    def _make_models(name, generic, iowner, models_engines):
        make = _new(Make, name=name)
        for eng in engine_names:
            models_engines.append(('%s %s' % (generic, eng[:3].lower()), eng))
        models = [ _new(Model, name=model, make=make, engine=engines[eng])
            for model, eng in models_engines ]
        if iowner is not None:
            model = models[iowner]
            engine = model.engine
            car = _new(Car, owner=owners[iowner], model=model, year=2015-iowner, plate=str(iowner + 1) * 6)
            service = _new(Service, car=car, odometer=(iowner + 1) * 10000, total='24.31')
            tasks = engine.task_set.all() # only compatible ones.
            servicetasks = [ _new(ServiceTask, service=service, task=task) for task in tasks ]

    _make_models('Honda', 'Civic', 0, [
        ('Fit', 'Gasoline'),
    ])

    _make_models('Toyota', 'RAV4', 1, [
        ('Prius', 'Hybrid'),
    ])

    _make_models('Volkswagen', 'Jetta', 2, [
        ('e-Golf', 'Electric'),
    ])

    _make_models('Nissan', 'Sentra', None, [
        ('Leaf', 'Electric'),
    ])

    return 'Done'
    """
