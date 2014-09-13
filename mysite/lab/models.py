from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext as _
from django.contrib.auth import get_user_model

from decimal import Decimal
import json

from mptt.fields import TreeForeignKey
from mptt.models import MPTTModel


def _kw_merge(kwmain, **kwdef):
    return dict(kwdef, **kwmain)

def _name(**kwargs):
    return models.CharField(_('name'), **_kw_merge(kwargs, max_length=200, unique=True))

def _datetime(*args, **kwargs):
    return models.DateTimeField(*args, **_kw_merge(kwargs, blank=True, null=True))

def _text(**kwargs):
    return models.TextField(**_kw_merge(kwargs, blank=True))

def multiple_(row, prop):
    return ', '.join(sorted([ str(each) for each in getattr(row, prop).all() ]))

def _str(row, tmpl, values):
    v = (tmpl % values) if tmpl else values
    # v = '(%s. %s)' % (row.id, v) # parenthesis to separate nested row ids in values, e.g. items: ids for item / cat / subcat.
    # print '_str', v
    return unicode(v)



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user
# from django.contrib.auth.models import User

# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#django.contrib.auth.get_user_model
User = get_user_model()

'''
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

class UserManager(BaseUserManager):

    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            raise ValueError('Users must have an email address')
        user = self.model(
            email = self.normalize_email(email),
            first_name = first_name,
            last_name = last_name,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password=password)
        user.is_admin = True
        user.save(using=self._db)
        return user

class User(AbstractBaseUser):
    email = models.EmailField(verbose_name='email address', max_length=255, unique=True)
    first_name = models.CharField(max_length=200)
    last_name = models.CharField(max_length=200)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = [ 'first_name', 'last_name' ]

    def __unicode__(self):
        return _str(self, '%s %s : %s', (self.first_name, self.last_name, self.email))

    def get_full_name(self):
        return self.email

    def get_short_name(self):
        return self.email

    def has_perm(self, perm, obj=None): # does the user have a specific permission?.
        return True

    def has_module_perms(self, app_label): # does the user have permissions to view the app "app_label"?.
        return True

    @property
    def is_staff(self): # is the user a member of staff?.
        return self.is_admin

    def fullname(self):
        return '%s %s' % (self.first_name, self.last_name)
'''



class Country(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class State(models.Model):
    name = _name()
    country = models.ForeignKey(Country)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.country))

class City(models.Model):
    name = _name()
    state = models.ForeignKey(State)

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
    brick = models.ForeignKey(Brick)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.brick))



