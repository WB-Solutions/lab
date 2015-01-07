from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.translation import ugettext as _
from django.contrib.admin.util import flatten_fieldsets

from suit.admin import SortableModelAdmin
from mptt.admin import MPTTModelAdmin

from .models import *
from .forms import *
import utils
# models = utils.db_models()

def _admin(model, dbadmin):
    admin.site.register(model, dbadmin)

'''
from django.forms import CheckboxSelectMultiple
from django.utils.safestring import mark_safe

_go_tree = 'go_tree'

class GoTree(CheckboxSelectMultiple):

    # https://docs.djangoproject.com/en/1.6/topics/forms/media/
    class Media:
        css = dict(all=('%s.css' % _go_tree,))
        js = ('%s.js' % _go_tree,)

    def render(self, *args, **kwargs):
        v = super(GoTree, self).render(*args, **kwargs)
        # print 'GoTree.render', args, kwargs, type(v), v
        return mark_safe('<div class="go-tree"> %s </div>' % v)
'''

_fields = ('syscodes_',)
_fields_name = _fields + ('name',)
_search = ('syscode',)
_search_name = _search  + ('name',)

class AbstractAdmin(admin.ModelAdmin):
    list_display = _fields_name
    list_display_links = _fields_name
    search_fields = _search_name

    '''
    # formfield_overrides = dict(GoTreeM2MField=dict(widget=GoTree))
    def formfield_for_manytomany(self, *args, **kwargs):
        # print 'AbstractAdmin.formfield_for_manytomany', args, kwargs
        kwargs['widget'] = GoTree()
        v = super(AbstractAdmin, self).formfield_for_manytomany(*args, **kwargs)
        return v

    def response_add(self, request, obj, post_url_continue=None):
        print 'AbstractAdmin.response_add', type(obj), obj
        if isinstance(obj, AbstractTree):
            print '=' * 500
        return super(AbstractAdmin, self).response_add(request, obj, post_url_continue)
    '''

class AbstractInlineFormSet(forms.models.BaseInlineFormSet):

    """
    Necessary in order to NOT generate errors for GoNullableUniqueField types (syscode) during multiple inlines.
      - Please correct the duplicate data for syscode.
      - Please correct the duplicate values below.
    For now HARD-CODED for 'syscode', until we can dynamically detect every GoNullableUniqueField type.
    http://stackoverflow.com/questions/13526792/validation-of-dependant-inlines-in-django-admin
    """
    def clean(self):
        k = 'syscode' # hard-coded for now.
        for form in self.forms:
            d = form.cleaned_data
            print 'XXX', d
            if form.is_valid() and not d.get('DELETE') and d.get(k) == '':
                d[k] = None
        v = super(AbstractInlineFormSet, self).clean()
        return v

class AbstractInline(admin.options.InlineModelAdmin):
    extra = 0
    formset = AbstractInlineFormSet

class AbstractTabularInline(AbstractInline, admin.TabularInline):
    pass

class AbstractStackedInline(AbstractInline, admin.StackedInline):
    pass

class AbstractTreeAdmin(AbstractAdmin, MPTTModelAdmin): # SortableModelAdmin
    # sortable = 'order' # http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
    list_display = _fields_name + ('order',)
    mptt_indent_field  = 'name'



class StateInline(AbstractTabularInline):
    model = State

class CountryAdmin(AbstractAdmin):
    inlines = (StateInline,)

_admin(Country, CountryAdmin)



class CityInline(AbstractTabularInline):
    model = City

class StateAdmin(AbstractAdmin):
    list_display = _fields_name + ('country',)
    list_filter = ('country',)
    inlines = (CityInline,)

_admin(State, StateAdmin)



# Shared.
class RegionInline(AbstractTabularInline):
    model = Region



class CityAdmin(AbstractAdmin):
    list_display = _fields_name + ('state',)
    list_filter = ('state', 'state__country')
    inlines = (RegionInline,)

_admin(City, CityAdmin)



class ZipInline(AbstractTabularInline):
    model = Zip

class BrickAdmin(AbstractAdmin):
    inlines = (ZipInline,)

_admin(Brick, BrickAdmin)



class ZipAdmin(AbstractAdmin):
    list_display = _fields_name + ('brick',)
    inlines = (RegionInline,)

_admin(Zip, ZipAdmin)



class RegionAdmin(AbstractAdmin):
    list_display = _fields_name + ('city', 'zip')

