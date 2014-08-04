from django.contrib import admin
from django import forms

from lab.models import *

import utils
# dbmodels = utils.db_models()

class BrickAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'zips1')

"""
class ModelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'make', 'engine')

class TaskAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'engines_')

class CarAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner', 'make_', 'model_', 'engine_', 'year', 'plate')

class ServiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'owner_', 'make_', 'model_', 'engine_', 'year_', 'plate_', 'odometer', 'sched_', 'enter_', 'exit_', 'tasks_', 'total', 'observations')

class ServiceTaskAdminForm(forms.ModelForm):
    class Meta:
        model = ServiceTask

    def clean(self):
        data = self.cleaned_data
        # print 'clean @ ServiceTaskAdminForm @ admin.py', data
        error = utils.validate_engine(data)
        if error:
            raise forms.ValidationError(error)
        return data

class ServiceTaskAdmin(admin.ModelAdmin):
    form = ServiceTaskAdminForm
    list_display = ('id', 'owner_', 'make_', 'model_', 'year_', 'engine_', 'start_', 'end_', 'observations')
"""

dbadmins = [
    (Brick, BrickAdmin),
    # (Task, TaskAdmin),
    # (Car, CarAdmin),
    # (Service, ServiceAdmin),
    # (ServiceTask, ServiceTaskAdmin),
]

for dbmodel, dbadmin in dbadmins:
    admin.site.register(dbmodel, dbadmin)



# https://docs.djangoproject.com/en/1.6/topics/auth/customizing/#auth-custom-user

from django.contrib import admin
from django.contrib.auth.models import Group # User.
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Password confirmation', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email',)

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
        (None, {'fields': ('email', 'password')}),
        # ('Personal info', {'fields': ('date_of_birth',)}),
        ('Permissions', {'fields': ('is_admin',)}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)
    filter_horizontal = ()

admin.site.register(User, UserAdmin)
admin.site.unregister(Group)
