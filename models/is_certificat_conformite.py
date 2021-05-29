# -*- coding: utf-8 -*-
from openerp import models,fields,api
from openerp.tools.translate import _
from openerp.exceptions import Warning
from datetime import datetime
import os
from pyPdf import PdfFileWriter, PdfFileReader
import tempfile
from contextlib import closing


class is_liste_servir(models.Model):
    _inherit='is.liste.servir'

    def _compute_is_certificat_conformite_msg(self):
        for obj in self:
            msg = False
            if obj.partner_id.is_certificat_matiere:
                nb=0
                for line in obj.line_ids:
                    certificat = self.env['is.certificat.conformite'].GetCertificat(obj.partner_id.id, line.product_id.id)
                    if not certificat:
                        nb+=1
                msg=u"Ne pas oublier de fournir les certificats matières."
                if nb:
                    msg+=u"\nATTENTION : Il manque "+str(nb)+u" certificats !"
            obj.is_certificat_conformite_msg = msg

    is_certificat_conformite_msg = fields.Text('Certificat de conformité', compute='_compute_is_certificat_conformite_msg', store=False, readonly=True)


class is_liste_servir_line(models.Model):
    _inherit='is.liste.servir.line'

    def _compute_is_certificat_conformite_vsb(self):
        for obj in self:
            vsb = False
            if obj.liste_servir_id.partner_id.is_certificat_matiere:
                certificat = self.env['is.certificat.conformite'].GetCertificat(obj.liste_servir_id.partner_id.id, obj.product_id.id)
                if certificat:
                    vsb = 1
                else:
                    vsb = 2
            obj.is_certificat_conformite_vsb = vsb

    is_certificat_conformite_vsb = fields.Integer('Certificat de conformité', compute='_compute_is_certificat_conformite_vsb', store=False, readonly=True)


    @api.multi
    def pas_de_certifcat_action(self):
        for obj in self:
            print obj


    @api.multi
    def imprimer_certificat_action(self):
        dummy, view_id = self.env['ir.model.data'].get_object_reference('is_pg_2019', 'is_certificat_conformite_form_view')
        for obj in self:
            certificat = self.env['is.certificat.conformite'].GetCertificat(obj.liste_servir_id.partner_id.id, obj.product_id.id)
            if certificat:
                return {
                    'name': "Certificat de conformité",
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'is.certificat.conformite',
                    'type': 'ir.actions.act_window',
                    'res_id': certificat.id,
                    'domain': '[]',
                }


class stock_picking(models.Model):
    _inherit = "stock.picking"
    
    def _compute_is_certificat_conformite_msg(self):
        for obj in self:
            msg = False
            if obj.partner_id.is_certificat_matiere:
                nb=0
                for line in obj.move_lines:
                    certificat = self.env['is.certificat.conformite'].GetCertificat(obj.partner_id.id, line.product_id.id)
                    if not certificat:
                        nb+=1
                msg=u"Ne pas oublier de fournir les certificats matières."
                if nb:
                    msg+=u"\nATTENTION : Il manque "+str(nb)+u" certificats !"
            obj.is_certificat_conformite_msg = msg

    is_certificat_conformite_msg = fields.Text('Certificat de conformité', compute='_compute_is_certificat_conformite_msg', store=False, readonly=True)


    @api.multi
    def _merge_pdf(self, documents):
        """Merge PDF files into one.
        :param documents: list of path of pdf files
        :returns: path of the merged pdf
        """
        writer = PdfFileWriter()
        streams = []  # We have to close the streams *after* PdfFilWriter's call to write()
        for document in documents:
            pdfreport = file(document, 'rb')
            streams.append(pdfreport)
            reader = PdfFileReader(pdfreport)
            for page in range(0, reader.getNumPages()):
                writer.addPage(reader.getPage(page))
        merged_file_fd, merged_file_path = tempfile.mkstemp(suffix='.pdf', prefix='report.merged.tmp.')
        with closing(os.fdopen(merged_file_fd, 'w')) as merged_file:
            writer.write(merged_file)
        for stream in streams:
            stream.close()
        return merged_file_path


    @api.multi
    def imprimer_certificat_action(self):
        for obj in self:
            cr , uid, context = self.env.args
            db = self._cr.dbname
            path="/tmp/certificats-" + db + '-'+str(uid)
            cde="rm -Rf " + path
            os.popen(cde).readlines()
            if not os.path.exists(path):
                os.makedirs(path)
            paths=[]
            for move in obj.move_lines:
                certificat = self.env['is.certificat.conformite'].GetCertificat(obj.partner_id.id, move.product_id.id)
                if certificat:
                    self.env['is.certificat.conformite'].WriteCertificat(certificat,move)

                    #** Recherche des lots scannés ************************************
                    lots={}
                    if move.picking_id.is_sale_order_id:
                        if  move.picking_id.is_sale_order_id.is_liste_servir_id:
                            if move.picking_id.is_sale_order_id.is_liste_servir_id.galia_um_ids:
                                for um in move.picking_id.is_sale_order_id.is_liste_servir_id.galia_um_ids:
                                    if um.product_id == move.product_id:
                                        for uc in um.uc_ids:
                                            if uc.production not in lots:
                                                date_fabrication = uc.date_creation[:10]
                                                lots[uc.production] = date_fabrication
                    print("lots =",lots)

