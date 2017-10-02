<%inherit file="../${context.get('request').registry.settings.get('clld.app_template', 'app.mako')}"/>
<%namespace name="util" file="../util.mako"/>
<%! active_menu_item = "contributions" %>

<h2>${_('Author')} ${ctx.name}</h2>

${util.data()}

<% dt = request.registry.queryUtility(h.interfaces.IDataTable, 'values'); dt = dt(request, h.models.Value, contribution=ctx) %>
% if dt:
<div>
${dt.render()}
</div>
% endif