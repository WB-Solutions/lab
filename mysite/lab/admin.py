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


_go_tree = 'go_tree'

'''
from django.forms import CheckboxSelectMultiple
from django.utils.safestring import mark_safe

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

class AbstractAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

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



class StateInline(AbstractTabularInline):
    model = State

class CountryAdmin(AbstractAdmin):
    inlines = (StateInline,)

class CityInline(AbstractTabularInline):
    model = City

class StateAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'country')
    list_filter = ('country',)
    inlines = (CityInline,)

class CityAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'state')
    list_filter = ('state', 'state__country')



class ZipInline(AbstractTabularInline):
    model = Zip

class BrickAdmin(AbstractAdmin):
    inlines = (ZipInline,)

class ZipAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'brick')



class AbstractTreeAdmin(AbstractAdmin, MPTTModelAdmin): # SortableModelAdmin
    # http://django-suit.readthedocs.org/en/latest/sortables.html#django-mptt-tree-sortable
    # sortable = 'order'
    mptt_indent_field  = 'name'

class UserCatAdmin(AbstractTreeAdmin):
    pass

class ItemCatAdmin(AbstractTreeAdmin):
    pass

class LocCatAdmin(AbstractTreeAdmin):
    pass

class FormCatAdmin(AbstractTreeAdmin):
    pass



# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/#working-with-many-to-many-intermediary-models
class ForceVisitInline(AbstractTabularInline):
    model = ForceVisit
    exclude = ('observations', 'rec')

class ForceNodeAdmin(AbstractTreeAdmin):
    def _agenda(self, row):
        return utils._agenda('node', row)
    _agenda.allow_tags = True

    list_display = ('id', 'name', 'user', 'itemcats_', 'bricks_', 'locs_', '_agenda')
    list_display_links = ('id', 'name')
    list_filter = ('itemcats', 'bricks',)
    filter_vertical = ('bricks',)
    inlines = (ForceVisitInline,)



# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/
class ForceVisitAdmin(AbstractAdmin):
    list_display = ('id', 'datetime', 'status', 'accompanied', 'node', 'loc') # 'observations', 'rec'
    list_display_links = ('id', 'datetime')
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



class LocInline(AbstractStackedInline):
    model = Loc

# https://github.com/django/django/blob/stable/1.6.x/django/contrib/auth/admin.py

from django.contrib.auth.admin import UserAdmin as _UserAdmin

class UserAdmin(_UserAdmin, AbstractAdmin):
    #readonly_fields = ('private_uuid', 'public_id')

    def _agenda(self, row):
        return utils._agenda('user', row)
    _agenda.allow_tags = True

    fieldsets = (
        (None, {'fields': ('email', 'first_name', 'last_name', 'password')}),
        # (_('Personal info'), {'fields': ('first_name', 'last_name', 'display_name')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser')}), # 'groups', 'user_permissions'
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
        (_('Cats'), {'fields': ('cats',)}),
        #(_('Ids'), {'fields': ('private_uuid', 'public_id')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'password1', 'password2', 'cats')}
        ),
    )
    list_display = ('id', 'email', 'first_name', 'last_name', 'last_login', 'date_joined', 'cats_', '_agenda')
    list_display_links = ('id', 'email')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

    list_filter = ('cats',)

    form = UserAdminForm
    add_form = UserCreateAdminForm

    inlines = (LocInline,)



'''
    def _mgrs(scope, row):
        return format_html('<a href="/admin/lab/forcemgr/?force__name=%s"> Mgrs </a>' % (row.name))
'''



class ItemAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'cats_', 'visits_usercats_', 'visits_loccats_')
    list_filter = ('cats', 'visits_usercats', 'visits_loccats')

class LocAdmin(AbstractAdmin):
    list_display = ('id', 'street', 'unit', 'phone', 'zip', 'city', 'name', 'at', 'user', 'cats_')
    list_display_links = ('id', 'street')
    list_filter = ('cats',)



class FormFieldInline(AbstractStackedInline):
    model = FormField
    # suit_classes = 'suit-tab suit-tab-fields'

class FormAdmin(AbstractAdmin):
    def _h_all(self, row):
        return row._h_all()
    _h_all.allow_tags = True

    list_display = ('id', 'name', 'order', 'repitems_', 'cats_', '_h_all')
    filter_vertical = ('repitems', 'bricks',)
    list_filter = ('cats', 'usercats', 'itemcats', 'loccats', 'forcenodes')
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
            fields = [ 'bricks' ],
        )),
    ]
    '''

class FormFieldAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'form', 'default', 'required', 'opts_')



dbadmins = [

    (Country, CountryAdmin),
    (State, StateAdmin),
    (City, CityAdmin),

    (Zip, ZipAdmin),
    (Brick, BrickAdmin),

    (UserCat, UserCatAdmin),
    (ItemCat, ItemCatAdmin),
    (LocCat, LocCatAdmin),
    (FormCat, FormCatAdmin),

    (ForceNode, ForceNodeAdmin),
    (ForceVisit, ForceVisitAdmin),

    (User, UserAdmin),
    (Item, ItemAdmin),
    (Loc, LocAdmin),

    (Form, FormAdmin),
    (FormField, FormFieldAdmin),

]

for dbmodel, dbadmin in dbadmins:
    admin.site.register(dbmodel, dbadmin)



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user

'''

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

    list_display = ('id', 'email', 'first_name', 'last_name', 'is_admin')
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

'''
