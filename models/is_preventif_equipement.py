# -*- coding: utf-8 -*-

from openerp import models, fields, api
from openerp.exceptions import Warning
import time
import datetime
import os
from pyPdf import PdfFileWriter, PdfFileReader
from shutil import copy
import magic


class is_preventif_equipement_zone(models.Model):
    _name = 'is.preventif.equipement.zone'
    _order = "name"

    def pgcd(self,a,b):
        """pgcd(a,b): calcul du 'Plus Grand Commun Diviseur' entre les 2 nombres entiers a et b"""
        while b<>0:
            a,b=b,a%b
        return a

    def pgcdn(self,n):
        """Calcul du 'Plus Grand Commun Diviseur' de n valeurs entières (Euclide)"""
        if len(n)==0:
            return 0
        if len(n)==1:
            return n[0]
        p = self.pgcd(n[0], n[1])
        for x in n[2:]:
            p = self.pgcd(p, x)
        return p

    @api.depends('preventif_ids')
    def _compute_frequence(self):
        for obj in self:
            frequences = []
            for line in obj.preventif_ids:
                if line.frequence>0:
                    frequences.append(line.frequence)
            pgcdn = self.pgcdn(frequences)
            obj.frequence = pgcdn

    name           = fields.Char(u"Nom de la zone", required=True, index=True)
    description    = fields.Text(u"Description de la zone")
    equipement_ids = fields.One2many('is.equipement', 'zone_id', u"Equipements de cette zone")
    preventif_ids  = fields.One2many('is.preventif.equipement', 'zone_id', u"Préventifs")
    frequence      = fields.Integer(u"Fréquence préventif zone (H)", compute='_compute_frequence', store=True, readonly=True)
    active         = fields.Boolean(u"Active", default=True)


    @api.multi
    def imprimer_gammes_action(self):
        for obj in self:
            cr , uid, context = self.env.args
            db = self._cr.dbname
            path="/tmp/gamme_preventif-" + str(uid)
            cde="rm -Rf " + path
            os.popen(cde).readlines()
            if not os.path.exists(path):
                os.makedirs(path)
            paths=[]

            # ** Ajout du rapport *********************************************
            result = self.env['report'].get_pdf(obj, 'is_pg_2019.preventif_equipement_zone_report')
            file_name = path + '/zone.pdf'
            fd = os.open(file_name,os.O_RDWR|os.O_CREAT)
            try:
                os.write(fd, result)
            finally:
                os.close(fd)
            paths.append(file_name)
            #******************************************************************

            # ** Ajout des gammes *********************************************
            filestore = os.environ.get('HOME')+"/.local/share/Odoo/filestore/"+db+"/"
            for line in obj.preventif_ids:
                for gamme in line.gamme_ids:
                    src = filestore+gamme.store_fname
                    dst = path+"/"+str(gamme.id)+".pdf"
                    filetype = magic.from_file(src, mime=True)
                    if filetype=="application/pdf":
                        copy(src, dst)
                        paths.append(dst)
            # ******************************************************************

            # ** Merge des PDF *************************************************
            try:
                path_merged=self.env['stock.picking']._merge_pdf(paths)
            except:
                raise Warning(u"Impossible de générer le PDF => Les gammes doivent être au format PDF")
            pdfs = open(path_merged,'rb').read().encode('base64')
            # ******************************************************************

            # ** Recherche si une pièce jointe est déja associèe ***************
            attachment_obj = self.env['ir.attachment']
            name = 'zone.pdf'
            attachments = attachment_obj.search([('name','=',name)],limit=1)
            # ******************************************************************

            # ** Creation ou modification de la pièce jointe *******************
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
            #******************************************************************

            #** Envoi du PDF mergé dans le navigateur *************************
            if attachment_id:
                return {
                    'type' : 'ir.actions.act_url',
                    'url': '/web/binary/saveas?model=ir.attachment&field=datas&id='+str(attachment_id)+'&filename_field=name',
                    'target': 'new',
                }
            #******************************************************************

















class is_preventif_equipement(models.Model):
    _name = 'is.preventif.equipement'
    _order = "equipement_id"

    zone_id        = fields.Many2one('is.preventif.equipement.zone', u"Equipement", required=True, ondelete='cascade', readonly=True)
    equipement_id  = fields.Many2one('is.equipement', u"Equipement",required=True)
    type_preventif = fields.Selection([
            ('niveau2'       , u'Niveau 2'),
            ('niveau3'       , u'Niveau 3'),
            ('plastification', u'Plastification'),
            ('constructeur'  , u'Constructeur'),
        ], u"Type de préventif",required=True)
    frequence               = fields.Integer(u"Fréquence du préventif (H)", required=True)
    date_dernier_preventif  = fields.Date(u"Date du dernier préventif"  , readonly=True)
    date_prochain_preventif = fields.Date(u"Date du prochain préventif" , readonly=True)
    gamme_ids               = fields.Many2many('ir.attachment', 'is_preventif_equipement_gamme_rel', 'preventif_id', 'gamme_id', u'Gamme')


class is_preventif_equipement_heure(models.Model):
    _name = 'is.preventif.equipement.heure'
    _description = u"Nombre d'heures par équipement et par mois"
    _order = "equipement_id, mois desc"

    equipement_id  = fields.Many2one('is.equipement', u"Equipement", required=True, index=True)
    mois           = fields.Char(u"Mois"                           , required=True, index=True)
    nb_heures      = fields.Integer(u"Nb heures")