#('lots =', {u'OF028224': '2021-02-08', u'OF028923': '2021-03-12', u'OF028923b': '2021-03-12', u'OF028923c': '2021-03-12', u'OF028923a': '2021-03-12'})
                    if lots=={}:
                        lots[' ']=False


                    x=0
                    for lot in lots:
                        x+=1
                        print(lot, lots[lot])
                        certificat.num_lot = lot
                        certificat.date_fabrication = lots[lot]



                        result = self.env['report'].get_pdf(certificat, 'is_pg_2019.is_certificat_conformite_report')
                        file_name = path + '/'+str(move.id) + '-' + str(x) + '.pdf'
                        fd = os.open(file_name,os.O_RDWR|os.O_CREAT)
                        try:
                            os.write(fd, result)
                        finally:
                            os.close(fd)
                        paths.append(file_name)


            print("paths=",paths)

            # ** Merge des PDF *****************************************************
            path_merged=self._merge_pdf(paths)
            pdfs = open(path_merged,'rb').read().encode('base64')
            # **********************************************************************

            # ** Recherche si une pièce jointe est déja associèe *******************
            attachment_obj = self.env['ir.attachment']
            name = 'certificats.pdf'
            attachments = attachment_obj.search([('name','=',name)],limit=1)
            # **********************************************************************

            # ** Creation ou modification de la pièce jointe ***********************
            vals = {
                'name':        name,
                'datas_fname': name,
                'type':        'binary',
                'datas':       pdfs,
            }
            if attachments:
                for attachment in attachments:
                    attachment.write(vals)
                    attachment_id=attachment.id
            else:
                attachment = attachment_obj.create(vals)
                attachment_id=attachment.id
            #***********************************************************************

            #** Envoi du PDF mergé dans le navigateur ******************************
            if attachment_id:
                return {
                    'type' : 'ir.actions.act_url',
                    'url': '/web/binary/saveas?model=ir.attachment&field=datas&id='+str(attachment_id)+'&filename_field=name',
                    'target': 'new',
                }
            #***********************************************************************


