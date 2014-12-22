from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from lab.models import *
# from lab import utils

# https://docs.djangoproject.com/en/1.6/howto/custom-management-commands/

class Command(BaseCommand):
    args = 'none'
    help = 'setup_db'

    def handle(self, *args, **kwargs):
        def _email(pre):
            return '%s@go.com' % pre

        def _setup():

            def _first(model):
                return model.objects.first()

            def _last(model):
                return model.objects.last()

            def _at(model, i):
                # do NOT use get in case it failed below, and pk/id is NOT correct.
                # return model.objects.get(pk=pk)
                return model.objects.all()[i]

            def _new(model, **kwargs):
                print '_new', model, kwargs
                # kwargs.setdefault('syscode', None)
                return model.objects.create(**kwargs)

            for ecountry, states in [
                ('Mexico', [
                    ('Tamaulipas', [ 'Tampico', 'Madero', 'Victoria' ]),
                    ('Nuevo Leon', [ 'Monterrey', 'Cadereyta' ]),
                    ('Jalisco', [ 'Guadalajara' ]),
                ]),
                ('USA', [
                    ('Texas', [ 'Houston', 'Dallas', 'San Antonio' ]),
                ]),
            ]:
                country = _new(Country, name=ecountry)
                for estate, cities in states:
                    state = _new(State, country=country, name=estate)
                    for ecity in cities:
                        city = _new(City, state=state, name=ecity)

            for ebrick, zips in [
                ('Brick Tampico', [ '89000', '89440' ]),
                ('Brick Monterrey', [ 'mont01', 'mont02', 'mont03' ]),
            ]:
                brick = _new(Brick, name=ebrick)
                for ezip in zips:
                    zip = _new(Zip, brick=brick, name=ezip)

            def _new_cats(model, pre, isforce=False):
                def _cat(name, parent, **kw):
                    return _new(model, name='%s %s' % (pre, name), parent=parent, **kw)
                catpre = '' if isforce else 'cat '
                root = _cat('%sroot' % catpre, None)
                _cats = []
                for e1 in [ 'A', 'B', 'C' ]:
                    cat = _cat('%s%s' % (catpre, e1), root)
                    for e2 in range(1, 3):
                        _kw = dict(user=users.get('rep')) if isforce else dict()
                        sub = _cat('%s%s %s' % (catpre, e1, e2), cat, **_kw)
                        if isforce:
                            visit = _new(ForceVisit, node=sub, loc=users.get('doc').locs.first())
                    _cats.append(cat)
                return _cats

            generics = _new_cats(GenericCat, 'Generic')
            usercats = _new_cats(UserCat, 'User')
            itemcats = _new_cats(ItemCat, 'Item')
            loccats = _new_cats(LocCat, 'Loc')
            formcats = _new_cats(FormCat, 'Form')

            usercat = _first(UserCat) # root.

            users = dict()
            for ei, each in enumerate([ 'force', 'rep', 'doc' ]):
                user = _new(User, first_name=each, last_name=each, email=_email(each))
                users[each] = user
                user.cats.add(usercats.pop(0))
                address = _new(Address, name=each, street=each, city=_at(City, ei), zip=_at(Zip, ei))
                loc = _new(Loc, name=each, user=user, address=address)
                loc.cats.add(loccats.pop(0))

            nodes = _new_cats(ForceNode, 'Force', isforce=True)

            for each in [ 'Item A', 'Item B', 'Item C' ]:
                item = _new(Item, name=each, forms_description='Description @ %s' % each)
                item.cats.add(itemcats.pop(0))
                item.visits_usercats.add(usercat)

            for each in [ 'A', 'B', 'repitems' ]:
                ename = 'Form %s' % each
                form = _new(Form, name=ename, description='Description @ %s' % ename)
                form.cats.add(formcats.pop(0))
                form.visits_usercats.add(usercat)
                for ei in range(1, 3):
                    ename = 'Field %s %s' % (each, ei)
                    field = _new(FormField, form=form, name=ename, description='Description @ %s' % ename, default=ename, required=True)
            form.repitems.add(_first(Item), _last(Item)) # last form.

        err = None
        if User.objects.exists():
            err = 'db already setup'
        else:
            try:
                with transaction.atomic():
                    User.objects.create_superuser(_email('admin'), 'admin')
                    _setup()
            except:
                import sys
                e = sys.exc_info()[0]
                err = str(e)
                # raise(e)

        self.stdout.write('ERROR @ setup_db: %s' % err if err else 'Success')
