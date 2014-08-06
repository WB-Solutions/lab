from django.contrib import admin
from django import forms

from lab.models import *

import utils
# dbmodels = utils.db_models()

class AbstractAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    list_display_links = ('id', 'name')
    search_fields = ('name',)

class BrickAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'zips_')
    search_fields = ('name', 'zips1')

class DoctorCatAdmin(AbstractAdmin):
    pass

class DoctorSpecialtyAdmin(AbstractAdmin):
    pass

class DoctorAdmin(AbstractAdmin):
    list_display = ('id', 'user', 'cats_', 'specialties_')
    list_display_links = ('id',)
    list_filter = ('cats__name', 'specialties__name')
    filter_vertical = ('cats', 'specialties')

class DoctorLocAdmin(AbstractAdmin):
    def _bricks(self, row):
        return ', '.join(map(str, row.bricks()))
    list_display = ('id', 'doctor', 'name', 'street', 'unit', 'zip', '_bricks')
    search_fields = ('name', 'street', 'unit', 'zip')

class ItemCatAdmin(AbstractAdmin):
    pass

class ItemSubcatAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'cat')
    list_filter = ('cat__name',)

class ItemAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'subcat')
    list_filter = ('subcat__name', 'market__name')

class MarketAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'items_')
    filter_vertical = ('items',)

class ForceAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'markets_', 'bricks_')
    list_filter = ('markets__name', 'bricks__name')
    filter_vertical = ('markets', 'bricks')

class ForceMgrAdmin(AbstractAdmin):
    list_display = ('id', 'user', 'force')
    list_display_links = ('id',)

# https://docs.djangoproject.com/en/1.6/ref/contrib/admin/#working-with-many-to-many-intermediary-models
class ForceVisitInline(admin.TabularInline):
    model = ForceVisit
    extra = 1

class ForceRepAdmin(AbstractAdmin):
    list_display = ('id', 'user', 'mgr', 'locs_')
    list_display_links = ('id',)
    inlines = (ForceVisitInline,)

class FormAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'forces_', 'markets_', 'itemcats_', 'itemsubcats_')
    filter_vertical = ('forces', 'markets', 'itemcats', 'itemsubcats')

class FormFieldAdmin(AbstractAdmin):
    list_display = ('id', 'name', 'form', 'default', 'required', 'opts_')

dbadmins = [
    (Brick, BrickAdmin),
    (DoctorCat, DoctorCatAdmin),
    (DoctorSpecialty, DoctorSpecialtyAdmin),
    (Doctor, DoctorAdmin),
    (DoctorLoc, DoctorLocAdmin),
    (ItemCat, ItemCatAdmin),
    (ItemSubcat, ItemSubcatAdmin),
    (Item, ItemAdmin),
    (Market, MarketAdmin),
    (Force, ForceAdmin),
    (ForceMgr, ForceMgrAdmin),
    (ForceRep, ForceRepAdmin),
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

    list_display = ('email', 'is_admin')
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
