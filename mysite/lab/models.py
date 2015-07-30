from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext as _ # use ugettext_lazy instead?.
from django.utils import timezone

from decimal import Decimal
import datetime
import json

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel

import utils

def _time_choice(h, m):
    t = datetime.time(h, m)
    return (t, t.strftime('%H:%M'))

time_choices = reduce(lambda x, y: x + [ _time_choice(y, e) for e in [ 0, 15, 30, 45 ] ], range(24), [])

class GoTreeM2MField(models.ManyToManyField):

    pass

def _kw_merge(kwmain, **kwdef):
    return dict(kwdef, **kwmain)

def _char(*args, **kwargs):
    return models.CharField(*args, **_kw_merge(kwargs, max_length=200))

def _char_blank(*args, **kwargs):
    return _char(*args, **_kw_merge(kwargs, blank=True))

def _name(**kwargs):
    return _char(_('name'), **kwargs)

def _name_unique(**kwargs):
    return _name(**_kw_merge(kwargs, unique=True))

def _text(*args, **kwargs):
    return models.TextField(*args, **_kw_merge(kwargs, blank=True))

def _boolean(default, *args, **kwargs):
    return models.BooleanField(*args, **_kw_merge(kwargs, default=default))

def _int(*args, **kwargs):
    return models.IntegerField(*args, **_kw_merge(kwargs, default=0))

def _int_blank(*args, **kwargs):
    return _int(*args, **_kw_merge(kwargs, blank=True, null=True))

def _time(*args, **kwargs):
    return models.TimeField(*args, **kwargs)

def _time_blank(*args, **kwargs):
    return _time(*args, **_kw_merge(kwargs, blank=True, null=True))

def _duration(hrs=0, mins=45):
    return _time(
        choices = time_choices[1:7],
        default = datetime.time(hrs, mins),
    )

def _date(*args, **kwargs):
    return models.DateField(*args, **kwargs)

def _date_blank(*args, **kwargs):
    return _date(*args, **_kw_merge(kwargs, blank=True, null=True))

def _datetime(*args, **kwargs):
    return models.DateTimeField(*args, **kwargs)

def _datetime_now(*args, **kwargs):
    return _datetime(*args, **_kw_merge(kwargs, default=timezone.now))

def _datetime_blank(*args, **kwargs):
    return _datetime(*args, **_kw_merge(kwargs, blank=True, null=True))

def _datetime_blank_now(*args, **kwargs):
    return _datetime_blank(*args, **_kw_merge(kwargs, default=timezone.now))

def _one_one(to, related, **kwargs):
    return models.OneToOneField(to, related_name=related, **kwargs)

def _one_one_blank(*args, **kwargs):
    return _one_one(*args, **_kw_merge(kwargs, blank=True, null=True))

def _one(to, related, **kwargs):
    # print '_one', to, related, kwargs
    return models.ForeignKey(to, related_name=related, **kwargs)

def _one_blank(*args, **kwargs):
    return _one(*args, **_kw_merge(kwargs, blank=True, null=True))

def __base_many(base, to, related, **kwargs):
    return base(to, **_kw_merge(kwargs, blank=True, related_name=related))

def _many(*args, **kwargs):
    return __base_many(models.ManyToManyField, *args, **kwargs)

def _many_tree(*args, **kwargs):
    return __base_many(GoTreeM2MField, *args, **kwargs)

# do NOT allow EMPTY / BLANK, otherwise can NOT filter (ignored) in admin & REST.
def _choices(vmax, choices, **kwargs):
    choices = [ e if isinstance(e, (list, tuple)) else (e, e) for e in choices ]
    # print '_choices', choices
    return _char(**_kw_merge(kwargs, max_length=vmax, default=choices[0][0], choices=choices))

def multiple_(row, prop):
    return ', '.join(sorted([ str(each) for each in getattr(row, prop).all() ]))

def _str(row, tmpl, values):
    v = (tmpl % values) if tmpl else values
    # v = '(%s. %s)' % (row.id, v) # parenthesis to separate nested row ids in values, e.g. items: ids for item / cat / subcat.
    # print '_str', v
    return unicode(v)

def _form_expandable():
    return _boolean(False)

def _form_order():
    return _int_blank()

def _form_description():
    return _text()


# http://bitofpixels.com/blog/unique-on-charfield-when-blanktrue/
class GoNullableUniqueField(models.CharField):

    def to_python(self, value):
        val = super(GoNullableUniqueField, self).to_python(value)
        return '' if val is None else val

    def get_prep_value(self, value):
        return value or None

def _syscode(**kwargs):
    return GoNullableUniqueField(**_kw_merge(kwargs, max_length=200, blank=True, null=True, unique=True))


