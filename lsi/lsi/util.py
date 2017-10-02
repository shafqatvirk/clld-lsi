from itertools import groupby

from sqlalchemy.orm import joinedload_all, joinedload

from clld import RESOURCES
from clld.db.meta import DBSession
from clld.db.models.common import ValueSet, Value
from clld.web.util.helpers import button, icon
from clld.web.util.multiselect import CombinationMultiSelect
from clld.web.util.htmllib import HTML

from lsi.models import lsiLanguage
from lsi.maps import CombinedMap


def comment_button(req, valueset, class_=''):
    return HTML.form(
        button(icon('comment'), type='submit', class_=class_, title='comment'),
        class_='inline',
        method='POST',
        action=req.resource_url(valueset))


def dataset_detail_html(context=None, request=None, **kw):
    return {
        'stats': context.get_stats([rsc for rsc in RESOURCES if rsc.name in ['language', 'parameter', 'value']]),
        'stats_datapoints': "TODO"
    }


def icons(req, param):
    icon_map = req.registry.settings['icons']
    print "yes"
    print icon_map
    td = lambda spec: HTML.td(
        HTML.img(
            ##src=req.static_url('clld:web/static/icons/' + icon_map[spec] + '.png'),
            src=req.static_url('lsi:static/icons/' + icon_map[spec] + '.png'),
            height='20',
            width='20'),
        onclick='LSI.reload({"%s": "%s"})' % (param, spec))
    rows = [
        HTML.tr(*map(td, icons)) for c, icons in
        groupby(sorted(icon_map.keys()), lambda spec: spec[0])]
    return HTML.div(
        HTML.table(
            HTML.tbody(*rows),
            class_="table table-condensed"
        ),
        button('Close', **{'data-dismiss': 'clickover'}))


def _valuesets(parameter):
    return DBSession.query(ValueSet)\
        .filter(ValueSet.parameter_pk == parameter.pk)\
        .options(
            joinedload(ValueSet.language),
            joinedload_all(ValueSet.values, Value.domainelement))


def parameter_detail_html(context=None, request=None, **kw):
    return dict(select=CombinationMultiSelect(request, selected=[context]))


def parameter_detail_tab(context=None, request=None, **kw):
    query = _valuesets(context).options(
        joinedload_all(ValueSet.language, lsiLanguage.family))
    return dict(datapoints=query)


def combination_detail_html(context=None, request=None, **kw):
    """feature combination view
    """
    return dict(
        select=CombinationMultiSelect(request, combination=context),
        map=CombinedMap(context, request))