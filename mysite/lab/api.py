from rest_framework import viewsets, serializers, routers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
import django_filters # http://www.django-rest-framework.org/api-guide/filtering#djangofilterbackend

from .models import *
from . import admin
import utils

sets = []

router = routers.DefaultRouter()

def _all(model):
    return model.objects.all()

def _search(_admin):
    v = _admin.search_fields
    # print '_search', _admin, v
    return v

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

    # using detail_route @ AbstractTreeView instead.
    # 'children_ids', 'allchildren_ids', 'allparents_ids',
)

_filters_cat = ('order', 'level', 'parent')

def _filter_start(name):
    return django_filters.DateTimeFilter(name='datetime', lookup_type='gte')

def _filter_end(name):
    return django_filters.DateTimeFilter(name='datetime', lookup_type='lte')

class AbstractSerializer(serializers.HyperlinkedModelSerializer):
    pass

class AbstractTreeSerializer(AbstractSerializer):
    # level = serializers.Field(source='level') # NOT necessary because *Cat._meta.get_field('level').editable is False.
    parent_id = _id('parent')
    # children_ids = _ids('children')
    # allchildren_ids = _ids('get_descendants')
    # allparents_ids = _ids('get_ancestors')

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

    # http://www.django-rest-framework.org/api-guide/viewsets#marking-extra-actions-for-routing

    @detail_route()
    def test(self, request, pk=None):
        print 'test', self, request, pk
        return Response('test RESULT')

    @list_route()
    def tests(self, request):
        print 'tests', self, request
        return Response('tests RESULT')

    def retrieve(self, request, *args, **kwargs):
        # print 'retrieve', self, request, args, kwargs
        self.kwargs['_go_retrieve'] = True
        return super(AbstractView, self).retrieve(request, *args, **kwargs)

    def get_object(self, queryset=None):
        kw = self.kwargs
        if kw.get('_go_retrieve'):
            k = 'syscode'
            pk = kw.get('pk')
            pre = '@'
            if pk and pk.startswith(pre):
                self.lookup_field = k
                kw[k] = pk[len(pre):]
        v = super(AbstractView, self).get_object(queryset)
        # print 'get_object', self, queryset, v
        return v

    # http://www.django-rest-framework.org/api-guide/filtering
    def get_queryset(self):
        qset = super(AbstractView, self).get_queryset()
        for name, deep in [ ('incats', True), ('cats', False) ]:
            cats = self.request.QUERY_PARAMS.get(name)
            if cats:
                model = qset.model # self.get_serializer().opts.model
                field = model._meta.get_field('cats')
                if field:
                    cats = utils.str_ints(cats)
                    if cats:
                        if deep:
                            target = field.related.parent_model
                            cats = utils.list_compact([ utils.db_get(target, cat) for cat in cats ])
                            cats = utils.tree_all_downs(cats)
                        qset = qset.filter(cats__in=cats)
                        print 'get_queryset', self, type(qset), model, cats
        return qset

class AbstractTreeView(AbstractView):

    @list_route()
    def roots(self, request):
        serializer = self.get_serializer()
        model = serializer.opts.model
        roots = list(model.objects.root_nodes())
        # print 'AbstractTreeView.roots', self, model, roots
        natives = [ serializer.to_native(each) for each in roots ]
        return Response(natives)

    def _field_value(self, name):
        treenode = self.get_object()
        serializer = self.get_serializer()
        val = serializer.field_to_native(treenode, name)
        # print 'AbstractTreeView._field_value', self, name, treenode, val
        return Response(val)

    @detail_route()
    def children(self, request, pk=None):
        return self._field_value('children')

    @detail_route()
    def allchildren(self, request, pk=None):
        return self._field_value('get_descendants')

    @detail_route()
    def allparents(self, request, pk=None):
        return self._field_value('get_ancestors')

class AbstractFilter(django_filters.FilterSet):
    pass

'''
class GoFilter(django_filters.CharFilter):

    def filter(self, qs, value):
        print 'filter', self, value, len(value)
        return qs
'''

class AbstractTreeFilter(AbstractFilter):
    pass



model = Country
search = _search(admin.CountryAdmin)

class CountrySerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name

class CountryFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ()

class CountryViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = CountrySerializer
    search_fields = search
    filter_class = CountryFilter

_api('countries', CountryViewSet)



model = State
search = _search(admin.StateAdmin)

class StateSerializer(AbstractSerializer):
    country_id = _id('country')

    class Meta:
        model = model
        fields = _fields_name + (
            'country', 'country_id',
        )

class StateFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('country',)

class StateViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = StateSerializer
    search_fields = search
    filter_class = StateFilter

_api('states', StateViewSet)



model = City
search = _search(admin.CityAdmin)

class CitySerializer(AbstractSerializer):
    state_id = _id('state')

    class Meta:
        model = model
        fields = _fields_name + (
            'state', 'state_id',
        )

class CityFilter(AbstractFilter):
    country = django_filters.Filter(name='state__country')

    class Meta:
        model = model
        fields = ('state', 'country')

class CityViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = CitySerializer
    search_fields = search
    filter_class = CityFilter

_api('cities', CityViewSet)



model = Brick
search = _search(admin.BrickAdmin)

class BrickSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name

class BrickFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ()

class BrickViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = BrickSerializer
    search_fields = search
    filter_class = BrickFilter

_api('bricks', BrickViewSet)



model = Zip
search = _search(admin.ZipAdmin)

class ZipSerializer(AbstractSerializer):
    brick_id = _id('brick')

    class Meta:
        model = model
        fields = _fields_name + (
            'brick', 'brick_id',
        )

class ZipFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('brick',)

class ZipViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = ZipSerializer
    search_fields = search
    filter_class = ZipFilter

_api('zips', ZipViewSet)



model = Region
search = _search(admin.RegionAdmin)

class RegionSerializer(AbstractSerializer):
    city_id = _id('city')
    zip_id = _id('zip')

    class Meta:
        model = model
        fields = _fields_name + (
            'city', 'city_id',
            'zip', 'zip_id',
        )

class RegionFilter(AbstractFilter):
    state = django_filters.Filter(name='city__state')
    country = django_filters.Filter(name='city__state__country')
    brick = django_filters.Filter(name='zip__brick')

    class Meta:
        model = model
        fields = search + ('city', 'state', 'country', 'zip', 'brick')

class RegionViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = RegionSerializer
    search_fields = search
    filter_class = RegionFilter

_api('regions', RegionViewSet)



model = GenericCat
search = _search(admin.GenericCatAdmin)

class GenericCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = model
        fields = _fields_cat

class GenericCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class GenericCatViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = GenericCatSerializer
    search_fields = search
    filter_class = GenericCatFilter

_api('genericcats', GenericCatViewSet)



model = UserCat
search = _search(admin.UserCatAdmin)

class UserCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = model
        fields = _fields_cat

class UserCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class UserCatViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = UserCatSerializer
    search_fields = search
    filter_class = UserCatFilter

_api('usercats', UserCatViewSet)



model = ItemCat
search = _search(admin.ItemCatAdmin)

class ItemCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = model
        fields = _fields_cat

class ItemCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class ItemCatViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = ItemCatSerializer
    search_fields = search
    filter_class = ItemCatFilter

_api('itemcats', ItemCatViewSet)



model = LocCat
search = _search(admin.LocCatAdmin)

class LocCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = model
        fields = _fields_cat

class LocCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class LocCatViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = LocCatSerializer
    search_fields = search
    filter_class = LocCatFilter

_api('loccats', LocCatViewSet)



model = FormCat
search = _search(admin.FormCatAdmin)

class FormCatSerializer(AbstractTreeSerializer):

    class Meta:
        model = model
        fields = _fields_cat

class FormCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class FormCatViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = FormCatSerializer
    search_fields = search
    filter_class = FormCatFilter

_api('formcats', FormCatViewSet)



model = ForceNode
search = _search(admin.ForceNodeAdmin)

class ForceNodeSerializer(AbstractTreeSerializer):
    user_id = _id('user')
    itemcats_ids = _ids('itemcats')
    bricks_ids = _ids('bricks')
    locs_ids = _ids('locs')
    # visits = serializers.HyperlinkedRelatedField(source='visits', many=True, read_only=True, view_name='forcevisits') # NOT working, ERROR.
    visits_ids = _ids('visits')

    class Meta:
        model = model
        fields = _fields_cat + (
            'user', 'user_id',
            'itemcats', 'itemcats_ids',
            'bricks', 'bricks_ids',
            'locs', 'locs_ids',
            'visits_ids', # 'visits'
        )

class ForceNodeFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ('user',)

class ForceNodeViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = ForceNodeSerializer
    search_fields = search
    filter_class = ForceNodeFilter

_api('forcenodes', ForceNodeViewSet)



model = ForceVisit
search = _search(admin.ForceVisitAdmin)

