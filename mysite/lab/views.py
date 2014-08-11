from django.shortcuts import render
from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from decimal import Decimal

from lab.models import *
import json

import utils


from rest_framework import viewsets
from lab.serializers import *

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class BrickViewSet(viewsets.ModelViewSet):
    queryset = Brick.objects.all()
    serializer_class = BrickSerializer

class DoctorCatViewSet(viewsets.ModelViewSet):
    queryset = DoctorCat.objects.all()
    serializer_class = DoctorCatSerializer

class DoctorSpecialtyViewSet(viewsets.ModelViewSet):
    queryset = DoctorSpecialty.objects.all()
    serializer_class = DoctorSpecialtySerializer

class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer

class DoctorLocViewSet(viewsets.ModelViewSet):
    queryset = DoctorLoc.objects.all()
    serializer_class = DoctorLocSerializer

class ItemCatViewSet(viewsets.ModelViewSet):
    queryset = ItemCat.objects.all()
    serializer_class = ItemCatSerializer

class ItemSubcatViewSet(viewsets.ModelViewSet):
    queryset = ItemSubcat.objects.all()
    serializer_class = ItemSubcatSerializer

class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class MarketViewSet(viewsets.ModelViewSet):
    queryset = Market.objects.all()
    serializer_class = MarketSerializer

class ForceViewSet(viewsets.ModelViewSet):
    queryset = Force.objects.all()
    serializer_class = ForceSerializer

class ForceMgrViewSet(viewsets.ModelViewSet):
    queryset = ForceMgr.objects.all()
    serializer_class = ForceMgrSerializer

class ForceRepViewSet(viewsets.ModelViewSet):
    queryset = ForceRep.objects.all()
    serializer_class = ForceRepSerializer

class ForceVisitViewSet(viewsets.ModelViewSet):
    queryset = ForceVisit.objects.all()
    serializer_class = ForceVisitSerializer

class FormViewSet(viewsets.ModelViewSet):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

class FormFieldViewSet(viewsets.ModelViewSet):
    queryset = FormField.objects.all()
    serializer_class = FormFieldSerializer


def index(request):
    return render(request, 'lab/index.html', dict())

def setup(request):
    import setup_db
    return HttpResponse(setup_db.setup())

def _data(config=None):
    # print '_data', config
    def _all(dbmodel):
        return dbmodel.objects.all()
    def _list(dbmodel):
        return [ config.get(dbmodel) ] if config else _all(dbmodel)
    def _datetime(datetime):
        return str(datetime) if datetime else ''
    def _dict(data, fn):
        return dict([ (each.id, dict(id=each.id, full=str(each), **fn(each)))
            for each in data ])
    """
    data = dict(
        forces = _dict(_list(Force), lambda force: dict(
            name = force.name,
            mgrs = _dict(force.forcemgr_set.all(), lambda mgr: dict(
                reps = _dict(mgr.forcerep_set.all(), lambda rep: dict(
                )),
            )),
        )),
    )
    """
    rep = config.get('rep')
    def _names(rel):
        return ', '.join([ each.name for each in rel.all() ])
    def _visit(visit):
        loc = visit.loc
        doc = loc.doctor
        user = doc.user

        return dict(
            datetime = _datetime(visit.datetime),
            observations = visit.observations,
            doc_name = user.fullname(),
            doc_email = user.email,
            doc_cats = _names(doc.cats),
            doc_specialties = _names(doc.specialties),
            loc_name = loc.name,
            loc_address = '%s # %s, %s' % (loc.street, loc.unit, loc.zip),
        )
    data = dict(
        visits = _dict(rep.visits(), _visit),
    )
    """
    if not config:
        data.update(
            tasks = _dict(_all(Task), lambda task: dict(
                name = task.name,
                engines = [ engine.id for engine in task.engines.all() ],
            )),
            models = _dict(_all(Model), lambda model: dict(
                name = model.name,
                engine = model.engine.id,
                engine_name = model.engine.name,
            )),
        )
    """
    print '_data', config, data
    return data

