from django.contrib import admin
from django import forms
from django.utils.html import format_html
from django.utils.translation import ugettext as _

from suit.admin import SortableModelAdmin
from mptt.admin import MPTTModelAdmin

from .models import *
from .forms import *
import utils
# dbmodels = utils.db_models()

def _admin(dbmodel, dbadmin):
    admin.site.register(dbmodel, dbadmin)

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

class AbstractAdmin(admin.ModelAdmin):
    list_display = _fields_name
    list_display_links = _fields_name
    search_fields = ('syscode', 'name')

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

class AbstractTabularInline(admin.TabularInline):
    extra = 0

class AbstractStackedInline(admin.StackedInline):
    extra = 0

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



class CityAdmin(AbstractAdmin):
    list_display = _fields_name + ('state',)
    list_filter = ('state', 'state__country')

_admin(City, CityAdmin)



class ZipInline(AbstractTabularInline):
    model = Zip

class BrickAdmin(AbstractAdmin):
    inlines = (ZipInline,)

_admin(Brick, BrickAdmin)



class ZipAdmin(AbstractAdmin):
    list_display = _fields_name + ('brick',)

_admin(Zip, ZipAdmin)



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
    list_display = _fields + ('datetime', 'status', 'accompanied', 'node', 'loc') # 'observations', 'rec'
    list_display_links = _fields + ('datetime',)
    date_hierarchy = 'datetime'
    list_editable = ('status',)
    list_filter = ('datetime', 'status')
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

    def _agenda(self, row):
        return utils._agenda('user', row)
    _agenda.allow_tags = True

    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'syscode')}),
        # (_('Personal info'), {'fields': ('first_name', 'last_name', 'display_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}), # 'groups', 'user_permissions'
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Cats'), {'fields': ('cats',)}),
        #(_('Ids'), {'fields': ('private_uuid', 'public_id')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'cats', 'syscode')}
        ),
    )
    list_display = _fields + ('email', 'first_name', 'last_name', 'last_login', 'date_joined', 'cats_', '_agenda')
    list_display_links = _fields + ('email',)
    search_fields = ('syscode', 'email', 'first_name', 'last_name')
    ordering = ('email',)

    list_filter = ('cats',)

    form = UserAdminForm
    add_form = UserCreateAdminForm

    inlines = (LocInline,)

_admin(User, UserAdmin)



class ItemAdmin(AbstractAdmin):
    list_display = _fields_name + ('cats_', 'visits_usercats_', 'visits_loccats_', 'visits_expandable', 'visits_order')
    list_filter = ('cats', 'visits_usercats', 'visits_loccats')

_admin(Item, ItemAdmin)



class LocAdmin(AbstractAdmin):
    list_display = _fields_name + ('street', 'unit', 'phone', 'zip', 'city', 'at', 'user', 'cats_')
    list_display_links = _fields_name + ('street',)
    list_filter = ('cats',)

_admin(Loc, LocAdmin)



class FormFieldInline(AbstractStackedInline):
    model = FormField
    # suit_classes = 'suit-tab suit-tab-fields'

class FormAdmin(AbstractAdmin):
    def _h_all(self, row):
        return row._h_all()
    _h_all.allow_tags = True

    list_display = _fields_name + ('expandable', 'order', 'cats_', '_h_all', 'fields_')
    filter_vertical = ('visits_repitems', 'visits_bricks',)
    list_filter = ('cats', 'visits_repitemcats', 'visits_usercats', 'visits_itemcats', 'visits_loccats', 'visits_forcenodes')
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
    list_display = _fields_name + ('description', 'form', 'type', 'default', 'required', 'order', 'opts_')

_admin(FormField, FormFieldAdmin)
