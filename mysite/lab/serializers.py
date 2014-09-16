from rest_framework import serializers
from .models import *

import utils

class AbstractSerializer(serializers.HyperlinkedModelSerializer):
    pass



class BrickSerializer(AbstractSerializer):
    zips_ = serializers.Field(source='zips_')

    class Meta:
        model = Brick
        fields = ('url', 'id', 'name', 'zips1', 'zips_')
