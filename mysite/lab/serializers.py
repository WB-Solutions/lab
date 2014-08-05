from rest_framework import serializers
from lab.models import *

import utils

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'email')

class BrickSerializer(serializers.HyperlinkedModelSerializer):
    zips_ = serializers.Field(source='zips_')

    class Meta:
        model = Brick
        fields = ('url', 'id', 'name', 'zips_')

class DoctorCatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DoctorCat
        fields = ('url', 'id', 'name')

class DoctorSpecialtySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DoctorSpecialty
        fields = ('url', 'id', 'name')

class DoctorSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Doctor
        fields = ('url', 'id', 'user', 'cats', 'specialties')

class DoctorLocSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DoctorLoc
        fields = ('url', 'id', 'doctor', 'name', 'street', 'unit', 'zip')

class ItemCatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ItemCat
        fields = ('url', 'id', 'name')

class ItemSubcatSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ItemSubcat
        fields = ('url', 'id', 'name', 'cat')

class ItemSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Item
        fields = ('url', 'id', 'name', 'subcat')

class MarketSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Market
        fields = ('url', 'id', 'name', 'items')

class ForceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Force
        fields = ('url', 'id', 'name')