class AbstractModel(models.Model):

    syscode = _syscode()

    class Meta:
        abstract = True

    def __unicode__(self):
        return _str(self, None, self.name)

    def syscodes_(self):
        return ' : '.join([ str(each) for each in [ self.id, self.syscode ] if each ])

    def onoffperiod_visited_(self): return multiple_(self, 'onoffperiod_visited')
    def onoffperiod_visit_(self): return multiple_(self, 'onoffperiod_visit')
    def onofftime_visited_(self): return multiple_(self, 'onofftime_visited')
    def onofftime_visit_(self): return multiple_(self, 'onofftime_visit')

    def cats_(self):
        return multiple_(self, 'cats')


# http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
class AbstractTree(MPTTModel, AbstractModel):

    name = _name()
    parent = TreeForeignKey('self', blank=True, null=True, related_name='children')
    order = _form_order()

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ('order', 'name')

    def __unicode__(self):
        return _str(self, '%s %s', (self.str_level(), self.name))

    els_field = 'name'

    @classmethod
    def els_get(cls, cats):
        elsmodel = globals().get(cls.els_model)
        return elsmodel.objects.filter(cats__in=cats).order_by(cls.els_field).all()

    def str_level(self, diff=0):
        return ' -- ' * ((self.level or 0) - diff)

    def save(self, *args, **kwargs):
        # print 'AbstractTree.save', self, args, kwargs
        super(AbstractTree, self).save(*args, **kwargs)
        self.__class__.objects.rebuild()



class Country(AbstractModel):

    name = _name_unique()

    class Meta:
        ordering = ('name',)



class State(AbstractModel):

    name = _name()
    country = _one(Country, 'states')

    class Meta:
        unique_together = ('country', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.country))



class City(AbstractModel):

    name = _name()
    state = _one(State, 'cities')

    class Meta:
        unique_together = ('state', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.state))



class Brick(AbstractModel):

    name = _name_unique()

    class Meta:
        ordering = ('name',)



class Zip(AbstractModel):

    name = _name_unique()
    brick = _one(Brick, 'zips')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.brick))



