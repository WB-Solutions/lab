from django.shortcuts import render
from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError

from decimal import Decimal
import json

from .models import *

import utils

from rest_framework import viewsets
from .serializers import *

class AbstractView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    pass


class CountryViewSet(AbstractView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

class StateViewSet(AbstractView):
    queryset = State.objects.all()
    serializer_class = StateSerializer

class CityViewSet(AbstractView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

class BrickViewSet(AbstractView):
    queryset = Brick.objects.all()
    serializer_class = BrickSerializer

class ZipViewSet(AbstractView):
    queryset = Zip.objects.all()
    serializer_class = ZipSerializer


class UserCatViewSet(AbstractView):
    queryset = UserCat.objects.all()
    serializer_class = UserCatSerializer

class ItemCatViewSet(AbstractView):
    queryset = ItemCat.objects.all()
    serializer_class = ItemCatSerializer

class LocCatViewSet(AbstractView):
    queryset = LocCat.objects.all()
    serializer_class = LocCatSerializer

class FormCatViewSet(AbstractView):
    queryset = FormCat.objects.all()
    serializer_class = FormCatSerializer


class ForceNodeViewSet(AbstractView):
    queryset = ForceNode.objects.all()
    serializer_class = ForceNodeSerializer

class ForceVisitViewSet(AbstractView):
    queryset = ForceVisit.objects.all()
    serializer_class = ForceVisitSerializer


class UserViewSet(AbstractView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class ItemViewSet(AbstractView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

class LocViewSet(AbstractView):
    queryset = Loc.objects.all()
    serializer_class = LocSerializer

class FormViewSet(AbstractView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

class FormFieldViewSet(AbstractView):
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
    def _ext(db1, d2):
        d2.update(id=db1.id, full=str(db1))
        return d2
    def _dict(dbn, fn):
        return dict([ (each.id, _ext(each, fn(each)))
            for each in dbn ])
    data = None
    nodes = None
    user = config.get('user')
    if user:
        nodes = ForceNode.objects.filter(user=user)
    else:
        node = config.get('node')
        if node:
            nodes = [node]
    visit = config.get('visit')
    if visit:
        if nodes is not None: error
        nodes = [visit.node]
    if nodes:
        forms = Form.objects.order_by('order').all()
        def _reduce(_fn, _els):
            # print '_reduce'
            return reduce(list.__add__, [ list(_fn(each)) for each in _els ]) if _els else []
        def _names(rel):
            return ', '.join([ each.name for each in rel.all() ])
        def _visit(visit, ext=False):
            loc = visit.loc
            user = loc.user
            node = visit.node
            # print '_visit', visit, ext, user, loc, node
            def _ups(treenode):
                return treenode.get_ancestors(include_self=True)
            def _any(n1, n2, asdb=True, ups=True):
                n1 = n1.all() if asdb else n1
                if ups:
                    n1 = _reduce(lambda ex: _ups(ex), n1)
                # print '_any', n1, n2
                return any( [ each for each in n1 if each in n2.all() ] )
            upnodes = _ups(node)
            itemcats = _reduce(lambda node: node.itemcats.all(), upnodes)
            # bricks = _reduce(lambda node: node.bricks, upnodes)
            v = dict(
                datetime = _datetime(visit.datetime),
                status = visit.status,
                accompanied = visit.accompanied,
                observations = visit.observations,
                user_name = user.fullname(),
                user_email = user.email,
                user_cats = _names(user.cats),
                loc_name = loc.name,
                loc_address = '%s # %s, %s, %s' % (loc.street, loc.unit, loc.city, loc.zip),
                forms = [ form.id for form in forms
                          if False
                          or loc.zip.brick in form.bricks.all()
                          or _any(upnodes, form.forcenodes, ups=False)
                          or _any(user.cats, form.usercats)
                          or _any(itemcats, form.itemcats, asdb=False)
                          or _any(loc.cats, form.loccats)
                          ],
                rec = visit.rec_dict(),
            )
            if ext:
                _ext(visit, v)
            return v
        if visit:
            data = _visit(visit, ext=True)
        else:
            visits = _reduce(lambda node: node.visits.all(), nodes)
            # print 'visits', visits
            data = dict(
                visits = _dict(visits, _visit),
                forms = _dict(forms, lambda form: dict(
                    name = form.name,
                    fields = _dict(form.fields.all(), lambda field: dict(
                        name = field.name,
                        required = field.required,
                        default = field.default,
                        opts = field.opts(),
                    )),
                )),
            )
    # print '_data', config, data
    return data

def agenda(request):
    data = None
    def _dbget(dbmodel, dbid):
        return utils.db_get(dbmodel, dbid)
    for name, model in [ ('node', ForceNode), ('user', User), (None, User) ]:
        if name is None:
            user = request.user
            if user and user.is_authenticated():
                name = 'user'
                scope = user.id
            else:
                scope = None
        else:
            scope = request.GET.get(name)
        if scope:
            row = _dbget(model, scope)
            if row:
                # print 'agenda > scope', scope, model, row
                data = _data({name:row})
            break
    return render(request, 'lab/agenda.html', dict(agenda=True, data=json.dumps(data) or 'null'))

def ajax(request):
    pvars = json.loads(request.POST.get('data'), parse_float=Decimal)
    # print 'ajax', pvars
    def _get(key, default=None):
        pv = pvars.get(key)
        # print '_get', key, pv
        return pv or ('' if default is None else default)
    def _dbget(dbmodel, dbid):
        return utils.db_get(dbmodel, dbid)
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
    visit = _ref('ref_visit', ForceVisit)
    # print 'ajax', visit
    errors = []
    try:
        with transaction.atomic():
            def _update(_obj, _dbvars):
                # print '_update', _obj, _dbvars
                for dbk, dbv in _dbvars.items():
                    setattr(_obj, dbk, dbv)
                _obj.save()
            rec = visit.rec_dict()
            rec2 = pvars.get('rec')
            if rec2: # could be None.
                # print 'recs', rec, rec2
                rec.update(rec2)
            dbvars = dict(
                # sched = _get_datetime('sched'),
                status = _get('status'),
                observations = _get('observations'),
                rec = json.dumps(rec),
            )
            # print 'dbvars', dbvars
            _update(visit, dbvars)
    except IntegrityError as e:
        errors.append('Not unique, invalid.')
        # raise(e)
    except ValidationError as e:
        # print 'ValidationError @ views.py', e
        errors.append('Validation error:  %s' % '; '.join(e.messages))
        # raise(e)
    data = dict(
        error = ', '.join(errors),
        visit = None if errors else _data(dict(visit=visit)),
    )
    # print 'ajax > data', data
    return HttpResponse(json.dumps(data))




from django.shortcuts import render_to_response
from django.template import RequestContext
from django.contrib.auth.decorators import login_required

from django.views.generic.edit import UpdateView
from django.core.urlresolvers import reverse_lazy
from django.contrib import messages

from .forms import *


@login_required
def member_index(request):
    return render_to_response("member/member-index.html", RequestContext(request))

@login_required
def member_action(request):
    return render_to_response("member/member-action.html", RequestContext(request))


class UserEditView(UpdateView):
    """Allow view and update of basic user data.

    In practice this view edits a model, and that model is
    the User object itself, specifically the names that
    a user has.

    The key to updating an existing model, as compared to creating
    a model (i.e. adding a new row to a database) by using the
    Django generic view ``UpdateView``, specifically the
    ``get_object`` method.
    """
    form_class = UserEditForm
    template_name = "auth/profile.html"
    #success_url = '/email-sent/'
    view_name = 'account_profile'
    success_url = reverse_lazy(view_name)

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        # TODO: not sure how to enforce *minimum* length of a field.
        #print "form valid..."
        #print "save to user:", self.request.user, form.cleaned_data
        form.save()
        messages.add_message(self.request, messages.INFO, 'User profile updated')
        return super(UserEditView, self).form_valid(form)

account_profile = login_required(UserEditView.as_view())
