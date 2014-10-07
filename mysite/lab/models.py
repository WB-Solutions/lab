from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext as _ # use ugettext_lazy instead?.
from django.utils import timezone

from decimal import Decimal
import json

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


class GoTreeM2MField(models.ManyToManyField):
    pass

def _kw_merge(kwmain, **kwdef):
    return dict(kwdef, **kwmain)

def _name(**kwargs):
    return models.CharField(_('name'), **_kw_merge(kwargs, max_length=200, unique=True))

def _datetime(*args, **kwargs):
    return models.DateTimeField(*args, **_kw_merge(kwargs, blank=True, null=True))

def _text(**kwargs):
    return models.TextField(**_kw_merge(kwargs, blank=True))

def _many(*args, **kwargs):
    return models.ManyToManyField(*args, **_kw_merge(kwargs, blank=True))

def _many_tree(*args, **kwargs):
    return GoTreeM2MField(*args, **_kw_merge(kwargs, blank=True))

def multiple_(row, prop):
    return ', '.join(sorted([ str(each) for each in getattr(row, prop).all() ]))

def _str(row, tmpl, values):
    v = (tmpl % values) if tmpl else values
    # v = '(%s. %s)' % (row.id, v) # parenthesis to separate nested row ids in values, e.g. items: ids for item / cat / subcat.
    # print '_str', v
    return unicode(v)


def _form_expandable(**kwargs):
    return models.BooleanField(**_kw_merge(kwargs, default=False))

def _form_order(**kwargs):
    return models.IntegerField(**_kw_merge(kwargs, blank=True, null=True, default=0))

def _form_description(**kwargs):
    return models.TextField(**_kw_merge(kwargs, blank=True))


class Country(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class State(models.Model):
    name = _name()
    country = models.ForeignKey(Country, related_name='states')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.country))

class City(models.Model):
    name = _name()
    state = models.ForeignKey(State, related_name='cities')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.state))

class Brick(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class Zip(models.Model):
    name = _name()
    brick = models.ForeignKey(Brick, related_name='zips')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.brick))



# http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
class AbstractTree(MPTTModel):
    name = _name(unique=False)
    parent = TreeForeignKey('self', blank=True, null=True, related_name='children')
    order = _form_order()

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ('order', 'name')

    def __unicode__(self):
        return _str(self, '%s %s', (self.h_level(), self.name))

    def h_level(self):
        return ' -- ' * (self.level or 0)

    def save(self, *args, **kwargs):
        # print 'AbstractTree.save', self, args, kwargs
        super(AbstractTree, self).save(*args, **kwargs)
        self.__class__.objects.rebuild()

class UserCat(AbstractTree):
    pass

class ItemCat(AbstractTree):
    pass

class LocCat(AbstractTree):
    pass

class FormCat(AbstractTree):
    pass



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

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(_('email address'), blank=False, unique=True)
    first_name = models.CharField(_('first name'), max_length=40, blank=True, null=True, unique=False)
    last_name = models.CharField(_('last name'), max_length=40, blank=True, null=True, unique=False)
    display_name = models.CharField(_('display name'), max_length=14, blank=True, null=True, unique=False)
    is_staff = models.BooleanField(_('staff status'), default=False, help_text=_('Designates whether the user can log into this admin site.'))
    is_active = models.BooleanField(_('active'), default=True, help_text=_('Designates whether this user should be treated as active. Unselect this instead of deleting accounts.'))
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    cats = _many_tree(UserCat, related_name='users')

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

    def cats_(self):
        return multiple_(self, 'cats')

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

'''
    def has_perm(self, perm, obj=None): # does the user have a specific permission?.
        return True

    def has_module_perms(self, app_label): # does the user have permissions to view the app "app_label"?.
        return True
'''



class ForceNode(AbstractTree):
    user = models.ForeignKey(User, blank=True, null=True, related_name='nodes')
    itemcats = _many_tree(ItemCat, related_name='nodes')
    bricks = _many(Brick)
    locs = _many('Loc', through='ForceVisit')

    def __unicode__(self):
        return _str(self, '%s %s: %s', (self.h_level(), self.name, self.user))

    def itemcats_(self):
        return multiple_(self, 'itemcats')

    def bricks_(self):
        return multiple_(self, 'bricks')

    def locs_(self):
        return multiple_(self, 'locs')