class Area(AbstractModel):

    name = _name()
    city = _one(City, 'areas')
    zip = _one(Zip, 'areas')

    class Meta:
        unique_together = ('city', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s @ %s', (self.name, self.city, self.zip))



class GenericCat(AbstractTree):

    pass



class PeriodCat(AbstractTree):

    els_model = 'Period'



class UserCat(AbstractTree):

    els_model = 'User'
    els_field = 'email'

    forms_description = _form_description()
    forms_expandable = _form_expandable()
    forms_order = _form_order()



class ItemCat(AbstractTree):

    els_model = 'Item'



class LocCat(AbstractTree):

    els_model = 'Loc'



class PlaceCat(AbstractTree):

    els_model = 'Place'



class FormCat(AbstractTree):

    els_model = 'Form'



class DayConfig(AbstractModel):

    name = _char()

    class Meta:
        ordering = ('name',)



class TimeConfig(AbstractModel):

    name = _char_blank()
    day = _one(DayConfig, 'times')
    start = _time(choices=time_choices)
    end = _time(choices=time_choices)

    class Meta:
        ordering = ('start', 'end')

    def __unicode__(self):
        return _str(self, '%s: %s - %s', (self.name, self.start, self.end))

    def clean(self):
        utils.validate_start_end(self.start, self.end)



class WeekConfig(AbstractModel):

    name = _char()

    # @ utils.weekdays.
    mon = _one_blank(DayConfig, 'weeks_mon')
    tue = _one_blank(DayConfig, 'weeks_tue')
    wed = _one_blank(DayConfig, 'weeks_wed')
    thu = _one_blank(DayConfig, 'weeks_thu')
    fri = _one_blank(DayConfig, 'weeks_fri')
    sat = _one_blank(DayConfig, 'weeks_sat')
    sun = _one_blank(DayConfig, 'weeks_sun')

    class Meta:
        ordering = ('name',)

    def delete(self):
        if self.sys_user_visit or self.sys_user_visited or self.sys_period:
            raise ValidationError('Sys - can NOT be deleted.')



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils.http import urlquote
from django.core.mail import send_mail

class UserManager(BaseUserManager):

    def _create_user(self, email, password, is_staff, is_superuser, **extra_fields):
        # print '_create_user', email, password, is_staff, is_superuser, extra_fields
        now = timezone.now()
        email = self.normalize_email(email)
        user = self.model(email=email, is_staff=is_staff, is_active=True, is_superuser=is_superuser, date_joined=now, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        return self._create_user(email, password, False, False, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        # print 'create_superuser', email, password, extra_fields
        return self._create_user(email, password, True, True, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin, AbstractModel):

    email = models.EmailField(_('email address'), blank=False, unique=True)
    first_name = _char_blank()
    last_name = _char_blank()
    display_name = _char_blank()
    is_staff = _boolean(False, help_text=_('Designates whether the user can log into this admin site.'))
    is_active = _boolean(True, help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    date_joined = _datetime_blank_now()

    week_visit = _one_blank(WeekConfig, 'users_visit')
    week_visited = _one_blank(WeekConfig, 'users_visited')
    cats = _many_tree(UserCat, 'users')

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        # db_table = 'auth_user'
        # abstract = False

    def __unicode__(self):
        return _str(self, None, self.email) # _str(self, '%s [ %s ]', (self.email, self.cats_()))

    def fullname(self):
        return '%s %s' % (self.first_name, self.last_name)

    def get_absolute_url(self):
        # TODO: what is this for?
        return "/users/%s/" % urlquote(self.email)  # TODO: email ok for this? better to have uuid?

    @property
    def name(self):
        if self.first_name:
            return self.first_name
        elif self.display_name:
            return self.display_name
        return 'You'

    def get_full_name(self):
        """
        Returns the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        "Returns the short name for the user."
        return self.first_name

    def _pwd(self):
        return '@' if self.password else ''

    def guess_display_name(self):
        """Set a display name, if one isn't already set."""
        if self.display_name:
            return

        if self.first_name and self.last_name:
            dn = "%s %s" % (self.first_name, self.last_name[0]) # like "Andrew E"
        elif self.first_name:
            dn = self.first_name
        else:
            dn = 'You'
        self.display_name = dn.strip()

    def email_user(self, subject, message, from_email=None):
        """
        Sends an email to this User.
        """
        send_mail(subject, message, from_email, [self.email])

    def natural_key(self):
        return (self.email,)

    # def has_perm(self, perm, obj=None): return True # does the user have a specific permission?.
    # def has_module_perms(self, app_label): return True # does the user have permissions to view the app "app_label"?.

    def allcats(self):
        return utils.tree_all_downs(self.cats.all())

    def get_forms_reps(self, **kwargs):
        locs = self.locs.all()
        loccats = utils.list_flatten(locs, lambda loc: loc.cats.all())
        return Form.get_forms_reps(
            baseuser = self,
            user = self,
            loccats = loccats,
            usercats = self.allcats(),
            **kwargs
        )



class Item(AbstractModel):

    name = _name_unique()
    cats = _many_tree(ItemCat, 'items')

    visits_usercats = _many_tree(UserCat, 'visits_items')
    visits_loccats = _many_tree(LocCat, 'visits_items')

    forms_description = _form_description()
    forms_expandable = _form_expandable()
    forms_order = _form_order()

    class Meta:
        ordering = ('name',)

    def visits_usercats_(self):
        return multiple_(self, 'visits_usercats')

    def visits_loccats_(self):
        return multiple_(self, 'visits_loccats')



class Address(AbstractModel):

    # name = _char_blank()
    street = _char()
    unit = _char_blank()
    phone = _char_blank()
    phone2 = _char_blank()
    fax = _char_blank()
    # canplace = _boolean(False)

    area = _one(Area, 'addresses')
    # zip = _one(Zip, 'addresses')
    # city = _one(City, 'addresses')

    class Meta:
        ordering = ('street',)

    def __unicode__(self):
        return _str(self, '%s # %s, %s', (self.street, self.unit, self.area))

class Place(AbstractTree):

    address = _one_blank(Address, 'places') # must be blank & null to be able to set & validate in clean below.
    # canloc = _boolean(True)
    cats = _many_tree(PlaceCat, 'places')

    def clean(self):
        if self.address:
            for each in [ self.parent, self.children.first() ]:
                if each and each.address != self.address:
                    raise ValidationError('Invalid Address based on Parent / Children.')
        elif self.parent:
            self.address = self.parent.address
        else:
            raise ValidationError(dict(address='Address is required for root elements.'))

class Loc(AbstractModel):

    name = _char_blank()
    user = _one(User, 'locs')
    week = _one_blank(WeekConfig, 'locs')

    address = _one_one_blank(Address, 'loc') # limit_choices_to
    place = _one_one_blank(Place, 'loc')
    cats = _many_tree(LocCat, 'locs')

    class Meta:
        ordering = ('name',)
        # verbose_name = 'Domicilio'
        # verbose_name_plural = 'Domicilios'

    def __unicode__(self):
        return _str(self, '%s, %s @ %s', (self.user, self.name, self.address or self.place))

    def delete(self):
        if self.address:
            self.address.delete()
        super(Loc, self).delete()

    def clean(self):
        utils.validate_xor(self.address, self.place, 'Must select ONE of Address or Place.')

    def addr(self):
        return self.address or self.place.address



class ForceNode(AbstractTree):

    user = _one_blank(User, 'nodes')
    itemcats = _many_tree(ItemCat, 'nodes')
    bricks = _many(Brick, 'nodes')
    locs = _many('Loc', 'nodes', through='ForceVisit')

    def __unicode__(self):
        return _str(self, '%s %s: %s', (self.str_level(), self.name, self.user))

    def itemcats_(self):
        return multiple_(self, 'itemcats')

    def bricks_(self):
        return multiple_(self, 'bricks')

    def locs_(self):
        return multiple_(self, 'locs')



class AbstractFormRec(AbstractModel):

    datetime = _datetime_now()
    observations = _text()
    rec = _text()

    class Meta:
        abstract = True
        ordering = ('-datetime',)

    def clean(self):
        if self.rec:
            try: json.loads(self.rec)
            except: raise ValidationError('Invalid JSON @ rec')

    def rec_dict(self):
        return json.loads(self.rec, parse_float=Decimal) if self.rec else dict()

    def __unicode__(self):
        return _str(self, 'AbstractFormRec > %s', (self.datetime,))



class ForceVisit(AbstractFormRec):

    name = _char_blank()
    node = _one(ForceNode, 'visits')
    loc = _one(Loc, 'visits')
    duration = _duration()
    status = _choices(2, [ ('s', 'Scheduled'), ('v', 'Visited'), ('n', 'Negative'), ('r', 'Re-scheduled') ])
    accompanied = _boolean(False)
    builder = _one_blank('VisitBuilder', 'visits') # on_delete=models.SET_NULL

    f_contact = _choices(30, [ 'Presencial', 'Telefonica', 'Web' ])
    f_goal = _choices(30, [ 'Presentacion Inicial', 'Promocion', 'Pedido', 'Negociar' ])
    f_option = _choices(30, [ 'Planeada', 'Re-agendada', 'Asignada' ])

    def __unicode__(self):
        return _str(self, 'Force Visit: %s > %s @ %s', (self.datetime, self.node, self.loc))

    def prep(self, private):
        # print 'prep', self.id, private
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

        loc = self.loc
        user = loc.user
        formtypes, forms_ids, repdict_items_ids, repdict_usercats_ids = Form.get_forms_reps(
            baseuser = user,
            private = private,
            visit = self,
            usercats = user.cats.all(),
            loccats = loc.cats.all(),
            **_node_data(self.node)
        )
        addr = loc.addr()
        def _dt(datetime):
            return str(datetime) if datetime else ''
        dt = self.datetime
        v = dict(
            name = self.name,
            datetime = _dt(dt),
            end = _dt(utils.datetime_plus(dt, self.duration)),
            status = self.status,
            accompanied = self.accompanied,

            f_contact = self.f_contact,
            f_goal = self.f_goal,
            f_option = self.f_option,

            observations = self.observations,
            user_name = user.fullname(),
            user_email = user.email,
            user_cats = utils.db_names(user.cats),
            loc_name = loc.name,
            loc_address = '%s # %s, %s' % (addr.street, addr.unit, addr.area),
            formtypes = formtypes,
            forms = forms_ids,
            repdict_items = repdict_items_ids,
            repdict_usercats = repdict_usercats_ids,
            rec = self.rec_dict(),
        )
        # print 'prep', self, v
        return v

    def _get_prep(self, private):
        import json
        v = self.prep(private)
        return json.dumps(v)

    def get_prep_public(self):
        return self._get_prep(False)

    def get_prep_private(self):
        return self._get_prep(True)



class FormType(AbstractModel):

    name = _name_unique()
    order = _form_order()
    description = _form_description()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s - %s', (self.name, self.description))

    def forms_(self): return multiple_(self, 'forms')

    def formfields_(self): return multiple_(self, 'formfields')



class Form(AbstractModel):

    name = _name_unique()
    scope = _choices(20, [ 'visits', 'users' ])
    private = _boolean(False)
    start = _datetime_blank()
    end = _datetime_blank()
    description = _form_description()
    expandable = _form_expandable()
    order = _form_order()
    cats = _many_tree(FormCat, 'forms')
    types = _many(FormType, 'forms')

    repitems = _many(Item, 'repforms')
    repitemcats = _many_tree(ItemCat, 'repforms')
    repusercats = _many_tree(UserCat, 'repforms')

    users_usercats = _many_tree(UserCat, 'users_forms')
    users_loccats = _many_tree(LocCat, 'users_forms')

    visits_usercats = _many_tree(UserCat, 'visits_forms')
    visits_loccats = _many_tree(LocCat, 'visits_forms')
    visits_itemcats = _many_tree(ItemCat, 'visits_forms')
    visits_forcenodes = _many_tree(ForceNode, 'visits_forms')
    visits_bricks = _many(Brick, 'visits_forms')

    class Meta:
        ordering = ('name',)

    @classmethod
    def get_forms_reps(
        cls,
        baseuser = None, # mandatory.
        private = False,
        ids = True,
        user = None, visit = None, # user or visit.
        usercats = None, loccats = None, # common.
        upnodes = None, itemcats = None, items = None, # visit.
    ):
        # print 'get_forms_reps', private, user or visit
        if not baseuser: error
        if visit if user else not visit: error
        repdict_items = dict()
        repdict_usercats = dict()
        types = []
        _any = utils.tree_any
        def _doreps(form):
            def _reps(isitems, repdict, reps):
                # print '_doreps > reps', reps
                if len(reps): # must check, even if empty after the below filter.
                    # user will get ALL reps (items / usercats) without any filtering, as opposed to visit.
                    isvisititems = isitems and not user
                    if isvisititems:
                        reps = reps.filter(id__in=items).all()
                    for erep in reps:
                        if _any(usercats, erep.visits_usercats) or _any(loccats, erep.visits_loccats) if isvisititems else True:
                            '''
                            repdict:
                              @ visit = dict[erep] = forms
                              @ user = dict[form] = reps (items / usercats)
                            '''
                            k = form.id if user else erep.id
                            rforms = repdict.get(k) or []
                            repdict[k] = rforms
                            rforms.append(erep if user else form)
                    return True
                return False
            def _reps_items():
                reps1 = form.repitems.all()
                repcats = utils.tree_all_downs(form.repitemcats.all())
                reps2 = ItemCat.els_get(repcats)
                nreps = (reps1 | reps2).distinct()
                return _reps(True, repdict_items, nreps)
            def _reps_usercats():
                ucats = utils.tree_all_downs(form.repusercats.all())
                ucats2 = baseuser.allcats()
                nreps = ucats & ucats2
                # print '_reps_usercats', baseuser, len(ucats), len(ucats2), len(nreps)
                return _reps(False, repdict_usercats, nreps)
            # priority to repitems, then (if none) repusercats.
            types.extend(form.types.all())
            return not (_reps_items() or _reps_usercats())
        forms = Form.objects.filter(scope='users' if user else 'visits')
        forms = [ form for form in forms
                  if (
                      form.private is private and (
                          False
                          or (user and (
                              False
                              or _any(usercats, form.users_usercats)
                              or _any(loccats, form.users_loccats)
                          ))
                          or (visit and (
                              False
                              or _any(usercats, form.visits_usercats)
                              or _any(loccats, form.visits_loccats)
                              or visit.loc.addr().area.zip.brick in form.visits_bricks.all()
                              or _any(upnodes, form.visits_forcenodes, ups=False)
                              or _any(itemcats, form.visits_itemcats)
                          ))
                      )
                  ) and _doreps(form) ]
        if ids:
            forms = utils.db_ids(forms)
            for repdict in [ repdict_items, repdict_usercats ]:
                for erep, erepforms in repdict.items():
                    erepforms[:] = utils.db_ids(erepforms)
        types = [ dict(id=form.id, name=form.name) for form in sorted(set(types), key=lambda form: (form.order, form.name)) ]
        # print 'get_forms_reps', private, user or visit, types, forms, repdict_items, repdict_usercats
        return types, forms, repdict_items, repdict_usercats

    '''
    # can't access multiple vals during validation?, it incorrectly returns previous values instead.
    def clean(self, *args, **kwargs):
        utils.validate_xor(
            utils.list_flatten([ self.repitems, self.repitemcats ], lambda each: each.all()),
            self.repusercats.all(),
            'Must select ONE type of reps, either items (repitems / repitemcats) or usercats.'
        )
    '''

    def _h_all(self):
        rels = []
        for each in [
            'repitems', 'repitemcats', 'repusercats',
            'users_usercats', 'users_loccats',
            'visits_usercats', 'visits_loccats',
            'visits_itemcats', 'visits_forcenodes', 'visits_bricks',
            # 'types',
        ]:
            ev = multiple_(self, each)
            if ev:
                rels.append('<b>%s</b> : %s' % (each, ev))
        # print 'Form.all_', self, rels
        return '<br>'.join(rels)

    def repitems_(self): return multiple_(self, 'repitems')
    def repitemcats_(self): return multiple_(self, 'repitemcats')

    def users_usercats_(self): return multiple_(self, 'users_usercats')
    def users_loccats_(self): return multiple_(self, 'users_loccats')

    def visits_usercats_(self): return multiple_(self, 'visits_usercats')
    def visits_loccats_(self): return multiple_(self, 'visits_loccats')
    def visits_itemcats_(self): return multiple_(self, 'visits_itemcats')
    def visits_forcenodes_(self): return multiple_(self, 'visits_forcenodes')

    def visits_bricks_(self): return multiple_(self, 'visits_bricks')

    def fields_(self): return multiple_(self, 'fields')

    def types_(self): return multiple_(self, 'types')



class FormField(AbstractModel):

    name = _name()
    description = _form_description()
    form = _one(Form, 'fields')
    type = _choices(20, [
        'string',
        'boolean',
        'date',
        'opts', 'optscat', 'optscat-all', # must start with 'opts', used in lab.js.
    ])
    widget = _choices(20, [ 'def', 'radios', 'textarea' ])
    default = _char_blank()
    required = _boolean(False)
    order = _form_order()
    opts1 = _text(help_text=_('Each option in a separate line with format Value:Label'))
    optscat = _one_blank(GenericCat, 'fields')
    types = _many(FormType, 'formfields')

    class Meta:
        unique_together = ('form', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.form))

    def _opts1_lines(self):
        return self.opts1.splitlines()

    def opts1_(self):
        return ', '.join(self._opts1_lines())

    def opts(self):
        opts = None
        if self.type.startswith('opts'):
            if self.type == 'opts':
                opts = [ [ each.strip() for each in opt.split(':', 1) ] for opt in self._opts1_lines() ]
            else: # optscat, optscat-all.
                cat = self.optscat
                if cat:
                    if self.type == 'optscat':
                        opts = cat.children
                        fn = lambda ecat: ecat.name
                    else:
                        opts = cat.get_descendants()
                        fn = lambda ecat: '%s %s' % (ecat.str_level(diff=cat.level + 1), ecat.name)
                    opts = [ (str(ecat.id), fn(ecat)) for ecat in opts.all() ]
        if opts is not None and not self.required:
            opts.insert(0, ('', '-'))
        return opts

    def types_(self): return multiple_(self, 'types')



class UserFormRec(AbstractFormRec):

    user = _one(User, 'userformrecs')
    form = _one(Form, 'userformrecs')

    class Meta:
        unique_together = ('user', 'form')

    def __unicode__(self):
        return _str(self, 'User Form Rec: %s > %s @ %s', (self.datetime, self.user, self.form))

    def jsrec(self):
        return dict(
            observations = self.observations,
            rec = self.rec_dict(),
        )



class Period(AbstractModel):

    name = _name_unique()
    end = _date()
    week = _one_blank(WeekConfig, 'periods')
    cats = _many_tree(PeriodCat, 'periods')

    class Meta:
        ordering = ('-end',)

    def __unicode__(self):
        return _str(self, 'Period: %s @ %s', (self.name, self.end))

    def prev(self):
        return Period.objects.order_by('end').filter(end__lt=self.end).last()

    def dates(self):
        p0 = self.prev()
        return (
            p0.end + datetime.timedelta(days=1) if p0 else self.end,
            self.end,
        )



def _q(_fname, _rels):
    _rels = list(_rels)
    # print '_q', _fname, len(_rels)
    return models.Q(**{_fname: _rels})
def _qn_and(_qn):
    # print '_qn_and', len(_qn)
    return reduce(lambda x, y: x & y, _qn)
def _qn_or(_qn):
    # print '_qn_or', len(_qn)
    return reduce(lambda x, y: x | y, _qn)

def _qty():
    return _int_blank(default=None, editable=False)

class VisitBuilder(AbstractModel):

    qty_slots = _qty()
    qty_slots_skips = _qty()
    qty_locs = _qty()
    qty_locs_skips = _qty()
    qty_node_skips = _qty()
    qty_visits = _qty()
    generated = _datetime_blank(editable=False)
    generate = _boolean(False)

    name = _name_unique()
    node = _one(ForceNode, 'builders')
    forcebricks = _boolean(True)

    duration = _duration()
    gap = _duration(mins=15)

    periods = _many(Period, 'builders')
    periodcats = _many_tree(PeriodCat, 'builders')

    orderby = _choices(20, [ 'area', 'city', 'state', 'country', 'zip', 'brick' ], default='zip')
    isand = _boolean(True, help_text='Check to use [AND] & [OR] levels, otherwise [OR] & [AND]. Note that [OR] is always implicit within each group.')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, 'Builder: %s > %s', (self.name, self.generated))

    def delete(self, *args, **kwargs):
        if self.generated:
            raise ValidationError('INVALID delete.')

    def validate_generated(self):
        if self.generated:
            raise ValidationError('NOT allowed to update, already generated.')

    def clean(self):
        self.validate_generated()
        # utils.validate_xor(self.period, self.start, 'Must select ONE of Period or Start/End.')
        # utils.validate_start_end(self.start, self.end, required=False)

    def save(self, *args, **kwargs):
        if self.generated:
            raise ValidationError('INVALID save.') # must have been previously caught by clean, for both: admin & api.
        if self.generate and self.qty_slots is not None: # in progress.
            self.generated = datetime.datetime.now()
        super(VisitBuilder, self).save(*args, **kwargs)

    def _generate_check(self):
        print '_generate_check', self.generate
        if self.generate:
            self._generate()

    # must be executed AFTER save, in order to have access to m2m relationships.
    def _generate(self):
        sys = Sys.objects.first()
        print '_generate', self, sys

        qn = [] # collection of multiple conds.

        def _qn_and_or(_qn, _isand):
            return _qn_and(_qn) if _isand else _qn_or(_qn)

        for cond in self.conds.all():
            eqn = cond.qn()
            if eqn:
                qn.append(_qn_and_or(eqn, not self.isand))

        if not qn: # not any ([ getattr(self, e).exists() for e in 'usercats loccats areas cities states countries zips bricks'.split() ])
            # raise ValidationError('Must select at least one condition for Users / Locs.')
            self.generate = False
            self.save()
            return # revert generate and ABORT, so we do NOT waste this builder.

        if qn:
            locs = Loc.objects.filter(_qn_and_or(qn, self.isand))
            # print 'query', locs.query
            locs = list(locs)
        else:
            locs = []

        def _sortkey(eloc):
            addr = eloc.addr()
            by = self.orderby
            def _val():
                v = addr.area
                if by == 'area': return v
                if by in [ 'zip', 'brick' ]:
                    v = v.zip
                    return v if by == 'zip' else v.brick
                v = v.city
                if by == 'city': return v
                v = v.state
                if by == 'state': return v
                v = v.country
                if by == 'country': return v
                error
            val = _val().name
            # print '_sortkey', by, val, eloc
            return val

        locs = sorted(locs, key=_sortkey)
        print 'locs', len(locs), locs

        pcats = utils.tree_all_downs(self.periodcats.all())
        pn1 = list(PeriodCat.els_get(pcats))
        pn2 = list(self.periods.all())
        pn = sorted(set(pn1 + pn2), key=lambda e: e.end)
        print 'pn', pn

        def _day(week, date):
            return getattr(week, utils.weekdays[date.weekday()])

        def _onoff(dt, week, sources, suffix):
            day = _day(week, dt)
            # print '_onoff', dt, week, day
            ok = False
            if day:
                dtdate = dt.date()
                dttime = dt.time()
                intime = False
                for time in day.times.all():
                    if dttime >= time.start and dttime <= time.end:
                        intime = True
                        break
                if intime:
                    sources = utils.list_compact(sources) # remove None's.
                    def _get(prefix, cmp2, checkdate):
                        xn = utils.list_flatten(sources, lambda e: getattr(e, prefix + suffix).all())
                        # print '_onoff._get', cmp2, xn
                        def _filter(e):
                            return cmp2 >= e.start and cmp2 <= e.end and (not e.date or e.date == dtdate if checkdate else True)
                        return utils.list_last(sorted(
                            [ e for e in xn if _filter(e) ],
                            key = lambda e: e.start,
                        ))
                    def _ison(pt):
                        return not pt or pt.on
                    operiod = _get('onoffperiod', dtdate, False)
                    if _ison(operiod):
                        otime = _get('onofftime', dttime, True)
                        if _ison(otime):
                            ok = True
            # if not ok: print '_onoff - FAILED', dt
            return ok

        with transaction.atomic():
            mgr = ForceVisit.objects
            self.qty_slots = 0
            self.qty_slots_skips = 0
            self.qty_locs = len(locs)
            self.qty_locs_skips = 0
            self.qty_node_skips = 0
            nodeskips = 0
            visits = []

            for ep in pn:
                start, end = ep.dates()
                qv = mgr.filter(datetime__range=(start, end)) # query within the current period (start - end).
                delta = end - start
                dates = [ start + datetime.timedelta(days=i) for i in range(delta.days + 1) ]
                week = ep.week or sys.week_period
                print '_generate > ep', ep, week, start, end # dates
                for edate in dates:
                    day = _day(week, edate)
                    print '_generate > edate', edate, day
                    if day:
                        def _datetime(_time): # can't use timedelta with simple times.
                            return datetime.datetime.combine(edate, _time)
                        for etime in day.times.all():
                            dt = _datetime(etime.start)
                            dt2 = _datetime(etime.end)
                            while dt < dt2:
                                self.qty_slots += 1
                                # print '_generate > slot', dt
                                user = self.node.user
                                ison = _onoff(
                                    dt,
                                    (user.week_visit if user else None) or sys.week_user_visit,
                                    [ user ],
                                    '_visit',
                                )
                                if ison:
                                    if qv.filter(node=self.node, datetime=dt).exists(): # visit already generated for the node in this time slot.
                                        self.qty_node_skips += 1
                                        print '_generate > qty_node_skips', dt, self.node
                                    else:

                                        # try (potentially multiple) locs for this specific time slot.
                                        tryloc = True
                                        locs2 = [] # queue for tried locs, which should be retried in the next time slot.
                                        while locs and tryloc:
                                            loc = locs.pop(0) if locs else None
                                            # print '_tryloc', dt, loc
                                            if loc:
                                                if qv.filter(loc=loc): # loc already visited during this period.
                                                    self.qty_locs_skips += 1
                                                    print '_generate > qty_locs_skips', dt, loc
                                                else:
                                                    ison = _onoff(
                                                        dt,
                                                        loc.week or loc.user.week_visited or sys.week_user_visited,
                                                        [ loc, loc.user ],
                                                        '_visited',
                                                    )
                                                    if ison:
                                                        visit = mgr.create(
                                                            builder = self,
                                                            node = self.node,
                                                            loc = loc,
                                                            datetime = dt,
                                                            duration = self.duration,
                                                        )
                                                        print '==> _generate > visit', dt, visit
                                                        visits.append(visit)
                                                        tryloc = False
                                                    else:
                                                        # print '_generate > SKIP VISITED (locs2 queue)', dt, loc
                                                        locs2.append(loc)
                                        locs[0:0] = locs2 # re-insert in order at the beginning, for immediate try during the subsequent time slots.

                                else:
                                    # print '_generate > SKIP VISIT', dt, user
                                    pass
                                dt = utils.datetime_plus(dt, self.duration, self.gap)
            self.qty_visits = len(visits)
            print 'done > generated visits & remaining locs', self.qty_visits, len(locs)
            self.save()



class VisitCond(AbstractModel):

    name = _char_blank()
    builder = _one(VisitBuilder, 'conds')

    usercats = _many_tree(UserCat, 'conds')
    loccats = _many_tree(LocCat, 'conds')
    placecats = _many_tree(PlaceCat, 'conds')
    # locs = _many(Loc, 'conds')

    areas = _many(Area, 'conds')
    cities = _many(City, 'conds')
    states = _many(State, 'conds')
    countries = _many(Country, 'conds')

    zips = _many(Zip, 'conds')
    bricks = _many(Brick, 'conds')

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.builder))

    def clean(self):
        if self.builder:
            self.builder.validate_generated()

    def qn(self):
        qn = []

        # cats.
        for fname, mrel in [
            ('cats__in', self.loccats),
            ('user__cats__in', self.usercats),
            ('place__cats__in', self.placecats),
        ]:
            if mrel.exists():
                mrel = utils.tree_all_downs(mrel.all())
                qn.append(_q(fname, mrel))

        # addresses.
        tmpl = 'address__%s__in'
        for suffix, mrel in [
            ('area', self.areas),
            ('area__city', self.cities),
            ('area__city__state', self.states),
            ('area__city__state__country', self.countries),
            ('area__zip', self.zips),
            ('area__zip__brick', self.bricks),
        ]:
            if mrel.exists():
                qn.append(_qn_or([ _q('%saddress__%s__in' % (prefix, suffix), mrel.all()) for prefix in [ '', 'place__' ] ]))

        # print 'VisitCond', self, qn

        return qn