def agenda(request):
    data = None
    def _dbget(dbmodel, dbid):
        return dbmodel.objects.get(pk=dbid)
    scope = request.GET.get('rep')
    if scope: # only rep scope supported for now.
        print 'agenda > rep scope', scope
        rep = _dbget(ForceRep, scope)
        if rep:
            data = _data(dict(rep=rep))
    return render(request, 'lab/agenda.html', dict(agenda=True, data=json.dumps(data or dict())))

def ajax(request):

    return HttpResponse('PENDING AJAX')

    pvars = json.loads(request.POST.get('data'), parse_float=Decimal)
    # print 'ajax', pvars
    def _get(key, default=None):
        pv = pvars.get(key)
        # print '_get', key, pv
        return pv or ('' if default is None else default)
    def _dbget(dbmodel, dbid):
        return dbmodel.objects.get(pk=dbid)
    def _ref(key, dbmodel):
        pv = _get(key)
        pv = _dbget(dbmodel, pv) if pv else None
        # print 'ajax > _ref', key, dbmodel, pv.id if pv else None, pv
        return pv
    def _get_datetime(key):
        return _get(key) or None
    def _new(dbmodel, **kwargs):
        return dbmodel.objects.create(**kwargs)
    def _int(string):
        try: v = int(string)
        except: v = None
        return v
    def _decimal(string):
        try: v = Decimal(string)
        except: v = None
        return v
    service = _ref('ref_service', Service)
    car = _ref('ref_car', Car)
    owner = _ref('ref_owner', Owner)
    # print 'ajax > refs', [ service, car, owner ]
    errors = []
    try:
        with transaction.atomic():
            def _update(_obj, _dbvars):
                # print '_update', _obj, _dbvars
                for dbk, dbv in _dbvars.items():
                    setattr(_obj, dbk, dbv)
                _obj.save()
            if service:
                car = service.car
            if car:
                owner = car.owner
            else:
                if not owner:
                    owner = _new(Owner, name=_get('car_owner_name'))
                model = _ref('car_model', Model)
                car = _new(Car,
                    owner = owner,
                    model = model,
                    year = _int(_get('car_year')) or 2000,
                    plate = _get('car_plate'),
                )
            dbvars = dict(
                car = car,
                odometer = _int(_get('odometer')) or 0,
                sched = _get_datetime('sched'),
                enter = _get_datetime('enter'),
                exit = _get_datetime('exit'),
                total = _decimal(_get('total')) or 0,
                observations = _get('observations'),
            )
            # print 'service dbvars', dbvars
            if service:
                _update(service, dbvars)
            else:
                service = _new(Service, **dbvars)
            # print 'car', car
            # print 'service', service
            webtasks = pvars.get('servicetasks') or []
            # print 'webtasks', webtasks
            for webtask in webtasks:
                pvars = webtask # reset to reuse _get methods above.
                servicetask_id = _int(webtask.get('id'))
                # print 'servicetask_id', servicetask_id
                task_id = _int(webtask.get('task'))
                task = _dbget(Task, task_id) if task_id else None
                # print 'task', task
                if task:
                    dbvars = dict(
                        start = _get_datetime('start'),
                        end = _get_datetime('end'),
                        observations = _get('observations'),
                    )
                    # print 'servicetask dbvars', dbvars
                    if servicetask_id: # update.
                        servicetask = _dbget(ServiceTask, servicetask_id)
                        _update(servicetask, dbvars)
                    else: # create.
                        dbvars.update(
                            service = service,
                            task = task,
                        )
                        err = utils.validate_engine(dbvars)
                        if err:
                            raise ValidationError(err)
                        _new(ServiceTask, **dbvars)
            # NO deletes for now.
    except IntegrityError as e:
        errors.append('Not unique, invalid.')
        # raise(e)
    except ValidationError as e:
        # print 'ValidationError @ views.py', e
        errors.append('Validation error:  %s' % '; '.join(e.messages))
        # raise(e)
    data = dict(
        error = ', '.join(errors),
        data = dict() if errors else _data({ Owner: owner, Car: car, Service: service }),
    )
    # print 'ajax > data', data
    return HttpResponse(json.dumps(data))
