from django.contrib import admin
from django import forms
from django.utils.html import format_html

from suit.admin import SortableModelAdmin
from mptt.admin import MPTTModelAdmin

from lab.models import *
import utils
# dbmodels = utils.db_models()


class AbstractAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)



class StateInline(admin.TabularInline):
    model = State
    extra = 0

class CountryAdmin(AbstractAdmin):
    inlines = (StateInline,)

class CityInline(admin.TabularInline):
    model = City
    extra = 0

class StateAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'country')
    list_filter = ('country__name',)
    inlines = (CityInline,)

class CityAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'state')
    list_filter = ('state__name', 'state__country__name')



class ZipAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'brick')

class ZipInline(admin.TabularInline):
    model = Zip
    extra = 0

class BrickAdmin(AbstractAdmin):
    inlines = (ZipInline,)



class DoctorCatAdmin(AbstractAdmin):
    pass

class DoctorSpecialtyAdmin(AbstractAdmin):
    pass

class DoctorLocInline(admin.StackedInline):
    model = DoctorLoc
    extra = 1

class DoctorAdmin(AbstractAdmin):
    list_display = ('id', 'user', 'cats_', 'specialties_')
    list_display_links = ('id', 'user')
    list_filter = ('cats__name', 'specialties__name')
    filter_vertical = ('cats', 'specialties')
    inlines = (DoctorLocInline,)

class LocInline(admin.StackedInline):
    model = Loc
    extra = 0

class LocCatAdmin(AbstractAdmin):
    inlines = (LocInline,)

class LocAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'street', 'unit', 'zip', 'city', 'cat')

class DoctorLocAdmin(LocAdmin):
    list_display = ('id', 'name', 'doctor', 'street', 'unit', 'zip', 'city')



class ItemSubcatInline(admin.TabularInline):
    model = ItemSubcat
    extra = 0

class ItemCatAdmin(AbstractAdmin):
    inlines = (ItemSubcatInline,)

class ItemInline(admin.TabularInline):
    model = Item
    extra = 0

class ItemSubcatAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'cat')
    list_filter = ('cat__name',)
    inlines = (ItemInline,)

class ItemAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'subcat')
    list_filter = ('subcat__name', 'market__name')



class MarketInline(admin.TabularInline):
    model = Market
    extra = 0

class MarketCatAdmin(AbstractAdmin):
    inlines = (MarketInline,)

class MarketAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'cat', 'items_')
    list_filter = ('cat__name',)
    filter_vertical = ('items',)



class ForceMgrInline(admin.TabularInline):
    model = ForceMgr
    extra = 0

class ForceAdmin(AbstractAdmin):
    def _mgrs(scope, row):
        return format_html('<a href="/admin/lab/forcemgr/?force__name=%s"> Mgrs </a>' % (row.name))

    list_display = ('id', 'name', 'markets_', '_mgrs')
    list_filter = ('markets__name',)
    filter_vertical = ('markets',)
    inlines = (ForceMgrInline,)

class ForceRepInline(admin.TabularInline):
    model = ForceRep
    extra = 0

class ForceMgrAdmin(AbstractAdmin, MPTTModelAdmin, SortableModelAdmin):
    def _agenda(self, row):
        return utils._agenda('mgr', row)
    _agenda.allow_tags = True

    # user first for tree view.
    list_display = ('user', 'id', 'force') # '_agenda'
    list_display_links = ('user', 'id')
    list_filter = ('force__name',)
    inlines = (ForceRepInline,)

    # http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
    mptt_level_indent = 20
    sortable = 'order'

# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/#working-with-many-to-many-intermediary-models
class ForceVisitInline(admin.TabularInline): # TabularInline / StackedInline
    model = ForceVisit
    extra = 0
    exclude = ('observations', 'rec')

class ForceRepAdmin(AbstractAdmin):
    def _agenda(self, row):
        return utils._agenda('rep', row)
    _agenda.allow_tags = True

    list_display = ('id', 'user', 'mgr', 'bricks_', 'locs_', '_agenda')
    list_display_links = ('id', 'user')
    list_filter = ('bricks__name',)
    filter_vertical = ('bricks',)
    inlines = (ForceVisitInline,)



# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/
class ForceVisitAdmin(AbstractAdmin):
    list_display = ('id', 'datetime', 'status', 'rep', 'loc', 'mgr') # 'observations', 'rec'
    list_display_links = ('id', 'datetime')
    date_hierarchy = 'datetime'
    list_editable = ('status',)
    list_filter = ('datetime', 'status')
    # radio_fields = dict(status=admin.VERTICAL)
    # raw_id_fields = ('rep',)
    # readonly_fields = ('datetime',)
    # def has_add_permission(self, request): return False
    # def get_queryset(self, request): ... FILTER by current user and such?.
    # formfield_for_foreignkey / formfield_for_manytomany ... FILTER optios subset !!
    # class Media: ... css / js.



class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    suit_classes = 'suit-tab suit-tab-fields'

class FormAdmin(AbstractAdmin):
    def _h_all(self, row):
        return row._h_all()
    _h_all.allow_tags = True

    list_display = ('id', 'name', '_h_all')
    filter_vertical = ('forces', 'marketcats', 'markets', 'bricks', 'itemcats', 'itemsubcats', 'doctorcats', 'doctorspecialties', 'loccats', 'locs')
    inlines = (FormFieldInline,)

    suit_form_tabs = (('general', 'General'), ('rels', 'Relations'), ('fields', 'Fields'))

    fieldsets = [
        (None, dict(
            classes = ('suit-tab suit-tab-general',),
            fields = [ 'name' ],
        )),
        (None, dict(
            classes = ('suit-tab suit-tab-rels',),
            fields = [ 'forces', 'marketcats', 'markets', 'bricks', 'itemcats', 'itemsubcats', 'doctorcats', 'doctorspecialties', 'loccats', 'locs' ],
        )),
    ]

class FormFieldAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'form', 'default', 'required', 'opts_')



dbadmins = [

    (LocCat, LocCatAdmin),
    (Loc, LocAdmin),

    (Country, CountryAdmin),
    (State, StateAdmin),
    (City, CityAdmin),

    (Zip, ZipAdmin),
    (Brick, BrickAdmin),

    (DoctorCat, DoctorCatAdmin),
    (DoctorSpecialty, DoctorSpecialtyAdmin),
    (Doctor, DoctorAdmin),
    (DoctorLoc, DoctorLocAdmin),

    (ItemCat, ItemCatAdmin),
    (ItemSubcat, ItemSubcatAdmin),
    (Item, ItemAdmin),

    (MarketCat, MarketCatAdmin),
    (Market, MarketAdmin),

    (Force, ForceAdmin),
    (ForceMgr, ForceMgrAdmin),
    (ForceRep, ForceRepAdmin),
    (ForceVisit, ForceVisitAdmin),

    (Form, FormAdmin),
    (FormField, FormFieldAdmin),

]

for dbmodel, dbadmin in dbadmins:
    admin.site.register(dbmodel, dbadmin)



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user

from django.contrib import admin
from django.contrib.auth.models import Group # User.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class UserCreationForm(forms.ModelForm):
    """
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)
    """

    class Meta:
        model = User
        fields = ('email',)

    """
    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2
    def save(self, commit=True):
        user = super(UserCreationForm, self).save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
    """

class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'is_active', 'is_admin')

    def clean_password(self):
        return self.initial["password"]

class UserAdmin(UserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm

    def _agenda(self, row):
        return utils._agenda('user', row)
    _agenda.allow_tags = True

    list_display = ('id', 'email', 'first_name', 'last_name', 'is_admin') # '_agenda'
    list_display_links = ('id', 'email')
    list_filter = ('is_admin',)

    fieldsets = (
        (None, dict(fields=('email', 'password'))),
        ('Personal info', dict(fields=('first_name', 'last_name'))),
        ('Permissions', dict(fields=('is_admin',))),
    )
    add_fieldsets = (
        (None, dict(
            classes = ('wide',),
            fields = ('email', 'first_name', 'last_name'), # 'password1', 'password2'
        )),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
