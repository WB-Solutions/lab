from rest_framework import viewsets, serializers, routers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route

from .models import *

sets = []

router = routers.DefaultRouter()

def _api(name, viewset):
    router.register(name, viewset)

def _id(source, **kwargs):
    return serializers.PrimaryKeyRelatedField(source=source, read_only=True, **kwargs)

def _ids(source):
    return _id(source, many=True)

_fields = ('url', 'id', 'syscode')

_fields_name = _fields + ('name',)

_fields_cat = _fields_name + (
    'order', 'level',
    'parent', 'parent_id',
    'children_ids',
    'all_children_ids',
    'all_parents_ids',
)

class AbstractSerializer(serializers.HyperlinkedModelSerializer):
    pass

class AbstractTreeSerializer(AbstractSerializer):
    # level = serializers.Field(source='level') # NOT necessary because *Cat._meta.get_field('level').editable is False.
    parent_id = _id('parent')
    children_ids = _ids('children')
    all_children_ids = _ids('get_descendants')
    all_parents_ids = _ids('get_ancestors')
    pass

# http://www.django-rest-framework.org/api-guide/viewsets
class AbstractView(viewsets.ModelViewSet):
    # permission_classes = (IsAuthenticated,)
    '''
    def list(self, request):
    def create(self, request):
    def retrieve(self, request, pk=None):
    def update(self, request, pk=None):
    def partial_update(self, request, pk=None):
    def destroy(self, request, pk=None):
    '''

    @detail_route()
    def test(self, request, pk=None):
        print 'test', self, request, pk
        return Response('TEST here')



class CountrySerializer(AbstractSerializer):

    class Meta:
        model = Country
        fields = _fields_name

class CountryViewSet(AbstractView):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer

_api('countries', CountryViewSet)



class StateSerializer(AbstractSerializer):
    country_id = _id('country')

    class Meta:
        model = State
        fields = _fields_name + (
            'country', 'country_id',
        )

class StateViewSet(AbstractView):
    queryset = State.objects.all()
    serializer_class = StateSerializer

_api('states', StateViewSet)



class CitySerializer(AbstractSerializer):
    state_id = _id('state')

    class Meta:
        model = City
        fields = _fields_name + (
            'state', 'state_id',
        )

class CityViewSet(AbstractView):
    queryset = City.objects.all()
    serializer_class = CitySerializer

_api('cities', CityViewSet)



class BrickSerializer(AbstractSerializer):

    class Meta:
        model = Brick
        fields = _fields_name

class BrickViewSet(AbstractView):
    queryset = Brick.objects.all()
    serializer_class = BrickSerializer

_api('bricks', BrickViewSet)



class ZipSerializer(AbstractSerializer):
    brick_id = _id('brick')

    class Meta:
        model = Zip
        fields = _fields_name + (
            'brick', 'brick_id',
        )

class ZipViewSet(AbstractView):
    queryset = Zip.objects.all()
    serializer_class = ZipSerializer

_api('zips', ZipViewSet)



class UserCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = UserCat
        fields = _fields_cat

class UserCatViewSet(AbstractView):
    queryset = UserCat.objects.all()
    serializer_class = UserCatSerializer

_api('usercats', UserCatViewSet)



class ItemCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = ItemCat
        fields = _fields_cat

class ItemCatViewSet(AbstractView):
    queryset = ItemCat.objects.all()
    serializer_class = ItemCatSerializer

_api('itemcats', ItemCatViewSet)



class LocCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = LocCat
        fields = _fields_cat

class LocCatViewSet(AbstractView):
    queryset = LocCat.objects.all()
    serializer_class = LocCatSerializer

_api('loccats', LocCatViewSet)



class FormCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = FormCat
        fields = _fields_cat

class FormCatViewSet(AbstractView):
    queryset = FormCat.objects.all()
    serializer_class = FormCatSerializer

_api('formcats', FormCatViewSet)