class stock_move(models.Model):
    _inherit = "stock.move"
    
    def _compute_is_certificat_conformite_vsb(self):
        for obj in self:
            vsb = False
            if obj.picking_id.partner_id.is_certificat_matiere:
                certificat = self.env['is.certificat.conformite'].GetCertificat(obj.picking_id.partner_id.id, obj.product_id.id)
                if certificat:
                    vsb = 1
                else:
                    vsb = 2
            obj.is_certificat_conformite_vsb = vsb

    is_certificat_conformite_vsb = fields.Integer('Certificat de conformité', compute='_compute_is_certificat_conformite_vsb', store=False, readonly=True)


    @api.multi
    def pas_de_certifcat_action(self):
        for obj in self:
            print obj


    @api.multi
    def imprimer_certificat_action(self):
        dummy, view_id = self.env['ir.model.data'].get_object_reference('is_pg_2019', 'is_certificat_conformite_form_view')
        for obj in self:
            certificat = self.env['is.certificat.conformite'].GetCertificat(obj.picking_id.partner_id.id, obj.product_id.id)
            if certificat:
                self.env['is.certificat.conformite'].WriteCertificat(certificat,obj)
                return {
                    'name': "Certificat de conformité",
                    'view_mode': 'form',
                    'view_id': view_id,
                    'view_type': 'form',
                    'res_model': 'is.certificat.conformite',
                    'type': 'ir.actions.act_window',
                    'res_id': certificat.id,
                    'domain': '[]',
                }


class is_certificat_conformite(models.Model):
    _name='is.certificat.conformite'
    _order='product_id,client_id'
    _sql_constraints = [('product_id_client_id_uniq','UNIQUE(product_id,client_id)', u'Un certificat existe déjà pour ce client et pour cet article !')] 
    _rec_name = 'product_id'


    @api.depends('rsp_livraison')
    def _compute_job_id(self):
        for obj in self:
            job_id=False
            if obj.rsp_livraison:
                print(obj, obj.rsp_livraison)
                employes = self.env['hr.employee'].search([("user_id","=",obj.rsp_livraison.id)])
                for employe in employes:
                    job_id=employe.job_id.id
            obj.job_id=job_id





    product_id       = fields.Many2one('product.product', u"Article", domain=[('sale_ok','=',True)], required=True, select=True)
    client_id        = fields.Many2one('res.partner', u'Client', domain=[('is_company','=',True),('customer','=',True)], required=True, select=True)
    ref_client       = fields.Char(u"Référence client", related='product_id.is_ref_client', readonly=True)
    ref_plan         = fields.Char(u"Référence plan"  , related='product_id.is_ref_plan'  , readonly=True)
    ind_plan         = fields.Char(u"Indice plan"     , related='product_id.is_ind_plan'  , readonly=True)
    client_order_ref = fields.Char(u'N° commande client')
    order_id         = fields.Many2one('sale.order'   , u'N° de commande')
    picking_id       = fields.Many2one('stock.picking', u'N°BL', domain=[('picking_type_id','=',2)])
    date_bl          = fields.Date(u"Date d'expédition", related='picking_id.is_date_expedition', readonly=True)
    qt_liv           = fields.Float(u"Quantité livrée")
    num_lot          = fields.Char(u"N° de lot")
    date_fabrication = fields.Date(u"Date de fabrication")
    rsp_qualite      = fields.Many2one('res.users', u'Responsable qualité')
    rsp_livraison    = fields.Many2one('res.users', u'Responsable livraison')
    job_id           = fields.Many2one('hr.job', u'Fonction', compute='_compute_job_id', store=False, readonly=True)
    pourcentage_maxi = fields.Char(u"Pourcentage maxi de broyé", default="0%")
    reference_ids    = fields.One2many('is.certificat.conformite.reference', 'certificat_id', u"Références", copy=True)
    autre_ids        = fields.One2many('is.certificat.conformite.autre'    , 'certificat_id', u"Autre"     , copy=True)
    autre2_ids       = fields.One2many('is.certificat.conformite.autre2'   , 'certificat_id', u"Autre 2"   , copy=True)
    fabricant_ids    = fields.One2many('is.certificat.conformite.fabricant', 'certificat_id', u"Fabricants", copy=True)
    state            = fields.Selection([
            ('creation', u'Création'),
            ('valide'  , u"Validé"),
        ], "Etat", readonly=True, default="creation")


    @api.multi
    def GetCertificat(self,partner_id,product_id):
        filtre = [
            ('client_id' , '=', partner_id),
            ('product_id', '=', product_id),
            ('state'     , '=', 'valide'),
        ]
        certificats = self.env['is.certificat.conformite'].search(filtre)
        certificat = certificats and certificats[0] or False
        return certificat


    @api.multi
    def WriteCertificat(self,certificat,move):
        if move and move.is_sale_line_id and move.picking_id:
            if certificat.picking_id != move.picking_id:
                certificat.num_lot          = False
                certificat.date_fabrication = False
            vals={
                'client_order_ref': move.is_sale_line_id.is_client_order_ref,
                'order_id'        : move.is_sale_line_id.order_id.id,
                'picking_id'      : move.picking_id.id,
                'date_bl'         : move.picking_id.is_date_expedition,
                'qt_liv'          : move.product_uom_qty,
                'rsp_livraison'   : self._uid,
                'num_lot'         : False,
                'date_fabrication': False,
            }
            certificat.write(vals)

            # #** Recherche des lots scannés ************************************
            # if move.picking_id.is_sale_order_id:
            #     if  move.picking_id.is_sale_order_id.is_liste_servir_id:
            #         if move.picking_id.is_sale_order_id.is_liste_servir_id.galia_um_ids:
            #             lots={}
            #             for um in move.picking_id.is_sale_order_id.is_liste_servir_id.galia_um_ids:
            #                 if um.product_id == move.product_id:
            #                     for uc in um.uc_ids:
            #                         if uc.production not in lots:
            #                             print uc.production,lots
            #                             date_fabrication            = uc.date_creation[:10]
            #                             certificat.num_lot          = uc.production
            #                             certificat.date_fabrication = date_fabrication
            #                             #TODO Voir comment afficher plusieurs lots
            #                             #date_fabrication= datetime.strptime(date_fabrication, '%Y-%m-%d')
            #                             #date_fabrication =date_fabrication.strftime('%d/%m/%Y')
            #                             lots[uc.production] = date_fabrication


    @api.multi
    def vers_valide(self):
        for obj in self:
            obj.state='valide'


    @api.multi
    def vers_creation(self):
        for obj in self:
            obj.state='creation'


