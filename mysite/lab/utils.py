from django.core.exceptions import ValidationError
import datetime

weekdays = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')

def list_flatten(els, fn):
    return reduce(list.__add__, [ list(fn(each)) for each in els ]) if els else []

def list_compact(els):
    return [ each for each in els if each ]

def list_last(els):
    return els[-1] if els else None

def str_int(string):
    try: v = int(string)
    except: v = None
    return v

def str_ints(string, separator=','):
    return list_compact([ str_int(e) for e in string.split(separator) ])

def db_models():
    from django.db.models import get_app, get_models
    app = get_app('lab')
    models = get_models(app)
    # print 'utils.models', app, models
    return models

def db_get(model, dbid=None, **kwargs):
    if dbid:
        kwargs.update(pk=dbid)
    try:
        v = model.objects.get(**kwargs)
    except model.DoesNotExist:
        v = None
    # print 'db_get', model, v
    return v

def db_update(model, save_kwargs=None, **kwargs):
    # print 'utils.db_update', model, save_kwargs, kwargs
    for dbk, dbv in kwargs.items():
        setattr(model, dbk, dbv)
    kw = save_kwargs or dict()
    # print 'utils.db_update', kw
    model.save(**kw)

def db_names(rel):
    return ', '.join([ each.name for each in rel.all() ])

def db_ids(rows):
    return [ row.id for row in rows ]

def _agenda(scope, row, private=False):
    from django.utils.html import format_html
    return format_html('<a href="/lab/agenda?%s=%s&private=%s" target="_blank"> %s </a>' % (
        scope,
        row.id,
        int(private),
        'Private' if private else 'Agenda'
    ))

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

def tree_ups(node):
    return node.get_ancestors(include_self=True)

def tree_downs(node):
    return node.get_descendants(include_self=True)

def tree_any(n1, n2, ups=True):
    if ups:
        n1 = list_flatten(n1, lambda ex: tree_ups(ex))
    # print 'tree_any', n1, n2
    return any( [ each for each in n1 if each in n2.all() ] )

def tree_all_downs(cats):
    return set(list_flatten(cats, lambda ecat: tree_downs(ecat)))

def validate_one(list, msg):
    # print 'validate_one', list, msg
    if sum([ int(bool(each)) for each in list ]) != 1:
        raise ValidationError(msg)

def validate_xor(v1, v2, msg, reverse=False):
    # print 'validate_xor', v1, v2, msg, reverse
    def _val(v): # pending to support v as list.
        _v = bool(v)
        print 'validate_xor._val', v, _v
        return _v
    xor = _val(v1) ^ _val(v2)
    if xor if reverse else not xor:
        raise ValidationError(msg)

# datetime, date, time.
def validate_start_end(start, end, required=True):
    if start and end:
        if isinstance(start, datetime.date):
            msg = 'greater or equal'
            cond = end >= start
        else:
            msg = 'greater'
            cond = end > start
        if not cond:
            raise ValidationError('End must be %s than Start.' % msg)
    elif required:
        raise ValidationError('Start and End are required.')
    else:
        validate_xor(start, end, 'Start and End must both be either blank or entered', reverse=True)

def datetime_plus(dt, *durations):
    def _sum(attr):
        return sum([ getattr(e, attr) for e in durations ])
    return dt + datetime.timedelta(
        hours = _sum('hour'),
        minutes = _sum('minute'),
    )
