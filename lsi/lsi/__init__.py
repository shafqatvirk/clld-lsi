import re
from functools import partial

from pyramid.config import Configurator
from path import path

from clld.interfaces import IParameter, IMapMarker, IDomainElement, IValue, IValueSet
from clld.web.adapters.base import adapter_factory
from clld.web.app import menu_item
from clld_glottologfamily_plugin.util import LanguageByFamilyMapMarker

# we must make sure custom models are known at database initialization!
from lsi import models
import lsi


class MyMapMarker(LanguageByFamilyMapMarker):
    def get_icon(self, ctx, req):
        if IValue.providedBy(ctx):
            ##print ctx,[self],ctx.domainelement.parameter
            
            return ctx.domainelement.jsondata['icon']
        if IValueSet.providedBy(ctx):
            return ctx.values[0].domainelement.jsondata['icon']
        if IDomainElement.providedBy(ctx):
            
            return ctx.jsondata['icon']
        #print ctx, ctx.family
        return LanguageByFamilyMapMarker.get_icon(self, ctx, req)


def main(global_config, **settings):
    ##print "#############"
    """ This function returns a Pyramid WSGI application.
    """
    convert = lambda spec: ''.join(c if i == 0 else c + c for i, c in enumerate(spec))
    ##filename_pattern = re.compile('(?P<spec>(c|d|s|f|t)[0-9a-f]{3})\.png')
    filename_pattern = re.compile('(?P<spec>(.*?))\.png')
    icons = {}
    for name in sorted(
        path(lsi.__file__).dirname().joinpath('static', 'icons').files()
    ):
        m = filename_pattern.match(name.splitall()[-1])
        if m:
            icons[m.group('spec')] = convert(m.group('spec'))
    settings['icons'] = icons

    config = Configurator(settings=settings)
    config.include('clldmpg')
    config.include('clld_glottologfamily_plugin')
    config.registry.registerUtility(MyMapMarker(), IMapMarker)
    #config.registry.registerUtility(Blog(settings), IBlog)
    config.register_menu(
        ('dataset', partial(menu_item, 'dataset', label='Home')),
        ('parameters', partial(menu_item, 'parameters', label='Features')),
        ('languages', partial(menu_item, 'languages')),
        ('sources', partial(menu_item, 'sources')),
        ('designers', partial(menu_item, 'contributions', label="Contributors")),
        #('predicates', partial(menu_item, 'languages', label="Predicates")),
    )
    config.register_adapter(adapter_factory(
        'parameter/detail_tab.mako',
        mimetype='application/vnd.clld.tab',
        send_mimetype="text/plain",
        extension='tab',
        name='tab-separated values'), IParameter)
    
    ##app = config.make_wsgi_app()
    ##from paste.translogger import TransLogger
    ##app = TransLogger(app, setup_console_handler=False)
    ##return app
    return config.make_wsgi_app()