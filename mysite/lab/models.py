from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.translation import ugettext as _ # use ugettext_lazy instead?.
from django.utils import timezone

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

def _many(*args, **kwargs):
    return models.ManyToManyField(*args, **_kw_merge(kwargs, blank=True))

def multiple_(row, prop):
    return ', '.join(sorted([ str(each) for each in getattr(row, prop).all() ]))

def _str(row, tmpl, values):
    v = (tmpl % values) if tmpl else values
    # v = '(%s. %s)' % (row.id, v) # parenthesis to separate nested row ids in values, e.g. items: ids for item / cat / subcat.
    # print '_str', v
    return unicode(v)



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



# http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
class AbstractTree(MPTTModel):
    name = _name(unique=False)
    parent = TreeForeignKey('self', blank=True, null=True, related_name='children')
    # order = models.IntegerField() # also create @ REST api NOT working: IntegrityError: X.order may not be NULL.

    class Meta:
        abstract = True

    class MPTTMeta:
        order_insertion_by = ('name',) # 'order'

    def __unicode__(self):
        return _str(self, '%s %s', (' . ' * (self.level or 0), self.name))

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
# from django.contrib.auth.models import User

'''
# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#django.contrib.auth.get_user_model
from django.contrib.auth import get_user_model
User = get_user_model()
'''

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
'''


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

    cats = _many(UserCat)

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





class ForceNode(AbstractTree):
    user = models.ForeignKey(User)
    itemcats = _many(ItemCat)
    bricks = _many(Brick)
    locs = _many('Loc', through='ForceVisit')

    def __unicode__(self):
        return _str(self, '%s %s: %s', (' . ' * (self.level or 0), self.name, self.user))

    def itemcats_(self):
        return multiple_(self, 'itemcats')

    def bricks_(self):
        return multiple_(self, 'bricks')

    def locs_(self):
        return multiple_(self, 'locs')

    def visits(self):
        return self.forcevisit_set.all()

class Item(models.Model):
    name = _name()
    cats = _many(ItemCat)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s [ %s ]', (self.name, self.cats_()))

    def cats_(self):
        return multiple_(self, 'cats')

class Loc(models.Model):
    name = _name(unique=False, blank=True)
    user = models.ForeignKey(User)
    street = models.CharField(max_length=200)
    unit = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    fax = models.CharField(max_length=30, blank=True)
    zip = models.ForeignKey(Zip)
    city = models.ForeignKey(City)
    at = models.ForeignKey('self', blank=True, null=True)
    cats = _many(LocCat)

    class Meta:
        ordering = ('name',)
        # verbose_name = 'Domicilio'
        # verbose_name_plural = 'Domicilios'

    def __unicode__(self):
        return _str(self, '%s, %s # %s, %s [ %s ]', (self.name, self.street, self.unit, self.zip, self.cats_()))

    def cats_(self):
        return multiple_(self, 'cats')

class Form(models.Model):
    name = _name()
    order = models.IntegerField(blank=True, null=True, default=0)
    usercats = _many(UserCat)
    itemcats = _many(ItemCat)
    loccats = _many(LocCat)
    forcenodes = _many(ForceNode)
    bricks = _many(Brick)
    cats = _many(FormCat)

    class Meta:
        ordering = ('name',)

    def __unicode__(self):
        return _str(self, '%s [ %s ]', (self.name, self.cats_()))

    def _h_all(self):
        rels = []
        for each in [ 'usercats', 'itemcats', 'loccats', 'forcenodes', 'bricks' ]:
            ev = multiple_(self, each)
            if ev:
                rels.append('<b>%s</b> : %s' % (each, ev))
        # print 'Form.all_', self, rels
        return '<br>'.join(rels)

    def usercats_(self): return multiple_(self, 'usercats')
    def itemcats_(self): return multiple_(self, 'itemcats')
    def loccats_(self): return multiple_(self, 'loccats')
    def forcenodes_(self): return multiple_(self, 'forcenodes')
    def bricks_(self): return multiple_(self, 'bricks')

    def cats_(self):
        return multiple_(self, 'cats')

class FormField(models.Model):
    name = _name(unique=False)
    form = models.ForeignKey(Form)
    default = models.CharField(max_length=200, blank=True)
    required = models.BooleanField(default=False)
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
    node = models.ForeignKey(ForceNode)
    loc = models.ForeignKey(Loc)
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