class AbstractOnOff(AbstractModel):

    on = _boolean(False)

    # https://docs.djangoproject.com/en/1.7/topics/db/models/#model-inheritance

    visit_user = _one_blank(User, '%(class)s_visit', editable=False)
    visited_user = _one_blank(User, '%(class)s_visited', editable=False)

    visited_loc = _one_blank(Loc, '%(class)s_visited', editable=False)

    # visit_node = _one_blank(ForceNode, '%(class)s_visit', editable=False)

    class Meta:
        abstract = True

    def __unicode__(self):
        return _str(self, '%s : %s - %s %s', ('on' if self.on else 'off', self.start, self.end, self._str_extra()))

    def _str_extra(self):
        return ''

    def clean(self):
        utils.validate_start_end(self.start, self.end)
        utils.validate_one(
            [ self.visit_user, self.visited_user, self.visited_loc ],
            'Must select ONE of visit/visited.'
        )


class OnOffPeriod(AbstractOnOff):

    start = _date()
    end = _date()


class OnOffTime(AbstractOnOff):

    start = _time(choices=time_choices)
    end = _time(choices=time_choices)
    date = _date_blank()

    def _str_extra(self):
        return '@ %s' % self.date



class Sys(AbstractModel):

    week_user_visit = _one(WeekConfig, 'sys_user_visit')
    week_user_visited = _one(WeekConfig, 'sys_user_visited')
    week_period = _one(WeekConfig, 'sys_period')

    def __unicode__(self):
        return _str(self, 'Sys', ())

    def clean(self):
        if not self.id and Sys.objects.count():
            raise ValidationError('Singleton - can create only ONE instance.')

    def delete(self, *args, **kwargs):
        raise ValidationError('Singleton - can NOT be deleted.')
