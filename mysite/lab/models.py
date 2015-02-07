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



class ItemCat(AbstractTree):
    els_model = 'Item'



class LocCat(AbstractTree):
    els_model = 'Loc'



class FormCat(AbstractTree):
    els_model = 'Form'



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

    def get_forms_reps(self):
        locs = self.locs.all()
        loccats = utils.list_flatten(locs, lambda loc: loc.cats.all())
        return Form.get_forms_reps(
            user = self,
            loccats = loccats,
            usercats = utils.tree_all_downs(self.cats.all()),
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



class ForceVisit(AbstractModel):
    node = _one(ForceNode, 'visits')
    loc = _one(Loc, 'visits')
    datetime = _datetime_now()
    duration = _duration()
    status = _choices(2, [ ('s', 'Scheduled'), ('v', 'Visited'), ('n', 'Negative'), ('r', 'Re-scheduled') ])
    accompanied = _boolean(False)
    observations = _text()
    rec = _text()
    builder = _one_blank('VisitBuilder', 'visits') # on_delete=models.SET_NULL

    class Meta:
        ordering = ('-datetime',)

    def __unicode__(self):
        return _str(self, 'Force Visit: %s > %s @ %s', (self.datetime, self.node, self.loc))

    def clean(self):
        if self.rec:
            try: json.loads(self.rec)
            except: raise ValidationError('Invalid JSON @ rec')

    def rec_dict(self):
        return json.loads(self.rec, parse_float=Decimal) if self.rec else dict()



class Form(AbstractModel):
    name = _name_unique()
    scope = _choices(20, [ 'visits', 'users' ])
    start = _datetime_blank()
    end = _datetime_blank()
    description = _form_description()
    expandable = _form_expandable()
    order = _form_order()
    cats = _many_tree(FormCat, 'forms')

    repitems = _many(Item, 'repforms')
    repitemcats = _many_tree(ItemCat, 'repforms')

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
        ids=True,
        user=None, visit=None, # user or visit.
        usercats=None, loccats=None, # common.
        upnodes=None, itemcats=None, items=None, # @ visit.
    ):
        # print 'get_forms_reps', user or visit, usercats, loccats
        if visit if user else not visit: error
        repforms = dict()
        _any = utils.tree_any
        def _doreps(form):
            reps1 = form.repitems.all()
            repcats = utils.tree_all_downs(form.repitemcats.all())
            reps2 = ItemCat.els_get(repcats)
            reps = (reps1 | reps2).distinct()
            # print '_doreps > reps', reps
            # user will get ALL items (reps) without any filtering, as opposed to visit.
            if reps.exists(): # must check, even if empty after the below filter.
                reps = reps if user else reps.filter(id__in=items).all()
                for item in reps:
                    if user or _any(usercats, item.visits_usercats) or _any(loccats, item.visits_loccats):
                        '''
                        repforms:
                          @ user = dict[form] = items
                          @ visit = dict[item] = forms
                        '''
                        k = form.id if user else item.id
                        rforms = repforms.get(k) or []
                        repforms[k] = rforms
                        rforms.append(item if user else form)
                return False
            return True
        forms = Form.objects.filter(scope='users' if user else 'visits')
        forms = [ form for form in forms
                  if (
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
                          or visit.loc.zip.brick in form.visits_bricks.all()
                          or _any(upnodes, form.visits_forcenodes, ups=False)
                          or _any(itemcats, form.visits_itemcats)
                      ))
                  ) and _doreps(form) ]
        if ids:
            forms = utils.db_ids(forms)
            for eitem, erepforms in repforms.items():
                erepforms[:] = utils.db_ids(erepforms)
        print 'get_forms_reps', user or visit, forms, repforms
        return forms, repforms

    def _h_all(self):
        rels = []
        for each in [
            'repitems', 'repitemcats',
            'users_usercats', 'users_loccats',
            'visits_usercats', 'visits_loccats',
            'visits_itemcats', 'visits_forcenodes', 'visits_bricks',
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



class FormField(AbstractModel):
    name = _name()
    description = _form_description()
    form = _one(Form, 'fields')
    type = _choices(20, [
        'string',
        'boolean',
        'opts', 'optscat', 'optscat-all', # must start with 'opts', used in lab.js.
    ])
    widget = _choices(20, [ 'def', 'radios', 'textarea' ])
    default = _char_blank()
    required = _boolean(False)
    order = _form_order()
    opts1 = _text(help_text=_('Each option in a separate line with format Value:Label'))
    optscat = _one_blank(GenericCat, 'fields')

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



class Period(AbstractModel):
    name = _name_unique()
    end = _date()
    cats = _many_tree(PeriodCat, 'periods')

    class Meta:
        ordering = ('-end',)

    def __unicode__(self):
        return _str(self, 'Period: %s @ %s', (self.name, self.end))

    def prev(self):
        return Period.objects.order_by('end').filter(end__lt=self.end).first()

    def dates(self):
        p0 = self.prev()
        return (
            p0.end + datetime.timedelta(days=1) if p0 else self.end,
            self.end,
        )



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
    skipbricks = _boolean(True)

    week = _one(WeekConfig, 'builders')
    duration = _duration()
    gap = _duration(mins=15)

    periods = _many(Period, 'builders')
    periodcats = _many_tree(PeriodCat, 'builders')
    start = _date_blank()
    end = _date_blank()

    orderby = _choices(20, [ 'area', 'city', 'state', 'country', 'zip', 'brick' ], default='zip')
    isand = _boolean(True, help_text='Check to use [AND] among groups; note that [OR] is implicit within each group.')

    usercats = _many_tree(UserCat, 'builders')
    loccats = _many_tree(LocCat, 'builders')
    # locs = _many(Loc, 'builders')

    areas = _many(Area, 'builders')
    cities = _many(City, 'builders')
    states = _many(State, 'builders')
    countries = _many(Country, 'builders')

    zips = _many(Zip, 'builders')
    bricks = _many(Brick, 'builders')

    class Meta:
        ordering = ('name',)

    def delete(self, *args, **kwargs):
        if self.generated:
            raise ValidationError('INVALID delete.')

    def clean(self):
        if self.generated:
            raise ValidationError('NOT allowed to update, already generated.')
        # utils.validate_xor(self.period, self.start, 'Must select ONE of Period or Start/End.')
        utils.validate_start_end(self.start, self.end, required=False)

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
        print '_generate', self
        none = True

        qn = []
        def _q(_fname, _rels):
            _rels = list(_rels)
            print '_q', _fname, len(_rels)
            return models.Q(**{_fname: _rels})
        def _qn_and(_qn):
            print '_qn_and', len(_qn)
            return reduce(lambda x, y: x & y, _qn)
        def _qn_or(_qn):
            print '_qn_or', len(_qn)
            return reduce(lambda x, y: x | y, _qn)

        # cats.
        for fname, mrel in [
            ('cats__in', self.loccats),
            ('user__cats__in', self.usercats),
        ]:
            if mrel.exists():
                none = False
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
                none = False
                qn.append(_qn_or([ _q('%saddress__%s__in' % (prefix, suffix), mrel.all()) for prefix in [ '', 'place__' ] ]))

        if not any ([ getattr(self, e).exists() for e in 'usercats loccats areas cities states countries zips bricks'.split() ]):
            # raise ValidationError('Must select at least one condition for Users / Locs.')
            self.generate = False
            self.save()
            return # revert generate an ABORT, so we do NOT waste this builder.

        if qn:
            locs = Loc.objects.filter(_qn_and(qn) if self.isand else _qn_or(qn))
            # print 'query', locs.query
            locs = list(locs)
        else:
            locs = []

        def _sortkey(eloc):
            addr = eloc.address or eloc.place.address
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
            print '_sortkey', by, val, eloc
            return val

        locs = sorted(locs, key=_sortkey)
        print 'locs', len(locs), locs

        pcats = utils.tree_all_downs(self.periodcats.all())
        ranges = []
        for pn in [
            PeriodCat.els_get(pcats),
            self.periods.all(),
        ]:
            ranges.extend([ ep.dates() for ep in pn ])
        if self.start:
            ranges.append((self.start, self.end))
        dates = set()
        for d1, d2 in ranges:
            delta = d2 - d1
            for i in range(delta.days + 1):
                dates.add(d1 + datetime.timedelta(days=i))
        dates = sorted(dates)
        print 'dates', dates

        with transaction.atomic():
            mgr = ForceVisit.objects
            self.qty_slots = 0
            self.qty_slots_skips = 0
            self.qty_locs = len(locs)
            self.qty_locs_skips = 0
            self.qty_node_skips = 0
            nodeskips = 0
            visits = []
            for edate in dates:
                print '_generate > DATE @ VisitBuilder', edate
                day = getattr(self.week, utils.weekdays[edate.weekday()])
                if day:
                    def _datetime(_time): # can't use timedelta with simple times.
                        return datetime.datetime.combine(edate, _time)
                    for etime in day.times.all():
                        dt = _datetime(etime.start)
                        while dt < _datetime(etime.end):
                            self.qty_slots += 1
                            qv = mgr.filter(datetime=dt)
                            if qv.exists():
                                self.qty_slots_skips += 1
                                print '_generate > SKIP slot', dt
                            elif qv.filter(node=self.node).exists():
                                self.qty_node_skips += 1
                                print '_generate > SKIP node', dt, self.node
                            else:
                                loc = locs.pop(0) if locs else None
                                print '_generate > TIME @ VisitBuilder', dt, loc
                                if loc:
                                    if mgr.filter(loc=loc, datetime__in=dates):
                                        self.qty_locs_skips += 1
                                        print '_generate > SKIP loc', loc
                                    else:
                                        visits.append(mgr.create(
                                            builder = self,
                                            node = self.node,
                                            loc = loc,
                                            datetime = dt,
                                            duration = self.duration,
                                        ))
                            dt = utils.datetime_plus(dt, self.duration, self.gap)
            self.qty_visits = len(visits)
            self.save()
