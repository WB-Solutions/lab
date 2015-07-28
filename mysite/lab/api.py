from rest_framework import viewsets, serializers, routers
from rest_framework.response import Response
from rest_framework.decorators import detail_route, list_route
import django_filters # http://www.django-rest-framework.org/api-guide/filtering#djangofilterbackend

from .models import *
from . import admin
import utils

from django import forms
from django.forms import widgets

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

class GoRelatedField(serializers.PrimaryKeyRelatedField):

    def field_from_native(self, data, files, field_name, into):
        # print 'GoRelatedField > field_from_native', field_name
        if self.many and isinstance(self.widget, widgets.Input):
            # print 'GoRelatedField > field_from_native - MANY', data
            vn = data.getlist(field_name)
            if vn:
                v1 = vn[0]
                if len(v1) > 1 and v1[0] == '[' and v1[-1] == ']': # handle [1,2,3] array format.
                    v1 = v1[1:-1]
                vn[:] = [ e for e in [ e.strip() for e in v1.split(',') ] if e ]
            # print 'GoRelatedField > vn', vn
        return super(GoRelatedField, self).field_from_native(data, files, field_name, into)

    '''
    def field_to_native(self, obj, field_name):
        print 'GoRelatedField > field_to_native', field_name, obj
        return super(GoRelatedField, self).field_to_native(obj, field_name)
    '''

def _id_url(source, many=False):
    f = getattr(model, source).field
    rel = f.rel
    via = getattr(rel, 'through', None)
    readonly = via and not via._meta.auto_created
    # print 'rel & via', model, source, rel, via
    return (
        # http://tomchristie.github.io/rest-framework-2-docs/api-guide/serializers#how-hyperlinked-views-are-determined
        GoRelatedField(
            widget = widgets.TextInput,
            # source = source, # NOT necessary because the api field name automatically identifies the model field name.
            # write_only = True,
            read_only = readonly, # required @ ForceNode.locs, where values must NOT be editable, otherwise error: Cannot set values on a ManyToManyField which specifies an intermediary model.  Use lab.ForceVisit's Manager instead..
            required = not f.blank and not readonly,
            many = many,
        ),
        serializers.HyperlinkedRelatedField(
            source = source,
            view_name = '%s-detail' % rel.to.__name__.lower(),
            read_only = True,
            many = many,
            # lookup_field = source,
        ),
    )

def _ids_urls(*args, **kwargs):
    return _id_url(many=True, *args, **kwargs)

_fields = ('url', 'id', 'syscode')

_fields_name = _fields + ('name',)

_fields_cat = _fields_name + (
    'order', 'level',
    'parent', 'parent__url',

    # using detail_route @ AbstractTreeView instead.
    # 'children_ids', 'allchildren_ids', 'allparents_ids',
)

_filters_cat = ('order', 'level', 'parent')

def _filter_start(name):
    return django_filters.DateTimeFilter(name='datetime', lookup_type='gte')

def _filter_end(name):
    return django_filters.DateTimeFilter(name='datetime', lookup_type='lte')

class AbstractSerializer(serializers.HyperlinkedModelSerializer):

    '''
    def from_native(self, data, files):
        if data: pass
        return super(AbstractSerializer, self).from_native(data, files)
    '''

    pass

