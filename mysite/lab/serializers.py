from rest_framework import serializers
from lab.models import *

import utils

class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'id', 'email')

class BrickSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Brick
        fields = ('url', 'id', 'name', 'zips1')

"""
class MakeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Make
        fields = ('url', 'id', 'name')

class ModelSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Model
        fields = ('url', 'id', 'name', 'make', 'engine')

class EngineSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Engine
        fields = ('url', 'id', 'name')

class TaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Task
        fields = ('url', 'id', 'name')

class CarSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Car
        fields = ('url', 'id', 'owner', 'model', 'year', 'plate')

class ServiceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Service
        fields = ('url', 'id', 'car', 'odometer', 'sched', 'enter', 'exit', 'total', 'observations')

class ServiceTaskSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = ServiceTask
        fields = ('url', 'id', 'service', 'task', 'start', 'end', 'observations')

    def validate(self, data):
        # print 'validate @ ServiceTaskSerializer @ serializers.py', data
        error = utils.validate_engine(data)
        if error:
            raise serializers.ValidationError(error)
        return data
"""