_admin(Region, RegionAdmin)



class GenericCatAdmin(AbstractTreeAdmin):
    pass

_admin(GenericCat, GenericCatAdmin)



class UserCatAdmin(AbstractTreeAdmin):
    pass

_admin(UserCat, UserCatAdmin)



class ItemCatAdmin(AbstractTreeAdmin):
    pass

_admin(ItemCat, ItemCatAdmin)



class LocCatAdmin(AbstractTreeAdmin):
    pass

_admin(LocCat, LocCatAdmin)



class FormCatAdmin(AbstractTreeAdmin):
    pass

_admin(FormCat, FormCatAdmin)



# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/#working-with-many-to-many-intermediary-models
class ForceVisitInline(AbstractTabularInline):
    model = ForceVisit
    exclude = ('observations', 'rec')

class ForceNodeAdmin(AbstractTreeAdmin):
    def _agenda(self, row):
        return utils._agenda('node', row)
    _agenda.allow_tags = True

    list_display = _fields_name + ('order', 'user', 'itemcats_', 'bricks_', 'locs_', '_agenda')
    list_filter = ('itemcats', 'bricks',)
    filter_vertical = ('bricks',)
    inlines = (ForceVisitInline,)

_admin(ForceNode, ForceNodeAdmin)



# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/
class ForceVisitAdmin(AbstractAdmin):
    list_display = _fields + ('datetime', 'duration', 'status', 'accompanied', 'node', 'loc') # 'observations', 'rec'
    list_display_links = _fields + ('datetime',)
    date_hierarchy = 'datetime'
    list_editable = ('status',)
    list_filter = ('datetime', 'status')
    search_fields = _search  + ('observations',) # 'rec'
    # radio_fields = dict(status=admin.VERTICAL)
    # raw_id_fields = ('node',)
    # readonly_fields = ('datetime',)
    # def has_add_permission(self, request): return False
    # def get_queryset(self, request): ... FILTER by current user and such?.
    # formfield_for_foreignkey / formfield_for_manytomany ... FILTER optios subset !!
    # class Media: ... css / js.

_admin(ForceVisit, ForceVisitAdmin)



# https://github.com/django/django/blob/stable/1.6.x/django/contrib/auth/admin.py

from django.contrib.auth.admin import UserAdmin as _UserAdmin

class LocInline(AbstractStackedInline):
    model = Loc

class UserAdmin(_UserAdmin, AbstractAdmin):
    #readonly_fields = ('private_uuid', 'public_id')

    '''
    class Media:
        js = ('loc.js',)
    '''

    def _agenda(self, row):
        return utils._agenda('user', row)
    _agenda.allow_tags = True

    fieldsets = (
        (None, dict(fields=('email', 'first_name', 'last_name', 'syscode'))),
        # (_('Personal info'), dict(fields=('first_name', 'last_name', 'display_name'))),
        (_('Permissions'), dict(fields=('is_active', 'is_staff', 'is_superuser'))), # 'groups', 'user_permissions'
        (_('Important dates'), dict(fields=('last_login', 'date_joined'))),
        (_('Cats'), dict(fields=('cats',))),
        #(_('Ids'), dict(fields=('private_uuid', 'public_id'))),
    )

    add_fieldsets = (
        (None, dict(
            classes = ('wide',),
            fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'cats', 'syscode'),
        )),
    )

    list_display = _fields + ('email', 'first_name', 'last_name', 'last_login', 'date_joined', 'cats_', '_agenda')
    list_display_links = _fields + ('email',)
    search_fields = _search  + ('email', 'first_name', 'last_name')
    ordering = ('email',)

    list_filter = ('cats',)

    form = UserAdminForm
    add_form = UserCreateAdminForm

    inlines = (LocInline,)

_admin(User, UserAdmin)



class ItemAdmin(AbstractAdmin):
    list_display = _fields_name + ('cats_', 'visits_usercats_', 'visits_loccats_', 'forms_expandable', 'forms_order')
    list_filter = ('cats', 'visits_usercats', 'visits_loccats')
    search_fields = _search_name + ('forms_description',)

_admin(Item, ItemAdmin)



class AddressAdmin(AbstractAdmin):
    list_display = _fields + ('street', 'unit', 'phone', 'phone2', 'fax', 'region')
    list_display_links = _fields + ('street',)
    search_fields = _search + ('street', 'unit')

_admin(Address, AddressAdmin)