class is_certificat_conformite_reference(models.Model):
    _name='is.certificat.conformite.reference'
    _order='certificat_id,reference'

    certificat_id = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    reference     = fields.Char(u"Référence", required=True)
    fabricant     = fields.Char(u"Fabricant de la matière de base", required=True)
    ref_precise   = fields.Char(u"Référence précise de la matière de base")
    epaisseur     = fields.Char(u"Epaisseur minimale mesurable sur la pièce")
    classe        = fields.Char(u"Classe d'inflammabilité de la matière dans l'épaisseur mini")


class is_certificat_conformite_autre(models.Model):
    _name='is.certificat.conformite.autre'
    _order='certificat_id,autre_conformite'

    certificat_id         = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    autre_conformite      = fields.Char(u"Autres conformités", required=True)
    epaisseur_mini        = fields.Char(u"Epaisseur mini mesurable sur la pièce")
    classe_inflammabilite = fields.Char(u"Classe d'inflammabilité de la matière dans l'épaisseur mini")


class is_certificat_conformite_autre2(models.Model):
    _name='is.certificat.conformite.autre2'
    _order='certificat_id'

    certificat_id = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    autre         = fields.Char(u"Autre", required=True)


class is_certificat_conformite_fabricant(models.Model):
    _name='is.certificat.conformite.fabricant'
    _order='certificat_id,fabricant'

    certificat_id = fields.Many2one('is.certificat.conformite', "Certificat de conformité", required=True, ondelete='cascade', readonly=True)
    fabricant   = fields.Char(u"Fabricant de la matière pigmentée", required=True)
    pourcentage = fields.Char(u"% de la matière pigmentée", required=True)