class ForceVisitSerializer(AbstractSerializer):
    node_id = _id('node')
    loc_id = _id('loc')

    class Meta:
        model = model
        fields = _fields + (
            'datetime', 'duration', 'status', 'accompanied',
            'node', 'node_id',
            'loc', 'loc_id',
            'observations', 'rec',
        )

class ForceVisitFilter(AbstractFilter):
    starts = _filter_start('datetime')
    ends = _filter_end('datetime')

    class Meta:
        model = model
        fields = search + ('starts', 'ends', 'node', 'loc', 'status', 'accompanied') # 'observations', 'rec'

class ForceVisitViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = ForceVisitSerializer
    search_fields = search
    filter_class = ForceVisitFilter

_api('forcevisits', ForceVisitViewSet)



model = User
search = _search(admin.UserAdmin)

class UserSerializer(AbstractSerializer):
    cats_ids = _ids('cats')

    # read-only via Field.
    last_login = serializers.Field(source='last_login')
    date_joined = serializers.Field(source='date_joined')

    class Meta:
        model = model
        fields = _fields + (
            'email', 'first_name', 'last_name', 'last_login', 'date_joined',
            'cats', 'cats_ids',
        )

class UserFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ()

class UserViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = UserSerializer
    search_fields = search
    filter_class = UserFilter

_api('users', UserViewSet)



model = Item
search = _search(admin.ItemAdmin)

class ItemSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    visits_usercats_ids = _ids('visits_usercats')
    visits_loccats_ids = _ids('visits_loccats')

    class Meta:
        model = model
        fields = _fields_name + (
            'cats', 'cats_ids',
            'forms_description', 'forms_expandable', 'forms_order',
            'visits_usercats', 'visits_usercats_ids',
            'visits_loccats', 'visits_loccats_ids',
        )

class ItemFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('forms_expandable', 'forms_order')

class ItemViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = ItemSerializer
    search_fields = search
    filter_class = ItemFilter

_api('items', ItemViewSet)



model = Address
search = _search(admin.AddressAdmin)

class AddressSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields + (
            'street', 'unit', 'phone', 'phone2', 'fax', 'region',
        )

class AddressFilter(AbstractFilter):
    city = django_filters.Filter(name='region__city')
    state = django_filters.Filter(name='region__city__state')
    country = django_filters.Filter(name='region__city__state__country')
    zip = django_filters.Filter(name='region__zip')
    brick = django_filters.Filter(name='region__zip__brick')

    class Meta:
        model = model
        fields = search + ('city', 'state', 'country', 'zip', 'brick')

class AddressViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = AddressSerializer
    search_fields = search
    filter_class = AddressFilter

_api('addresses', AddressViewSet)


model = Place
search = _search(admin.PlaceAdmin)

class PlaceSerializer(AbstractTreeSerializer):
    address_id = _id('address')

    class Meta:
        model = model
        fields = _fields_cat + (
            'address', 'address_id',
            'canloc',
        )

class PlaceFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ('address', 'canloc')

class PlaceViewSet(AbstractTreeView):
    queryset = _all(model)
    serializer_class = PlaceSerializer
    search_fields = search
    filter_class = PlaceFilter

_api('places', PlaceViewSet)


model = Loc
search = _search(admin.LocAdmin)

class LocSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    user_id = _id('user')
    address_id = _id('address')
    place_id = _id('place')

    class Meta:
        model = model
        fields = _fields_name + (
            'cats', 'cats_ids',
            'user', 'user_id',
            'address', 'address_id',
            'place', 'place_id',
        )

class LocFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('user', 'address', 'place')

class LocViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = LocSerializer
    search_fields = search
    filter_class = LocFilter

_api('locs', LocViewSet)



model = Form
search = _search(admin.FormAdmin)

class FormSerializer(AbstractSerializer):
    cats_ids = _ids('cats')
    repitems_ids = _ids('repitems')
    repitemcats_ids = _ids('repitemcats')
    users_usercats_ids = _ids('users_usercats')
    users_loccats_ids = _ids('users_loccats')
    visits_usercats_ids = _ids('visits_usercats')
    visits_loccats_ids = _ids('visits_loccats')
    visits_itemcats_ids = _ids('visits_itemcats')
    visits_forcenodes_ids = _ids('visits_forcenodes')
    visits_bricks_ids = _ids('visits_bricks')

    class Meta:
        model = model
        fields = _fields_name + (
            'scope', 'start', 'end', 'description', 'expandable', 'order',
            'cats', 'cats_ids',
            'repitems', 'repitems_ids',
            'repitemcats', 'repitemcats_ids',
            'users_usercats', 'users_usercats_ids',
            'users_loccats', 'users_loccats_ids',
            'visits_usercats', 'visits_usercats_ids',
            'visits_loccats', 'visits_loccats_ids',
            'visits_itemcats', 'visits_itemcats_ids',
            'visits_forcenodes', 'visits_forcenodes_ids',
            'visits_bricks', 'visits_bricks_ids',
        )

class FormFilter(AbstractFilter):
    start_starts = _filter_start('start')
    start_ends = _filter_end('start')
    end_starts = _filter_start('end')
    end_ends = _filter_end('end')

    class Meta:
        model = model
        fields = search + ('scope', 'start_starts', 'start_ends', 'end_starts', 'end_ends', 'expandable', 'order')

class FormViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = FormSerializer
    search_fields = search
    filter_class = FormFilter

_api('forms', FormViewSet)



model = FormField
search = _search(admin.FormFieldAdmin)

class FormFieldSerializer(AbstractSerializer):
    form_id = _id('form')
    optscat_id = _id('optscat')

    class Meta:
        model = model
        fields = _fields_name + (
            'description', 'type', 'widget', 'default', 'required', 'order', 'opts1',
            'optscat', 'optscat_id',
            'form', 'form_id',
        )

class FormFieldFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('form', 'type', 'widget', 'required', 'order')

class FormFieldViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = FormFieldSerializer
    search_fields = search
    filter_class = FormFieldFilter

_api('formfields', FormFieldViewSet)



model = Period
search = _search(admin.PeriodAdmin)

class PeriodSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name + (
            'end',
        )

class PeriodFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('end',)

class PeriodViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = PeriodSerializer
    search_fields = search
    filter_class = PeriodFilter

_api('periods', PeriodViewSet)



model = WeekConfig
search = _search(admin.WeekConfigAdmin)

class WeekConfigSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name + utils.weekdays + (
        )

class WeekConfigFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ()

class WeekConfigViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = WeekConfigSerializer
    search_fields = search
    filter_class = WeekConfigFilter

_api('weekconfigs', WeekConfigViewSet)



model = DayConfig
search = _search(admin.DayConfigAdmin)

class DayConfigSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name + (
        )

class DayConfigFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ()

class DayConfigViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = DayConfigSerializer
    search_fields = search
    filter_class = DayConfigFilter

_api('dayconfigs', DayConfigViewSet)



model = TimeConfig
search = _search(admin.TimeConfigAdmin)

class TimeConfigSerializer(AbstractSerializer):
    day_id = _id('day')

    class Meta:
        model = model
        fields = _fields_name + (
            'start', 'end',
            'day', 'day_id',
        )

class TimeConfigFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('day', 'start', 'end')

class TimeConfigViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = TimeConfigSerializer
    search_fields = search
    filter_class = TimeConfigFilter

_api('timeconfigs', TimeConfigViewSet)



model = VisitBuilder
search = _search(admin.VisitBuilderAdmin)

class VisitBuilderSerializer(AbstractSerializer):
    node_id = _id('node')
    week_id = _id('week')
    period_id = _id('period')

    usercats_ids = _ids('usercats')
    loccats_ids = _ids('loccats')

    regions_ids = _ids('regions')
    cities_ids = _ids('cities')
    states_ids = _ids('states')
    countries_ids = _ids('countries')

    zips_ids = _ids('zips')
    bricks_ids = _ids('bricks')

    class Meta:
        model = model
        fields = _fields_name + (
            'duration', 'start', 'end', 'generate',
            'generated', 'qty', # editable=False.

            'node', 'node_id',
            'week', 'week_id',
            'period', 'period_id',

            'usercats', 'usercats_ids',
            'loccats', 'loccats_ids',

            'regions', 'regions_ids',
            'cities', 'cities_ids',
            'states', 'states_ids',
            'countries', 'countries_ids',

            'zips', 'zips_ids',
            'bricks', 'bricks_ids',

        )

class VisitBuilderFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('node', 'week', 'duration', 'period', 'start', 'end')

class VisitBuilderViewSet(AbstractView):
    queryset = _all(model)
    serializer_class = VisitBuilderSerializer
    search_fields = search
    filter_class = VisitBuilderFilter

    def destroy(self, request, pk=None):
        return Response('Delete NOT Allowed', status=405)

    def post_save(self, obj, created):
        obj._generate_check()

_api('visitbuilders', VisitBuilderViewSet)
