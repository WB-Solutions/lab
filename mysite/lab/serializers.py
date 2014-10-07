from rest_framework import serializers
from .models import *

import utils

class AbstractSerializer(serializers.HyperlinkedModelSerializer):
    pass

_fields = ('url', 'id')
_fields_name = _fields + ('name',)
_fields_cat = _fields_name + ('order', 'parent', 'level')



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



class AbstractTreeSerializer(serializers.HyperlinkedModelSerializer):
    # level = serializers.Field(source='level') # NOT necessary because *Cat._meta.get_field('level').editable is False.
    pass

class UserCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = UserCat
        fields = _fields_cat

class ItemCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = ItemCat
        fields = _fields_cat

class LocCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = LocCat
        fields = _fields_cat

class FormCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = FormCat
        fields = _fields_cat



class ForceNodeSerializer(AbstractTreeSerializer):
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
        fields = _fields_name + ('cats', 'visits_usercats', 'visits_loccats', 'visits_description', 'visits_expandable', 'visits_order')

class LocSerializer(AbstractSerializer):

    class Meta:
        model = Loc
        fields = _fields_name + ('street', 'unit', 'phone', 'zip', 'city', 'at', 'user', 'cats')


class FormSerializer(AbstractSerializer):

    class Meta:
        model = Form
        fields = _fields_name + ('description', 'expandable', 'order', 'cats', 'visits_repitems', 'visits_repitemcats', 'visits_usercats', 'visits_itemcats', 'visits_loccats', 'visits_forcenodes', 'visits_bricks')

class FormFieldSerializer(AbstractSerializer):

    class Meta:
        model = FormField
        fields = _fields_name + ('description', 'form', 'type', 'default', 'required', 'order', 'opts1')
