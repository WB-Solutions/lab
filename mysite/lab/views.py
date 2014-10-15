from django.shortcuts import render
from django.http import HttpResponse
from django.db import IntegrityError, transaction
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy

from decimal import Decimal
import json

from .models import *

import utils


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
        def _cats_items(_cats):
            return Item.objects.filter(cats__in=_cats).order_by('name').all()
        cached = dict()
        def _node_data(_node):
            d = cached.get(_node)
            iscached = d is not None
            if not iscached:
                _upnodes = utils.tree_ups(_node)
                _itemcats = utils.tree_all_downs(utils.list_flatten(_upnodes, lambda enode: enode.itemcats.all()))
                d = dict(
                    upnodes = _upnodes,
                    itemcats = _itemcats,
                    items = _cats_items(_itemcats),
                )
                cached[_node] = d
            # print '_node_data cached', iscached, _node, d
            return d
        allforms = Form.objects.order_by('order', 'name').all()
        _any = utils.tree_any
        def _visit(visit, ext=False):
            loc = visit.loc
            loccats = loc.cats
            user = loc.user
            usercats = user.cats
            node = visit.node
            nodedata = _node_data(node)
            # print '_visit', visit, ext, user, loc, node, nodedata
            upnodes = nodedata.get('upnodes')
            itemcats = nodedata.get('itemcats')
            items = nodedata.get('items')
            repforms = dict()
            def _doreps(form):
                reps1 = form.repitems.all()
                repcats = utils.tree_all_downs(form.repitemcats.all())
                reps2 = _cats_items(repcats)
                reps = (reps1 | reps2).distinct()
                # print '_doreps > reps', reps
                if reps.exists(): # must check, even if empty after the below filter.
                    reps = reps.filter(id__in=items).all()
                    for item in reps:
                        if _any(usercats, item.visits_usercats) or _any(loccats, item.visits_loccats):
                            k = item.id
                            rforms = repforms.get(k) or []
                            repforms[k] = rforms
                            rforms.append(form.id)
                    return False
                return True
            forms = [ form for form in allforms
                      if (
                          False
                          or loc.zip.brick in form.visits_bricks.all()
                          or _any(upnodes, form.visits_forcenodes, ups=False)
                          or _any(usercats, form.visits_usercats)
                          or _any(itemcats, form.visits_itemcats, asdb=False)
                          or _any(loccats, form.visits_loccats)
                      ) and _doreps(form) ]
            # print 'repforms', repforms
            v = dict(
                datetime = _datetime(visit.datetime),
                status = visit.status,
                accompanied = visit.accompanied,
                observations = visit.observations,
                user_name = user.fullname(),
                user_email = user.email,
                user_cats = utils.db_names(user.cats),
                loc_name = loc.name,
                loc_address = '%s # %s, %s, %s' % (loc.street, loc.unit, loc.city, loc.zip),
                forms = utils.db_ids(forms),
                repforms = repforms,
                rec = visit.rec_dict(),
            )
            if ext:
                _ext(visit, v)
            return v
        if visit:
            data = _visit(visit, ext=True)
        else:
            visits = utils.list_flatten(nodes, lambda node: node.visits.all())
            # print 'visits', visits
            allitems = _all(Item)
            # print 'allitems', allitems
            data = dict(
                visits = _dict(visits, _visit),
                items = _dict(allitems, lambda item: dict(
                    name = item.name,
                    description = item.visits_description,
                    expandable = item.visits_expandable,
                    order = item.visits_order,
                )),
                forms = _dict(allforms, lambda form: dict(
                    name = form.name,
                    description = form.description,
                    expandable = form.expandable,
                    order = form.order,
                    repitems = utils.db_ids(form.repitems.all()),
                    fields = _dict(form.fields.all(), lambda field: dict(
                        name = field.name,
                        description = field.description,
                        type = field.type or '',
                        widget = field.widget or '',
                        default = field.default,
                        required = field.required,
                        order = field.order,
                        opts = field.opts(),
                    )),
                )),
            )
    # print '_data', config, data
    return data

def agenda(request):
    data = None
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
            row = utils.db_get(model, scope)
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
