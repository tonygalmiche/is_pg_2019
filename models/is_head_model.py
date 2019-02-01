# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.osv.orm import BaseModel
from lxml import etree
import itertools
import re


def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
    """ fields_view_get([view_id | view_type='form'])

    Get the detailed composition of the requested view like fields, model, view architecture

    :param view_id: id of the view or None
    :param view_type: type of the view to return if view_id is None ('form', 'tree', ...)
    :param toolbar: true to include contextual actions
    :param submenu: deprecated
    :return: dictionary describing the composition of the requested view (including inherited views and extensions)
    :raise AttributeError:
                        * if the inherited view has unknown position to work with other than 'before', 'after', 'inside', 'replace'
                        * if some tag other than 'position' is found in parent view
    :raise Invalid ArchitectPartenaireureError: if there is view type other than form, tree, calendar, search etc defined on the structure
    """
    if context is None:
        context = {}
    View = self.pool['ir.ui.view']
    result = {
        'model': self._name,
        'field_parent': False,
    }

    # try to find a view_id if none provided
    if not view_id:
        # <view_type>_view_ref in context can be used to overrride the default view
        view_ref_key = view_type + '_view_ref'
        view_ref = context.get(view_ref_key)
        if view_ref:
            if '.' in view_ref:
                module, view_ref = view_ref.split('.', 1)
                cr.execute("SELECT res_id FROM ir_model_data WHERE model='ir.ui.view' AND module=%s AND name=%s", (module, view_ref))
                view_ref_res = cr.fetchone()
                if view_ref_res:
                    view_id = view_ref_res[0]
            else:
                _logger.warning('%r requires a fully-qualified external id (got: %r for model %s). '
                    'Please use the complete `module.view_id` form instead.', view_ref_key, view_ref,
                    self._name)

        if not view_id:
            # otherwise try to find the lowest priority matching ir.ui.view
            view_id = View.default_view(cr, uid, self._name, view_type, context=context)

    # context for post-processing might be overriden
    ctx = context
    if view_id:
        # read the view with inherited views applied
        root_view = View.read_combined(cr, uid, view_id, fields=['id', 'name', 'field_parent', 'type', 'model', 'arch'], context=context)
        result['arch'] = root_view['arch']
        result['name'] = root_view['name']
        result['type'] = root_view['type']
        result['view_id'] = root_view['id']
        result['field_parent'] = root_view['field_parent']
        # override context from postprocessing
        if root_view.get('model') != self._name:
            ctx = dict(context, base_model_name=root_view.get('model'))
    else:
        # fallback on default views methods if no ir.ui.view could be found
        try:
            get_func = getattr(self, '_get_default_%s_view' % view_type)
            arch_etree = get_func(cr, uid, context)
            result['arch'] = etree.tostring(arch_etree, encoding='utf-8')
            result['type'] = view_type
            result['name'] = 'default'
        except AttributeError:
            raise except_orm(_('Invalid Architecture!'), _("No default view of type '%s' could be found !") % view_type)

    # Apply post processing, groups and modifiers etc...
    xarch, xfields = View.postprocess_and_fields(cr, uid, self._name, etree.fromstring(result['arch']), view_id, context=ctx)
    
    result['arch'] = xarch
    result['fields'] = xfields

    # Add related action information if aksed
    if toolbar:
        toclean = ('report_sxw_content', 'report_rml_content', 'report_sxw', 'report_rml', 'report_sxw_content_data', 'report_rml_content_data')
        def clean(x):
            x = x[2]
            for key in toclean:
                x.pop(key, None)
            return x
        ir_values_obj = self.pool.get('ir.values')
        resprint = ir_values_obj.get(cr, uid, 'action', 'client_print_multi', [(self._name, False)], False, context)
        resaction = ir_values_obj.get(cr, uid, 'action', 'client_action_multi', [(self._name, False)], False, context)
        resrelate = ir_values_obj.get(cr, uid, 'action', 'client_action_relate', [(self._name, False)], False, context)
        resaction = [clean(action) for action in resaction if view_type == 'tree' or not action[2].get('multi')]
        resprint = [clean(print_) for print_ in resprint if view_type == 'tree' or not print_[2].get('multi')]
        #When multi="True" set it will display only in More of the list view
        resrelate = [clean(action) for action in resrelate
                     if (action[2].get('multi') and view_type == 'tree') or (not action[2].get('multi') and view_type == 'form')]

        for x in itertools.chain(resprint, resaction, resrelate):
            x['string'] = x['name']

        result['toolbar'] = {
            'print': resprint,
            'action': resaction,
            'relate': resrelate
        }
    abc= result['arch'].split('<sheet')[0]
    s=result['arch']
    sheetname = '<sheet>'
    if result['type'] == 'form':
        resul1=re.compile('<sheet(.*?)>').search(s)
        sheetname = '<sheet'
        if resul1:
            sheetname = sheetname + str(resul1.group(1)) + '>'
    if result['type'] == 'form' and result['arch'].find(sheetname) > 0:
        model_obj = self.pool['ir.model']
        model_id = model_obj.search(cr, uid,[('name','=', 'is.head.model.form.view')])
        if model_id:
            is_head_view_obj = self.pool['is.head.model.form.view']
            is_head = is_head_view_obj.search_read(cr, uid, [('model_id.model','=', self._name)],['name','color','picture'] ,context=context)
            if is_head:
                is_head = is_head[0]
                img_src = ""
                if is_head.get('picture',False):
                    img_src = "<img src='data:image/gif;base64,"+is_head.get('picture')+"' height='42' width='42' />"
                result['arch'] =  str(abc) + str(str(sheetname) + "<div height='60px' width='100%' style='padding: 10px;font-size:18px;background-color: "+is_head.get('color')+";'> "+img_src+" "+is_head.get('name')+"</div><br/>") + str(result['arch'].split(sheetname)[1])
    return result

BaseModel.fields_view_get = fields_view_get


class is_head_model_form_view(models.Model):
    _name = 'is.head.model.form.view'

    model_id = fields.Many2one('ir.model', string='Modèle', required=True)
    name = fields.Char(string='Nom du modèle', required=True)
    picture = fields.Binary(string="Image", type="binary")
    color = fields.Char(string='Couleur', required=True, default='#E1E1E1')

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: