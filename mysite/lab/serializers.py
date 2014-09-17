from rest_framework import serializers
from .models import *

import utils

class AbstractSerializer(serializers.HyperlinkedModelSerializer):
    pass

_fields = ('url', 'id')
_fields_name = _fields + ('name',)
_fields_cat = _fields_name + ('parent',)



class CountrySerializer(AbstractSerializer):

    class Meta:
        model = Country
        fields = _fields_name

class StateSerializer(AbstractSerializer):

    class Meta:
        model = State
        fields = _fields_name + ('country',)

class CitySerializer(AbstractSerializer):

    class Meta:
        model = City
        fields = _fields_name + ('state',)

class BrickSerializer(AbstractSerializer):

    class Meta:
        model = Brick
        fields = _fields_name

class ZipSerializer(AbstractSerializer):

    class Meta:
        model = Zip
        fields = _fields_name + ('brick',)



class UserCatSerializer(AbstractSerializer):

    class Meta:
        model = UserCat
        fields = _fields_cat

class ItemCatSerializer(AbstractSerializer):

    class Meta:
        model = ItemCat
        fields = _fields_cat

class LocCatSerializer(AbstractSerializer):

    class Meta:
        model = LocCat
        fields = _fields_cat

class FormCatSerializer(AbstractSerializer):

    class Meta:
        model = FormCat
        fields = _fields_cat



class ForceNodeSerializer(AbstractSerializer):
    # visits = serializers.Field(source='visits')

    class Meta:
        model = ForceNode
        fields = _fields_cat + ('user', 'itemcats', 'bricks', 'locs') # 'visits'

class ForceVisitSerializer(AbstractSerializer):

    class Meta:
        model = ForceVisit
        fields = _fields + ('datetime', 'status', 'accompanied', 'node', 'loc')



class UserSerializer(AbstractSerializer):

    class Meta:
        model = User
        fields = _fields + ('email', 'first_name', 'last_name', 'last_login', 'date_joined', 'cats')

class ItemSerializer(AbstractSerializer):

    class Meta:
        model = Item
        fields = _fields + ('cats',)

class LocSerializer(AbstractSerializer):

    class Meta:
        model = Loc
        fields = _fields_name + ('street', 'unit', 'phone', 'zip', 'city', 'at', 'user', 'cats')


class FormSerializer(AbstractSerializer):

    class Meta:
        model = Form
        fields = _fields_name + ('order', 'cats')

class FormFieldSerializer(AbstractSerializer):

    class Meta:
        model = FormField
        fields = _fields_name + ('form', 'default', 'required', 'opts1')
