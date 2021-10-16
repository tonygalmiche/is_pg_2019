# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
import datetime


class is_facture_proforma_outillage(models.Model):
    _name='is.facture.proforma.outillage'
    _order='name desc'

    @api.depends('line_ids')
    def _compute(self):
        for obj in self:
            total = 0
            for line in obj.line_ids:
                total += line.total
            obj.total = total


    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.term_id = self.partner_id.property_payment_term.id


    @api.onchange('term_id','date_facture')
    def onchange_payment_term_date_invoice(self):
        date_due = self.date_facture
        if self.term_id and self.date_facture:
            pterm = self.env['account.payment.term'].browse(self.term_id.id)
            pterm_list = pterm.compute(value=1, date_ref=self.date_facture)[0]
            print(pterm_list)
            if pterm_list:
                date_due = max(line[0] for line in pterm_list)
        self.date_due = date_due




    name           = fields.Char(u"Facture proforma outillage", readonly=True)
    date_facture   = fields.Date(u"Date facture"             , required=True, default=lambda *a: fields.datetime.now())
    date_due       = fields.Date(u"Date d'échéance")
    partner_id     = fields.Many2one('res.partner', 'Adresse de facturation', required=True, domain=[('is_code','=like','50%'),('customer','=',True)])
    cofor          = fields.Char("N° fournisseur (COFOR)" , related="partner_id.is_cofor", readonly=True)
    vat            = fields.Char("N° fiscal" , related="partner_id.vat", readonly=True)
    term_id        = fields.Many2one('account.payment.term', 'Conditions de paiement')
    type_reglement = fields.Many2one('account.journal', 'Type règlement', related="partner_id.is_type_reglement", readonly=True)
    rib_id         = fields.Many2one('res.partner.bank', 'RIB', related="partner_id.is_rib_id", readonly=True)
    num_cde          = fields.Char("N° de commande")
    bl_manuel_id     = fields.Many2one('is.bl.manuel', 'BL manuel')
    picking_id       = fields.Many2one('stock.picking', 'Livraison', domain=[('picking_type_id','=', 2)])
    mold_id          = fields.Many2one('is.mold', 'Moule', required=True)
    mold_designation = fields.Char('Désignation', related="mold_id.designation", readonly=True)
    total        = fields.Float("Total (€)", digits=(14,2), compute='_compute', readonly=True, store=True)
    commentaire  = fields.Text(u'Commentaire')
    line_ids     = fields.One2many('is.facture.proforma.outillage.line', 'proforma_id', u"Lignes", copy=True)

    
    @api.model
    def create(self, vals):
        data_obj = self.env['ir.model.data']
        sequence_ids = data_obj.search([('name','=','is_facture_proforma_outillage_seq')])
        if sequence_ids:
            sequence_id = data_obj.browse(sequence_ids[0].id).res_id
            vals['name'] = self.env['ir.sequence'].get_id(sequence_id, 'id')
        obj = super(is_facture_proforma_outillage, self).create(vals)
        return obj


class is_facture_proforma_outillage_line(models.Model):
    _name='is.facture.proforma.outillage.line'
    _order='proforma_id,sequence'


    @api.depends('pourcentage','prix')
    def _compute(self):
        for obj in self:
            obj.total=obj.pourcentage*obj.prix/100

    proforma_id = fields.Many2one('is.facture.proforma.outillage', "Facture proforma outillage", required=True, ondelete='cascade', readonly=True)
    sequence    = fields.Integer('Ordre')
    designation = fields.Text(u'Désignation'      , required=True)
    pourcentage = fields.Float("Pourcentage (%)"  , digits=(14,0), required=True)
    prix        = fields.Float("Prix unitaire (€)", digits=(14,2), required=True)
    total       = fields.Float("Total (€)"        , digits=(14,2), compute='_compute', readonly=True, store=True)