class AbstractTreeSerializer(AbstractSerializer):

    # level = serializers.Field(source='level') # NOT necessary because *Cat._meta.get_field('level').editable is False.

    # children_ids = _get_ids('children')
    # allchildren_ids = _get_ids('get_descendants')
    # allparents_ids = _get_ids('get_ancestors')

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
        # print 'retrieve', self, request, args, kwargs, request.DATA
        self.kwargs['_go_retrieve'] = True
        v = super(AbstractView, self).retrieve(request, *args, **kwargs)
        return v

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
                        # print 'get_queryset', self, type(qset), model, cats
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

    country, country__url = _id_url('country')

    class Meta:
        model = model
        fields = _fields_name + (
            'country', 'country__url',
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

    state, state__url = _id_url('state')

    class Meta:
        model = model
        fields = _fields_name + (
            'state', 'state__url',
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

    brick, brick__url = _id_url('brick')

    class Meta:
        model = model
        fields = _fields_name + (
            'brick', 'brick__url',
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



model = Area
search = _search(admin.AreaAdmin)

class AreaSerializer(AbstractSerializer):

    city, city__url = _id_url('city')
    zip, zip__url = _id_url('zip')

    class Meta:
        model = model
        fields = _fields_name + (
            'city', 'city__url',
            'zip', 'zip__url',
        )

class AreaFilter(AbstractFilter):

    state = django_filters.Filter(name='city__state')
    country = django_filters.Filter(name='city__state__country')
    brick = django_filters.Filter(name='zip__brick')

    class Meta:
        model = model
        fields = search + ('city', 'state', 'country', 'zip', 'brick')

class AreaViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = AreaSerializer
    search_fields = search
    filter_class = AreaFilter

_api('areas', AreaViewSet)



model = GenericCat
search = _search(admin.GenericCatAdmin)

class GenericCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

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



model = PeriodCat
search = _search(admin.PeriodCatAdmin)

class PeriodCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

    class Meta:
        model = model
        fields = _fields_cat

class PeriodCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class PeriodCatViewSet(AbstractTreeView):

    queryset = _all(model)
    serializer_class = PeriodCatSerializer
    search_fields = search
    filter_class = PeriodCatFilter

_api('periodcats', PeriodCatViewSet)



model = UserCat
search = _search(admin.UserCatAdmin)

class UserCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

    class Meta:
        model = model
        fields = _fields_cat + (
            'forms_description', 'forms_expandable', 'forms_order',
        )

class UserCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ('forms_expandable', 'forms_order')

class UserCatViewSet(AbstractTreeView):

    queryset = _all(model)
    serializer_class = UserCatSerializer
    search_fields = search
    filter_class = UserCatFilter

_api('usercats', UserCatViewSet)



model = ItemCat
search = _search(admin.ItemCatAdmin)

class ItemCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

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

    parent, parent__url = _id_url('parent')

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



model = PlaceCat
search = _search(admin.PlaceCatAdmin)

class PlaceCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

    class Meta:
        model = model
        fields = _fields_cat

class PlaceCatFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ()

class PlaceCatViewSet(AbstractTreeView):

    queryset = _all(model)
    serializer_class = PlaceCatSerializer
    search_fields = search
    filter_class = PlaceCatFilter

_api('placecats', PlaceCatViewSet)



model = FormCat
search = _search(admin.FormCatAdmin)

class FormCatSerializer(AbstractTreeSerializer):

    parent, parent__url = _id_url('parent')

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

    parent, parent__url = _id_url('parent')

    user, user__url = _id_url('user')

    itemcats, itemcats__urls = _ids_urls('itemcats')

    bricks, bricks__urls = _ids_urls('bricks')
    locs, locs__urls = _ids_urls('locs')

    # visits, visits__urls = _ids_urls('visits')

    class Meta:
        model = model
        fields = _fields_cat + (
            'user', 'user__url',
            'itemcats', 'itemcats__urls',
            'bricks', 'bricks__urls',
            'locs', 'locs__urls',
            # 'visits', 'visits__urls'
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

    node, node__url = _id_url('node')
    loc, loc__url = _id_url('loc')
    builder, builder__url = _id_url('builder')

    get_prep_public = serializers.Field()
    get_prep_private = serializers.Field()

    class Meta:
        model = model
        fields = _fields_name + (
            'datetime', 'duration', 'status', 'accompanied',

            'node', 'node__url',
            'loc', 'loc__url',
            'builder', 'builder__url',

            'observations', 'rec',

            'f_contact', 'f_goal', 'f_option',
            'get_prep_public', 'get_prep_private',
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

    week_visit, week_visit__url = _id_url('week_visit')
    week_visited, week_visited__url = _id_url('week_visited')

    cats, cats__urls = _ids_urls('cats')

    # read-only via Field.
    last_login = serializers.Field()
    date_joined = serializers.Field()

    _pwd = serializers.Field()
    pwd = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = model
        fields = _fields + (
            'email', 'first_name', 'last_name', 'last_login', 'date_joined',
            'week_visit', 'week_visit__url',
            'week_visited', 'week_visited__url',
            'cats', 'cats__urls',
            '_pwd', 'pwd',
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

    def pre_save(self, obj):
        print '.' * 100, 'pre_save', obj

    def post_save(self, obj, created):
        pwd = obj.pwd
        # print 'post_save', created, pwd, obj
        if pwd:
            obj.set_password(pwd)
            obj.save()

_api('users', UserViewSet)



model = UserFormRec
search = _search(admin.UserFormRecAdmin)

class UserFormRecSerializer(AbstractSerializer):

    user, user__url = _id_url('user')
    form, form__url = _id_url('form')

    class Meta:
        model = model
        fields = _fields + (
            'datetime', 'observations', 'rec',
            'user', 'user__url',
            'form', 'form__url',
        )

class UserFormRecFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search # + ('observations', 'rec')

class UserFormRecViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = UserFormRecSerializer
    search_fields = search
    filter_class = UserFormRecFilter

_api('userformrecs', UserFormRecViewSet)



model = Item
search = _search(admin.ItemAdmin)

class ItemSerializer(AbstractSerializer):

    cats, cats__urls = _ids_urls('cats')
    visits_usercats, visits_usercats__urls = _ids_urls('visits_usercats')
    visits_loccats, visits_loccats__urls = _ids_urls('visits_loccats')

    class Meta:
        model = model
        fields = _fields_name + (
            'cats', 'cats__urls',
            'forms_description', 'forms_expandable', 'forms_order',
            'visits_usercats', 'visits_usercats__urls',
            'visits_loccats', 'visits_loccats__urls',
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

    area, area__url = _id_url('area')

    class Meta:
        model = model
        fields = _fields + (
            'street', 'unit', 'phone', 'phone2', 'fax',
            'area', 'area__url',
        )

class AddressFilter(AbstractFilter):

    city = django_filters.Filter(name='area__city')
    state = django_filters.Filter(name='area__city__state')
    country = django_filters.Filter(name='area__city__state__country')
    zip = django_filters.Filter(name='area__zip')
    brick = django_filters.Filter(name='area__zip__brick')

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

    parent, parent__url = _id_url('parent')

    address, address__url = _id_url('address')
    cats, cats__urls = _ids_urls('cats')

    class Meta:
        model = model
        fields = _fields_cat + (
            'address', 'address__url',
            'cats', 'cats__urls',
        )

class PlaceFilter(AbstractTreeFilter):

    class Meta:
        model = model
        fields = search + _filters_cat + ('address',)

class PlaceViewSet(AbstractTreeView):

    queryset = _all(model)
    serializer_class = PlaceSerializer
    search_fields = search
    filter_class = PlaceFilter

_api('places', PlaceViewSet)


model = Loc
search = _search(admin.LocAdmin)

class LocSerializer(AbstractSerializer):

    user, user__url = _id_url('user')
    week, week__url = _id_url('week')
    cats, cats__urls = _ids_urls('cats')
    address, address__url = _id_url('address')
    place, place__url = _id_url('place')

    class Meta:
        model = model
        fields = _fields_name + (
            'user', 'user__url',
            'week', 'week__url',
            'cats', 'cats__urls',
            'address', 'address__url',
            'place', 'place__url',
        )

class LocFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('user', 'week', 'address', 'place')

class LocViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = LocSerializer
    search_fields = search
    filter_class = LocFilter

_api('locs', LocViewSet)



model = FormType
search = _search(admin.FormTypeAdmin)

class FormTypeSerializer(AbstractSerializer):

    class Meta:
        model = model
        fields = _fields_name + (
            'order', 'description',
        )

class FormTypeFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search

class FormTypeViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = FormTypeSerializer
    search_fields = search
    filter_class = FormTypeFilter

_api('formtypes', FormTypeViewSet)



model = Form
search = _search(admin.FormAdmin)

class FormSerializer(AbstractSerializer):

    cats, cats__urls = _ids_urls('cats')

    repitems, repitems__urls = _ids_urls('repitems')
    repitemcats, repitemcats__urls = _ids_urls('repitemcats')
    repusercats, repusercats__urls = _ids_urls('repusercats')

    users_usercats, users_usercats__urls = _ids_urls('users_usercats')
    users_loccats, users_loccats__urls = _ids_urls('users_loccats')
    visits_usercats, visits_usercats__urls = _ids_urls('visits_usercats')
    visits_loccats, visits_loccats__urls = _ids_urls('visits_loccats')
    visits_itemcats, visits_itemcats__urls = _ids_urls('visits_itemcats')
    visits_forcenodes, visits_forcenodes__urls = _ids_urls('visits_forcenodes')
    visits_bricks, visits_bricks__urls = _ids_urls('visits_bricks')
    types, types__urls = _ids_urls('types')

    class Meta:
        model = model
        fields = _fields_name + (
            'scope', 'start', 'end', 'description', 'expandable', 'order', 'private',
            'cats', 'cats__urls',

            'repitems', 'repitems__urls',
            'repitemcats', 'repitemcats__urls',
            'repusercats', 'repusercats__urls',

            'users_usercats', 'users_usercats__urls',
            'users_loccats', 'users_loccats__urls',
            'visits_usercats', 'visits_usercats__urls',
            'visits_loccats', 'visits_loccats__urls',
            'visits_itemcats', 'visits_itemcats__urls',
            'visits_forcenodes', 'visits_forcenodes__urls',
            'visits_bricks', 'visits_bricks__urls',
            'types', 'types__urls',
        )

class FormFilter(AbstractFilter):

    start_starts = _filter_start('start')
    start_ends = _filter_end('start')
    end_starts = _filter_start('end')
    end_ends = _filter_end('end')

    class Meta:
        model = model
        fields = search + ('scope', 'start_starts', 'start_ends', 'end_starts', 'end_ends', 'expandable', 'order', 'private')

class FormViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = FormSerializer
    search_fields = search
    filter_class = FormFilter

_api('forms', FormViewSet)



model = FormField
search = _search(admin.FormFieldAdmin)

class FormFieldSerializer(AbstractSerializer):

    form, form__url = _id_url('form')
    optscat, optscat__url = _id_url('optscat')
    types, types__urls = _ids_urls('types')

    class Meta:
        model = model
        fields = _fields_name + (
            'description', 'type', 'widget', 'default', 'required', 'order', 'opts1',
            'optscat', 'optscat__url',
            'form', 'form__url',
            'types', 'types__urls',
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

    week, week__url = _id_url('week')
    cats, cats__urls = _ids_urls('cats')

    class Meta:
        model = model
        fields = _fields_name + (
            'end',
            'week', 'week__url',
            'cats', 'cats__urls',
        )

class PeriodFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('end', 'week')

class PeriodViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = PeriodSerializer
    search_fields = search
    filter_class = PeriodFilter

_api('periods', PeriodViewSet)



model = WeekConfig
search = _search(admin.WeekConfigAdmin)

class WeekConfigSerializer(AbstractSerializer):

    mon, mon__url = _id_url('mon')
    tue, tue__url = _id_url('tue')
    wed, wed__url = _id_url('wed')
    thu, thu__url = _id_url('thu')
    fri, fri__url = _id_url('fri')
    sat, sat__url = _id_url('sat')
    sun, sun__url = _id_url('sun')

    class Meta:
        model = model
        fields = _fields_name + (
            'mon', 'mon__url',
            'tue', 'tue__url',
            'wed', 'wed__url',
            'thu', 'thu__url',
            'fri', 'fri__url',
            'sat', 'sat__url',
            'sun', 'sun__url',
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

    day, day__url = _id_url('day')

    class Meta:
        model = model
        fields = _fields_name + (
            'start', 'end',
            'day', 'day__url',
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

    node, node__url = _id_url('node')
    periods, periods__urls = _ids_urls('periods')
    periodcats, periodcats__urls = _ids_urls('periodcats')

    class Meta:
        model = model
        fields = _fields_name + (
            'duration', 'orderby', 'isand', 'generate',
            'generated', 'qty_slots', 'qty_slots_skips', 'qty_locs', 'qty_locs_skips', 'qty_node_skips', 'qty_visits', # editable=False.

            'node', 'node__url',

            'periods', 'periods__urls',
            'periodcats', 'periodcats__urls',
        )

class VisitBuilderFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('node', 'duration', 'gap', 'forcebricks', 'generated')

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



model = VisitCond
search = _search(admin.VisitCondAdmin)

class VisitCondSerializer(AbstractSerializer):

    builder, builder__url = _id_url('builder')

    usercats, usercats__urls = _ids_urls('usercats')
    loccats, loccats__urls = _ids_urls('loccats')
    placecats, placecats__urls = _ids_urls('placecats')

    areas, areas__urls = _ids_urls('areas')
    cities, cities__urls = _ids_urls('cities')
    states, states__urls = _ids_urls('states')
    countries, countries__urls = _ids_urls('countries')

    zips, zips__urls = _ids_urls('zips')
    bricks, bricks__urls = _ids_urls('bricks')

    class Meta:
        model = model
        fields = _fields_name + (
            'builder', 'builder__url',

            'usercats', 'usercats__urls',
            'loccats', 'loccats__urls',
            'placecats', 'placecats__urls',

            'areas', 'areas__urls',
            'cities', 'cities__urls',
            'states', 'states__urls',
            'countries', 'countries__urls',

            'zips', 'zips__urls',
            'bricks', 'bricks__urls',
        )

class VisitCondFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search

class VisitCondViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = VisitCondSerializer
    search_fields = search
    filter_class = VisitCondFilter

_api('visitconds', VisitCondViewSet)



model = OnOffPeriod
search = _search(admin.OnOffPeriodAdmin)

class OnOffPeriodSerializer(AbstractSerializer):

    visit_user, visit_user__url = _id_url('visit_user')
    visited_user, visited_user__url = _id_url('visited_user')
    visited_loc, visited_loc__url = _id_url('visited_loc')

    class Meta:
        model = model
        fields = _fields + (
            'on', 'start', 'end',

            'visit_user', 'visit_user__url',
            'visited_user', 'visited_user__url',
            'visited_loc', 'visited_loc__url',
        )

class OnOffPeriodFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('start', 'end')

class OnOffPeriodViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = OnOffPeriodSerializer
    search_fields = search
    filter_class = OnOffPeriodFilter

_api('onoffperiods', OnOffPeriodViewSet)



model = OnOffTime
search = _search(admin.OnOffTimeAdmin)

class OnOffTimeSerializer(AbstractSerializer):

    visit_user, visit_user__url = _id_url('visit_user')
    visited_user, visited_user__url = _id_url('visited_user')
    visited_loc, visited_loc__url = _id_url('visited_loc')

    class Meta:
        model = model
        fields = _fields + (
            'on', 'start', 'end', 'date',

            'visit_user', 'visit_user__url',
            'visited_user', 'visited_user__url',
            'visited_loc', 'visited_loc__url',
        )

class OnOffTimeFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('start', 'end', 'date')

class OnOffTimeViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = OnOffTimeSerializer
    search_fields = search
    filter_class = OnOffTimeFilter

_api('onofftimes', OnOffTimeViewSet)



model = Sys
search = _search(admin.SysAdmin)

class SysSerializer(AbstractSerializer):

    week_user_visit, week_user_visit__url = _id_url('week_user_visit')
    week_user_visited, week_user_visited__url = _id_url('week_user_visited')
    week_period, week_period__url = _id_url('week_period')

    class Meta:
        model = model
        fields = _fields + (
            'week_user_visit', 'week_user_visit__url',
            'week_user_visited', 'week_user_visited__url',
            'week_period', 'week_period__url',
        )

class SysFilter(AbstractFilter):

    class Meta:
        model = model
        fields = search + ('week_user_visit', 'week_user_visited', 'week_period')

class SysViewSet(AbstractView):

    queryset = _all(model)
    serializer_class = SysSerializer
    search_fields = search
    filter_class = SysFilter

_api('sys', SysViewSet)