class DoctorCat(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class DoctorSpecialty(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class Doctor(models.Model):
    user = models.OneToOneField(User)
    cats = models.ManyToManyField(DoctorCat, blank=True)
    specialties = models.ManyToManyField(DoctorSpecialty, blank=True)

    def __unicode__(self):
        return _str(self, '%s [ %s ] [ %s ]', (self.user, self.cats_(), self.specialties_()))

    def cats_(self):
        return multiple_(self, 'cats')

    def specialties_(self):
        return multiple_(self, 'specialties')

class AbstractLoc(models.Model):
    street = models.CharField(max_length=200)
    unit = models.CharField(max_length=30, blank=True, null=True)
    zip = models.ForeignKey(Zip)
    city = models.ForeignKey(City)

    class Meta:
        abstract = True

    def __unicode__(self):
        return _str(self, '%s, %s # %s, %s', (self.name, self.street, self.unit, self.zip))

class LocCat(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class Loc(AbstractLoc):
    name = _name()
    cat = models.ForeignKey(LocCat)

    class Meta:
        ordering = ('name',)
        verbose_name = 'Domicilio'
        verbose_name_plural = 'Domicilios'

class DoctorLoc(AbstractLoc):
    doctor = models.ForeignKey(Doctor)
    loc = models.ForeignKey(Loc)
    name = _name(unique=False, blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'name')
        ordering = ('name',)



class ItemCat(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class ItemSubcat(models.Model):
    name = _name(unique=False)
    cat = models.ForeignKey(ItemCat)

    class Meta:
        unique_together = ('cat', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s > %s', (self.cat, self.name))

class Item(models.Model):
    name = _name()
    subcat = models.ForeignKey(ItemSubcat)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.subcat))



class MarketCat(models.Model):
    name = _name()

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

class Market(models.Model):
    name = _name(unique=False)
    cat = models.ForeignKey(MarketCat)
    items = models.ManyToManyField(Item, blank=True)

    class Meta:
        unique_together = ('cat', 'name')
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s @ %s [ %s ]', (self.name, self.cat, self.items_()))

    def items_(self):
        return multiple_(self, 'items')



class Force(models.Model):
    name = _name()
    markets = models.ManyToManyField(Market, blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

    def markets_(self):
        return multiple_(self, 'markets')

# http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
class ForceMgr(MPTTModel):
    name = _name(unique=False)
    force = models.ForeignKey(Force)
    user = models.ForeignKey(User)

    class Meta:
        unique_together = ('user', 'force', 'parent')

    def __unicode__(self):
        return _str(self, 'Force Mgr : %s @ %s', (self.user, self.force))

    # mptt.
    parent = TreeForeignKey('self', blank=True, null=True, related_name='children')
    order = models.IntegerField()
    class MPTTMeta:
        order_insertion_by = ('order',)
    def save(self, *args, **kwargs):
        cls = self.__class__
        print 'ForceMgr.save', self, cls, args, kwargs
        super(cls, self).save(*args, **kwargs)
        cls.objects.rebuild()

class ForceRep(models.Model):
    # force = models.ForeignKey(Force)
    user = models.ForeignKey(User)
    mgr = models.ForeignKey(ForceMgr)
    bricks = models.ManyToManyField(Brick, blank=True)
    locs = models.ManyToManyField(DoctorLoc, blank=True, through='ForceVisit')

    class Meta:
        unique_together = ('user', 'mgr')

    def __unicode__(self):
        return _str(self, 'Force Rep : %s @ %s', (self.user, self.mgr))

    def locs_(self):
        return multiple_(self, 'locs')

    def bricks_(self):
        return multiple_(self, 'bricks')

    def visits(self):
        return self.forcevisit_set.all()

class ForceVisit(models.Model):
    # force = models.ForeignKey(Force)
    rep = models.ForeignKey(ForceRep)
    loc = models.ForeignKey(DoctorLoc)
    mgr = models.ForeignKey(ForceMgr, blank=True, null=True)
    datetime = models.DateTimeField()
    status = models.CharField(max_length=2, blank=True, default='', choices=[ ('v', 'Visited'), ('n', 'Negative'), ('r', 'Re-scheduled') ])
    observations = _text()
    rec = models.TextField(blank=True)

    class Meta:
        ordering = ('-datetime',)

    def __unicode__(self):
        return _str(self, 'Force Visit: %s > %s @ %s', (self.datetime, self.rep, self.loc))

    def rec_dict(self):
        return json.loads(self.rec, parse_float=Decimal) if self.rec else dict()



class Form(models.Model):
    name = _name()
    forces = models.ManyToManyField(Force, blank=True)
    marketcats = models.ManyToManyField(MarketCat, blank=True)
    markets = models.ManyToManyField(Market, blank=True)
    bricks = models.ManyToManyField(Brick, blank=True)
    itemcats = models.ManyToManyField(ItemCat, blank=True)
    itemsubcats = models.ManyToManyField(ItemSubcat, blank=True)
    doctorcats = models.ManyToManyField(DoctorCat, blank=True)
    doctorspecialties = models.ManyToManyField(DoctorSpecialty, blank=True)
    loccats = models.ManyToManyField(LocCat, blank=True)
    locs = models.ManyToManyField(Loc, blank=True)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, None, self.name)

    def _h_all(self):
        rels = []
        for each in [ 'forces', 'marketcats', 'markets', 'bricks', 'itemcats', 'itemsubcats', 'doctorcats', 'doctorspecialties', 'loccats', 'locs' ]:
            ev = multiple_(self, each)
            if ev:
                rels.append('<b>%s</b> : %s' % (each, ev))
        print 'Form.all_', self, rels
        return '<br>'.join(rels)

    def forces_(self): return multiple_(self, 'forces')
    def marketcats_(self): return multiple_(self, 'marketcats')
    def markets_(self): return multiple_(self, 'markets')
    def bricks_(self): return multiple_(self, 'bricks')
    def itemcats_(self): return multiple_(self, 'itemcats')
    def itemsubcats_(self): return multiple_(self, 'itemsubcats')
    def doctorcats_(self): return multiple_(self, 'doctorcats')
    def doctorspecialties_(self): return multiple_(self, 'doctorspecialties')
    def loccats_(self): return multiple_(self, 'loccats')
    def locs_(self): return multiple_(self, 'locs')

class FormField(models.Model):
    name = _name(unique=False)
    form = models.ForeignKey(Form)
    default = models.CharField(max_length=200, blank=True)
    required = models.BooleanField(default=False)
    opts1 = models.TextField(blank=True)

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
