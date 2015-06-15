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

def _data(request, config=None):
    # print '_data', config
    def _all(model):
        return model.objects.all()
    def _list(model):
        return [ config.get(model) ] if config else _all(model)
    def _datetime(datetime):
        return str(datetime) if datetime else ''
    def _ext(db1, d2):
        d2.update(id=db1.id, full=str(db1))
        return d2
    def _dict(dbn, fn):
        return dict([ (each.id, _ext(each, fn(each)))
            for each in dbn ])
    private = bool(utils.str_int(request.GET.get('private')))
    # print '_data.private', private
    data = None
    go_nodes = None
    go_user = config.get('user')
    if go_user:
        go_nodes = ForceNode.objects.filter(user=go_user)
    else:
        go_node = config.get('node')
        if go_node:
            go_nodes = [go_node]
            go_user = go_node.user # could be None.
    visit = config.get('visit')
    if visit:
        if go_nodes is not None: error
        go_nodes = [visit.node]
    if go_nodes:
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
                    items = ItemCat.els_get(_itemcats),
                )
                cached[_node] = d
            # print '_node_data cached', iscached, _node, d
            return d

        def _visit(visit, ext=False):
            loc = visit.loc
            user = loc.user
            forms_ids, repdict_items_ids, repdict_usercats_ids = Form.get_forms_reps(
                baseuser = user,
                private = private,
                visit = visit,
                usercats = user.cats.all(),
                loccats = loc.cats.all(),
                **_node_data(visit.node)
            )
            addr = loc.addr()
            dt = visit.datetime
            v = dict(
                datetime = _datetime(dt),
                end = _datetime(utils.datetime_plus(dt, visit.duration)),
                status = visit.status,
                accompanied = visit.accompanied,
                observations = visit.observations,
                user_name = user.fullname(),
                user_email = user.email,
                user_cats = utils.db_names(user.cats),
                loc_name = loc.name,
                loc_address = '%s # %s, %s' % (addr.street, addr.unit, addr.area),
                forms = forms_ids,
                repdict_items = repdict_items_ids,
                repdict_usercats = repdict_usercats_ids,
                rec = visit.rec_dict(),
            )
            if ext:
                _ext(visit, v)
            return v

        if visit:
            data = _visit(visit, ext=True)
        else:
            visits = utils.list_flatten(go_nodes, lambda node: node.visits.all())
            allitems = _all(Item)
            allusercats = _all(UserCat)
            allformtypes = _all(FormType)
            allforms = Form.objects.order_by('order', 'name').all()
            user_dict = None
            if go_user:
                forms_ids, repdict_items_ids, repdict_usercats_ids = go_user.get_forms_reps(private=private)
                formids = forms_ids + repdict_items_ids.keys() + repdict_usercats_ids.keys()
                recs = UserFormRec.objects.filter(form__in=formids)
                user_dict = dict(
                    id = go_user.id,
                    name = go_user.fullname(),
                    forms = forms_ids,
                    repdict_items = repdict_items_ids,
                    repdict_usercats = repdict_usercats_ids,
                    recs = dict([ (rec.form.id, rec.rec_dict()) for rec in recs ])
                )
            def _types(row):
                types = row.types.all()
                # return _dict(types, lambda field: dict())
                return utils.db_ids(types)
            def _reps(reps):
                return _dict(reps, lambda erep: dict(
                    name = erep.name,
                    description = erep.forms_description,
                    expandable = erep.forms_expandable,
                    order = erep.forms_order,
                ))
            data = dict(
                user = user_dict,
                nodes = _dict(go_nodes, lambda node: dict(
                    name = node.name,
                )),
                visits = _dict(visits, _visit),
                allitems = _reps(allitems),
                allusercats = _reps(allusercats),
                allformtypes = _dict(allformtypes, lambda ftype: dict(
                    name = ftype.name,
                    description = ftype.description,
                    order = ftype.order,
                )),
                allforms = _dict(allforms, lambda form: dict(
                    name = form.name,
                    description = form.description,
                    expandable = form.expandable,
                    order = form.order,
                    fields = _dict(form.fields.all(), lambda field: dict(
                        name = field.name,
                        description = field.description,
                        type = field.type,
                        widget = field.widget,
                        default = field.default,
                        required = field.required,
                        order = field.order,
                        opts = field.opts(),
                        types = _types(field),
                    )),
                    types = _types(form),
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
                data = _data(request, {name:row})
            break
    return render(request, 'lab/agenda.html', dict(agenda=True, data=json.dumps(data) or 'null'))

def ajax(request):
    pvars = json.loads(request.POST.get('data'), parse_float=Decimal)
    # print 'ajax', pvars
    def _get(key, default=None):
        pv = pvars.get(key)
        # print '_get', key, pv
        return pv or ('' if default is None else default)
    def _ref(key, model):
        pv = _get(key)
        pv = utils.db_get(model, pv) if pv else None
        # print 'ajax > _ref', key, model, pv.id if pv else None, pv
        return pv
    def _get_datetime(key):
        return _get(key) or None
    def _new(model, **kwargs):
        return model.objects.create(**kwargs)
    def _int(string):
        try: v = int(string)
        except: v = None
        return v
    def _decimal(string):
        try: v = Decimal(string)
        except: v = None
        return v
    visit = _ref('ref_visit', ForceVisit)
    user = _ref('ref_user', User)
    form = _ref('ref_form', Form)
    print 'ajax', visit, user, form
    errors = []
    try:
        with transaction.atomic():
            if visit:
                base = visit
                rec = visit.rec_dict()
            else:
                if not (user and form):
                    raise ValidationError('User and Form are required.')
                dbgetvars = dict(user=user, form=form)
                base = utils.db_get(UserFormRec, **dbgetvars)
                rec = dict()
            rec2 = pvars.get('rec')
            if rec2: # could be None.
                # print 'recs', rec, rec2
                rec.update(rec2)
            dbvars = dict(
                observations = _get('observations'),
                rec = json.dumps(rec),
            )
            if visit:
                dbvars.update(
                    # sched = _get_datetime('sched'),
                    status = _get('status'),
                    accompanied = _get('accompanied'),
                )
            elif not base:
                dbvars.update(dbgetvars)
            print 'dbvars', dbvars
            if base:
                utils.db_update(base, **dbvars)
            else:
                base = _new(UserFormRec, **dbvars)
    except IntegrityError as e:
        errors.append('Not unique, invalid.')
        # raise(e)
    except ValidationError as e:
        # print 'ValidationError @ views.py', e
        errors.append('Validation error:  %s' % '; '.join(e.messages))
        # raise(e)
    data = dict(
        error = ', '.join(errors),
        visit = None if errors else _data(request, dict(visit=visit)),
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
