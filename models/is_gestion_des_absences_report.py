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
        titre = "Calendrier des absences"
        etablissement = ''
        service = ''
        section = ''
        nom = ''
        date_debut = ''
        nb_jours = 7
        start_date = ''
        end_date = ''
        back_forward_days = 0
        emp_domain = []
        data_pool = self.env['ir.model.data']
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        dummy, act_id = data_pool.get_object_reference('is_pg_2019', "is_demande_absence_action")
        dummy, act_id_demande = data_pool.get_object_reference('is_pg_2019', "is_demande_conges_action")
        if filter:
            nom = filter['nom']
            nb_jours = filter['nb_jours']
            date_debut = filter['date_debut']
            start_date = filter['start_date']
            end_date = filter['end_date']
            back_forward_days = int(filter['back_forward_days'] or 0)
        width=220+40+int(nb_jours)*(24+2)+22
        NomCol = []
        where_condition = ''
        if nom:
#             where_condition += " and emp_name ilike '%" + nom + "%'"
            emp_domain.append(('name','ilike', nom))
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
            #where_condition += " and date_debut = '" + \
            #    str(select_date.strftime('%Y-%m-%d')) + "'"
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
#         html = "<div id='table_head'>"
        html ="<div style=\"width:"+str(width+20)+"px;\" id=\"table_head\">\n"
        html += "<div><a value='back' type='main'><< Semaine Précédente</a> <a style='padding-left:25px;' value='forward' type='main'>Semaine Suivante >></a></div>"
        html += "<style>"
        html += "#table2 table {border-collapse: collapse;border: 1px solid black;} "
        html += "#table2 th {border-collapse: collapse;border: 1px solid black;} "
        html += "#table2 td {border-collapse: collapse;border: 1px solid black;}"
        html += "</style>"
        html+="<table id='table21' style=\"border-width:0px;border-spacing:0px;padding:0px;width:"+str(width)+"px;\">\n";
        html += "<thead><tr class=\"TitreTabC\">\n"
        html += "<td style=\"width:220px;\"></td>\n"
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
        html += "<td style='width:220px;color:black;text-align:center;'>Nom</td>\n"
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

#         SQL = """
#             select distinct emp_id,emp_name,date_debut from
#             (
#             select emp.id as emp_id,resource_resource.name as emp_name,is_demande_conges.date_debut as date_debut
#                 from hr_employee emp
#                 inner join resource_resource on resource_resource.id=emp.resource_id
#                 inner join is_demande_conges on is_demande_conges.demandeur_id=resource_resource.user_id
#             union all
#             select emp.id as emp_id,resource_resource.name as emp_name,is_demande_absence.date_debut as date_debut
#                 from hr_employee emp
#                 inner join resource_resource on resource_resource.id=emp.resource_id
#                 inner join hr_employee_is_demande_absence_rel absence_rel on absence_rel.hr_employee_id=emp.id
#                 inner join is_demande_absence on is_demande_absence.id=absence_rel.is_demande_absence_id
#             ) a where 1=1 """ + where_condition + """
#         """
#         cr.execute(SQL)
#         if where_condition != '':
#             employee_ids = []
#             result = cr.fetchall()
#             for row in result:
#                 employee_ids.append(row[0])
#             emp_domain.append(('id', 'in', employee_ids))
        emp_ids = self.env['hr.employee'].search(emp_domain)
        is_demande_absence_obj = self.env['is.demande.absence']
        is_demande_conges_obj = self.env['is.demande.conges']
        html+="</table>\n"
        html+="</div>\n"
        html+="<div style=\"width:"+str(width+20)+"px;\" id=\"table_body\">\n";
        html+="<table id='table2' style=\"border-width:0px;border-spacing:0px;padding:0px;width:"+str(width)+"px;\">\n";
        for emp in emp_ids:
            html += "<tr>"
            html += "<td style='width:220px;font-weight:normal;text-align:left;'>" + \
                emp.name + "</td>\n"
            for col in sorted(week_per_year.keys()):
                align = 'center'
                week_days = (week_per_year[col][
                             'last_week_date'] - week_per_year[col]['first_week_date']).days + 1
                display_date = week_per_year[col]['first_week_date']
                for day_index in range(0, week_days):
                    M_C = ''
                    conges_count = absence_count = False
                    if emp.user_id:
                        conges_count = is_demande_conges_obj.search(
                            [('demandeur_id', '=', emp.user_id.id),
                             ('date_debut', '<=', display_date),
                             ('date_fin', '>=', display_date),])
                        if not conges_count:
                            conges_count = is_demande_conges_obj.search(
                                [('demandeur_id', '=', emp.user_id.id), ('date_debut', '=', display_date)])
                        if conges_count:
                            M_C = '<a type=\'CF\' docid='+str(conges_count[0].id)+'>C</a>'
                    absence_count = is_demande_absence_obj.search(
                        [('employe_ids', 'in', [emp.id]),
                         ('date_debut', '<=', display_date),
                         ('date_fin', '>=', display_date),
                        ])
                    if not absence_count:
                        absence_count = is_demande_absence_obj.search(
                        [('employe_ids', 'in', [emp.id]),
                         ('date_debut', '=', display_date),
                        ])
                    if absence_count:
                        M_C = '<a type=\'MF\' docid='+str(absence_count[0].id)+'>M</a>'
                    if absence_count and conges_count:
                        M_C = '<a type=\'CF\' docid='+str(conges_count[0].id)+'>C</a>  ' + '<a type=\'MF\' docid='+str(absence_count[0].id)+'>M</a>'
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
            'etablissement': etablissement,
            'service': service,
            'section': section,
            'nom': nom,
            'date_debut': date_debut,
            'nb_jours': nb_jours,
            'start_date': first_date_year.strftime("%d.%m.%Y"),
            'end_date': last_date_year.strftime("%d.%m.%Y"),
            'back_forward_days': back_forward_days,
            'html': html,
        }
        return vals
