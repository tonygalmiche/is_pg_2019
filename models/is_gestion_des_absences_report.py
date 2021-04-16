# -*- coding: utf-8 -*-

from openerp import models, fields, api
import datetime
from collections import defaultdict
from openerp.exceptions import except_orm, Warning, RedirectWarning
from openerp.tools.translate import _


class is_demande_conges(models.Model):
    _inherit = 'is.demande.conges'

    @api.model
    def analyse_des_absences(self, filter=False):
        cr, uid, context = self.env.args
        validation = filter['validation']
        if validation=='ko':
            #** Lecture des critères enregistrés *******************************
            nom        = self.env['is.mem.var'].get(uid,'nom')
            service    = self.env['is.mem.var'].get(uid,'service')
            poste      = self.env['is.mem.var'].get(uid,'poste')
            nb_jours   = self.env['is.mem.var'].get(uid,'nb_jours')
            n1         = self.env['is.mem.var'].get(uid,'n1')
            n2         = self.env['is.mem.var'].get(uid,'n2')
        else:
            #** Lecture des filtres ********************************************
            nom      = filter['nom']
            service  = filter['service']
            poste    = filter['poste']
            nb_jours = filter['nb_jours']
            n1       = filter['n1']
            n2       = filter['n2']
            #*******************************************************************

            #** Enregistrement des critères enregistrés ************************
            self.env['is.mem.var'].set(uid, 'nom'     , nom)
            self.env['is.mem.var'].set(uid, 'service' , service)
            self.env['is.mem.var'].set(uid, 'poste'   , poste)
            self.env['is.mem.var'].set(uid, 'nb_jours', nb_jours)
            self.env['is.mem.var'].set(uid, 'n1'      , n1)
            self.env['is.mem.var'].set(uid, 'n2'      , n2)
            #*******************************************************************

        #** Valeur par défaut **************************************************
        nom      = nom  or ''
        service  = service  or ''
        poste    = poste  or ''
        nb_jours = nb_jours  or 7
        n1       = n1  or ''
        n2       = n2  or ''
       #***********************************************************************

        titre = "Calendrier des absences"
        #nom = ''
        #service = ''
        #poste = ''
        #nb_jours = 7
        date_debut = ''
        start_date = ''
        end_date = ''
        back_forward_days = 0
        emp_domain = []
        data_pool = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dummy, act_id = data_pool.get_object_reference('is_pg_2019', "is_demande_absence_action")
        dummy, act_id_demande = data_pool.get_object_reference('is_pg_2019', "is_demande_conges_action")
        if filter:
            #nom        = filter['nom']
            #service    = filter['service']
            #poste      = filter['poste']
            #nb_jours   = filter['nb_jours']
            date_debut = filter['date_debut']
            start_date = filter['start_date']
            end_date   = filter['end_date']
            back_forward_days = int(filter['back_forward_days'] or 0)
        width=240+180+180+180+180+40+int(nb_jours)*(24+2)+22
        NomCol = []
        where_condition = ''

        if service:
            emp_domain.append(('department_id','ilike', service))
        if poste:
            emp_domain.append(('job_id','ilike', poste))
        if nom:
            emp_domain.append(('name','ilike', nom))
        if n1:
            emp_domain.append(('is_valideur_n1','ilike', n1))
        if n2:
            emp_domain.append(('is_valideur_n2','ilike', n2))

        emp_domain.append(('job_id','!=', 'INTERIMAIRE'))


        week_per_year = defaultdict(dict)
        today_date = datetime.date.today()
        first_date_year = today_date + datetime.timedelta(days=-today_date.weekday())
        last_date_year = first_date_year + datetime.timedelta(days=+int(nb_jours) - 1)
        if date_debut:
            try:
                date_custom_format = '%d.%m.%Y'
                if len(date_debut.split('.')) == 3 and len(date_debut.split('.')[2]) == 2:
                    date_custom_format = '%d.%m.%y'
                if '/' in date_debut:
                    date_custom_format = '%d/%m/%Y'
                    if len(date_debut.split('/')) == 3 and len(date_debut.split('/')[2]) == 2:
                        date_custom_format = '%d/%m/%y'
                date_debut
                select_date = datetime.datetime.strptime(date_debut, date_custom_format).date()
            except Exception as e:
                raise except_orm(_('Date Format!'),
                                 _(" %s ") % (str(e).decode('utf-8'),))
            last_date_year = select_date + \
                datetime.timedelta(days=-select_date.weekday() - 1, weeks=1)
            first_date_year = last_date_year - datetime.timedelta(days=6)
            last_date_year = first_date_year + datetime.timedelta(days=int(nb_jours)-1)
        if back_forward_days:
            if start_date and back_forward_days < 0:
                select_date = datetime.datetime.strptime(end_date, "%d.%m.%Y").date()
                last_date_year = select_date - datetime.timedelta(days=7)
                select_date = datetime.datetime.strptime(start_date, "%d.%m.%Y").date()
                first_date_year = select_date - datetime.timedelta(days=7)
            elif end_date and back_forward_days > 0:
                select_date = datetime.datetime.strptime(end_date, "%d.%m.%Y").date()
                last_date_year = select_date + datetime.timedelta(days=7)
                select_date = datetime.datetime.strptime(start_date, "%d.%m.%Y").date()
                first_date_year = select_date + datetime.timedelta(days=7)
        first_week_date = first_date_year
        last_week_date = first_week_date + \
            datetime.timedelta(days=-first_week_date.weekday() - 1, weeks=1)
        col_start = first_date_year.isocalendar()[1]
        col_end = last_date_year.isocalendar()[1]
        for col in range(1, 53):
            if col >= col_start and col <= col_end:
                line_data = {
                    'first_week_date': first_week_date,
                    'last_week_date': last_week_date,
                }
                week_per_year[col].update(line_data)
                first_week_date = first_week_date + \
                    datetime.timedelta(
                        days=-first_week_date.weekday(), weeks=1)
                last_week_date = first_week_date + \
                    datetime.timedelta(
                        days=-first_week_date.weekday() - 1, weeks=1)
                if last_date_year < last_week_date:
                    last_week_date = last_date_year
        html ="<div style=\"width:"+str(width+20)+"px;\" id=\"table_head\">\n"
        html += "<div><a value='back' type='main'><< Semaine Précédente</a> <a style='padding-left:25px;' value='forward' type='main'>Semaine Suivante >></a></div>"
        html += "<style>"
        html += "#table2 table {border-collapse: collapse;border: 1px solid black;} "
        html += "#table2 th {border-collapse: collapse;border: 1px solid black;} "
        html += "#table2 td {border-collapse: collapse;border: 1px solid black;}"
        html += "</style>"
        html+="<table id='table21' style=\"border-width:0px;border-spacing:0px;padding:0px;width:"+str(width)+"px;\">\n";
        html += "<thead><tr class=\"TitreTabC\">\n"
        html += "<td style=\"width:240px;\"></td>\n"
        html += "<td style=\"width:180px;\"></td>\n"
        html += "<td style=\"width:180px;\"></td>\n"
        html += "<td style=\"width:180px;\"></td>\n"
        html += "<td style=\"width:180px;\"></td>\n"
        for col in sorted(week_per_year.keys()):
            align = 'center'
            main_heading = 'Sem ' + \
                str(col) + '<br/> (' + \
                week_per_year[col]['first_week_date'].strftime(
                    "%d.%m.%Y") + ')'
            week_days = (week_per_year[col][
                         'last_week_date'] - week_per_year[col]['first_week_date']).days + 1
            html += "<th colspan=" + \
                str(week_days) + " style=\"width:30px;text-align:" + \
                align + "\">" + main_heading + "</th>\n"
        html += "</tr>"
        # data Display
        html += "<tr>"
        html += "<td style='width:240px;color:black;text-align:center;'>Service</td>\n"
        html += "<td style='width:180px;color:black;text-align:center;'>Poste</td>\n"
        html += "<td style='width:180px;color:black;text-align:center;'>Nom</td>\n"
        html += "<td style='width:180px;color:black;text-align:center;'>N+1</td>\n"
        html += "<td style='width:180px;color:black;text-align:center;'>N+2</td>\n"
        for col in sorted(week_per_year.keys()):
            align = 'center'
            week_days = (week_per_year[col][
                         'last_week_date'] - week_per_year[col]['first_week_date']).days + 1
            display_date = week_per_year[col]['first_week_date']
            for day_index in range(0, week_days):
                html += "<td style='width:30px;color:black;text-align:center;'>" + \
                    str(display_date.day) + "</td>\n"
                display_date = display_date + datetime.timedelta(days=+1)
        html += "</tr>"

        emp_ids = self.env['hr.employee'].search(emp_domain,order="department_id,job_id")
        is_demande_absence_obj = self.env['is.demande.absence']
        is_demande_conges_obj = self.env['is.demande.conges']
        html+="</table>\n"
        html+="</div>\n"
        html+="<div style=\"width:"+str(width+20)+"px;\" id=\"table_body\">\n";
        html+="<table id='table2' style=\"border-width:0px;border-spacing:0px;padding:0px;width:"+str(width)+"px;\">\n";
        for emp in emp_ids:
            html += "<tr>"
            html += "<td style='width:240px;font-weight:normal;text-align:left;'>" + (emp.department_id.name or '') + "</td>\n"
            html += "<td style='width:180px;font-weight:normal;text-align:left;'>" + (emp.job_id.name or '') + "</td>\n"
            html += "<td style='width:180px;font-weight:normal;text-align:left;'>" + emp.name + "</td>\n"
            html += "<td style='width:180px;font-weight:normal;text-align:left;'>" + (emp.is_valideur_n1.name or '') + "</td>\n"
            html += "<td style='width:180px;font-weight:normal;text-align:left;'>" + (emp.is_valideur_n2.name or '') + "</td>\n"
            for col in sorted(week_per_year.keys()):
                align = 'center'
                week_days = (week_per_year[col][
                             'last_week_date'] - week_per_year[col]['first_week_date']).days + 1
                display_date = week_per_year[col]['first_week_date']
                for day_index in range(0, week_days):
                    M_C = ''
                    conges_count = absence_count = False
                    if emp.user_id:
                        conges_count = is_demande_conges_obj.search([
                             ('demandeur_id', '=', emp.user_id.id),
                             ('date_debut', '<=', display_date),
                             ('date_fin', '>=', display_date),
                            ('state','not in', ['refuse','annule']),
                        ])
                        if not conges_count:
                            conges_count = is_demande_conges_obj.search([
                                ('demandeur_id', '=', emp.user_id.id),
                                ('le', '=', display_date),
                                ('state','not in', ['refuse','annule']),
                            ])
                        if conges_count:
                            x='C'
                            if conges_count[0].type_demande=='rc_heures':
                                NbHeures = conges_count[0].heure_fin - conges_count[0].heure_debut
                                if NbHeures<0:
                                    NbHeures=24+NbHeures
                                NbHeures=int(NbHeures)
                                x='RC'+str(NbHeures)
                            M_C = '<a title="" type=\'CF\' docid='+str(conges_count[0].id)+'>'+x+'</a>'

                    absence_count = is_demande_absence_obj.search([
                        ('employe_ids', 'in', [emp.id]),
                        ('date_debut', '<=', display_date),
                        ('date_fin', '>=', display_date),
                    ])
                    if not absence_count:
                        absence_count = is_demande_absence_obj.search([
                            ('employe_ids', 'in', [emp.id]),
                            ('date_debut', '=', display_date),
                        ])
                    if absence_count:
                        code = 'Abs'
                        title = absence_count[0].type_absence.name
                        if absence_count[0].type_absence.code:
                            code = absence_count[0].type_absence.code
                        M_C = '<a type=\'MF\' docid='+str(absence_count[0].id)+' title="'+title+'">'+code+'</a>'
                    if absence_count and conges_count:
                        M_C = '<a type=\'CF\' docid='+str(conges_count[0].id)+'>C</a>  ' + '<a type=\'MF\' title="" docid='+str(absence_count[0].id)+'>'+code+'</a>'
                    td_color = ''
                    if display_date.weekday() in (5, 6):
                        td_color = 'black;background-color:red;'
                    html += "<td style='width:30px;font-weight:normal;" + \
                        td_color + "text-align:center;'>" + \
                            str(M_C) + "</td>\n"
                    display_date = display_date + datetime.timedelta(days=+1)
            html += "</tr>"
        html += "</tbody>\n"
        html += "</table>\n"
        html += "</div>\n"

        vals = {
            'service': service,
            'poste': poste,
            'nom': nom,
            'n1': n1,
            'n2': n2,
            'date_debut': date_debut,
            'nb_jours': nb_jours,
            'start_date': first_date_year.strftime("%d.%m.%Y"),
            'end_date': last_date_year.strftime("%d.%m.%Y"),
            'back_forward_days': back_forward_days,
            'html': html,
        }
        return vals
