
def db_models():
    from django.db.models import get_app, get_models
    app = get_app('lab')
    models = get_models(app)
    # print 'utils.models', app, models
    return models

def validate_X(data):
    isvalid = False
    service = data.get('service')
    task = data.get('task')
    if service and task:
        engine = service.car.model.engine
        engines = task.engines.all()
        isvalid = engine in engines
    # print 'validate_engine @ utils.py', [ service, task, isvalid ]
    if not isvalid:
        return 'Error: Incompatible Engine.'
