from django.db import models
from django.core.validators import MaxValueValidator, MinValueValidator

def _name(**kwargs):
    return models.CharField('Name', max_length=200, unique=True, **kwargs)

def _datetime(*args, **kwargs):
    return models.DateTimeField(blank=True, null=True, *args, **kwargs)

def _text(**kwargs):
    return models.TextField(blank=True, **kwargs)

def multiple_(row, prop):
    return ', '.join(sorted([ str(each) for each in getattr(row, prop).all() ]))

def _str(row, tmpl, values):
    # parenthesis to separate nested row ids in values.
    # e.g. items: ids for item / cat / subcat.
    v = '(%s. %s)' % (row.id, (tmpl % values) if tmpl else values)
    # print '_str', v
    return unicode(v)



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user

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



class Brick(models.Model):
    name = _name()
    zips1 = models.TextField(blank=True) # linear, simple space separated list for now ... https://gist.github.com/jonashaag/1200165

    def __unicode__(self):
        return _str(self, '%s [ %s ]', (self.name, self.zips_()))

    def zips_(self):
        return ', '.join(self.zips1.split())

class DoctorCat(models.Model):
    name = _name()

    def __unicode__(self):
        return _str(self, None, self.name)

class DoctorSpecialty(models.Model):
    name = _name()

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

class DoctorLoc(models.Model):
    doctor = models.ForeignKey(Doctor)
    name = _name()
    street = models.CharField(max_length=200)
    unit = models.CharField(max_length=30)
    zip = models.CharField(max_length=10)

    def __unicode__(self):
        return _str(self, '%s, %s # %s, %s', (self.name, self.street, self.unit, self.zip))

    def bricks(self):
        return Brick.objects.filter(zips1__icontains=self.zip)

class ItemCat(models.Model):
    name = _name()

    def __unicode__(self):
        return _str(self, None, self.name)

class ItemSubcat(models.Model):
    name = _name()
    cat = models.ForeignKey(ItemCat)

    def __unicode__(self):
        return _str(self, '%s > %s', (self.cat, self.name))

class Item(models.Model):
    name = _name()
    subcat = models.ForeignKey(ItemSubcat)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.subcat))

class Market(models.Model):
    name = _name()
    items = models.ManyToManyField(Item, blank=True)

    def __unicode__(self):
        return _str(self, '%s [ %s ]', (self.name, self.items_()))

    def items_(self):
        return multiple_(self, 'items')

class Force(models.Model):
    name = _name()
    markets = models.ManyToManyField(Market, blank=True)
    bricks = models.ManyToManyField(Brick, blank=True)

    def __unicode__(self):
        return _str(self, None, self.name)

    def markets_(self):
        return multiple_(self, 'markets')

    def bricks_(self):
        return multiple_(self, 'bricks')

class ForceMgr(models.Model):
    user = models.ForeignKey(User)
    force = models.ForeignKey(Force)

    def __unicode__(self):
        return _str(self, 'Force Mgr : %s @ %s', (self.user, self.force))

class ForceRep(models.Model):
    user = models.ForeignKey(User)
    mgr = models.ForeignKey(ForceMgr)
    locs = models.ManyToManyField(DoctorLoc, blank=True, through='ForceVisit')

    def __unicode__(self):
        return _str(self, 'Force Rep : %s @ %s', (self.user, self.mgr))

    def locs_(self):
        return multiple_(self, 'locs')

    def visits(self):
        return self.forcevisit_set.all()

class ForceVisit(models.Model):
    rep = models.ForeignKey(ForceRep)
    loc = models.ForeignKey(DoctorLoc)
    datetime = models.DateTimeField()
    observations = _text()

    def __unicode__(self):
        return _str(self, 'Force Visit: %s > %s @ %s', (self.datetime, self.rep, self.loc))

class Form(models.Model):
    name = _name()
    forces = models.ManyToManyField(Force, blank=True)
    markets = models.ManyToManyField(Market, blank=True)
    itemcats = models.ManyToManyField(ItemCat, blank=True)
    itemsubcats = models.ManyToManyField(ItemSubcat, blank=True)

    def __unicode__(self):
        return _str(self, None, self.name)

    def forces_(self):
        return multiple_(self, 'forces')

    def markets_(self):
        return multiple_(self, 'markets')

    def itemcats_(self):
        return multiple_(self, 'itemcats')

    def itemsubcats_(self):
        return multiple_(self, 'itemsubcats')

class FormField(models.Model):
    name = _name()
    form = models.ForeignKey(Form)
    default = models.CharField(max_length=200)
    required = models.BooleanField(default=False)
    opts = models.TextField(blank=True)

    def __unicode__(self):
        return _str(self, '%s @ %s', (self.name, self.form))

    def opts_(self):
        return ', '.join(self.opts.splitlines())
