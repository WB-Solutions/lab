from django import forms
from django.core.validators import MinLengthValidator
from django.contrib.auth.forms import UserCreationForm

from .models import *


class UserEditForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        # TODO: this doesn't seem to work. Need to get to the bottom of it.
        #self.base_fields["display_name"].min_length = 2
        #self.base_fields["display_name"].validators.append(MinLengthValidator)
        #print self.base_fields['display_name'].validators
        super(forms.ModelForm, self).__init__(*args, **kwargs)

    class Meta:
        model = User
        fields = ('first_name', 'last_name') # 'display_name'


class UserAdminForm(forms.ModelForm):

    class Meta:
        model = User

    def is_valid(self):
        #log.info(force_text(self.errors))
        return super(UserAdminForm, self).is_valid()


class UserCreateAdminForm(UserCreationForm):
    username = forms.CharField(required=False) # ignored / hidden, just to NOT validate as mandatory during save.

    class Meta:
        model = User
        fields = ('email',)

    def clean_username(self):
        pass