class PlaceAdmin(AbstractTreeAdmin):
    list_display = _fields_name + ('order', 'address', 'canloc')

_admin(Place, PlaceAdmin)

'''
https://github.com/charettes/django-admin-enhancer
https://github.com/charettes/django-admin-enhancer/blob/master/admin_enhancer/tests/admin.py
    admin_enhancer @ settings.
    from admin_enhancer import admin as enhanced_admin
    class LocAdmin(enhanced_admin.EnhancedModelAdminMixin, AbstractAdmin):
'''

class LocAdmin(AbstractAdmin):
    list_display = _fields_name + ('address', 'place', 'user', 'cats_')
    list_filter = ('cats',)
    # show_change_link = True

    '''
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        print 'formfield_for_foreignkey', db_field, kwargs
        if db_field.name == "address":
            kwargs["queryset"] = Address.objects.filter(id=0)
        return super(LocAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)
    '''

_admin(Loc, LocAdmin)



class FormFieldInline(AbstractStackedInline):
    model = FormField
    # suit_classes = 'suit-tab suit-tab-fields'

class FormAdmin(AbstractAdmin):
    def _h_all(self, row):
        return row._h_all()
    _h_all.allow_tags = True

    list_display = _fields_name + ('scope', 'start', 'end', 'expandable', 'order', 'cats_', '_h_all', 'fields_')
    filter_vertical = ('repitems', 'visits_bricks',)
    list_filter = (
        'scope', 'cats', 'repitemcats',
        'users_usercats', 'users_loccats',
        'visits_usercats', 'visits_loccats',
        'visits_itemcats', 'visits_forcenodes',
    )
    search_fields = _search_name + ('description',)
    inlines = (FormFieldInline,)

    '''
    # pending also to use suit_classes @ inline(s).
    suit_form_tabs = (('general', 'General'), ('rels', 'Relations'), ('fields', 'Fields'))
    fieldsets = [
        (None, dict(
            classes = ('suit-tab suit-tab-general',),
            fields = [ 'name' ],
        )),
        (None, dict(
            classes = ('suit-tab suit-tab-rels',),
            fields = [ 'visits_bricks' ],
        )),
    ]
    '''

_admin(Form, FormAdmin)



class FormFieldAdmin(AbstractAdmin):
    list_display = _fields_name + ('form', 'type', 'widget', 'default', 'required', 'order', 'opts1_', 'optscat')
    search_fields = _search_name + ('description',)

_admin(FormField, FormFieldAdmin)



class PeriodAdmin(AbstractAdmin):
    list_display = _fields_name + ('end',)
    date_hierarchy = 'end'
    list_editable = ('end',)

_admin(Period, PeriodAdmin)



class TimeConfigAdmin(AbstractAdmin):
    list_display = _fields_name + ('start', 'end', 'day')
    list_filter = ('day',)

_admin(TimeConfig, TimeConfigAdmin)



class TimeInline(AbstractStackedInline):
    model = TimeConfig

class DayConfigAdmin(AbstractAdmin):
    inlines = (TimeInline,)

_admin(DayConfig, DayConfigAdmin)



class WeekConfigAdmin(AbstractAdmin):
    list_display = _fields_name + utils.weekdays

_admin(WeekConfig, WeekConfigAdmin)



_geos = ('regions', 'cities', 'states', 'countries', 'zips', 'bricks')

class VisitBuilderAdmin(AbstractAdmin):
    list_display = _fields_name + ('node', 'week', 'period', 'start', 'end', 'duration', 'generated', 'qty')
    filter_horizontal = _geos
    list_filter = ('period',)

    fieldsets = (
        (None, dict(fields=('syscode', 'name', 'node', 'week', 'duration'))),
        ('Generate', dict(fields=('generate',))), # generated, qty.
        ('Period', dict(fields=('period', 'start', 'end'))),
        ('Users', dict(fields=('usercats', 'loccats') + _geos))
    )

    def get_readonly_fields(self, request, obj=None):
        # print 'get_readonly_fields', obj
        return flatten_fieldsets(self.declared_fieldsets) if obj and obj.generated else []

    def has_delete_permission(self, request, obj=None):
        # print 'has_delete_permission', obj
        return False

    def save_related(self, request, form, formsets, change):
        builder = form.instance
        super(VisitBuilderAdmin, self).save_related(request, form, formsets, change)
        builder._generate_check()

_admin(VisitBuilder, VisitBuilderAdmin)