class Item(models.Model):
    name = _name()
    cats = _many_tree(ItemCat, related_name='items')
    visits_usercats = _many_tree(UserCat, related_name='visits_items')
    visits_loccats = _many_tree(LocCat, related_name='visits_items')
    visits_description = _form_description()
    visits_expandable = _form_expandable()
    visits_order = _form_order()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name) # _str(self, '%s [ %s ]', (self.name, self.cats_()))

    def cats_(self):
        return multiple_(self, 'cats')

    def visits_usercats_(self):
        return multiple_(self, 'visits_usercats')

    def visits_loccats_(self):
        return multiple_(self, 'visits_loccats')

class Loc(models.Model):
    name = _name(unique=False, blank=True)
    user = models.ForeignKey(User, related_name='locs')
    street = models.CharField(max_length=200)
    unit = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    zip = models.ForeignKey(Zip, related_name='locs')
    city = models.ForeignKey(City, related_name='locs')
    at = models.ForeignKey('self', blank=True, null=True, related_name='locs')
    cats = _many_tree(LocCat, related_name='locs')

    class Meta:
        ordering = ('name',)
        # verbose_name = 'Domicilio'
        # verbose_name_plural = 'Domicilios'

    def __unicode__(self):
        return _str(self, '%s, %s # %s, %s', (self.name, self.street, self.unit, self.zip)) # self.cats_()

    def cats_(self):
        return multiple_(self, 'cats')

class Form(models.Model):
    name = _name()
    description = _form_description()
    expandable = _form_expandable()
    order = _form_order()
    cats = _many_tree(FormCat, related_name='forms')

    visits_repitems = _many(Item, related_name='visits_repforms')
    visits_repitemcats = _many_tree(ItemCat, related_name='visits_repforms')

    visits_usercats = _many_tree(UserCat, related_name='visits_forms')
    visits_itemcats = _many_tree(ItemCat, related_name='visits_forms')
    visits_loccats = _many_tree(LocCat, related_name='visits_forms')
    visits_forcenodes = _many_tree(ForceNode, related_name='visits_forms')
    visits_bricks = _many(Brick, related_name='visits_forms')

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name) # _str(self, '%s [ %s ]', (self.name, self.cats_()))

    def _h_all(self):
        rels = []
        for each in [ 'visits_repitems', 'visits_repitemcats', 'visits_usercats', 'visits_itemcats', 'visits_loccats', 'visits_forcenodes', 'visits_bricks' ]:
            ev = multiple_(self, each)
            if ev:
                rels.append('<b>%s</b> : %s' % (each, ev))
        # print 'Form.all_', self, rels
        return '<br>'.join(rels)

    def cats_(self): return multiple_(self, 'cats')

    def visits_repitems_(self): return multiple_(self, 'visits_repitems')
    def visits_repitemcats_(self): return multiple_(self, 'visits_repitemcats')

    def visits_usercats_(self): return multiple_(self, 'visits_usercats')
    def visits_itemcats_(self): return multiple_(self, 'visits_itemcats')
    def visits_loccats_(self): return multiple_(self, 'visits_loccats')
    def visits_forcenodes_(self): return multiple_(self, 'visits_forcenodes')

    def visits_bricks_(self): return multiple_(self, 'visits_bricks')

    def fields_(self): return multiple_(self, 'fields')

class FormField(models.Model):
    name = _name(unique=False)
    description = _form_description()
    form = models.ForeignKey(Form, related_name='fields')
    type = models.CharField(max_length=30, blank=True, default='', choices=[ (e, e) for e in [ 'boolean', 'textarea', 'opts-select', 'opts-radios' ] ])
    default = models.CharField(max_length=200, blank=True)
    required = models.BooleanField(default=False)
    order = _form_order()
    opts1 = models.TextField(blank=True, help_text=_('Each option in a separate line with format Value:Label'))

    class Meta:
        unique_together = ('form', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.form))

    def _opts(self):
        return self.opts1.splitlines()

    def opts_(self):
        return ', '.join(self._opts())

    def opts(self):
        return [ [ each.strip() for each in opt.split(':', 1) ] for opt in self._opts() ]



class ForceVisit(models.Model):
    node = models.ForeignKey(ForceNode, related_name='visits')
    loc = models.ForeignKey(Loc, related_name='visits')
    datetime = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=2, blank=True, default='', choices=[ ('v', 'Visited'), ('n', 'Negative'), ('r', 'Re-scheduled') ])
    accompanied = models.BooleanField(default=False)
    observations = _text()
    rec = models.TextField(blank=True)

    class Meta:
        ordering = ('-datetime',)

    def __unicode__(self):
        return _str(self, 'Force Visit: %s > %s @ %s', (self.datetime, self.node, self.loc))

    def rec_dict(self):
        return json.loads(self.rec, parse_float=Decimal) if self.rec else dict()
