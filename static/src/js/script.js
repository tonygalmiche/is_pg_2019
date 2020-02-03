openerp.is_pg_2019 = function(instance, local) {

    var _t = instance.web._t,
        _lt = instance.web._lt,
        QWeb = instance.web.qweb;
    instance.session.on('module_loaded', this, function () {
        var self = this;
        var dataset = new instance.web.DataSetSearch(self, 'res.company', {}, [['id', '=', instance.session.company_id]]);
        dataset.read_slice([],0).then(function(result){
            if(result.length){
                var $topbar = window.$('#oe_main_menu_navbar');
                if(result[0].text_color && result[0].bg_color && $topbar.length)
                    $topbar.find('a').css('color', result[0].text_color);
                    $topbar.css('background-color', result[0].bg_color);
            }
        })
    });

    local.Calendrier_des_absences = instance.Widget.extend({
        template: "Calendrier_des_absences",
        events: {
            "click a"     : "click_a",
            "click button": "click_button",
        },
        init: function(parent) {
            this._super(parent);
        },
        start: function() {
            d={};
            des_absence_load_data(instance)
        },
        click_a: function(e) {
            d.obj=e.currentTarget;
            b_value=$(d.obj).attr("value");
            if(b_value=='back'){
                $("#back_forward_days").val('-7');
            }
            if(b_value=='forward'){
                $("#back_forward_days").val('7');
            }
            des_absence_load_data(instance)
        },
        click_button: function(e) {
            $("#validation").val('ok');
            $("#back_forward_days").val('0');
            des_absence_load_data(instance)
        },
    });
    //Cette ligne permet de déclarer la fonction précédente  et de faire le lien avec l'action Odoo
    instance.web.client_actions.add('is_pg_2019.is_Calendrier_des_absences_tag', 'instance.is_pg_2019.Calendrier_des_absences');
}

function des_absence_load_data(instance){
    date = new Date(); t1=date.getTime();
    var html;

    var id = document.getElementById("table_body");

    height=window.innerHeight-190; // Recupere l'espace disponilbe dans le navigateur
    width=window.innerWidth-250;   // Recupere l'espace disponilbe dans le navigateur

    var filter = {
        etablissement     : $("#etablissement").val(),
        service           : $("#service").val(),
        section           : $("#section").val(),
        nom               : $("#nom").val(),
        date_debut        : $("#date_debut").val(),
        nb_jours          : $("#nb_jours").val(),
        start_date        : $("#start_date").val(),
        end_date          : $("#end_date").val(),
        back_forward_days : $("#back_forward_days").val(),
        height            : height,
        width             : width,
    }; 

    var is_demande_conges = new openerp.Model('is.demande.conges');

    is_demande_conges.call('analyse_des_absences',[filter],{}).then(function (data) {
        $("#titre").html(data['titre']);
        $('#etablissement').val(data['etablissement']);
        $('#service').val(data['service']);
        $('#section').val(data['section']);
        $('#nom').val(data['nom']);
        $('#date_debut').val(data['date_debut']);
        $('#nb_jours').val(data['nb_jours']);
        $('#start_date').val(data['start_date']);
        $('#end_date').val(data['end_date']);
        $('#back_forward_days').val(data['back_forward_days']);
        html=data['html'];
        //$("#Calendrier_analysecbn").append("<table><tr><th>ABC</th><th>XYZ</th></tr></table>");
        $("#Calendrier_analysecbn").html(html);
        $("#table_body").height(height);
    });
}