class ForceNodeSerializer(AbstractTreeSerializer):
    user_id = _id('user')
    itemcats_ids = _ids('itemcats')
    bricks_ids = _ids('bricks')
    locs_ids = _ids('locs')
    # visits = serializers.HyperlinkedRelatedField(source='visits', many=True, read_only=True, view_name='forcevisits') # NOT working, ERROR.
    visits_ids = _ids('visits')

    class Meta:
        model = ForceNode
        fields = _fields_cat + (
            'user', 'user_id',
            'itemcats', 'itemcats_ids',
            'bricks', 'bricks_ids',
            'locs', 'locs_ids',
            'visits_ids', # 'visits'
        )

class ForceNodeViewSet(AbstractView):
    queryset = ForceNode.objects.all()
    serializer_class = ForceNodeSerializer

_api('forcenodes', ForceNodeViewSet)



class ForceVisitSerializer(AbstractSerializer):
    node_id = _id('node')
    loc_id = _id('loc')

    class Meta:
        model = ForceVisit
        fields = _fields + (
            'datetime', 'status', 'accompanied',
            'node', 'node_id',
            'loc', 'loc_id',
        )

class ForceVisitViewSet(AbstractView):
    queryset = ForceVisit.objects.all()
    serializer_class = ForceVisitSerializer

_api('forcevisits', ForceVisitViewSet)



class UserSerializer(AbstractSerializer):
    cats_ids = _ids('cats')

    # read-only via Field.
    last_login = serializers.Field(source='last_login')
    date_joined = serializers.Field(source='date_joined')

    class Meta:
        model = User
        fields = _fields + (
            'email', 'first_name', 'last_name', 'last_login', 'date_joined',
            'cats', 'cats_ids',
        )

class UserViewSet(AbstractView):
    queryset = User.objects.all()
    serializer_class = UserSerializer

_api('users', UserViewSet)



class ItemSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    visits_usercats_ids = _ids('visits_usercats')
    visits_loccats_ids = _ids('visits_loccats')

    class Meta:
        model = Item
        fields = _fields_name + (
            'cats', 'cats_ids',
            'visits_description', 'visits_expandable', 'visits_order',
            'visits_usercats', 'visits_usercats_ids',
            'visits_loccats', 'visits_loccats_ids',
        )

class ItemViewSet(AbstractView):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer

_api('items', ItemViewSet)



class LocSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    at_id = _id('at')
    user_id = _id('user')

    class Meta:
        model = Loc
        fields = _fields_name + (
            'street', 'unit', 'phone', 'zip', 'city',
            'cats', 'cats_ids',
            'at', 'at_id',
            'user', 'user_id',
        )

class LocViewSet(AbstractView):
    queryset = Loc.objects.all()
    serializer_class = LocSerializer

_api('locs', LocViewSet)



class FormSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    visits_repitems_ids = _ids('visits_repitems')
    visits_repitemcats_ids = _ids('visits_repitemcats')
    visits_usercats_ids = _ids('visits_usercats')
    visits_itemcats_ids = _ids('visits_itemcats')
    visits_loccats_ids = _ids('visits_loccats')
    visits_forcenodes_ids = _ids('visits_forcenodes')
    visits_bricks_ids = _ids('visits_bricks')

    class Meta:
        model = Form
        fields = _fields_name + (
            'description', 'expandable', 'order',
            'cats', 'cats_ids',
            'visits_repitems', 'visits_repitems_ids',
            'visits_repitemcats', 'visits_repitemcats_ids',
            'visits_usercats', 'visits_usercats_ids',
            'visits_itemcats', 'visits_itemcats_ids',
            'visits_loccats', 'visits_loccats_ids',
            'visits_forcenodes', 'visits_forcenodes_ids',
            'visits_bricks', 'visits_bricks_ids',
        )

class FormViewSet(AbstractView):
    queryset = Form.objects.all()
    serializer_class = FormSerializer

_api('forms', FormViewSet)



class FormFieldSerializer(AbstractSerializer):
    form_id = _id('form')

    class Meta:
        model = FormField
        fields = _fields_name + (
            'description', 'type', 'default', 'required', 'order', 'opts1',
            'form', 'form_id',
        )

class FormFieldViewSet(AbstractView):
    queryset = FormField.objects.all()
    serializer_class = FormFieldSerializer

_api('formfields', FormFieldViewSet)
