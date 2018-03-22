#!/usr/bin/python

# coding=utf-8
#import sys
#reload(sys)
#sys.setdefaultencoding("utf8")
import ast
import json
import datetime
from django.conf import settings
from django.core.mail import send_mail, EmailMessage
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.template.loader import render_to_string
from django.utils.html import  strip_tags

#To return 404 page
from django.http import Http404, JsonResponse

#To query db
from core.models import Content_item
from core.models import Latest_Thinking_item
from core.models import Media_Release_item
from core.models import Event_item
from core.models import Page
from core.models import Carousel_item

from core.models import KeyHealthIssue
from core.models import EmrResources

from core.models import SolutionsCategory
from core.models import ContentType
from core.models import SolutionsFor
from core.models import Pharmacy_Product_Category, Pharmacy_Product, PharmacyProduct_Order, CartItem
from core.models import ProductContact
import json
#Copy
from core.copy import Copy
from core.ajax_query import query_lt_home, query_media_releases, query_upcoming_events

from core import views


from django.template.context_processors import request

#Set the language
def set_lang(request):
    domain = request.META['HTTP_HOST']

    if domain == 'prod-fr.thps.co':
        request.session['lang'] = 'FR'
    else:
        request.session['lang'] = 'EN'
    
    #Set the session lang
    if request.method == 'GET' and 'lang' in request.GET:

        lang = request.GET['lang']
        request.session['lang'] = lang
        
    else:
        lang = request.session.get('lang', 'EN')

    #Return the lang
    return lang

#Set the region
def set_region(request):

    #Set the session region
    if request.method == 'GET' and 'region' in request.GET:

        region = request.GET['region']
        request.session['region'] = region

    else:
        region = request.session.get('region', 'ON')

    #Return the region
    return region

#TODO: set link
def set_link(page_id, lang):
    pass

def page(request, page_url):

    #Get lang and region
    lang = set_lang(request)
    region = set_region(request)

    #Reformat for DB query
    page_url = "/"+page_url+"/"

    try:

        if lang == "EN":
            page = Page.objects.get(url_en=page_url)

        elif lang == "FR":
            page = Page.objects.get(url_fr=page_url)

        #Set page id
        request.session['page_id'] = page.id

        #Get the function dynamically
        return getattr(views, page.view)(request)

    except Page.DoesNotExist:
        raise Http404("Page ( {} ) does not exist in {}".format(page_url, lang))

##############
# Core views #
##############


def base_context(request):

    #Get page info
    page_id = request.session.get('page_id')
    page = Page.objects.get(id=page_id)

    #Get lang and region
    lang = set_lang(request)
    region = set_region(request)

    #Get copy
    copy = Copy(lang, region, page)
    dictionary = copy.base_dictionary()

    if lang == 'EN':
        section_page = Page.objects.get(page_name_en=page.section_name_en)
        section_name = section_page.page_name_en
        section_url = section_page.url_en
        page_title_tag = page.page_name_en + " - " + "TELUS Health"

        #Get carousel items
        carousel_items = Carousel_item.objects.filter(pages__id=page_id).exclude(title_en__isnull=True)
        if carousel_items.count() > 0 :
            first_carousel_item_id = carousel_items[0].id
            carousel_items_count = carousel_items.count()
            carousel_items_range = range(0, carousel_items_count)
        else:
            first_carousel_item_id = 0
            carousel_items_count = 0
            carousel_items_range = range(0, 0)

    elif lang == 'FR':
        section_page = Page.objects.get(page_name_fr=page.section_name_fr)
        section_name = section_page.page_name_fr
        section_url = section_page.url_fr
        page_title_tag = page.page_name_fr + " - " + "TELUS Santé"

        #Get carousel items
        carousel_items = Carousel_item.objects.filter(pages__id=page_id).exclude(title_fr__isnull=True)
        if carousel_items.count() > 0 :
            first_carousel_item_id = carousel_items[0].id
            carousel_items_count = carousel_items.count()
            carousel_items_range = range(0, carousel_items_count)
        else:
            first_carousel_item_id = 0
            carousel_items_count = 0
            carousel_items_range = range(0, 0)

    breadcrumb_string = "<a title=\"{}\" href=\"/\" class=\"main-home\">{}</a>&nbsp;/&nbsp;".format(dictionary['site_name'], dictionary['site_name'])
    if dictionary['page_title'] != section_name:
        breadcrumb_string += "<a title=\"{}\" href=\"{}\" class=\"post post-page\">{}</a>&nbsp;/&nbsp;".format(section_name, section_url, section_name)
    breadcrumb_string += "{}".format(dictionary['page_title'])



    #Set base context dictionary
    context = {

        'lang' : lang,
        'region' : region,
        'breadcrumb_string' : breadcrumb_string,
        'carousel_items' : carousel_items,
        'carousel_items_range' : carousel_items_range,
        'first_carousel_item_id' : first_carousel_item_id,
        'carousel_items_count' : carousel_items_count,
        'page_title_tag' : page_title_tag,
        'page_id' : page_id,
    }

    context.update(dictionary)

    return context

def emr_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {
            'sales_product_inquiries' : 'Sales & Product Inquiries',
            'sales_product_inquiries_url' : '/health-solutions/electronic-medical-records/sales/',
            'technical_support' : 'Technical Support',
            'technical_support_url' : '/health-solutions/electronic-medical-records/support/',

            'welcome' : {
                'text' : 'Welcome',
                'url' : '/health-solutions/electronic-medical-records/overview/'
            },

            'electronic_medical_records_emr' : {
                'text' : 'Electronic medical records (EMR)',
                'url' : '/health-solutions/electronic-medical-records/electronic-medical-records-emr/'
            },

            'implementation_training' : {
                'text' : 'Implementation & Training',
                'url' : '/health-solutions/electronic-medical-records/implementation-training/'
            },

            'services' : {
                'text' : 'Services',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/'
            },

            'internet_phone_tv' : {
                'text' : 'Internet, Phone & TV',
                'url' : '/health-solutions/electronic-medical-records/internet-phone-tv/'
            },

            'resources' : {
                'text' : 'Resources',
                'url' : '/health-solutions/electronic-medical-records/resources/'
            },

            'welcome_overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/electronic-medical-records/overview/'
            },

            'general_practitioners' : {
                'text' : 'General practitioners',
                'url' : '/health-solutions/electronic-medical-records/overview/general-practitioners/'
            },

            'specialists' : {
                'text' : 'Specialists',
                'url' : '/health-solutions/electronic-medical-records/overview/specialists/'
            },

            'emr_overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/electronic-medical-records/electronic-medical-records-emr/'
            },

            'emr_mobile' : {
                'text' : 'EMR Mobile',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/mobile-emr/'
            },

            'kinlogix_emr' : {
                'text' : 'KinLogix EMR',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/kinlogix-emr/'
            },

            'med_access_emr' : {
                'text' : 'Med Access EMR',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/med-access-emr/'
            },

            'medesync_emr' : {
                'text' : 'Medesync EMR',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/medesync-emr/'
            },

            'ps_suite_emr' : {
                'text' : 'PS Suite EMR',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/ps-suite-emr/'
            },

            'wolf_emr' : {
                'text' : 'Wolf EMR',
                'url' : '/health-solutions/electronic-medical-records/our-solutions/wolf-emr/'
            },

            'services_overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/'
            },

            'emr_conversion' : {
                'text' : 'EMR Conversion',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/data-conversion/'
            },

            'hardware' : {
                'text' : 'Hardware',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/hardware/'
            },

            'practice_optimization' : {
                'text' : 'Practice Optimization',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/practice-consulting/'
            },

            'outcome_services' : {
                'text' : 'Outcome Services',
                'url' : '/health-solutions/electronic-medical-records/consulting-services/outcome-services/'
            },

            'section_sales_url' : '/health-solutions/electronic-medical-records/sales/',

        }

    elif lang == 'FR':

        short_copy = {
            'sales_product_inquiries' : 'Ventes et nouveaux services',
            'sales_product_inquiries_url' : '/solutions-en-sante/dossiers-medicaux-electroniques/ventes/',

            'technical_support' : 'Soutien technique',
            'technical_support_url' : '/solutions-en-sante/dossiers-medicaux-electroniques/soutien-technique/',

            'welcome' : {
                'text' : 'Bienvenue',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/apercu/'
            },

            'electronic_medical_records_emr' : {
                'text' : 'Dossiers médicaux électroniques',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/nos-solutions-dme/'
            },

            'implementation_training' : {
                'text' : 'Formation et déploiement',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/formation-et-deploiement/'
            },

            'services' : {
                'text' : 'Services',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/'
            },

            'internet_phone_tv' : {
                'text' : 'Internet, téléphone et télévision',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/internet-telephone-television/'
            },

            'resources' : {
                'text' : 'Ressources',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/ressources/'
            },

            'welcome_overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/apercu/'
            },

            'general_practitioners' : {
                'text' : 'Médecins généralistes',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/apercu/medecins-generalistes/'
            },

            'specialists' : {
                'text' : 'Spécialistes',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/apercu/specialistes/'
            },

            'emr_overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/nos-solutions-dme/'
            },

            'emr_mobile' : {
                'text' : 'DME Mobile',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-mobile/'
            },

            'kinlogix_emr' : {
                'text' : 'KinLogix DME',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-kinlogix/'
            },

            'med_access_emr' : {
                'text' : 'Med Access DME',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-med-access/'
            },

            'medesync_emr' : {
                'text' : 'Medesync DME',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/medesync-dme/'
            },

            'ps_suite_emr' : {
                'text' : 'PS Suite DME',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-suite-sc/'
            },

            'wolf_emr' : {
                'text' : 'Wolf DME',
                'url' : '/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-wolf/'
            },

            'services_overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/'
            },

            'emr_conversion' : {
                'text' : 'Transfert de données',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/conversion-de-donnees/'
            },

            'hardware' : {
                'text' : 'Équipements informatiques',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/equipements-informatiques/'
            },

            'practice_optimization' : {
                'text' : 'Optimisation de votre pratique',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/optimisation-de-votre-pratique/'
            },

            'outcome_services' : {
                'text' : 'Optimisation des résultats cliniques',
                'url' : '/solutions-en-sante/dossiers-medicaux-electroniques/services/optimisation-des-resultats-cliniques/'
            },

            'section_sales_url' : '/solutions-en-sante/dossiers-medicaux-electroniques/ventes/',

        }

    #Set base context dictionary
    emr_base_context = {


        'section_solutions_category' : 3,

        #Set menu classes
        'menu_welcome_class'                    : '',
        'menu_emr_class'                        : '',
        'menu_implementation_class'             : '',
        'menu_services_class'                   : '',
        'menu_internet_class'                   : '',
        'menu_resources_class'                  : '',

        'submenu_welcome_class'                 : '',
        'submenu_our_solutions_class'           : '',
        'submenu_services_class'                : '',

        'submenu_welcome_overview_class'        : '',
        'submenu_welcome_gm_class'              : '',
        'submenu_welcome_specialists_class'     : '',

        'submenu_emr_overview_class'            : '',
        'submenu_emr_mobile_class'              : '',
        'submenu_emr_kin_class'                 : '',
        'submenu_emr_medaccess_class'           : '',
        'submenu_emr_medesync_class'            : '',
        'submenu_emr_pss_class'                 : '',
        'submenu_emr_wolf_class'                : '',

        'submenu_services_overview_class'       : '',
        'submenu_services_conversion_class'     : '',
        'submenu_services_hardware_class'       : '',
        'submenu_services_consulting_class'     : '',
        'submenu_services_outcome_class'        : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,

    }

    #Set context dictionary
    context.update(emr_base_context)
    context.update(short_copy)

    return context

#TODO: After content integration, if views differ only slightly: Build higher level of abstraction

def emr_welcome_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        learnSectionTitle = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionTitle').content_en
        learnSectionCol1 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol1').content_en
        learnSectionCol2 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol2').content_en
        learnSectionCol3 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol3').content_en
        segmentSectionTitle = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionTitle').content_en
        segmentSectionCol1 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionCol1').content_en
        segmentSectionCol2 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionCol2').content_en
    elif lang == "FR":
        learnSectionTitle = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionTitle').content_fr
        learnSectionCol1 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol1').content_fr
        learnSectionCol2 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol2').content_fr
        learnSectionCol3 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='learnSectionCol3').content_fr
        segmentSectionTitle = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionTitle').content_fr
        segmentSectionCol1 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionCol1').content_fr
        segmentSectionCol2 = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='segmentSectionCol2').content_fr

    #Set context dictionary
    context.update({


        'menu_welcome_class' : 'current_page_item',
        'submenu_welcome_overview_class' : 'active',

        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

        'learnSectionTitle' : learnSectionTitle,
        'learnSectionCol1' : learnSectionCol1,
        'learnSectionCol2' : learnSectionCol2,
        'learnSectionCol3' : learnSectionCol3,

        'segmentSectionTitle' : segmentSectionTitle,
        'segmentSectionCol1' : segmentSectionCol1,
        'segmentSectionCol2' : segmentSectionCol2,
        'show_latest_thinking'  : True,
        'show_media_releases'  : True,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-media_release_date')[:3]

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_welcome_overview.html', locals())

def emr_welcome_general_practitioners(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='page_title').content_en
        greyIntroTitle = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyIntroTitle').content_en
        greyIntroParagraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyIntroParagraph').content_en
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox1Title').content_en
        greyBox1Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox1Paragraph').content_en
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox2Title').content_en
        greyBox2Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox2Paragraph').content_en
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox3Title').content_en
        greyBox3Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox3Paragraph').content_en
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox4Title').content_en
        greyBox4Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox4Paragraph').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='page_title').content_fr
        greyIntroTitle = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyIntroTitle').content_fr
        greyIntroParagraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyIntroParagraph').content_fr
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox1Title').content_fr
        greyBox1Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox1Paragraph').content_fr
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox2Title').content_fr
        greyBox2Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox2Paragraph').content_fr
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox3Title').content_fr
        greyBox3Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox3Paragraph').content_fr
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox4Title').content_fr
        greyBox4Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_general_practitioners', role='greyBox4Paragraph').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_welcome_class' : 'current_page_item',
        'submenu_welcome_gm_class' : 'active',

        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

        'greyIntroTitle' : greyIntroTitle,
        'greyIntroParagraph' : greyIntroParagraph,
        'greyBox1Title' : greyBox1Title,
        'greyBox1Paragraph' : greyBox1Paragraph,
        'greyBox2Title' : greyBox2Title,
        'greyBox2Paragraph' : greyBox2Paragraph,
        'greyBox3Title' : greyBox3Title,
        'greyBox3Paragraph' : greyBox3Paragraph,
        'greyBox4Title' : greyBox4Title,
        'greyBox4Paragraph' : greyBox4Paragraph,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_welcome_general_practitioners.html', locals())

def emr_welcome_specialists(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='page_title').content_en
        greyIntroTitle = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyIntroTitle').content_en
        greyIntroParagraph = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyIntroParagraph').content_en
        greyBox1Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox1Label').content_en
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox1Content').content_en
        greyBox2Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox2Label').content_en
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox2Content').content_en
        greyBox3Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox3Label').content_en
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox3Content').content_en
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox4Title').content_en
        greyBox4Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox4Paragraph').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='page_title').content_fr
        greyIntroTitle = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyIntroTitle').content_fr
        greyIntroParagraph = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyIntroParagraph').content_fr
        greyBox1Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox1Label').content_fr
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox1Content').content_fr
        greyBox2Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox2Label').content_fr
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox2Content').content_fr
        greyBox3Label = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox3Label').content_fr
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox3Content').content_fr
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox4Title').content_fr
        greyBox4Paragraph = Content_item.objects.get(section='emr', page='emr_welcome_specialists', role='greyBox4Paragraph').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_welcome_class' : 'current_page_item',
        'submenu_welcome_specialists_class' : 'active',

        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

        'greyIntroTitle' : greyIntroTitle,
        'greyIntroParagraph' : greyIntroParagraph,
        'greyBox1Label' : greyBox1Label,
        'greyBox1Content' : greyBox1Content,
        'greyBox2Label' : greyBox2Label,
        'greyBox2Content' : greyBox2Content,
        'greyBox3Label' : greyBox3Label,
        'greyBox3Content' : greyBox3Content,
        'greyBox4Title' : greyBox4Title,
        'greyBox4Paragraph' : greyBox4Paragraph,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_welcome_specialists.html', locals())

def emr_emr_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        province_get = str(request.GET['province']) if 'province' in request.GET else ""

    else:

        province_get = ""

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_overview', role='page_title').content_en
        head1 = Content_item.objects.get(section='emr', page='emr_overview', role='head1').content_en
        head1_links1 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_links1').content_en
        results1_head1 = Content_item.objects.get(section='emr', page='emr_overview', role='results1_head1').content_en
        results1_intro1 = Content_item.objects.get(section='emr', page='emr_overview', role='results1_intro1').content_en
        head1_intro2 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro2').content_en
        head1_intro3 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro3').content_en
        head1_intro4 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro4').content_en
        head1_intro5 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro5').content_en
        head1_intro6 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro6').content_en
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_overview', role='page_title').content_fr
        head1 = Content_item.objects.get(section='emr', page='emr_overview', role='head1').content_fr
        head1_links1 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_links1').content_fr
        results1_head1 = Content_item.objects.get(section='emr', page='emr_overview', role='results1_head1').content_fr
        results1_intro1 = Content_item.objects.get(section='emr', page='emr_overview', role='results1_intro1').content_fr
        head1_intro2 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro2').content_fr
        head1_intro3 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro3').content_fr
        head1_intro4 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro4').content_fr
        head1_intro5 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro5').content_fr
        head1_intro6 = Content_item.objects.get(section='emr', page='emr_overview', role='head1_intro6').content_fr
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_overview_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    #Search lists:
    provinces = {
        'emr_mobile' : ['AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
        'kinlogix' : ['QC'],
        'med_access' : ['AB', 'BC', 'MB', 'NB', 'NL', 'NS', 'ON', 'PE', 'SK'],
        'medesync' : ['QC'],
        'ps_suite' : ['BC', 'NB', 'NL', 'NS', 'ON', 'PE'],
        'wolf' : ['AB', 'BC', 'NL', 'NT', 'NU', 'YT']
    }

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_overview.html', locals())

def emr_emr_mobile_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='page_title').content_en
        head1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head1').content_en
        head2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head2').content_en
        head3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head3').content_en
        head4 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head4').content_en
        head5 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head5').content_en
        section1_title = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section1_title').content_en
        section1_box1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section1_box1').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_title').content_en
        section2_head1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head1').content_en
        section2_box1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box1').content_en
        section2_head2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head2').content_en
        section2_box2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box2').content_en
        section2_head3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head3').content_en
        section2_box3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box3').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_mobile_emr', role='page_title').content_fr
        head1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head1').content_fr
        head2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head2').content_fr
        head3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head3').content_fr
        head4 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head4').content_fr
        head5 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='head5').content_fr
        section1_title = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section1_title').content_fr
        section1_box1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section1_box1').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_title').content_fr
        section2_head1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head1').content_fr
        section2_box1 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box1').content_fr
        section2_head2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head2').content_fr
        section2_box2 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box2').content_fr
        section2_head3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_head3').content_fr
        section2_box3 = Content_item.objects.get(section='emr', page='emr_mobile_emr', role='section2_box3').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_mobile_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_mobile_emr.html', locals())

def emr_emr_kinlogix_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='page_title').content_en
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro1').content_en
        section4_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro2').content_en
        section4_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro3').content_en
        section5_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_title').content_en
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro1').content_en
        section5_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_intro1').content_en
        section6_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section6_title').content_en
        section6_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section6_intro1').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='page_title').content_fr
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro1').content_fr
        section4_intro2 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro2').content_fr
        section4_intro3 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro3').content_fr
        section5_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_title').content_fr
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section4_intro1').content_fr
        section5_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section5_intro1').content_fr
        section6_title = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section6_title').content_fr
        section6_intro1 = Content_item.objects.get(section='emr', page='emr_kinlogix_emr', role='section6_intro1').content_fr
    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_kin_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_kinlogix_emr.html', locals())

def emr_emr_med_access_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_med_access_emr', role='page_title').content_en
        section1_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section4_intro1').content_en
        section5_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section5_title').content_en
        section5_list1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section5_list1').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_med_access_emr', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section4_intro1').content_fr
        section5_title = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section5_title').content_fr
        section5_list1 = Content_item.objects.get(section='emr', page='emr_med_access_emr', role='section5_list1').content_fr
    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_medaccess_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_med_access_emr.html', locals())

def emr_emr_medesync_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_medesync_emr', role='page_title').content_en
        section1_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_title').content_en
        section1_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro1_img').content_en
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro1').content_en
        section1_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2_title').content_en
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2').content_en
        section1_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2_img').content_en
        section1_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro3_img').content_en
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro1').content_en
        section2_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro1_img').content_en
        section2_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2_title').content_en
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2').content_en
        section2_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2_img').content_en
        section2_intro3_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3_title').content_en
        section2_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3_img').content_en
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3').content_en
        section2_intro4 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro4').content_en
        section2_intro4_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro4_img').content_en
        section2_intro5_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro5_img').content_en
        section2_intro5 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro5').content_en
        section2_intro6_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6_title').content_en
        section2_intro6 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6').content_en
        section2_intro6_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6_img').content_en
        section3_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_title').content_en
        section3_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro1_img').content_en
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro2').content_en
        section3_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro2_img').content_en
        section3_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro3_img').content_en
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro1').content_en
        section4_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2_title').content_en
        section4_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2_img').content_en
        section4_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_medesync_emr', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_title').content_fr
        section1_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro1_img').content_fr
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro1').content_fr
        section1_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2_title').content_fr
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2').content_fr
        section1_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro2_img').content_fr
        section1_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro3_img').content_fr
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro1').content_fr
        section2_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro1_img').content_fr
        section2_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2_title').content_fr
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2').content_fr
        section2_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro2_img').content_fr
        section2_intro3_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3_title').content_fr
        section2_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3_img').content_fr
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro3').content_fr
        section2_intro4 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro4').content_fr
        section2_intro4_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro4_img').content_fr
        section2_intro5_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro5_img').content_fr
        section2_intro5 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro5').content_fr
        section2_intro6_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6_title').content_fr
        section2_intro6 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6').content_fr
        section2_intro6_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section2_intro6_img').content_fr
        section3_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_title').content_fr
        section3_intro1_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro1_img').content_fr
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro2').content_fr
        section3_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro2_img').content_fr
        section3_intro3_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro3_img').content_fr
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro1').content_fr
        section4_intro2_title = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2_title').content_fr
        section4_intro2_img = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2_img').content_fr
        section4_intro2 = Content_item.objects.get(section='emr', page='emr_medesync_emr', role='section4_intro2').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_medesync_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_medesync_emr.html', locals())

def emr_emr_pssuite_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_pssuite_emr', role='page_title').content_en
        section1_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro3').content_en
        section1_box1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box3').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section2_intro1').content_en
        section3_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section3_intro1').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_pssuite_emr', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_intro3').content_fr
        section1_box1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section1_box3').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section2_intro1').content_fr
        section3_title = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_pssuite_emr', role='section3_intro1').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_pss_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_pssuite_emr.html', locals())

def emr_emr_wolf_emr(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_wolf_emr', role='page_title').content_en
        section1_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section4_intro1').content_en
        section5_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section5_title').content_en
        section5_links1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section5_links1').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_emr_wolf_emr', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section4_intro1').content_fr
        section5_title = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section5_title').content_fr
        section5_links1 = Content_item.objects.get(section='emr', page='emr_wolf_emr', role='section5_links1').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_emr_class' : 'current_page_item',
        'submenu_emr_wolf_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_emr_wolf_emr.html', locals())


def emr_implementation_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='page_title').content_en
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Title').content_en
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Content').content_en
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Title').content_en
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Content').content_en
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Title').content_en
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Content').content_en
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Title').content_en
        greyBox4Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Content').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='page_title').content_fr
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Title').content_fr
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Content').content_fr
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Title').content_fr
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Content').content_fr
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Title').content_fr
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Content').content_fr
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Title').content_fr
        greyBox4Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Content').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_implementation_class' : 'current_page_item',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

        'greyBox1Title' : greyBox1Title,
        'greyBox1Content' : greyBox1Content,
        'greyBox2Title' : greyBox2Title,
        'greyBox2Content' : greyBox2Content,
        'greyBox3Title' : greyBox3Title,
        'greyBox3Content' : greyBox3Content,
        'greyBox4Title' : greyBox4Title,
        'greyBox4Content' : greyBox4Content,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_implementation_overview.html', locals())

def emr_services_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_services_overview', role='page_title').content_en
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Title').content_en
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Content').content_en
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Title').content_en
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Content').content_en
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Title').content_en
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Content').content_en
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Title').content_en
        greyBox4Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Content').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_services_overview', role='page_title').content_fr
        greyBox1Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Title').content_fr
        greyBox1Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox1Content').content_fr
        greyBox2Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Title').content_fr
        greyBox2Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox2Content').content_fr
        greyBox3Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Title').content_fr
        greyBox3Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox3Content').content_fr
        greyBox4Title = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Title').content_fr
        greyBox4Content = Content_item.objects.get(section='emr', page='emr_implementation_overview', role='greyBox4Content').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_services_class' : 'current_page_item',
        'submenu_services_overview_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',

        'greyBox1Title' : greyBox1Title,
        'greyBox1Content' : greyBox1Content,
        'greyBox2Title' : greyBox2Title,
        'greyBox2Content' : greyBox2Content,
        'greyBox3Title' : greyBox3Title,
        'greyBox3Content' : greyBox3Content,
        'greyBox4Title' : greyBox4Title,
        'greyBox4Content' : greyBox4Content,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_services_overview.html', locals())

def emr_services_data_conversion(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_services_data_conversion', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_services_data_conversion', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_services_class' : 'current_page_item',
        'submenu_services_conversion_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_services_data_conversion.html', locals())

def emr_services_hardware(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_services_hardware', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_services_hardware', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_services_class' : 'current_page_item',
        'submenu_services_hardware_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_services_hardware.html', locals())

def emr_services_consulting(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_services_consulting', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_services_consulting', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_services_class' : 'current_page_item',
        'submenu_services_consulting_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_services_consulting.html', locals())

def emr_services_outcome(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_services_outcome', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_services_outcome', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_services_class' : 'current_page_item',
        'submenu_services_outcome_class' : 'active',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_services_outcome.html', locals())

def emr_internet_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_internet_overview', role='page_title').content_en
        box1Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box1Label').content_en
        box1Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box1Content').content_en
        box2Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box2Label').content_en
        box2Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box2Content').content_en
        box3Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box3Label').content_en
        box3Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box3Content').content_en
        box4Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box4Label').content_en
        box4Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box4Content').content_en
        box5Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box5Label').content_en
        box5Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box5Content').content_en
        box6Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box6Label').content_en
        box6Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box6Content').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_internet_overview', role='page_title').content_fr
        box1Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box1Label').content_fr
        box1Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box1Content').content_fr
        box2Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box2Label').content_fr
        box2Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box2Content').content_fr
        box3Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box3Label').content_fr
        box3Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box3Content').content_fr
        box4Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box4Label').content_fr
        box4Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box4Content').content_fr
        box5Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box5Label').content_fr
        box5Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box5Content').content_fr
        box6Label = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box6Label').content_fr
        box6Content = Content_item.objects.get(section='emr', page='emr_internet_overview', role='box6Content').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_internet_class' : 'current_page_item',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

        'box1Label' : box1Label,
        'box1Content' : box1Content,
        'box2Label' : box2Label,
        'box2Content' : box2Content,
        'box3Label' : box3Label,
        'box3Content' : box3Content,
        'box4Label' : box4Label,
        'box4Content' : box4Content,
        'box5Label' : box5Label,
        'box5Content' : box5Content,
        'box6Label' : box6Label,
        'box6Content' : box6Content,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_internet_overview.html', locals())

def emr_resources_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Set search filters
    if request.method == 'GET':

        solution = request.GET['solution'] if 'solution' in request.GET else ""
        category = request.GET['category'] if 'category' in request.GET else ""
        type = request.GET['type'] if 'type' in request.GET else ""

    else:

        solution = ""
        category = ""
        type = ""

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_resources_overview', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_resources_overview', role='page_title').content_fr

    resource_items = EmrResources.objects.filter(solution=solution,category=category,type=type)

    #Set context dictionary
    context.update({
        'page_title' : page_title,

        'menu_resources_class' : 'current_page_item',

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/emr/emr_resources_overview.html', locals())

def emr_sales(request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    product_link_name = ""
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True
        product_link_name = request.GET['solution']

    #Get Marketo Form
    product_link_name_list = ['emr-general', 'kinlogix-emr', 'med-access-emr', 'medesync-emr', 'ps-suite-emr', 'wolf-emr',
                              'dme-general', 'dme-kinlogix', 'dme-med-access', 'medesync-dme', 'dme-suite-sc', 'dme-wolf']

    if product_link_name not in product_link_name_list:
        product_link_name = 'emr-general' if lang == 'EN' else 'dme-general'

    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'not_customer' : 'I am not a TELUS EMR customer',
            'sales_general' : {
                'text' : "I'd like to speak to a TELUS  Health team member",
                'url' : "?solution=emr-general"
                },
            'currently_use' : 'I currently use the following EMR',
            'sales_kin' : {
                'text' : "Kinlogix EMR",
                'url' : "?solution=kinlogix-emr"
                },
            'sales_medaccess' : {
                'text' : "Med Access EMR",
                'url' : "?solution=med-access-emr"
                },
            'sales_medesync' : {
                'text' : "Medesync EMR",
                'url' : "?solution=medesync-emr"
                },
            'sales_pss' : {
                'text' : "PS Suite EMR",
                'url' : "?solution=ps-suite-emr"
                },
            'sales_wolf' : {
                'text' : "Wolf EMR",
                'url' : "?solution=wolf-emr"
                }

            }

    elif lang == 'FR':

        short_copy = {

            'not_customer' : 'Je ne suis pas un client de TELUS Santé',
            'sales_general' : {
                'text' : "Je voudrais parler à un membre de l'équipe TELUS Santé",
                'url' : "?solution=dme-general"
                },
            'currently_use' : "J'utilise actuellement le DME suivant",
            'sales_kin' : {
                'text' : "Kinlogix DME",
                'url' : "?solution=dme-kinlogix"
                },
            'sales_medaccess' : {
                'text' : "Med Access DME",
                'url' : "?solution=dme-med-access"
                },
            'sales_medesync' : {
                'text' : "Medesync DME",
                'url' : "?solution=medesync-dme"
                },
            'sales_pss' : {
                'text' : "Suite SC DME",
                'url' : "?solution=dme-suite-sc"
                },
            'sales_wolf' : {
                'text' : "Wolf DME",
                'url' : "?solution=dme-wolf"
                }

            }

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_sales', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_sales', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,
        'show_carousel' : False,

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/emr/emr_sales.html', locals())

def emr_support(request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    product_link_name = ""

    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name_list = ['kinlogix-emr', 'med-access-emr', 'medesync-emr', 'ps-suite-emr', 'wolf-emr',
                              'dme-kinlogix', 'dme-med-access', 'medesync-dme', 'dme-suite-sc', 'dme-wolf']

    if product_link_name not in product_link_name_list:
        product_link_name = 'kinlogix-emr' if lang == 'EN' else 'dme-kinlogix'

    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'need_support' : 'Experiencing a technical issue and need support?',
            'select_issue' : 'Select the TELUS Health solution you are experiencing an issue with:',

            'support_kin' : {
                'text' : "Kinlogix EMR",
                'url' : "?solution=kinlogix-emr"
                },
            'support_medaccess' : {
                'text' : "Med Access EMR",
                'url' : "?solution=med-access-emr"
                },
            'support_medesync' : {
                'text' : "Medesync EMR",
                'url' : "?solution=medesync-emr"
                },
            'support_pss' : {
                'text' : "PS Suite EMR",
                'url' : "?solution=ps-suite-emr"
                },
            'support_wolf' : {
                'text' : "Wolf EMR",
                'url' : "?solution=wolf-emr"
                },
            'support_nightingale' : {
                'text' : "Nightingale",
                'url' : "?solution=emr-general"
                },
            'support_zrx' : {
                'text' : "ZRx Prescriber",
                'url' : "?solution=emr-general"
                }

            }

    elif lang == 'FR':

        short_copy = {

            'need_support' : 'Besoin de soutien technique ?',
            'select_issue' : "J'utilise actuellement le solution suivant:",

            'support_kin' : {
                'text' : "Kinlogix DME",
                'url' : "?solution=dme-kinlogix"
                },
            'support_medaccess' : {
                'text' : "Med Access DME",
                'url' : "?solution=dme-med-access"
                },
            'support_medesync' : {
                'text' : "Medesync DME",
                'url' : "?solution=medesync-dme"
                },
            'support_pss' : {
                'text' : "Suite SC DME",
                'url' : "?solution=dme-suite-sc"
                },
            'support_wolf' : {
                'text' : "Wolf DME",
                'url' : "?solution=dme-wolf"
                },
            'support_nightingale' : {
                'text' : "Nightingale",
                'url' : "/solutions-en-sante/dossiers-medicaux-electroniques/soutien-technique/"
                },
            'support_zrx' : {
                'text' : "ZRx Prescriber",
                'url' : "/solutions-en-sante/dossiers-medicaux-electroniques/soutien-technique/"
                }

            }

    #Get base generic context
    context = emr_base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='emr', page='emr_support', role='page_title').content_en
    elif lang == "FR":
        page_title = Content_item.objects.get(section='emr', page='emr_support', role='page_title').content_fr

    #Set context dictionary
    context.update({
        'page_title' : page_title,
        'show_carousel' : False,

        'submenu_welcome_class' : 'style=display:none!important',
        'submenu_our_solutions_class' : 'style=display:none!important',
        'submenu_services_class' : 'style=display:none!important',

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/emr/emr_support.html', locals())

######################################################################################################################
#PHARMACY
######################################################################################################################

def pharmacy_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contact sales today',
                'url' : '/health-solutions/pharmacy-management/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/pharmacy-management/overview/'
            },

            'benefits' : {
                'text' : 'Benefits',
                'url' : '/health-solutions/pharmacy-management/benefits/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/pharmacy-management/our-solutions/'
            },

            'reviews' : {
                'text' : 'Reviews',
                'url' : '/health-solutions/pharmacy-management/reviews/'
            },

            'contact_sales' : {
                'text' : 'Contact Sales',
                'url' : '/health-solutions/pharmacy-management/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/pharmacy-management/support/'
            },

            'pharmacy_ubik' : {
                'text' : 'Ubik',
                'url' : '/health-solutions/pharmacy-management/our-solutions/telus-ubik/'
            },

            'rx_vigilance' : {
                'text' : 'Rx Vigilance',
                'url' : '/health-solutions/pharmacy-management/our-solutions/rx-vigilance'
            },

            'xpill_pharma' : {
                'text' : 'xPill PHARMA',
                'url' : '/health-solutions/pharmacy-management/our-solutions/xpill-pharma/'
            },

            'pharma_space' : {
                'text' : 'Pharma Space',
                'url' : '/health-solutions/pharmacy-management/our-solutions/pharma-space/'
            },

            'do_pill' : {
                'text' : 'DO-Pill',
                'url' : '/health-solutions/pharmacy-management/our-solutions/do-pill/'
            },

            'assyst_pos' : {
                'text' : 'Assyst Point-of-sale',
                'url' : '/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/'
            },

            'assyst_pos_qc' : {
                'text' : 'Assyst Point-of-sale (Quebec)',
                'url' : '/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/'
            },

            'assyst_network_plus' : {
                'text' : 'Assyst Network Plus',
                'url' : '/health-solutions/pharmacy-management/our-solutions/assyst-network/'
            },

            'section_sales_url' : '/health-solutions/pharmacy-management/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/apercu/'
            },

            'benefits' : {
                'text' : 'Avantages',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/avantages/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/solutions-gestion-pharmacies/'
            },

            'reviews' : {
                'text' : 'On en parle',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/on-en-parle/'
            },

            'contact_sales' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/soutien-technique/'
            },

            'pharmacy_ubik' : {
                'text' : 'Ubik (Qc)',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/'
            },

            'rx_vigilance' : {
                'text' : 'Rx Vigilance',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/'
            },

            'xpill_pharma' : {
                'text' : 'xPill PHARMA (Qc)',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/'
            },

            'pharma_space' : {
                'text' : 'Espace pharma',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/'
            },

            'do_pill' : {
                'text' : 'DO-Pill',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/'
            },

            'assyst_pos' : {
                'text' : 'Assyst Point de vente',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/'
            },

            'assyst_pos_qc' : {
                'text' : 'Assyst Point de vente (Qc)',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/'
            },

            'assyst_network_plus' : {
                'text' : 'Assyst Réseau Plus',
                'url' : '/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/'
            },

            'section_sales_url' : '/solutions-en-sante/solutions-de-gestion-de-pharmacies/ventes/',

        }

    #Set base context dictionary
    pharmacy_base_context = {

        'section_solutions_category' : 10,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_benefits_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_reviews_class'                    : '',
        'menu_contact_sales_class'              : '',
        'menu_customer_support_class'           : '',

        'submenu_our_solutions_class'                   : 'style=display:none!important',
        'submenu_our_solutions_ubik_class'              : '',
        'submenu_our_solutions_rx_vigilance_class'      : '',
        'submenu_our_solutions_xpill_pharma_class'      : '',
        'submenu_our_solutions_pharma_space_class'      : '',
        'submenu_our_solutions_do_pill_class'           : '',
        'submenu_our_solutions_assyst_pos_class'        : '',
        'submenu_our_solutions_assyst_pos_qc_class'     : '',
        'submenu_our_solutions_assyst_net_class'   : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(pharmacy_base_context)
    context.update(short_copy)

    return context

def pharmacy_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        pharmacy_overview_links = {
            'benefits' : "/health-solutions/pharmacy-management/benefits/",
            'reviews' : "/health-solutions/pharmacy-management/reviews/"
        }

        page_title = Content_item.objects.get(section='pharmacy', page='overview', role='page_title').content_en
        first_section_title = Content_item.objects.get(section='pharmacy', page='overview', role='first_section_title').content_en
        section1_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_box2').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_intro2').content_en
        second_section_title = Content_item.objects.get(section='pharmacy', page='overview', role='second_section_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro3').content_en
        section2_impress1 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress1').content_en
        section2_impress2 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress2').content_en
        section2_impress3 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress3').content_en
        section2_impress4 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress4').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='overview', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box1').content_en
        section3_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro2').content_en
        section3_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box2').content_en
        section3_intro3 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro3').content_en
        section3_box3 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box3').content_en
        section3_box4 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box4').content_en
        section4_title1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_title1').content_en
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_intro1').content_en
        section4_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_box1').content_en
        section4_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_intro2').content_en
        section4_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_box2').content_en
        section5_title1 = Content_item.objects.get(section='pharmacy', page='overview', role='section5_title1').content_en
        section6_title = Content_item.objects.get(section='pharmacy', page='overview', role='section6_title').content_en

    elif lang == "FR":
        pharmacy_overview_links = {
            'benefits' : "/solutions-en-sante/solutions-de-gestion-de-pharmacies/avantages/",
            'reviews' : "/solutions-en-sante/solutions-de-gestion-de-pharmacies/on-en-parle/"
        }

        page_title = Content_item.objects.get(section='pharmacy', page='overview', role='page_title').content_fr
        first_section_title = Content_item.objects.get(section='pharmacy', page='overview', role='first_section_title').content_fr
        section1_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_box2').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section1_intro2').content_fr
        second_section_title = Content_item.objects.get(section='pharmacy', page='overview', role='second_section_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_intro3').content_fr
        section2_impress1 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress1').content_fr
        section2_impress2 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress2').content_fr
        section2_impress3 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress3').content_fr
        section2_impress4 = Content_item.objects.get(section='pharmacy', page='overview', role='section2_impress4').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='overview', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box1').content_fr
        section3_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro2').content_fr
        section3_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box2').content_fr
        section3_intro3 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_intro3').content_fr
        section3_box3 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box3').content_fr
        section3_box4 = Content_item.objects.get(section='pharmacy', page='overview', role='section3_box4').content_fr
        section4_title1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_title1').content_fr
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_intro1').content_fr
        section4_box1 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_box1').content_fr
        section4_intro2 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_intro2').content_fr
        section4_box2 = Content_item.objects.get(section='pharmacy', page='overview', role='section4_box2').content_fr
        section5_title1 = Content_item.objects.get(section='pharmacy', page='overview', role='section5_title1').content_fr
        section6_title = Content_item.objects.get(section='pharmacy', page='overview', role='section6_title').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_overview_class' : 'current_page_item',
        #'first_section_title' : first_section_title,
        'section1_box1' : section1_box1,
        'second_section_title' : second_section_title,
        'section1_box2' : section1_box2,
        'show_latest_thinking'                  : True,
    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]
    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_overview.html', locals())

def pharmacy_benefits(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":

        section1_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box3').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_title').content_en
        section2_intro = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_intro').content_en
        section2_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box3').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box2').content_en
        section3_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box3').content_en
    elif lang == "FR":

        section1_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section1_box3').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_title').content_fr
        section2_intro = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_intro').content_fr
        section2_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section2_box3').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box2').content_fr
        section3_box3 = Content_item.objects.get(section='pharmacy', page='benefits', role='section3_box3').content_fr
    #Set context dictionary
    context.update({

        'menu_benefits_class' : 'current_page_item',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_benefits.html', locals())

def pharmacy_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        province_get = str(request.GET['province']) if 'province' in request.GET else ""
        segment_get = int(request.GET['segment']) if 'segment' in request.GET else 0

    else:

        province_get = ""
        segment_get = 0

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro2').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section2_intro1').content_en
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))
        all_segments = ((1, 'Pharmacy Management Systems'),
                        (2, 'Clinical Solutions and Collaboration Tools'),
                        (3, 'Patient-Centric Solutions'),
                        (4, 'Point-of-Sale Solutions'),
                        (5, 'Network and Hardware Solutions'))

    elif lang == "FR":
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro2').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions', role='section2_intro1').content_fr
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))
        all_segments = ((1, "Solutions de gestion d'officine et modules optionnels"),
                        (2, 'Solutions cliniques et outils de collaboration'),
                        (3, "Solutions orientée-patient"),
                        (4, "Solutions de point de vente"),
                        (5, "Solutions réseau"))
    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta' : False,

    })

    provinces = {
        'ubik'          : ['QC'],
        'rx_vigilance'  : ['AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
        'xpill '        : ['QC'],
        'pharma_space'  : ['AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT'],
        'do_pill'       : ['QC'],
        'assyst_pos'    : ['AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'SK', 'YT'],
        'assyst_pos_qc' : ['QC'],
        'assyst_net'    : ['AB', 'BC', 'MB', 'NB', 'NL', 'NT', 'NS', 'NU', 'ON', 'PE', 'QC', 'SK', 'YT']
    }

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions.html', locals())


def pharmacy_our_solutions_ubik(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='page_title').content_en
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_intro2').content_en
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section4_intro1').content_en
        section5_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section5_intro1').content_en
        section6_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section6_title').content_en
        section6_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section6_intro1').content_en
        section7_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section7_title').content_en
        section7_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section7_intro1').content_en
        section8_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section8_title').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section3_intro2').content_fr
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section4_intro1').content_fr
        section5_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section5_intro1').content_fr
        section6_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section6_title').content_fr
        section6_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section6_intro1').content_fr
        section7_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section7_title').content_fr
        section7_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section7_intro1').content_fr
        section8_title = Content_item.objects.get(section='pharmacy', page='our_solutions_ubik', role='section8_title').content_fr


    #Set context dictionary
    context.update({

        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_ubik_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_ubik.html', locals())

def pharmacy_our_solutions_rx_vigilance(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='page_title').content_en
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section3_intro1').content_en
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section4_intro1').content_en

    if lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section3_intro1').content_fr
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_rx_vigilance', role='section4_intro1').content_fr


    #Set context dictionary
    context.update({
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_rx_vigilance_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_rx_vigilance.html', locals())

def pharmacy_our_solutions_xpill_pharma(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='page_title').content_en
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_intro2').content_en
        section1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_box2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section2_intro1').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_intro2').content_fr
        section1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section1_box2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_xpill_pharma', role='section2_intro1').content_fr

    #Set context dictionary
    context.update({

        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_xpill_pharma_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_xpill_pharma.html', locals())

def pharmacy_our_solutions_pharma_space(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='page_title').content_en
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro3').content_en
        section1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_box2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section2_title').content_en
        section2_intro = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section2_intro').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_title').content_en
        section3_head1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head1').content_en
        section3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box1').content_en
        section3_head2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head2').content_en
        section3_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box2').content_en
        section3_head3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head3').content_en
        section3_box3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box3').content_en
        section3_head4 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head4').content_en
        section3_box4 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box4').content_en
        section3_head5 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head5').content_en
        section3_box5 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box5').content_en
        section3_head6 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head6').content_en
        section3_box6 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box6').content_en
        section3_head7 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head7').content_en
        section3_box7 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box7').content_en
        section3_head8 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head8').content_en
        section3_box8 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box8').content_en
        section3_head9 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head9').content_en
        section3_box9 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box9').content_en
        section3_head10 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head10').content_en
        section3_box10 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box10').content_en
        section3_head11 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head11').content_en
        section3_box11 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box11').content_en
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_intro1').content_en
        section4_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_box1').content_en
        section5_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section5_title').content_en
        read_more = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='read_more').content_en
        link1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='link1').content_en

    if lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_intro3').content_fr
        section1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section1_box2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section2_title').content_fr
        section2_intro = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section2_intro').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_title').content_fr
        section3_head1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head1').content_fr
        section3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box1').content_fr
        section3_head2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head2').content_fr
        section3_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box2').content_fr
        section3_head3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head3').content_fr
        section3_box3 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box3').content_fr
        section3_head4 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head4').content_fr
        section3_box4 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box4').content_fr
        section3_head5 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head5').content_fr
        section3_box5 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box5').content_fr
        section3_head6 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head6').content_fr
        section3_box6 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box6').content_fr
        section3_head7 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head7').content_fr
        section3_box7 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box7').content_fr
        section3_head8 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head8').content_fr
        section3_box8 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box8').content_fr
        section3_head9 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head9').content_fr
        section3_box9 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box9').content_fr
        section3_head10 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head10').content_fr
        section3_box10 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box10').content_fr
        section3_head11 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_head11').content_fr
        section3_box11 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section3_box11').content_fr
        section4_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_intro1').content_fr
        section4_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section4_box1').content_fr
        section5_title = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='section5_title').content_fr
        read_more = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='read_more').content_fr
        link1 = Content_item.objects.get(section='pharmacy', page='our_solutions_pharma_space', role='link1').content_fr

    #Set context dictionary
    context.update({

        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_pharma_space_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_pharma_space.html', locals())

def pharmacy_our_solutions_do_pill(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='page_title').content_en
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section2_intro1').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section3_title').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='page_title').content_fr
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section2_intro1').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_do_pill', role='section3_title').content_fr

    #Set context dictionary
    context.update({

        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_do_pill_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_do_pill.html', locals())

def pharmacy_our_solutions_assyst_pos(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1').content_en
        section2_intro1_title1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title1').content_en
        section2_intro1_title1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title1_box1').content_en
        section2_intro1_title2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title2').content_en
        section2_intro1_title2_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title2_box1').content_en
        section2_intro1_title3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title3').content_en
        section2_intro1_title3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title3_box1').content_en
        section2_intro1_title4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title4').content_en
        section2_intro1_title4_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title4_box1').content_en
        section2_intro1_title5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title5').content_en
        section2_intro1_title5_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title5_box1').content_en
        section2_intro1_title6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title6').content_en
        section2_intro1_title6_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title6_box1').content_en
        section2_intro1_title7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title7').content_en
        section2_intro1_title7_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title7_box1').content_en
        section2_intro1_title8 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title8').content_en
        section2_intro1_title8_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title8_box1').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_intro1').content_en
        section3_intro1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_intro1_box1').content_en
    if lang == "FR":
        #
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1').content_fr
        section2_intro1_title1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title1').content_fr
        section2_intro1_title1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title1_box1').content_fr
        section2_intro1_title2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title2').content_fr
        section2_intro1_title2_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title2_box1').content_fr
        section2_intro1_title3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title3').content_fr
        section2_intro1_title3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title3_box1').content_fr
        section2_intro1_title4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title4').content_fr
        section2_intro1_title4_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title4_box1').content_fr
        section2_intro1_title5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title5').content_fr
        section2_intro1_title5_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title5_box1').content_fr
        section2_intro1_title6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title6').content_fr
        section2_intro1_title6_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title6_box1').content_fr
        section2_intro1_title7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title7').content_fr
        section2_intro1_title7_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title7_box1').content_fr
        section2_intro1_title8 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title8').content_fr
        section2_intro1_title8_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section2_intro1_title8_box1').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_intro1').content_fr
        section3_intro1_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos', role='section3_intro1_box1').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_assyst_pos_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_assyst_pos.html', locals())

def pharmacy_our_solutions_assyst_pos_qc(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='page_title').content_en
        sections1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='sections1_intro1').content_en
        sections1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='sections1_intro2').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2').content_en
        section2_intro2_title1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title1').content_en
        section2_intro2_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box1').content_en
        section2_intro2_title2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title2').content_en
        section2_intro2_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box2').content_en
        section2_intro2_title3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title3').content_en
        section2_intro2_box3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box3').content_en
        section2_intro2_title4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title4').content_en
        section2_intro2_box4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box4').content_en
        section2_intro2_title5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title5').content_en
        section2_intro2_box5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box5').content_en
        section2_intro2_title6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title6').content_en
        section2_intro2_box6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box6').content_en
        section2_intro2_title7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title7').content_en
        section2_intro2_box7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box7').content_en
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_box1').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='page_title').content_fr
        sections1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='sections1_intro1').content_fr
        sections1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='sections1_intro2').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2').content_fr
        section2_intro2_title1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title1').content_fr
        section2_intro2_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box1').content_fr
        section2_intro2_title2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title2').content_fr
        section2_intro2_box2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box2').content_fr
        section2_intro2_title3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title3').content_fr
        section2_intro2_box3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box3').content_fr
        section2_intro2_title4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title4').content_fr
        section2_intro2_box4 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box4').content_fr
        section2_intro2_title5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title5').content_fr
        section2_intro2_box5 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box5').content_fr
        section2_intro2_title6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title6').content_fr
        section2_intro2_box6 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box6').content_fr
        section2_intro2_title7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_title7').content_fr
        section2_intro2_box7 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section2_intro2_box7').content_fr
        section3_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_pos_qc', role='section3_box1').content_fr

    #Set context dictionary
    context.update({

        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_assyst_pos_qc_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_assyst_pos_qc.html', locals())

def pharmacy_our_solutions_assyst_net(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section2_intro1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='our_solutions_assyst_net', role='section2_intro1').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_assyst_net_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_our_solutions_assyst_net.html', locals())

def pharmacy_reviews (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro4').content_en
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='reviews', role='section2_intro1').content_en
    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='pharmacy', page='reviews', role='section1_intro4').content_fr
        section2_intro1 = Content_item.objects.get(section='pharmacy', page='reviews', role='section2_intro1').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_reviews_class' : 'current_page_item',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_reviews.html', locals())

def pharmacy_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'pharmacy-management' if lang == 'EN' else 'solutions-de-gestion-de-pharmacies'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'pm_sales_support' : 'Sales support',
            'pm_contact_th' : 'Contact TELUS Health',

            'pm_call_us' : 'Call us',
            'pm_call_us_tel' : '1-800-363-9398',
            'pm_call_us_hours' : '7:00am to 10:00pm (EST) (M-F)<br> 8:00am to 10:00pm (EST) (W-E)',

        }

    elif lang == 'FR':

        short_copy = {

            'pm_sales_support' : 'Soutien aux ventes',
            'pm_contact_th' : 'Contactez TELUS Santé',

            'pm_call_us' : 'Appelez-nous',
            'pm_call_us_tel' : '1-800-363-9398',
            'pm_call_us_hours' : 'De 7 h à 22 h du lundi au vendredi, heure de l’Est <br />De 8 h à 22 h samedi et dimanche, heure de l’Est',

        }

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_sales.html', locals())

def pharmacy_support (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'pharmacy-management' if lang == 'EN' else 'solutions-de-gestion-de-pharmacies'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'pm_technical_support' : 'Technical support',
            'pm_other_support' : {
                'title' : 'Other support',
                'text' : 'For all non-technical support request please click here.',
                'url' : '?solution=non-technical'
                },

            "pm_assys_network_plus" : { 'text' : "Assyst Network Plus", 'url' : '?solution=assyst-network' },
            "pm_assyst_pos" : { 'text' : "Assyst Point-of-sale", 'url' : '?solution=assyst-point-sale-assyst-pos' },
            "pm_assyst_pos_qc" : { 'text' : "Assyst Point-of-sale (Quebec)", 'url' : '?solution=assyst-point-sale-quebec-assyst-pos-quebec' },
            "pm_assyst_rx" : { 'text' : "Assyst Rx", 'url' : '?solution=assyst-rx' },
            "pm_accuscrip" : { 'text' : "Assyst Rx-A (AccuScrip)", 'url' : '?solution=assyst-rx-accuscrip' },
            "pm_flexipharm" : { 'text' : "Assyst Rx-F (Flexipharm)", 'url' : '?solution=assyst-rx-f-flexipharm' },
            "pm_ah" : { 'text' : "Assyst Rx-H (AH)", 'url' : '?solution=assyst-rx-h' },
            "pm_mentor" : { 'text' : "Assyst Rx-M (Mentor)", 'url' : '?solution=assyst-rx-m' },
            "pm_qs_1" : { 'text' : "Assyst Rx-Q (QS 1)", 'url' : '?solution=assyst-rx-q' },
            "pm_simplicity" : { 'text' : "Assyst Rx-S (Simplicity +)", 'url' : '?solution=assyst-rx-s-simplicity' },
            "pm_trex" : { 'text' : "Assyst Rx-T (T Rex One)", 'url' : '?solution=assyst-rx-t-t-rex-one' },
            "pm_do_pill" : { 'text' : "DO-Pill", 'url' : '?solution=pill' },
            "pm_pharma_space" : { 'text' : "Pharma Space", 'url' : '?solution=pharma-space' },
            "pm_rx_vigilance" : { 'text' : "Rx Vigilance", 'url' : '?solution=rx-vigilance' },
            "pm_ubik" : { 'text' : "Ubik", 'url' : '?solution=telus-ubik' },
            "pm_xpill" : { 'text' : "xPill PHARMA", 'url' : '?solution=xpill' },

        }

    elif lang == 'FR':

        short_copy = {

            'pm_technical_support' : 'Support technique',
            'pm_other_support' : {
                'title' : 'Autre soutien',
                'text' : 'Pour toute autre demande non-technique, veuillez cliquer ici.',
                'url' : '?solution=non-technique'
                },

            "pm_assys_network_plus" : { 'text' : "Assyst Réseau Plus", 'url' : '?solution=assyst-reseau-plus' },
            "pm_assyst_pos" : { 'text' : "Assyst Point de vente", 'url' : '?solution=assyst-point-de-vente' },
            "pm_assyst_pos_qc" : { 'text' : "Assyst Point de vente (Qc)", 'url' : '?solution=assyst-point-de-vente-qc' },
            "pm_assyst_rx" : { 'text' : "Assyst Rx", 'url' : '?solution=assyst-rx' },
            "pm_accuscrip" : { 'text' : "Assyst Rx-A (AccuScrip)", 'url' : '?solution=assyst-rx-a' },
            "pm_flexipharm" : { 'text' : "Assyst Rx-F (Flexipharm)", 'url' : '?solution=assyst-rx-f' },
            "pm_ah" : { 'text' : "Assyst Rx-H (AH)", 'url' : '?solution=assyst-rx-h' },
            "pm_mentor" : { 'text' : "Assyst Rx-M (Mentor)", 'url' : '?solution=assyst-rx-m' },
            "pm_qs_1" : { 'text' : "Assyst Rx-Q (QS 1)", 'url' : '?solution=assyst-rx-q' },
            "pm_simplicity" : { 'text' : "Assyst Rx-S (Simplicity +)", 'url' : '?solution=assyst-rx-s' },
            "pm_trex" : { 'text' : "Assyst Rx-T (T Rex One)", 'url' : '?solution=assyst-rx-t' },
            "pm_do_pill" : { 'text' : "DO-Pill", 'url' : '?solution=do-pill' },
            "pm_pharma_space" : { 'text' : "Espace pharma", 'url' : '?solution=espace-pharma' },
            "pm_rx_vigilance" : { 'text' : "Rx Vigilance", 'url' : '?solution=rx-vigilance' },
            "pm_ubik" : { 'text' : "Ubik (Qc)", 'url' : '?solution=ubik' },
            "pm_xpill" : { 'text' : "xPill PHARMA (Qc)", 'url' : '?solution=xpill-pharma' },

        }

    #Get base generic context
    context = pharmacy_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/pharmacy/pharmacy_support.html', locals())

######################################################################################################################
#Claims and Benefits Management
######################################################################################################################

def cbm_home (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_solutions_for_everyone' : 'Solutions for everyone',
            'cbm_solutions_for_everyone_sub' : "TELUS Health offers a complete selection of claims and benefits management solutions.",

            'cbm_learn_more' : 'Learn more',

            'cbm_for_ie' : {
                'title' : 'For Insurers and Employers',
                'text' : "An efficient and cost-effective way for insurers and employers to manage drug, dental and extended health claims.",
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/overview/'

                },

            'cbm_for_ahp' : {
                'title' : 'For Allied Healthcare Providers',
                'text' : "Submit claims on behalf of your patients and reduce their out-of-pocket expenses while you reduce your transaction fees.",
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/overview/'

                },

            'cbm_for_wcb' : {
                'title' : 'For Workers’ Compensation Boards',
                'text' : "Accelerate efficiencies and improve the quality of service, both for injured workers and their healthcare providers.",
                'url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/overview/'

                },

            'for_pharmacists' : 'For Pharmacists',
            'for_pharmacists_text' : "Access all manuals, documents, and forms needed to submit your patients’ claims.",

            'support_docs_pharmacists' : {
                'text' : 'Support documents for pharmacists',
                'url' : '/support-documents-pharmacists/'
                },

            'provider_info' : {
                'text' : 'PSHCP Provider Information',
                'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/overview/'
                }

        }

    elif lang == 'FR':

        short_copy = {

            'cbm_solutions_for_everyone' : 'Des solutions pour tous',
            'cbm_solutions_for_everyone_sub' : "TELUS Santé offre des solutions de gestion des demandes de règlement en santé qui proposent aux assureurs une façon économique, simple et efficace de gérer les demandes de règlement de médicaments, de soins dentaires et de soins complémentaires, de même que la facturation pour l’indemnisation des travailleurs.",

            'cbm_learn_more' : 'En savoir plus',

            'cbm_for_ie' : {
                'title' : 'Pour les assureurs et employeurs',
                'text' : "Propose aux assureurs et employeurs une façon économique, simple et efficace de gérer les demandes de règlement.",
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/apercu/'

                },

            'cbm_for_ahp' : {
                'title' : 'Pour fournisseurs de soins de santé affiliés',
                'text' : "Soumettez les demandes de règlement pour vos patients et jouissez de remboursements plus rapides.",
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/apercu/'

                },

            'cbm_for_wcb' : {
                'title' : 'Pour commissions des accidents de travail',
                'text' : "Améliorez la qualité du service offert, autant pour les travailleurs blessés que les professionnels qui leur fournissent des soins.",
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/apercu/'

                },

            'for_pharmacists' : 'Pour pharmaciens',
            'for_pharmacists_text' : "Partout au Canada, nous transportons les demandes de règlement au nom des assureurs et payeurs canadiens et transmettons des millions de demandes de règlement de médicaments chaque année.",

            'support_docs_pharmacists' : {
                'text' : 'Documents de soutien pour pharmaciens',
                'url' : '/documents-soutien-pharmaciens/'
                },

            'provider_info' : {
                'text' : 'Renseignements sur le fournisseur du RSSFP',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/apercu/'
                }

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({


    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/cbm_home.html', locals())


# For Insurers and Employers
def cbm_iande_base(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contact us today',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/overview/'
            },

            'benefits' : {
                'text' : 'Benefits',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/benefits/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/'
            },

            'contact_us' : {
                'text' : 'Contact us',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/support/'
            },

            'drug_claims_for_insurers' : {
                'text' : 'Drug Claims for Insurers',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-dental-extended-claims-insurers/'
            },

            'drug_coverage_validation' : {
                'text' : 'Drug Coverage Validation',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-coverage-validation/'
            },

            'dental_claims' : {
                'text' : 'Dental Claims',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/dental-claims/'
            },

            'extended_healthcare_claims' : {
                'text' : 'Extended Healthcare Claims',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/extended-healthcare-claims/'
            },

            'eclaims_insurers' : {
                'text' : 'eClaims for Insurers',
                'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/eclaims/'
            },

            'section_sales_url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/apercu/'
            },

            'benefits' : {
                'text' : 'Avantages',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/avantages/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/nos-solutions/'
            },

            'contact_us' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/soutien-technique/'
            },

            'drug_claims_for_insurers' : {
                'text' : 'Demandes de règlement de médicaments pour assureurs',
                'url' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-medicaments-soins-dentaires-et-de-sante-complementaires-assureurs/'
            },

            'drug_coverage_validation' : {
                'text' : 'Validation de la couverture d’assurance médicaments',
                'url' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/validation-de-la-couverture-dassurance-medicaments/'
            },

            'dental_claims' : {
                'text' : 'Demandes de règlement pour soins dentaires',
                'url' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-dentaires/'
            },

            'extended_healthcare_claims' : {
                'text' : 'Demandes de règlement pour soins complémentaires',
                'url' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-complementaires/'
            },

            'eclaims_insurers' : {
                'text' : 'eRéclamations pour assureurs',
                'url' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-en-ligne/'
            },

            'section_sales_url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/ventes/',

        }

    #Set base context dictionary
    cbm_iande_context = {

        'section_solutions_category' : 5,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_benefits_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_sales_class'                      : '',
        'menu_support_class'                    : '',

        'submenu_our_solutions_class'                   : 'style=display:none!important',
        'submenu_our_solutions_drug_dental_class'       : '',
        'submenu_our_solutions_drug_coverage_class'     : '',
        'submenu_our_solutions_dental_claims_class'     : '',
        'submenu_our_solutions_extended_class'          : '',
        'submenu_our_solutions_eclaims_class'           : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(cbm_iande_context)
    context.update(short_copy)

    return context

def cbm_iande_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        cbm_iande_overview_more_benefits = {
            'text' : 'Discover more benefits',
            'url' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/benefits/',
            }

        section1_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro3').content_en
        #section3_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section3_intro1').content_en
    elif lang == "FR":
        cbm_iande_overview_more_benefits = {
            'text' : "Découvrez plus d’avantages",
            'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/assureurs-et-employeurs/avantages/',
            }

        section1_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_overview', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_overview', role='section2_intro3').content_fr
        #section3_title = Content_item.objects.get(section='cbm', page='iande_overview', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_overview', role='section3_intro1').content_fr


    #Set context dictionary
    context.update({
        #
        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking': True,
    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]
    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_overview.html', locals())

def cbm_iande_benefits(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_intro1').content_en
        section2_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box3').content_en
        section3_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box2').content_en
        section3_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box3').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section1_box3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_intro1').content_fr
        section2_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section2_box3').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box2').content_fr
        section3_box3 = Content_item.objects.get(section='cbm', page='iande_benefits', role='section3_box3').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_benefits_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_benefits.html', locals())

def cbm_iande_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        cbm_iande_our_solutions_links = {
            'eclaims' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/eclaims/",
            'extended_claims' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/extended-healthcare-claims/",
            'dental_claims' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/dental-claims/",
            'drug_coverage' : '/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-coverage-validation/',
            'drug_dental' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-dental-extended-claims-insurers/"
            }
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro5').content_en
    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='cbm', page='iande_our_solutions', role='section1_intro5').content_fr
        cbm_iande_our_solutions_links = {
            'eclaims' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-en-ligne/",
            'extended_claims' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-complementaires/",
            'dental_claims' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-dentaires/",
            'drug_coverage' : '/solutions-sante/assureurs-et-employeurs/nos-solutions/validation-de-la-couverture-dassurance-medicaments/',
            'drug_dental' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-medicaments-soins-dentaires-et-de-sante-complementaires-assureurs/"
            }
    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta'                    : False,
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions.html', locals())

def cbm_iande_our_solutions_drug_dental(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_intro2').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section2_intro2').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section3_intro2').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section4_intro1').content_en
        section4_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section4_intro2').content_en
        section5_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_intro1').content_en
        section5_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_intro2').content_en
        section6_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro1').content_en
        section6_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro2').content_en
        section6_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_link1').content_en
        section6_link2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_link2').content_en
        section6_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro3').content_en
        section7_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section7_intro1').content_en
        section7_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section7_intro2').content_en
        section8_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section8_intro1').content_en
        section8_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section8_intro2').content_en
        section9_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section9_intro1').content_en
        section9_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section9_intro2').content_en
        section1_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_link1').content_en
        top_button = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='top_button').content_en
        section5_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_link1').content_en
        section5_link2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_link2').content_en
    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_intro2').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section2_intro2').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section3_intro2').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section4_intro1').content_fr
        section4_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section4_intro2').content_fr
        section5_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_intro1').content_fr
        section5_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_intro2').content_fr
        section6_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro1').content_fr
        section6_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro2').content_fr
        section6_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_link1').content_fr
        section6_link2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_link2').content_fr
        section6_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section6_intro3').content_fr
        section7_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section7_intro1').content_fr
        section7_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section7_intro2').content_fr
        section8_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section8_intro1').content_fr
        section8_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section8_intro2').content_fr
        section9_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section9_intro1').content_fr
        section9_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section9_intro2').content_fr
        section1_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section1_link1').content_fr
        top_button = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='top_button').content_fr
        section5_link1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_link1').content_fr
        section5_link2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_dental', role='section5_link2').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_drug_dental_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions_drug_dental.html', locals())

def cbm_iande_our_solutions_drug_coverage(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section3_intro1').content_en
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section4_intro1').content_en
        video = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='video').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section3_intro1').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='section4_title').content_fr
        video = Content_item.objects.get(section='cbm', page='iande_our_solutions_drug_coverage', role='video').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_drug_coverage_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions_drug_coverage.html', locals())

def cbm_iande_our_solutions_dental_claims(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section4_intro1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_dental_claims', role='section4_intro1').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_dental_claims_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions_dental_claims.html', locals())

def cbm_iande_our_solutions_extended_healthcare(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro3').content_en
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section4_intro1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section3_intro3').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_extended_healthcare', role='section4_intro1').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_extended_class'          : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions_extended_healthcare.html', locals())

def cbm_iande_our_solutions_eclaims(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section2_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section3_intro2').content_en
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_intro1').content_en
        section4_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_intro2').content_en
        section5_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section5_intro1').content_en
        section6_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section6_title').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section2_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section3_intro2').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_intro1').content_fr
        section4_intro2 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section4_intro2').content_fr
        section5_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section5_intro1').content_fr
        section6_title = Content_item.objects.get(section='cbm', page='iande_our_solutions_eclaims', role='section6_title').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_eclaims_class'           : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_our_solutions_eclaims.html', locals())

def cbm_iande_sales(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_iande_sales_support' : 'Sales support',
            'cbm_iande_contact_thps' : 'Contact TELUS Health',
            'cbm_iande_call_us' : 'Call us',
            'cbm_iande_tel' : '1-888-709-8759',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_iande_sales_support' : 'Soutien aux ventes',
            'cbm_iande_contact_thps' : 'Contactez TELUS Santé',
            'cbm_iande_call_us' : 'Appelez-nous',
            'cbm_iande_tel' : '1-888-709-8759',

            }

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_sales.html', locals())

def cbm_iande_support(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_iande_technical_support' : 'Technical support',
            'cbm_iande_contact_thps' : 'Contact TELUS Health',
            'cbm_iande_call_us' : 'Call us',
            'cbm_iande_tel' : '1-888-709-8759',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_iande_sales_support' : 'Support technique',
            'cbm_iande_contact_thps' : 'Contactez TELUS Santé',
            'cbm_iande_call_us' : 'Appelez-nous',
            'cbm_iande_tel' : '1-888-709-8759',

            }

    #Get base generic context
    context = cbm_iande_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/insurers_employers/cbm_iande_support.html', locals())

#For Allied Healthcare Providers

def cbm_ahp_base(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'register_now' : {
                'text' : 'Register now',
                'url' : 'https://www.telushealth.co/eclaims'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/overview/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/'
            },

            'reviews' : {
                'text' : 'Reviews',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/reviews/'
            },

            'contact_us' : {
                'text' : 'Contact us',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/support/'
            },

            'eclaims_allied_healthcare_providers' : {
                'text' : 'eClaims for Allied Healthcare Providers',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/eclaims-allied-healthcare-providers/'
            },

            'wsib_eservices' : {
                'text' : 'WSIB eServices',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/wsib-eservices/'
            },

            'worksafebc_providers' : {
                'text' : 'WorkSafeBC providers',
                'url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/worksafe-bc-providers/'
            },

            'section_sales_url' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'register_now' : {
                'text' : 'Inscrivez-vous',
                'url' : 'https://www.telussante.co/eclaims'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/apercu/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/nos-solutions/'
            },

            'reviews' : {
                'text' : 'On en parle',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/on-en-parle/'
            },

            'contact_us' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/soutien-technique/'
            },

            'eclaims_allied_healthcare_providers' : {
                'text' : 'eRéclamations pour soins complémentaires',
                'url' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/nos-solutions/demandes-de-reglement-en-ligne-soins-complementaires/'
            },

            'wsib_eservices' : {
                'text' : 'CSPAAT – services en ligne',
                'url' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/cspaat-services-en-ligne/'
            },

            'worksafebc_providers' : {
                'text' : 'WorkSafe BC – fournisseur',
                'url' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/worksafe-bc-fournisseus/'
            },

            'section_sales_url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/ventes/',

        }

    #Set base context dictionary
    cbm_ahp_context = {

        'section_solutions_category' : 4,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_reviews_class'                    : '',
        'menu_sales_class'                      : '',
        'menu_support_class'                    : '',

        'submenu_our_solutions_class'                   : 'style=display:none!important',
        'submenu_our_solutions_eclaims_class'           : '',
        'submenu_our_solutions_worksafebc_class'        : '',
        'submenu_our_solutions_wsib_class'              : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(cbm_ahp_context)
    context.update(short_copy)

    return context

def cbm_ahp_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":

        section1_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_intro2').content_en
        section1_box1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_box1').content_en
        section2_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section2_title').content_en
        section3_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_box1').content_en
        read_more_testimonials_url = "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/reviews/"
    if lang == "FR":

        section1_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_intro2').content_fr
        section1_box1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section1_box1').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section2_title').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='cbm', page='ahp_overview', role='section3_box1').content_fr
        read_more_testimonials_url = "/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/on-en-parle/"

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    #Set context dictionary
    context.update({
        #
        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking'                  : True,
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_overview.html', locals())

def cbm_ahp_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro3').content_en
        result = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='result').content_en
        button = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='button').content_en
        ahp_our_solutions_links = {
            'eclaims' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/eclaims-allied-healthcare-providers/',
            'wsib' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/wsib-eservices/',
            'worksafebc' : '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/worksafe-bc-providers/'
            }
    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='section1_intro3').content_fr
        result = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='result').content_fr
        button = Content_item.objects.get(section='cbm', page='ahp_our_solutions', role='button').content_fr
        ahp_our_solutions_links = {
            'eclaims' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/nos-solutions/demandes-de-reglement-en-ligne-soins-complementaires/',
            'wsib' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/cspaat-services-en-ligne/',
            'worksafebc' : '/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/worksafe-bc-fournisseus/'
            }

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta'                    : False,
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_our_solutions.html', locals())

def cbm_ahp_our_solutions_eclaims(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro3').content_en
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_title').content_en
        section4_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_intro1').content_en
        section4_box1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_box1').content_en
        section5_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section5_intro1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_intro3').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section3_title').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_intro1').content_fr
        section4_box1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section4_box1').content_fr
        section5_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_eclaims', role='section5_intro1').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_eclaims_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_our_solutions_eclaims.html', locals())

def cbm_ahp_our_solutions_wsib (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro1').content_en
        section1_link1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_link1').content_en
        section1_link2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_link2').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro4').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro1').content_fr
        section1_link1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_link1').content_fr
        section1_link2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_link2').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_wsib', role='section1_intro4').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_wsib_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_our_solutions_wsib.html', locals())

def cbm_ahp_our_solutions_worksafebc (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        worksafebc_support_link = '/health-solutions/claims-and-benefits-management/allied-healthcare-providers/support-worksafebc/'
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro3').content_en
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section3_title').content_en
        section4_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_intro1').content_en
        section4_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_intro2').content_en
        section5_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section5_intro1').content_en
        section4_box1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_box1').content_en
        video = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='video').content_en

        section6_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section6_title').content_en
        section6_text = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section6_text').content_en
        section7_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section7_title').content_en

    elif lang == "FR":
        worksafebc_support_link = '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/prestataires-de-soins-de-sante-affilies/soutien-technique-worksafebc/'
        section1_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section2_intro3').content_fr
        section3_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section3_title').content_fr
        section4_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_intro1').content_fr
        section4_intro2 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_intro2').content_fr
        section5_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section5_intro1').content_fr
        section4_box1 = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section4_box1').content_fr
        video = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='video').content_fr

        section6_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section6_title').content_fr
        section6_text = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section6_text').content_fr
        section7_title = Content_item.objects.get(section='cbm', page='ahp_our_solutions_worksafebc', role='section7_title').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class'                 : '',
        'submenu_our_solutions_worksafebc_class'     : 'active',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_our_solutions_worksafebc.html', locals())

def cbm_ahp_reviews (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box1').content_en
        section1_link1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro2').content_en
        section1_box2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box2').content_en
        section1_link2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro3').content_en
        section1_box3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box3').content_en
        section1_link3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link3').content_en
        section1_intro4 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro4').content_en
        section1_box4 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box4').content_en
        section1_intro5 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro5').content_en
        section1_box5 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box5').content_en
        section1_intro6 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro6').content_en
        section1_box6 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box6').content_en


    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box1').content_fr
        section1_link1 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro2').content_fr
        section1_box2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box2').content_fr
        section1_link2 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro3').content_fr
        section1_box3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box3').content_fr
        section1_link3 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_link3').content_fr
        section1_intro4 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro4').content_fr
        section1_box4 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box4').content_fr
        section1_intro5 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro5').content_fr
        section1_box5 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box5').content_fr
        section1_intro6 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_intro6').content_fr
        section1_box6 = Content_item.objects.get(section='cbm', page='ahp_reviews', role='section1_box6').content_fr

    #Set context dictionary
    context.update({
        #'page_title' : page_title,
        'menu_reviews_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_reviews.html', locals())

def cbm_ahp_sales(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_ahp_sales_support' : 'Sales support',
            'cbm_ahp_contact_thps' : 'Contact TELUS Health',
            'cbm_ahp_call_us' : 'Call us',
            'cbm_ahp_tel' : '1-866-240-7492',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_ahp_sales_support' : 'Soutien aux ventes',
            'cbm_ahp_contact_thps' : 'Contactez TELUS Santé',
            'cbm_ahp_call_us' : 'Appelez-nous',
            'cbm_ahp_tel' : '1-866-240-7492',

            }

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_sales.html', locals())

def cbm_ahp_support(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_ahp_technical_support' : 'Technical support',
            'cbm_ahp_contact_thps' : 'Contact TELUS Health',
            'cbm_ahp_call_us' : 'Call us',
            'cbm_ahp_tel' : '1-866-240-7492',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_ahp_technical_support' : 'Support technique',
            'cbm_ahp_contact_thps' : 'Contactez TELUS Santé',
            'cbm_ahp_call_us' : 'Appelez-nous',
            'cbm_ahp_tel' : '1-866-240-7492',

            }

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_support.html', locals())

def cbm_ahp_worksafebc_support(request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {
            'cbm_ahp_technical_support' : 'Technical support for WorkSafeBC providers',
            'cbm_ahp_contact_thps' : 'Contact TELUS Health',
            'cbm_ahp_call_us' : 'Call us',
            'cbm_ahp_tel' : '1-855-284-5900',
            'cbm_ahp_hours' : '8:00am to 8:00pm (PST)',

            }

    elif lang == 'FR':

        short_copy = {
            'cbm_ahp_technical_support' : 'Soutien technique pour les fournisseurs WorkSafeBC',
            'cbm_ahp_contact_thps' : 'Contactez TELUS Santé',
            'cbm_ahp_call_us' : 'Appelez-nous',
            'cbm_ahp_tel' : '1-855-284-5900',
            'cbm_ahp_hours' : '8:00am to 8:00pm (PST)',

            }

    #Get base generic context
    context = cbm_ahp_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/allied-healthcare-providers/cbm_ahp_worksafebc_support.html', locals())

######

def cbm_wcb_base(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contact us today',
                'url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/overview/'
            },

            'contact_us' : {
                'text' : 'Contact us',
                'url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/support/'
            },

            'section_sales_url' : '/health-solutions/claims-and-benefits-management/workers-compensation-boards/sales/',


        }

    elif lang == 'FR':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/apercu/'
            },

            'contact_us' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/soutien-technique/'
            },

            'section_sales_url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/commissions-des-accidents-de-travail/ventes/',

        }

    #Set base context dictionary
    cbm_wcb_context = {

        'section_solutions_category'            : 6,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_sales_class'                      : '',
        'menu_support_class'                    : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(cbm_wcb_context)
    context.update(short_copy)

    return context

def cbm_wcb_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = cbm_wcb_base(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro3').content_en
        section2_title = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_intro1').content_en
        section2_box1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_box1').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section1_intro3').content_fr
        section2_title = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_intro1').content_fr
        section2_box1 = Content_item.objects.get(section='cbm', page='wcb_overview', role='section2_box1').content_fr

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    #Set context dictionary
    context.update({
        #
        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking'                  : True,
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/cbm/workers_compensation_boards/cbm_wcb_overview.html', locals())

def cbm_wcb_sales(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_wcb_sales_support' : 'Sales support',
            'cbm_wcb_contact_thps' : 'Contact TELUS Health',
            'cbm_wcb_call_us' : 'Call us',
            'cbm_wcb_tel' : '1-866-240-7492',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_wcb_sales_support' : 'Soutien aux ventes',
            'cbm_wcb_contact_thps' : 'Contactez TELUS Santé',
            'cbm_wcb_call_us' : 'Appelez-nous',
            'cbm_wcb_tel' : '1-866-240-7492',

            }

    #Get base generic context
    context = cbm_wcb_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    if lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/workers_compensation_boards/cbm_wcb_sales.html', locals())

def cbm_wcb_support(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'claims-and-benefits-management' if lang == 'EN' else 'gestion-des-demandes-de-reglement-en-sante'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'cbm_wcb_technical_support' : 'Technical support',
            'cbm_wcb_contact_thps' : 'Contact TELUS Health',
            'cbm_wcb_call_us' : 'Call us',
            'cbm_wcb_tel' : '1-866-240-7492',

            }

    elif lang == 'FR':

        short_copy = {

            'cbm_wcb_technical_support' : 'Support technique',
            'cbm_wcb_contact_thps' : 'Contactez TELUS Santé',
            'cbm_wcb_call_us' : 'Appelez-nous',
            'cbm_wcb_tel' : '1-866-240-7492',

            }

    #Get base generic context
    context = cbm_wcb_base(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/cbm/workers_compensation_boards/cbm_wcb_support.html', locals())

######################################################################################################################
# EHR
######################################################################################################################

def ehr_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contact sales today',
                'url' : '/health-solutions/electronic-health-records/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/electronic-health-records/overview/'
            },

            'benefits' : {
                'text' : 'Benefits',
                'url' : '/health-solutions/electronic-health-records/benefits/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/electronic-health-records/our-solutions/'
            },

            'reviews' : {
                'text' : 'Reviews',
                'url' : '/health-solutions/electronic-health-records/reviews/'
            },

            'contact_sales' : {
                'text' : 'Contact Sales',
                'url' : '/health-solutions/electronic-health-records/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/electronic-health-records/support/'
            },

            'health_integration_platform' : {
                'text' : 'Health Integration Platform',
                'url' : '/health-solutions/electronic-health-records/our-solutions/health-integration-platform/'
            },

            'drug_information_system' : {
                'text' : 'Drug Information System',
                'url' : '/health-solutions/electronic-health-records/our-solutions/drug-information-system/'
            },

            'oacis' : {
                'text' : 'OACIS',
                'url' : '/health-solutions/electronic-health-records/our-solutions/oacis-clinical-information-system/'
            },

            'ischeduler' : {
                'text' : 'iScheduler',
                'url' : '/health-solutions/electronic-health-records/our-solutions/ischeduler/'
            },

            'section_sales_url' : '/health-solutions/electronic-health-records/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/apercu/'
            },

            'benefits' : {
                'text' : 'Avantages',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/avantages/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/nos-solutions/'
            },

            'reviews' : {
                'text' : 'On en parle',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/on-en-parle/'
            },

            'contact_sales' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/soutien-technique/'
            },

            'health_integration_platform' : {
                'text' : 'Plateforme d’intégration des soins de santé',
                'url' : '/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/plateforme-dintegration-des-soins-de-sante'
            },

            'drug_information_system' : {
                'text' : 'Système d’information sur les médicaments (SIM)',
                'url' : '/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/systeme-dinformation-sur-les-medicaments-sim/'
            },

            'oacis' : {
                'text' : 'OACIS',
                'url' : '/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/oacis-soins-cliniques/'
            },

            'ischeduler' : {
                'text' : 'iScheduler',
                'url' : '/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/ischeduler/'
            },

            'section_sales_url' : '/solutions-en-sante/dossiers-de-sante-electroniques/ventes/',

        }

    #Set base context dictionary
    ehr_base_context = {

        'section_solutions_category'            : 2,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_benefits_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_reviews_class'                    : '',
        'menu_contact_sales_class'              : '',
        'menu_customer_support_class'           : '',

        'submenu_our_solutions_class'           : 'style=display:none!important',
        'submenu_our_solutions_hip'             : '',
        'submenu_our_solutions_dis'             : '',
        'submenu_our_solutions_oasis'           : '',
        'submenu_our_solutions_ischeduler'      : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(ehr_base_context)
    context.update(short_copy)

    return context

def ehr_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ehr', page='overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro4').content_en
        section2_title = Content_item.objects.get(section='ehr', page='overview', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro3').content_en
        section2_box1 = Content_item.objects.get(section='ehr', page='overview', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='ehr', page='overview', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='ehr', page='overview', role='section2_box3').content_en
        section2_box4 = Content_item.objects.get(section='ehr', page='overview', role='section2_box4').content_en
        section3_title = Content_item.objects.get(section='ehr', page='overview', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='ehr', page='overview', role='section3_box1').content_en
        more = Content_item.objects.get(section='ehr', page='overview', role='more').content_en
        testimony = Content_item.objects.get(section='ehr', page='overview', role='testimony').content_en

    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ehr', page='overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='ehr', page='overview', role='section1_intro4').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='overview', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='ehr', page='overview', role='section2_intro3').content_fr
        section2_box1 = Content_item.objects.get(section='ehr', page='overview', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='ehr', page='overview', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='ehr', page='overview', role='section2_box3').content_fr
        section2_box4 = Content_item.objects.get(section='ehr', page='overview', role='section2_box4').content_fr
        section3_title = Content_item.objects.get(section='ehr', page='overview', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='ehr', page='overview', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='ehr', page='overview', role='section3_box1').content_fr
        more = Content_item.objects.get(section='ehr', page='overview', role='more').content_fr
        testimony = Content_item.objects.get(section='ehr', page='overview', role='testimony').content_fr

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    #Set context dictionary
    context.update({
        #
        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking' : True,
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_overview.html', locals())

def ehr_benefits(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    if lang == "EN":
        #Get page specific content
        #
        section1_title = Content_item.objects.get(section='ehr', page='benefits', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box3').content_en
        section2_title = Content_item.objects.get(section='ehr', page='benefits', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section2_intro1').content_en
        section2_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box3').content_en
        section3_title = Content_item.objects.get(section='ehr', page='benefits', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box2').content_en
        section3_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box3').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='ehr', page='benefits', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section1_box3').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='benefits', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section2_intro1').content_fr
        section2_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section2_box3').content_fr
        section3_title = Content_item.objects.get(section='ehr', page='benefits', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='ehr', page='benefits', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box2').content_fr
        section3_box3 = Content_item.objects.get(section='ehr', page='benefits', role='section3_box3').content_fr

    #Set context dictionary
    context.update({
        'page_title':'page_title',
        'menu_benefits_class' : 'current_page_item',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_benefits.html', locals())

def ehr_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        ehr_our_solutions_links = {
            'hip' : "/health-solutions/electronic-health-records/our-solutions/health-integration-platform/",
            'dis' : "/health-solutions/electronic-health-records/our-solutions/drug-information-system/",
            'oacis' : "/health-solutions/electronic-health-records/our-solutions/oacis-clinical-information-system/",
            'ischeduler' : "/health-solutions/electronic-health-records/our-solutions/ischeduler/"
        }
        section1_title1 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title1').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro2').content_en
        section1_title2 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title2').content_en
        section1_intro3 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro3').content_en
        section1_title3 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title3').content_en
        section1_intro4 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro4').content_en
        learnMore = Content_item.objects.get(section='ehr', page='our_solutions', role='learnMore').content_en
        segments = Content_item.objects.get(section='ehr', page='our_solutions', role='segments').content_en
        results = Content_item.objects.get(section='ehr', page='our_solutions', role='results').content_en
        regoins = Content_item.objects.get(section='ehr', page='our_solutions', role='regions').content_en
    elif lang == "FR":
        ehr_our_solutions_links = {
            'hip' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/plateforme-dintegration-des-soins-de-sante/",
            'dis' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/systeme-dinformation-sur-les-medicaments-sim/",
            'oacis' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/oacis-soins-cliniques/",
            'ischeduler' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/ischeduler/"
        }
        section1_title1 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title1').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro2').content_fr
        section1_title2 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title2').content_fr
        section1_intro3 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro3').content_fr
        section1_title3 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_title3').content_fr
        section1_intro4 = Content_item.objects.get(section='ehr', page='our_solutions', role='section1_intro4').content_fr
        learnMore = Content_item.objects.get(section='ehr', page='our_solutions', role='learnMore').content_fr
        segments = Content_item.objects.get(section='ehr', page='our_solutions', role='segments').content_fr
        results = Content_item.objects.get(section='ehr', page='our_solutions', role='results').content_fr
        regoins = Content_item.objects.get(section='ehr', page='our_solutions', role='regions').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_our_solutions.html', locals())


def ehr_our_solutions_hip(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section1_intro1').content_en
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro3').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section1_intro1').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_hip', role='section2_intro3').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_hip_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_our_solutions_hip.html', locals())

def ehr_our_solutions_dis(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section1_intro1').content_en
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro3').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section1_intro1').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_dis', role='section2_intro3').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_dis_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_our_solutions_dis.html', locals())

def ehr_our_solutions_oacis(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section1_intro1').content_en
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section2_intro1').content_en
        section3_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro2').content_en
        section3_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro3').content_en
        section3_box1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_box2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section1_intro1').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section2_intro1').content_fr
        section3_title = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro2').content_fr
        section3_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_intro3').content_fr
        section3_box1 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='ehr', page='our_solutions_oacis', role='section3_box2').content_fr

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_oacis_class' : 'active',
        'show_solutions_cta' : True,
        'show_latest_thinking' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_our_solutions_oacis.html', locals())

def ehr_our_solutions_ischeduler(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro5').content_en
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro3').content_en
        section2_box1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box3').content_en
        section3_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section3_intro1').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section1_intro5').content_fr
        section2_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_intro3').content_fr
        section2_box1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section2_box3').content_fr
        section3_title = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='ehr', page='our_solutions_ischeduler', role='section3_intro1').content_fr

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_ischeduler_class' : 'active',
        'show_solutions_cta' : True,
        'show_latest_thinking' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_our_solutions_ischeduler.html', locals())

def ehr_reviews (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_intro1 = Content_item.objects.get(section='ehr', page='reviews', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='ehr', page='reviews', role='section1_box1').content_en
        section2_intro1 = Content_item.objects.get(section='ehr', page='reviews', role='section2_intro1').content_en
        section2_box2 = Content_item.objects.get(section='ehr', page='reviews', role='section2_box2').content_en
        section3_intro3 = Content_item.objects.get(section='ehr', page='reviews', role='section3_intro3').content_en
        section3_box3 = Content_item.objects.get(section='ehr', page='reviews', role='section3_box3').content_en
        section4_intro4 = Content_item.objects.get(section='ehr', page='reviews', role='section4_intro4').content_en
        section4_box4 = Content_item.objects.get(section='ehr', page='reviews', role='section4_box4').content_en
        section5_intro5 = Content_item.objects.get(section='ehr', page='reviews', role='section5_intro5').content_en
        section5_box5 = Content_item.objects.get(section='ehr', page='reviews', role='section5_box5').content_en
        section6_intro6 = Content_item.objects.get(section='ehr', page='reviews', role='section6_intro6').content_en
        section6_box6 = Content_item.objects.get(section='ehr', page='reviews', role='section6_box6').content_en
        section7_intro7 = Content_item.objects.get(section='ehr', page='reviews', role='section7_intro7').content_en
        section7_box7 = Content_item.objects.get(section='ehr', page='reviews', role='section7_box7').content_en
        video = Content_item.objects.get(section='ehr', page='reviews', role='video').content_en
        information = Content_item.objects.get(section='ehr', page='reviews', role='information').content_en
    elif lang == "FR":
        section1_intro1 = Content_item.objects.get(section='ehr', page='reviews', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='ehr', page='reviews', role='section1_box1').content_fr
        section2_intro1 = Content_item.objects.get(section='ehr', page='reviews', role='section2_intro1').content_fr
        section2_box2 = Content_item.objects.get(section='ehr', page='reviews', role='section2_box2').content_fr
        section3_intro3 = Content_item.objects.get(section='ehr', page='reviews', role='section3_intro3').content_fr
        section3_box3 = Content_item.objects.get(section='ehr', page='reviews', role='section3_box3').content_fr
        section4_intro4 = Content_item.objects.get(section='ehr', page='reviews', role='section4_intro4').content_fr
        section4_box4 = Content_item.objects.get(section='ehr', page='reviews', role='section4_box4').content_fr
        section5_intro5 = Content_item.objects.get(section='ehr', page='reviews', role='section5_intro5').content_fr
        section5_box5 = Content_item.objects.get(section='ehr', page='reviews', role='section5_box5').content_fr
        section6_intro6 = Content_item.objects.get(section='ehr', page='reviews', role='section6_intro6').content_fr
        section6_box6 = Content_item.objects.get(section='ehr', page='reviews', role='section6_box6').content_fr
        section7_intro7 = Content_item.objects.get(section='ehr', page='reviews', role='section7_intro7').content_fr
        section7_box7 = Content_item.objects.get(section='ehr', page='reviews', role='section7_box7').content_fr
        video = Content_item.objects.get(section='ehr', page='reviews', role='video').content_fr
        information = Content_item.objects.get(section='ehr', page='reviews', role='information').content_fr

    #Set context dictionary
    context.update({

        'menu_reviews_class' : 'current_page_item',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ehr/ehr_reviews.html', locals())

def ehr_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'electronic-health-records' if lang == 'EN' else 'dossiers-de-sante-electroniques'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'ehr_sales_support' : 'Sales support',

            'ehr_dis' : {
                'text' : 'Drug Information System',
                'url' : '?solution=drug-information-system',
                },

            'ehr_ischeduler' : {
                'text' : 'iScheduler',
                'url' : '?solution=telus-ischeduler',
                },

            'ehr_oacis' : {
                'text' : 'OACIS',
                'url' : '?solution=oacis',
                },

            'ehr_hip' : {
                'text' : 'Health Integration Platform',
                'url' : '?solution=health-integration-platform',
                },

            'ehr_unsure' : {
                'text' : 'Unsure what to choose? Click here to find out which solution is right for you',
                'url' : '/health-solutions/electronic-health-records/our-solutions/',
                },

            }

    elif lang == 'FR':

        short_copy = {

            'ehr_sales_support' : 'Soutien aux ventes',

            'ehr_dis' : {
                'text' : 'Système d’information sur les médicaments (SIM)',
                'url' : '?solution=systeme-dinformation-sur-les-medicaments',
                },

            'ehr_ischeduler' : {
                'text' : 'iScheduler',
                'url' : '?solution=ischeduler',
                },

            'ehr_oacis' : {
                'text' : 'OACIS',
                'url' : '?solution=oacis',
                },

            'ehr_hip' : {
                'text' : 'Plateforme d’intégration des soins de santé',
                'url' : '?solution=plateforme-dintegration-des-soins-de-sante',
                },

            'ehr_unsure' : {
                'text' : 'Vous ne savez pas quoi choisir? Cliquez ici pour découvrir la solution qui vous convient le mieux',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/nos-solutions/',
                },

            }

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        #
        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/ehr/ehr_sales.html', locals())

#TODO: For Support, ask Earl why not only 1 form with drop down.
def ehr_support (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'electronic-health-records' if lang == 'EN' else 'dossiers-de-sante-electroniques'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'ehr_technical_support' : 'Technical support',

            'ehr_dis' : {
                'text' : 'Drug Information System',
                'url' : '?solution=drug-information-system',
                },

            'ehr_ischeduler' : {
                'text' : 'iScheduler',
                'url' : '?solution=telus-ischeduler',
                },

            'ehr_oacis' : {
                'text' : 'OACIS',
                'url' : '?solution=oacis',
                },

            'ehr_hip' : {
                'text' : 'Health Integration Platform',
                'url' : '?solution=health-integration-platform',
                },

            'ehr_unsure' : {
                'text' : 'Unsure what to choose? Click here to find out which solution is right for you',
                'url' : '/health-solutions/electronic-health-records/our-solutions/',
                },

            }

    elif lang == 'FR':

        short_copy = {

            'ehr_technical_support' : 'Support technique',

            'ehr_dis' : {
                'text' : 'Système d’information sur les médicaments (SIM)',
                'url' : '?solution=systeme-dinformation-sur-les-medicaments',
                },

            'ehr_ischeduler' : {
                'text' : 'iScheduler',
                'url' : '?solution=ischeduler',
                },

            'ehr_oacis' : {
                'text' : 'OACIS',
                'url' : '?solution=oacis',
                },

            'ehr_hip' : {
                'text' : 'Plateforme d’intégration des soins de santé',
                'url' : '?solution=health-integration-platform',
                },

            'ehr_unsure' : {
                'text' : 'Vous ne savez pas quoi choisir? Cliquez ici pour découvrir la solution qui vous convient le mieux',
                'url' : '/solutions-en-sante/dossiers-de-sante-electroniques/nos-solutions/',
                },

            }

    #Get base generic context
    context = ehr_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        #
        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/ehr/ehr_support.html', locals())


######################################################################################################################
# Patient and Consumer Health Platforms
######################################################################################################################

def pchp_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contact sales today',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/overview/'
            },

            'benefits' : {
                'text' : 'Benefits',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/benefits/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/our-solutions/'
            },

            'reviews' : {
                'text' : 'Reviews',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/reviews/'
            },

            'contact_sales' : {
                'text' : 'Contact Sales',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/support/'
            },

            'hhm' : {
                'text' : 'Home Health Monitoring (HHM)',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/our-solutions/home-health-monitoring/'
            },

            'phr' : {
                'text' : 'Personal Health Records (PHRs)',
                'url' : '/health-solutions/patient-and-consumer-health-platforms/our-solutions/personal-health-records/'
            },

            'section_sales_url' : '/health-solutions/patient-and-consumer-health-platforms/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/apercu/'
            },

            'benefits' : {
                'text' : 'Avantages',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/avantages/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/nos-solutions/'
            },

            'reviews' : {
                'text' : 'On en parle',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/on-en-parle/'
            },

            'contact_sales' : {
                'text' : 'Contactez les ventes',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/soutien-technique/'
            },

            'hhm' : {
                'text' : 'Télésoins à domicile',
                'url' : '/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/telesoins-domicile/'
            },

            'phr' : {
                'text' : 'Dossiers de santé personnels (DSP)',
                'url' : '/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/dossiers-de-sante-personnels-dsp/'
            },

            'section_sales_url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/ventes/',

        }

    #Set base context dictionary
    pchp_base_context = {

        'section_solutions_category'            : 9,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_benefits_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_reviews_class'                    : '',
        'menu_contact_sales_class'              : '',
        'menu_customer_support_class'           : '',

        'submenu_our_solutions_class'           : 'style=display:none!important',
        'submenu_our_solutions_hhm'             : '',
        'submenu_our_solutions_phr'             : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(pchp_base_context)
    context.update(short_copy)

    return context

def pchp_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":

        pchp_overview_links = {
            'benefits' : "/health-solutions/patient-and-consumer-health-platforms/benefits/",
            'reviews' : "/health-solutions/patient-and-consumer-health-platforms/reviews/"
        }

        section1_title = Content_item.objects.get(section='pchp', page='overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro4').content_en
        section2_title = Content_item.objects.get(section='pchp', page='overview', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro2').content_en
        section2_intro3 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro3').content_en
        section2_box1 = Content_item.objects.get(section='pchp', page='overview', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='pchp', page='overview', role='section2_box2').content_en
        section2_box3 = Content_item.objects.get(section='pchp', page='overview', role='section2_box3').content_en
        section2_box4 = Content_item.objects.get(section='pchp', page='overview', role='section2_box4').content_en
        section3_title = Content_item.objects.get(section='pchp', page='overview', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='pchp', page='overview', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='pchp', page='overview', role='section3_box2').content_en
    elif lang == "FR":

        pchp_overview_links = {
            'benefits' : "/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/avantages/",
            'reviews' : "/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/on-en-parle/"
        }

        section1_title = Content_item.objects.get(section='pchp', page='overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='pchp', page='overview', role='section1_intro4').content_fr
        section2_title = Content_item.objects.get(section='pchp', page='overview', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro2').content_fr
        section2_intro3 = Content_item.objects.get(section='pchp', page='overview', role='section2_intro3').content_fr
        section2_box1 = Content_item.objects.get(section='pchp', page='overview', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='pchp', page='overview', role='section2_box2').content_fr
        section2_box3 = Content_item.objects.get(section='pchp', page='overview', role='section2_box3').content_fr
        section2_box4 = Content_item.objects.get(section='pchp', page='overview', role='section2_box4').content_fr
        section3_title = Content_item.objects.get(section='pchp', page='overview', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pchp', page='overview', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='pchp', page='overview', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='pchp', page='overview', role='section3_box2').content_fr

    #Set context dictionary
    context.update({

        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking' : True,
    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/overview.html', locals())

def pchp_benefits(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":

        section1_title = Content_item.objects.get(section='pchp', page='benefits', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pchp', page='benefits', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='pchp', page='benefits', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pchp', page='benefits', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='pchp', page='benefits', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section3_intro1').content_en
    elif lang == "FR":

        section1_title = Content_item.objects.get(section='pchp', page='benefits', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pchp', page='benefits', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='pchp', page='benefits', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pchp', page='benefits', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='pchp', page='benefits', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pchp', page='benefits', role='section3_intro1').content_fr

    #Set context dictionary
    context.update({

        'menu_benefits_class' : 'current_page_item',

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/benefits.html', locals())

def pchp_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        pchp_our_solutions_links ={
            'hhm' : "/health-solutions/patient-and-consumer-health-platforms/our-solutions/home-health-monitoring/",
            'phr' : "/health-solutions/patient-and-consumer-health-platforms/our-solutions/personal-health-records/"
        }
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_intro2').content_en
    elif lang == "FR":
        pchp_our_solutions_links ={
            'hhm' : "/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/telesoins-domicile/",
            'phr' : "/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/dossiers-de-sante-personnels-dsp/"
        }
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pchp', page='our_solutions', role='section1_intro2').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/our_solutions.html', locals())

def pchp_our_solutions_hhm (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_box1').content_en
        section2_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_intro2').content_en
        section2_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_box1').content_en
        section2_box2 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_box2').content_en
        section3_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_box1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section1_box1').content_fr
        section2_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_intro2').content_fr
        section2_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_box1').content_fr
        section2_box2 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section2_box2').content_fr
        section3_title = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='pchp', page='our_solutions_hhm', role='section3_box1').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_hhm_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/our_solutions_hhm.html', locals())

def pchp_our_solutions_phr (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section1_intro1').content_en
        section2_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section2_intro1').content_en
        section3_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_intro2').content_en
        section3_box1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_box1').content_en
        section3_box2 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_box2').content_en
        section4_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section4_intro1').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section1_intro1').content_fr
        section2_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section2_intro1').content_fr
        section3_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_intro2').content_fr
        section3_box1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_box1').content_fr
        section3_box2 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section3_box2').content_fr
        section4_title = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='pchp', page='our_solutions_phr', role='section4_intro1').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_phr_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/our_solutions_phr.html', locals())

def pchp_reviews (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_intro1 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro4').content_en
        section2_intro1 = Content_item.objects.get(section='pchp', page='reviews', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='pchp', page='reviews', role='section2_intro2').content_en
    elif lang == "FR":
        #
        section1_intro1 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='pchp', page='reviews', role='section1_intro4').content_fr
        section2_intro1 = Content_item.objects.get(section='pchp', page='reviews', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='pchp', page='reviews', role='section2_intro2').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_reviews_class' : 'current_page_item',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pchp/reviews.html', locals())

def pchp_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'patient-and-consumer-health-platforms' if lang == 'EN' else 'plateformes-de-sante-pour-patients-et-grand-public'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'pchp_sales_support' : 'Sales support',

            'pchp_hhm' : {
                'text' : 'Home Health Monitoring (HHM)',
                'url' : '?solution=home-health-monitoring'

            },

            'pchp_phr' : {
                'text' : 'Personal Health Records (PHRs)',
                'url' : '?solution=personal-health-records'

            },

            'pchp_unsure' : {
                'text' : "Unsure what to choose? Click here to find out which solution is right for you",
                'url' : '/health-solutions/patient-and-consumer-health-platforms/our-solutions/'

            }

        }

    elif lang == 'FR':

        short_copy = {

            'pchp_sales_support' : 'Soutien aux ventes',

            'pchp_hhm' : {
                'text' : 'Télésoins à domicile',
                'url' : '?solution=telesoins-domicile'

            },

            'pchp_phr' : {
                'text' : 'Dossiers de santé personnels (DSP)',
                'url' : '?solution=dossiers-de-sante-personnels-dsp'

            },

            'pchp_unsure' : {
                'text' : "Vous ne savez pas quoi choisir? Cliquez ici pour découvrir la solution qui vous convient le mieux",
                'url' : '/solutions-en-sante/plateformes-de-sante-pour-patients-et-grand-public/nos-solutions/'

            }

        }

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/pchp/sales.html', locals())

#TODO: For Support, ask Earl why not only 1 form with drop down.
def pchp_support (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'patient-and-consumer-health-platforms' if lang == 'EN' else 'plateformes-de-sante-pour-patients-et-grand-public'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'pchp_technical_support' : 'Technical support',

            'pchp_hhm' : {
                'text' : 'Home Health Monitoring (HHM)',
                'url' : '?solution=home-health-monitoring'

            },

            'pchp_phr' : {
                'text' : 'Personal Health Records (PHRs)',
                'url' : '?solution=personal-health-records'

            },

        }

    elif lang == 'FR':

        short_copy = {

            'pchp_technical_support' : 'Support technique',

            'pchp_hhm' : {
                'text' : 'Télésoins à domicile',
                'url' : '?solution=telesoins-domicile'

            },

            'pchp_phr' : {
                'text' : 'Dossiers de santé personnels (DSP)',
                'url' : '?solution=dossiers-de-sante-personnels-dsp'

            },

        }

    #Get base generic context
    context = pchp_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/pchp/support.html', locals())

######################################################################################################################
# Patient and Consumer Health Platforms
######################################################################################################################

def ha_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contact us today',
                'url' : '/health-solutions/health-analytics/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/health-solutions/health-analytics/overview/'
            },

            'our_solutions' : {
                'text' : 'Our solutions',
                'url' : '/health-solutions/health-analytics/our-solutions/'
            },

            'contact_us' : {
                'text' : 'Contact us',
                'url' : '/health-solutions/health-analytics/sales/'
            },

            'customer_support' : {
                'text' : 'Customer support',
                'url' : '/health-solutions/health-analytics/support/'
            },

            'market_access_toolkit' : {
                'text' : 'Market Access Toolkit (MAT)',
                'url' : '/health-solutions/health-analytics/our-solutions/market-access-toolkit/'
            },

            'prism' : {
                'text' : 'PRISM',
                'url' : '/health-solutions/health-analytics/sales/'
            },

            'in_sites' : {
                'text' : 'In-Sites',
                'url' : '/health-solutions/health-analytics/sales/'
            },

            'analysis_consulting' : {
                'text' : 'Analysis and consulting',
                'url' : '/health-solutions/health-analytics/sales/'
            },

            'section_sales_url' : '/health-solutions/health-analytics/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_us_today' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/intelligence-daffaires/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/solutions-en-sante/intelligence-daffaires/apercu/'
            },

            'our_solutions' : {
                'text' : 'Nos solutions',
                'url' : '/solutions-en-sante/intelligence-daffaires/nos-solutions/'
            },

            'contact_us' : {
                'text' : 'Contactez-nous',
                'url' : '/solutions-en-sante/intelligence-daffaires/ventes/'
            },

            'customer_support' : {
                'text' : 'Service à la clientèle',
                'url' : '/solutions-en-sante/intelligence-daffaires/soutien-technique/'
            },

            'market_access_toolkit' : {
                'text' : 'Trousse d’accès au marché',
                'url' : '/solutions-sante/intelligence-daffaires/produits/trousse-dacces-au-marche/'
            },

            'prism' : {
                'text' : 'PRISM',
                'url' : '/solutions-en-sante/intelligence-daffaires/ventes/'
            },

            'in_sites' : {
                'text' : 'In-Sites',
                'url' : '/solutions-en-sante/intelligence-daffaires/ventes/'
            },

            'analysis_consulting' : {
                'text' : 'Analyse et consultation',
                'url' : '/solutions-en-sante/intelligence-daffaires/ventes/'
            },

            'section_sales_url' : '/solutions-en-sante/intelligence-daffaires/ventes/',

        }

    #Set base context dictionary
    ha_base_context = {

        'section_solutions_category'            : 8,

        #Set menu classes
        'menu_overview_class'                   : '',
        'menu_our_solutions_class'              : '',
        'menu_contact_sales_class'              : '',
        'menu_customer_support_class'           : '',

        'submenu_our_solutions_class'           : 'style=display:none!important',
        'submenu_our_solutions_mat'             : '',

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(ha_base_context)
    context.update(short_copy)

    return context

def ha_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ha_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ha', page='overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ha', page='overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ha', page='overview', role='section1_intro2').content_en
        section1_box1 = Content_item.objects.get(section='ha', page='overview', role='section1_box1').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ha', page='overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ha', page='overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ha', page='overview', role='section1_intro2').content_fr
        section1_box1 = Content_item.objects.get(section='ha', page='overview', role='section1_box1').content_fr

    #Set context dictionary
    context.update({
        'menu_overview_class' : 'current_page_item',
        'show_latest_thinking' : True,
    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    locals().update(context)

    #Return the view
    return render(request, 'core/ha/overview.html', locals())

def ha_our_solutions(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ha_base_context(request)

    #Get page specific content
    if lang == "EN":
        ha_our_solutions_links = {
            'mat' : "/health-solutions/health-analytics/our-solutions/market-access-toolkit/"
            }
        button_contact_us = {
            'text' : "Contact us",
            'url' : "/health-solutions/health-analytics/sales/"
        }
        section1_title = Content_item.objects.get(section='ha', page='our_solutions', role='section1_title').content_en
        section_intro1 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro1').content_en
        section_intro2 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro2').content_en
        section_intro3 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro3').content_en
        section_intro4 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro4').content_en
    elif lang == "FR":
        ha_our_solutions_links = {
            'mat' : "/solutions-sante/intelligence-daffaires/produits/trousse-dacces-au-marche/"
            }
        button_contact_us = {
            'text' : "Communiquez avec nos experts",
            'url' : "/solutions-en-sante/intelligence-daffaires/ventes/"
        }
        section1_title = Content_item.objects.get(section='ha', page='our_solutions', role='section1_title').content_fr
        section_intro1 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro1').content_fr
        section_intro2 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro2').content_fr
        section_intro3 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro3').content_fr
        section_intro4 = Content_item.objects.get(section='ha', page='our_solutions', role='section_intro4').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ha/our_solutions.html', locals())

def ha_our_solutions_mat (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ha_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box3').content_en
        section1_box4 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box4').content_en
        section1_box5 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box5').content_en
        section1_box6 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box6').content_en
        section1_box7 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box7').content_en
        #section2_title = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_title').content_en
        section2_intro = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section2_intro').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box3').content_fr
        section1_box4 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box4').content_fr
        section1_box5 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box5').content_fr
        section1_box6 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box6').content_fr
        section1_box7 = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_box7').content_fr
        #section2_title = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section1_title').content_fr
        section2_intro = Content_item.objects.get(section='ha', page='our_solutions_mat', role='section2_intro').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_our_solutions_class' : 'current_page_item',
        'submenu_our_solutions_class' : '',
        'submenu_our_solutions_mat_class' : 'active',
        'show_solutions_cta' : True,

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ha/our_solutions_mat.html', locals())

def ha_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get Marketo Form
    product_link_name = 'health-analytics' if lang == 'EN' else 'intelligence-daffaires'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='sales', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'ha_sales_support' : 'Sales support',
            'ha_contact_thps' : 'Contact TELUS Health',
            'ha_call_us' : 'Call us',
            'ha_tel' : '1-647-837-4987',
            'ha_hours' : '8:30am to 5:00pm (EST)',

            }

    elif lang == 'FR':

        short_copy = {

            'ha_sales_support' : 'Soutien aux ventes',
            'ha_contact_thps' : 'Contactez TELUS Santé',
            'ha_call_us' : 'Appelez-nous',
            'ha_tel' : '450 928-6000, poste 3717',
            'ha_hours' : "8 h 30 à 17 h, heure de l'Est",

            }

    #Get base generic context
    context = ha_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/ha/sales.html', locals())

def ha_support (request):

    lang = set_lang(request)
    region = set_region(request)

    show_marketo_form = False
    if request.method == 'GET' and 'solution' in request.GET:
        show_marketo_form = True

    #Get Marketo Form
    product_link_name = 'health-analytics' if lang == 'EN' else 'intelligence-daffaires'
    marketo_form_id = ProductContact.objects.get(product_link_name=product_link_name, sales_or_support='support', language=lang).marketo_form_id

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'ha_technical_support' : 'Technical support',
            'ha_analysis_consulting' : {
                    'text' : "Analysis and consultings",
                    'url' : "?solution=analysis-consulting"
                },
            'ha_in_sites' : {
                    'text' : "In-Sites",
                    'url' : "?solution=in-sites"
                },
            'ha_mat' : {
                    'text' : "Market Access Toolkit (MAT)",
                    'url' : "?solution=mat"
                },
            'ha_prism' : {
                    'text' : "PRISM",
                    'url' : "?solution=prism"
                }

        }

    elif lang == 'FR':

        short_copy = {

            'ha_technical_support' : 'Support technique',
            'ha_analysis_consulting' : {
                    'text' : "Analyse et consultation",
                    'url' : "?solution=analyse-et-consultation"
                },
            'ha_in_sites' : {
                    'text' : "In-Sites",
                    'url' : "?solution=insites"
                },
            'ha_mat' : {
                    'text' : "Trousse d’accès au marché",
                    'url' : "?solution=trousse"
                },
            'ha_prism' : {
                    'text' : "PRISM",
                    'url' : "?solution=prism"
                }

        }

    #Get base generic context
    context = ha_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

        'menu_support_class' : 'current_page_item',
        'show_solutions_cta' : False,
        'show_carousel' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/ha/support.html', locals())

#########################################################################################
# Solutions  For
#########################################################################################

def sf_base_context(request):

    #Get base generic context
    context = base_context(request)

    #Set base context dictionary
    sf_base_context = {

        'solutions_for' : {
                'ahp' : 1,
                'consumers' : 2,
                'hrh' : 3,
                'ie' : 4,
                'pharmaceutical' : 5,
                'pharmacists' : 6,
                'physicians' : 7,
                'wcb' : 8,
                'pharmacists_order_online' : 9,
            },

        #Show carousel
        'show_carousel'                         : True,
        'show_latest_thinking'                  : False,
        'show_media_releases'                   : False,
        'show_events'                           : False,
        'show_solutions_cta'                    : True,

    }

    #Set context dictionary
    context.update(sf_base_context)

    return context

def sf_ahp (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_ahp_portal_login' : {
                    'text' : "eClaims / WSIB Portal Login",
                    'url' : "https://providereservices.telushealth.com/"
                },

            'sf_ahp_register' : {
                    'text' : "Register for eClaims / WSIB eServices",
                    'url' : "/provider-registration/"
                },

            'media_releases_title' : 'Media releases',
            'mr_show_more' : {
                    'text' : 'Show more',
                    'url' : '/news-events/media-releases/'
                },

            'links' : {

                'eclaims' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/eclaims-allied-healthcare-providers/",
                'wsib' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/wsib-eservices/",
                'phr' : "/health-solutions/patient-and-consumer-health-platforms/our-solutions/personal-health-records/"

                }

        }

    elif lang == 'FR':

        short_copy = {

            'sf_ahp_portal_login' : {
                    'text' : "Accès aux portails",
                    'url' : "https://servicesenligneauxfournisseurs.telussante.com/"
                },

            'sf_ahp_register' : {
                    'text' : "Inscription portail fournisseurs",
                    'url' : "/inscription-des-fournisseurs/"
                },

            'media_releases_title' : 'Communiqués de presse',
            'mr_show_more' : {
                    'text' : 'En voir plus',
                    'url' : '/nouvelles-evenements/communiques-de-presse/'
                },

            'links' : {

                'eclaims' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/nos-solutions/demandes-de-reglement-en-ligne-soins-complementaires/",
                'wsib' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/cspaat-services-en-ligne/",
                'phr' : "/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/dossiers-de-sante-personnels-dsp/"

                }

        }

    #TODO: Remove contact sales Button when on Support of Sales
    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_intro1 = Content_item.objects.get(section='sf', page='ahp', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='sf', page='ahp', role='section1_box1').content_en
        section1_box2 = Content_item.objects.get(section='sf', page='ahp', role='section1_box2').content_en
        section1_box3 = Content_item.objects.get(section='sf', page='ahp', role='section1_box3').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='ahp', role='section1_intro2').content_en
        section1_box4 = Content_item.objects.get(section='sf', page='ahp', role='section1_box4').content_en
        section1_box5 = Content_item.objects.get(section='sf', page='ahp', role='section1_box5').content_en
    elif lang == "FR":
        section1_intro1 = Content_item.objects.get(section='sf', page='ahp', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='sf', page='ahp', role='section1_box1').content_fr
        section1_box2 = Content_item.objects.get(section='sf', page='ahp', role='section1_box2').content_fr
        section1_box3 = Content_item.objects.get(section='sf', page='ahp', role='section1_box3').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='ahp', role='section1_intro2').content_fr
        section1_box4 = Content_item.objects.get(section='sf', page='ahp', role='section1_box4').content_fr
        section1_box5 = Content_item.objects.get(section='sf', page='ahp', role='section1_box5').content_fr

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['ahp']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['ahp']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['ahp']).order_by('-event_date')[:2]

    #Set context dictionary
    context.update({
        #'page_title':"Solutions for Allied Healthcare Providers",
        'show_carousel' : True,
        'show_media_releases' : True,
        'show_events' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_ahp.html', locals())

def sf_consumers (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'links' : {

                'trackers' : "http://www.telus.com/en/on/mobility/accessories/catalog/all/health-fitness/fitness-trackers",
                'accessories' : "http://www.telus.com/mobility/accessories/catalog/all/health-fitness",
                'phr' : "/health-solutions/patient-and-consumer-health-platforms/our-solutions/personal-health-records/"

                }

        }

    elif lang == 'FR':

        short_copy = {

            'links' : {

                'trackers' : "http://www.telus.com/fr/qc/mobility/accessories/catalog/all/health-fitness/fitness-trackers",
                'accessories' : "http://www.telus.com/fr/qc/mobility/accessories/catalog/all/health-fitness",
                'phr' : "/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/dossiers-de-sante-personnels-dsp/"

                }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='consumers', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro3').content_en
        section1_title = Content_item.objects.get(section='sf', page='consumers', role='section1_title').content_en
        section2_intro1 = Content_item.objects.get(section='sf', page='consumers', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='sf', page='consumers', role='section2_intro2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='consumers', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='consumers', role='section1_intro3').content_fr
        section1_title = Content_item.objects.get(section='sf', page='consumers', role='section1_title').content_fr
        section2_intro1 = Content_item.objects.get(section='sf', page='consumers', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='sf', page='consumers', role='section2_intro2').content_fr

    #Set context dictionary
    context.update({
        #'page_title':"Solutions for Consumers",
        'show_carousel' : True,
        'show_media_releases' : False,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['consumers']).order_by('-publication_date')[:3]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_consumers.html', locals())

def sf_hrh (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'links' : {

                'dis' : "/health-solutions/electronic-health-records/our-solutions/drug-information-system/",
                'hip' : "/health-solutions/electronic-health-records/our-solutions/health-integration-platform/",
                'ischeduler' : "/health-solutions/electronic-health-records/our-solutions/ischeduler/",
                'oacis' : "/health-solutions/electronic-health-records/our-solutions/oacis-clinical-information-system/",
                'hhm' : "/health-solutions/patient-and-consumer-health-platforms/our-solutions/home-health-monitoring/"

                }

        }

    elif lang == 'FR':

        short_copy = {

            'links' : {

                'dis' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/systeme-dinformation-sur-les-medicaments-sim/",
                'hip' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/plateforme-dintegration-des-soins-de-sante/",
                'ischeduler' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/ischeduler/",
                'oacis' : "/solutions-sante/dossiers-de-sante-electroniques/nos-solutions/oacis-soins-cliniques/",
                'hhm' : "/solutions-sante/plateformes-de-sante-pour-patients-et-grand-public/produits/telesoins-domicile/"

                }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='hrh', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro5').content_en
        section2_title = Content_item.objects.get(section='sf', page='hrh', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='sf', page='hrh', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='sf', page='hrh', role='section2_intro2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='hrh', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='hrh', role='section1_intro5').content_fr
        section2_title = Content_item.objects.get(section='sf', page='hrh', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='sf', page='hrh', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='sf', page='hrh', role='section2_intro2').content_fr

    #Set context dictionary
    context.update({

        'show_carousel' : True,
        'show_media_releases' : True,
        'show_events' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['hrh']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['hrh']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['hrh']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_hrh.html', locals())

def sf_ie (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_ie_paf' : {
                    'text' : "Prior Authorization forms",
                    'url' : "/prior-authorization-forms/"
                },

            'sf_ie_ha_portal' : {
                    'text' : "Health Analytics client portal",
                    'url' : "https://healthanalytics.telushealth.com"
                },

            'links' : {

                'dental' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/dental-claims/",
                'drug' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-dental-extended-claims-insurers/",
                'coverage' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/drug-coverage-validation/",
                'eclaims' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/eclaims/",
                'extended' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/extended-healthcare-claims/",
                'worksafebc' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/worksafe-bc-providers/",
                'wsib' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/wsib-eservices/"

                },

        }

    elif lang == 'FR':

        short_copy = {

            'sf_ie_paf' : {
                    'text' : "Formulaires d'autorisation préalable ",
                    'url' : "/formulaires-dautorisation-prealable/"
                },

            'sf_ie_ha_portal' : {
                    'text' : "Portail d'intelligence d'affaires en santé",
                    'url' : "https://healthanalytics.telushealth.com/"
                },

            'links' : {

                'dental' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-dentaires/",
                'drug' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-medicaments-soins-dentaires-et-de-sante-complementaires-assureurs/",
                'coverage' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/validation-de-la-couverture-dassurance-medicaments/",
                'eclaims' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-en-ligne/",
                'extended' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-pour-soins-complementaires/",
                'worksafebc' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/worksafe-bc-fournisseus/",
                'wsib' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/cspaat-services-en-ligne/"

                },

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='ie', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='ie', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='ie', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='ie', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='ie', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='ie', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='sf', page='ie', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='sf', page='ie', role='section1_intro7').content_en
        section1_intro8 = Content_item.objects.get(section='sf', page='ie', role='section1_intro8').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='ie', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='ie', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='ie', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='ie', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='ie', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='ie', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='sf', page='ie', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='sf', page='ie', role='section1_intro7').content_fr
        section1_intro8 = Content_item.objects.get(section='sf', page='ie', role='section1_intro8').content_fr

    #Set context dictionary
    context.update({
        'page_title':"Solutions for Insurers & Employers",
        'show_carousel' : True,
        'show_media_releases' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['ie']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['ie']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['ie']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_ie.html', locals())

def sf_pharmaceutical (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmaceutical_mat' : {
                    'text' : "Health Analytics MAT and Employer Database access",
                    'url' : "https://healthanalytics.telushealth.com"
                },

            'links' : {

                'mat' : "/health-solutions/health-analytics/our-solutions/market-access-toolkit/",

                },

        }

    elif lang == 'FR':

        short_copy = {

            'sf_pharmaceutical_mat' : {
                    'text' : "Accès aux bases de données",
                    'url' : "https://healthanalytics.telushealth.com"
                },

            'links' : {

                'mat' : "/solutions-sante/intelligence-daffaires/produits/trousse-dacces-au-marche/",

                },

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_intro2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmaceutical', role='section1_intro2').content_fr

    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'show_media_releases' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['pharmaceutical']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['pharmaceutical']).order_by('-media_release_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_pharmaceutical.html', locals())

def sf_pharmacists (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Download claims documents ",
                    'url' : "/support-documents-pharmacists/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Order online ",
                    'url' : "/solutions-for/pharmacy-home/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Training",
                    'url' : "/training/"
                },


            'links' : {

                'network' : "/health-solutions/pharmacy-management/our-solutions/assyst-network/",
                'pos' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/",
                'posqc' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/",
                'dopill' : "/health-solutions/pharmacy-management/our-solutions/do-pill/",
                'ps' : "/health-solutions/pharmacy-management/our-solutions/pharma-space/",
                'rxvigi' : "/health-solutions/pharmacy-management/our-solutions/rx-vigilance/",
                'ubik' : "/health-solutions/pharmacy-management/our-solutions/telus-ubik/",
                'xpill' : "/health-solutions/pharmacy-management/our-solutions/xpill-pharma/",

                },

        }

    elif lang == 'FR':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Documents de Demandes de règlement",
                    'url' : "/documents-soutien-pharmaciens/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Commande en ligne",
                    'url' : "/solutions-pour/pharmaciens-maison/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Formation",
                    'url' : "/formation/"
                },

            'links' : {

                'network' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/",
                'pos' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/",
                'posqc' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/",
                'dopill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/",
                'ps' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/",
                'rxvigi' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/",
                'ubik' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/",
                'xpill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/",

                },

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_en
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_en
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_fr
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_fr
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_fr

    #Set context dictionary
    context.update({
        'show_carousel' : True,
        'show_media_releases' : True,
        'show_events' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_pharmacists.html', locals())

#Order Online
@csrf_exempt
def sf_pharmacists_order_online(request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Download claims documents ",
                    'url' : "/support-documents-pharmacists/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Order online ",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Training",
                    'url' : "/training/"
                },


            'links' : {

                'network' : "/health-solutions/pharmacy-management/our-solutions/assyst-network/",
                'pos' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/",
                'posqc' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/",
                'dopill' : "/health-solutions/pharmacy-management/our-solutions/do-pill/",
                'ps' : "/health-solutions/pharmacy-management/our-solutions/pharma-space/",
                'rxvigi' : "/health-solutions/pharmacy-management/our-solutions/rx-vigilance/",
                'ubik' : "/health-solutions/pharmacy-management/our-solutions/telus-ubik/",
                'xpill' : "/health-solutions/pharmacy-management/our-solutions/xpill-pharma/",

                }

        }

    elif lang == 'FR':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Documents de Demandes de règlement",
                    'url' : "/documents-soutien-pharmaciens/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Commande en ligne",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Formation",
                    'url' : "/formation/"
                },

            'links' : {

                'network' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/",
                'pos' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/",
                'posqc' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/",
                'dopill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/",
                'ps' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/",
                'rxvigi' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/",
                'ubik' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/",
                'xpill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/",

                }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":

        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_en
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_en
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_fr
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_fr
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_fr



    total = 0
    totalqty = 0

    #Get page specific content
    page_title = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='page_title')

    #Get all pharmacy products that are active
    pharmacy_products = Pharmacy_Product.objects.filter(active=True)

    #Get categories
    categories = Pharmacy_Product_Category.objects.filter(active=True)
        #Get page info
    page_id = request.session.get('page_id')
    page = Page.objects.get(id=page_id)

    #Get lang and region
    lang = set_lang(request)
    region = set_region(request)

    #Get copy
    copy = Copy(lang, region, page)
    dictionary = copy.base_dictionary()

    try:
        order = request.get_signed_cookie('order', salt='th1sw2bs3t4nam5')
    except KeyError:
        order = {}
    if type(order) is str:
        order = ast.literal_eval(order)
    xx = [x for x in order.keys()]
    ordered_products = Pharmacy_Product.objects.filter(id__in=xx)

    responsedata = {}
    productpk = {}

    for product in ordered_products:
        productdata = {}
        qty = order[product.id]
        price = qty * product.price
        productdata['min_qty'] = product.minimum_order
        productdata['price'] = product.price
        productdata['title'] = product.title
        productdata['description'] = product.description
        productdata['ptotal'] = price
        productdata['qty'] = order[product.id]
        productdata['id'] = product.id
        productdata['image'] = static("images/default_image.jpg")
        if product.image:
            productdata['image'] = product.image.url
        total += (price * product.minimum_order)
        totalqty += qty
        productpk[product.id] = productdata
    totalmain = 0
    totalsub = "00"
    if total != 0:
        total = str(total).split('.')
        totalmain = total[0]
        totalsub = total[1]
    if request.is_ajax():
        responsedata['products'] = productpk
        responsedata['extras'] = {'total': total, "totalmain":totalmain, 'totalqty':totalqty, "totalsub":totalsub}
        if request.method == 'POST':
            json_str =  (request.body).decode('utf-8')
            json_obj = json.loads(json_str)
            thisorder = PharmacyProduct_Order.objects.create(
                            firstname = json_obj['FirstName'],
                            lastname = json_obj['LastName'],
                            email = json_obj['Email'],
                            phone = json_obj['Phone'],
                            company = json_obj['Company'],
                            address = json_obj['Address'],
                            address2 = json_obj['BillingStreet'],
                            city = json_obj['City'],
                            state = json_obj['province'],
                            country = json_obj['Country'],
                            postalcode = json_obj['PostalCode'],
                            region = json_obj['customMarketoRegion'],
                        )
            for product in ordered_products:
                carty = CartItem.objects.create(order= thisorder,
                                    product = product,
                                    quantity = order[product.id],
                                    )
            order_dic_data = {
                'firstname': json_obj['FirstName'],
                'lastname':json_obj['LastName'],
                'email': json_obj['Email'],
                'order': order,
                'ordered_products': ordered_products,
                "total": total,
                "totalqty": totalqty,
                "order_date": carty.dateCreated,
                "order_id": carty.id,
                }
            client_feedback = render_to_string('includes/product_order_client.html', order_dic_data)
            seller_feedback = render_to_string('includes/product_order_seller.html', order_dic_data)
            send_mail('Your Order Was Received', strip_tags(client_feedback), settings.DEFAULT_FROM_EMAIL, [json_obj['Email']], html_message=client_feedback)
            send_mail('New Order Received', strip_tags(seller_feedback), settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_TO_EMAIL], html_message=client_feedback)

            responsedata['products'] = {}
            responsedata['extras'] = {'total': '0', "totalmain":0, 'totalqty':0, "totalsub":"00"}
            response = JsonResponse(responsedata)
            response.delete_cookie('order')
            return response
        response = JsonResponse(responsedata)
        return response


    #print('copy is', copy.base_dictionary())

    #Set context dictionary
    context.update({
        'page_title':"Order online Solutions for Pharmacists",
        'show_carousel' : False,
        'show_media_releases' : False,
        'show_events' : False,
        'show_latest_thinking' : False,
        'show_solutions_cta' : False,
        'pharmacy_products': pharmacy_products,
        'categories': categories,
        'totalmain': totalmain,
        'totalsub': totalsub,
        'totalqty': totalqty,

    })

    #Return the view
    # return render(request, 'core/sf/sf_pharmacists.html', locals())
    #Return the view
        #Get page specific content

    return render(request, 'core/sf/sf_pharmacists_order_online.html', context)

@csrf_exempt
def null_pharmacists_order_online(request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Download claims documents ",
                    'url' : "/support-documents-pharmacists/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Order online ",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Training",
                    'url' : "/training/"
                },


            'links' : {

                'network' : "/health-solutions/pharmacy-management/our-solutions/assyst-network/",
                'pos' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/",
                'posqc' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/",
                'dopill' : "/health-solutions/pharmacy-management/our-solutions/do-pill/",
                'ps' : "/health-solutions/pharmacy-management/our-solutions/pharma-space/",
                'rxvigi' : "/health-solutions/pharmacy-management/our-solutions/rx-vigilance/",
                'ubik' : "/health-solutions/pharmacy-management/our-solutions/telus-ubik/",
                'xpill' : "/health-solutions/pharmacy-management/our-solutions/xpill-pharma/",

                }

        }

    elif lang == 'FR':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Documents de Demandes de règlement",
                    'url' : "/documents-soutien-pharmaciens/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Commande en ligne",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Formation",
                    'url' : "/formation/"
                },

            'links' : {

                'network' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/",
                'pos' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/",
                'posqc' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/",
                'dopill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/",
                'ps' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/",
                'rxvigi' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/",
                'ubik' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/",
                'xpill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/",

                }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":

        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_en
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_en
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='pharmacists', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro7').content_fr
        section1_intro8 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro8').content_fr
        section1_intro9 = Content_item.objects.get(section='sf', page='pharmacists', role='section1_intro9').content_fr



    total = 0
    totalqty = 0

    #Get page specific content
    page_title = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='page_title')

    #Get all pharmacy products that are active
    pharmacy_products = Pharmacy_Product.objects.filter(active=True)

    #Get categories
    categories = Pharmacy_Product_Category.objects.filter(active=True)
        #Get page info
    page_id = request.session.get('page_id')
    page = Page.objects.get(id=page_id)

    #Get lang and region
    lang = set_lang(request)
    region = set_region(request)

    #Get copy
    copy = Copy(lang, region, page)
    dictionary = copy.base_dictionary()

    try:
        order = request.get_signed_cookie('order', salt='th1sw2bs3t4nam5')
    except KeyError:
        order = {}
    if type(order) is str:
        order = ast.literal_eval(order)
    xx = [x for x in order.keys()]
    ordered_products = Pharmacy_Product.objects.filter(id__in=xx)

    responsedata = {}
    productpk = {}

    for product in ordered_products:
        productdata = {}
        qty = order[product.id]
        price = qty * product.price
        productdata['min_qty'] = product.minimum_order
        productdata['price'] = product.price
        productdata['title'] = product.title
        productdata['description'] = product.description
        productdata['ptotal'] = price
        productdata['qty'] = order[product.id]
        productdata['id'] = product.id
        productdata['image'] = static("images/default_image.jpg")
        if product.image:
            productdata['image'] = product.image.url
            print("product image url is", product.image.url)
        total += price
        totalqty += qty
        productpk[product.id] = productdata
    totalmain = 0
    totalsub = "00"
    if total != 0:
        total = str(total).split('.')
        totalmain = total[0]
        totalsub = total[1]
    if request.is_ajax():
        responsedata['products'] = productpk

        responsedata['extras'] = {'total': total, "totalmain":totalmain, 'totalqty':totalqty, "totalsub":totalsub}
        if request.method == 'POST':
            json_str =  (request.body).decode('utf-8')
            json_obj = json.loads(json_str)
            thisorder = PharmacyProduct_Order.objects.create(
                            firstname = json_obj['FirstName'],
                            lastname = json_obj['LastName'],
                            email = json_obj['Email'],
                            phone = json_obj['Phone'],
                            company = json_obj['Company'],
                            address = json_obj['Address'],
                            address2 = json_obj['BillingStreet'],
                            city = json_obj['City'],
                            state = json_obj['province'],
                            country = json_obj['Country'],
                            postalcode = json_obj['PostalCode'],
                            region = json_obj['customMarketoRegion'],
                        )
            for product in ordered_products:
                carty = CartItem.objects.create(order= thisorder,
                                    product = product,
                                    quantity = order[product.id],
                                    )
            order_dic_data = {
                'firstname': json_obj['FirstName'],
                'lastname':json_obj['LastName'],
                'email': json_obj['Email'],
                'order': order,
                'ordered_products': ordered_products,
                "total": total,
                "totalqty": totalqty,
                "order_date": carty.dateCreated,
                "order_id": carty.id,
                }
            client_feedback = render_to_string('includes/product_order_client.html', order_dic_data)
            seller_feedback = render_to_string('includes/product_order_seller.html', order_dic_data)
            send_mail('Your Order Was Received', strip_tags(client_feedback), settings.DEFAULT_FROM_EMAIL, [json_obj['Email']], html_message=client_feedback)
            send_mail('New Order Received', strip_tags(seller_feedback), settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_TO_EMAIL], html_message=client_feedback)

            responsedata['products'] = {}
            responsedata['extras'] = {'total': '0', "totalmain":0, 'totalqty':0, "totalsub":"00"}
            response = JsonResponse(responsedata)
            response.delete_cookie('order')
            return response
        response = JsonResponse(responsedata)
        return response


    #print('copy is', copy.base_dictionary())

    #Set context dictionary
    context.update({
        'page_title':"Order online Solutions for Pharmacists",
        'show_carousel' : False,
        'show_media_releases' : False,
        'show_events' : False,
        'show_latest_thinking' : False,
        'show_solutions_cta' : False,
        'pharmacy_products': pharmacy_products,
        'categories': categories,
        'totalmain': totalmain,
        'totalsub': totalsub,
        'totalqty': totalqty,

    })

    #Return the view
    # return render(request, 'core/sf/sf_pharmacists.html', locals())
    #Return the view
        #Get page specific content

    return render(request, 'core/pharmacists_order_online/pharmacists.html', context)

# class AddDict(dict):
#     def __setitem__(self, key, value):
#         if key not in self:
#             dict.__setitem__(self, key, value)
#         else:
#             raise KeyError("Key already exists")

# class UpdateorAddDict(dict):
#     def __setitem__(self, key, value):
#         if key not in self:
#             dict.__setitem__(self, key, value)
#         else:
#             val = int(self[key])
#             value = val + int(value)
#             dict.__setitem__(self, key, value)


#Update Online Order
def sf_pharmacists_update_order_online(request, product_id, qty, action=''):
    totalmain = 0
    totalsub = "00"
    totalqty = 0
    total = 0
    try:
        order = request.get_signed_cookie('order', salt='th1sw2bs3t4nam5')
    except KeyError:
        order = {}
    product_id = int(product_id)
    qty = int(qty)
    print("Watch",action)
    if type(order) is str:
        order = ast.literal_eval(order)
    if action == 'update':
        order[product_id] = qty
    elif action == 'add':
        if product_id not in order:
            order[product_id] = qty
        else:
            order[product_id] = int(order[product_id]) + qty
    elif action == 'remove':
        if product_id in order:
            del order[product_id]
    check = list(order.keys())
    for key in check:
        if order[key] == 0:
            del order[key]
    xx = [x for x in order.keys()]
    ordered_products = Pharmacy_Product.objects.filter(id__in=xx)

    for product in ordered_products:
        qty = order[product.id]
        price = qty * product.price
        total += price
        totalqty += qty
    if total != 0:
        total = str(total).split('.')
        totalmain = total[0]
        if total[1] != '0':
            totalsub = total[1]
    response = JsonResponse({'total': total, "totalmain":totalmain, 'totalqty':totalqty, "totalsub":totalsub})
    response.set_signed_cookie('order', order, salt='th1sw2bs3t4nam5', expires=datetime.date.today() + datetime.timedelta(days=360))
    return response

def sf_physicians (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_physicians_nightingale' : {
                    'text' : "Support information for Nightingale users",
                    'url' : "#"
                },

            'links' : {

                'mobile' : "/health-solutions/electronic-medical-records/our-solutions/mobile-emr/",
                'kin' : "/health-solutions/electronic-medical-records/our-solutions/kinlogix-emr/",
                'med' : "/health-solutions/electronic-medical-records/our-solutions/med-access-emr/",
                'mede' : "/health-solutions/electronic-medical-records/our-solutions/medesync-emr/",
                'pss' : "/health-solutions/electronic-medical-records/our-solutions/ps-suite-emr/",
                'wolf' : "/health-solutions/electronic-medical-records/our-solutions/wolf-emr/"

                },

        }

    elif lang == 'FR':

        short_copy = {

            'sf_physicians_nightingale' : {
                    'text' : "Support information for Nightingale users",
                    'url' : "#"
                },

            'links' : {

                'mobile' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-mobile/",
                'kin' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-kinlogix/",
                'med' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-med-access/",
                'mede' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/medesync-dme/",
                'pss' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-suite-sc/",
                'wolf' : "/solutions-sante/dossiers-medicaux-electroniques/nos-solutions/dme-wolf/"

                },

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='physicians', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro7').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='physicians', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='sf', page='physicians', role='section1_intro7').content_fr

    #Set context dictionary
    context.update({
        'show_carousel' : True,
        'show_media_releases' : True,
        'show_events' : True,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['physicians']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['physicians']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['physicians']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_physicians.html', locals())

def sf_wcb (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_wcb_form_workers' : {
                    'text' : "WSIB Direct Deposit Form - Workers",
                    'url' : "http://www.telushealth.com/docs/claims-and-benefits-management/direct-deposit-enrollment-authorization---workers-wsib.pdf"
                },

            'sf_wcb_form_providers' : {
                    'text' : "Direct Deposit Form - Providers",
                    'url' : "http://www.telushealth.com/docs/default-source/claims-and-benefits-management/direct-deposit-enrollment-authorization-providers.pdf"
                },

            'sf_wcb_portal' : {
                    'text' : " WSIB / eClaims Portal Login ",
                    'url' : "https://providereservices.telushealth.com"
                },

            'links' : {

                'eclaims' : "/health-solutions/claims-and-benefits-management/insurers-and-employers/our-solutions/eclaims/",
                'worksafe' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/worksafe-bc-providers/",
                'wsib' : "/health-solutions/claims-and-benefits-management/allied-healthcare-providers/our-solutions/wsib-eservices/",

                },

        }

    elif lang == 'FR':

        short_copy = {

            'sf_wcb_form_workers' : {
                    'text' : "Dépôt direct (travailleurs CSPAAT)",
                    'url' : "http://www.telussante.com/docs/claims-and-benefits-management/autorisation-d-inscription-au-d%C3%A9p%C3%B4t-direct-(travailleurs).pdf"
                },

            'sf_wcb_form_providers' : {
                    'text' : "Dépôt direct (fournisseurs)",
                    'url' : "http://www.telussante.com/docs/default-source/claims-and-benefits-management/formulaire-d-inscription-au-d%C3%A9p%C3%B4t-direct-fournisseurs.pdf"
                },

            'sf_wcb_portal' : {
                    'text' : "Accès aux portails",
                    'url' : "https://servicesenligneauxfournisseurs.telussante.com"
                },

            'links' : {

                'eclaims' : "/solutions-sante/assureurs-et-employeurs/nos-solutions/demandes-de-reglement-en-ligne/",
                'worksafe' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/worksafe-bc-fournisseus/",
                'wsib' : "/solutions-sante/prestataires-de-soins-de-sante-affilies/produits/cspaat-services-en-ligne/",

                },

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='sf', page='wcb', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro4').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='sf', page='wcb', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='sf', page='wcb', role='section1_intro4').content_fr

    #Set context dictionary
    context.update({
        'show_carousel' : True,
        'show_media_releases' : True,
        'show_events' : False,
        'show_latest_thinking' : True,
        'show_solutions_cta' : False,

    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['wcb']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['wcb']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['wcb']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/sf/sf_wcb.html', locals())

######################################################################################################################
# Professional Services
######################################################################################################################

def ps_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contact sales today',
                'url' : '/professional-services/sales/'
            },

            'overview' : {
                'text' : 'Overview',
                'url' : '/professional-services/overview/'
            },

            'our_expertise' : {
                'text' : 'Our expertise',
                'url' : '/professional-services/expertise/'
            },

            'practice_leaders' : {
                'text' : 'Practice Leaders',
                'url' : '/professional-services/practice-leaders/'
            },

            'contact_sales' : {
                'text' : 'Contact Sales',
                'url' : '/professional-services/sales/'
            },

            'section_sales_url' : '/professional-services/sales/',

        }

    elif lang == 'FR':

        short_copy = {

            'contact_sales_today' : {
                'text' : 'Contactez les ventes',
                'url' : '/services-professionnels/ventes/'
            },

            'overview' : {
                'text' : 'Aperçu',
                'url' : '/services-professionnels/apercu/'
            },

            'our_expertise' : {
                'text' : 'Notre expertise',
                'url' : '/services-professionnels/notre-expertise/'
            },

            'practice_leaders' : {
                'text' : 'Nos experts-conseils',
                'url' : '/services-professionnels/nos-experts-conseils/'
            },

            'contact_sales' : {
                'text' : 'Contactez les ventes',
                'url' : '/services-professionnels/ventes/'
            },

            'section_sales_url' : '/services-professionnels/ventes/',

        }

    #Set base context dictionary
    ps_base_context = {

        'section_solutions_category'    : 11,

        #Set menu classes
        'menu_overview_class'           : '',
        'menu_expertise_class'          : '',
        'menu_practice_leaders_class'   : '',
        'menu_sales_class'              : '',

        #Show carousel
        'show_carousel'                 : True,
        'show_latest_thinking'          : False,
        'show_media_releases'           : False,
        'show_solutions_cta'            : True,

    }

    #Set context dictionary
    context.update(ps_base_context)
    context.update(short_copy)

    return context

def ps_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ps_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='ps', page='overview', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ps', page='overview', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ps', page='overview', role='section1_intro2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ps', page='overview', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ps', page='overview', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ps', page='overview', role='section1_intro2').content_fr

    #Set context dictionary
    context.update({
        'menu_overview_class' : 'current_page_item',
        'section1_title': section1_title,
        'section1_intro1': section1_intro1,
        'show_latest_thinking' : True,
    })

    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_category__id=context['section_solutions_category']).order_by('-publication_date')[:3]

    locals().update(context)

    #Return the view
    return render(request, 'core/ps/overview.html', locals())

def ps_expertise(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ps_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='ps', page='expertise', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro2').content_en
        section1_intro3 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro3').content_en
        section1_intro4 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro4').content_en
        section1_intro5 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro5').content_en
        section1_intro6 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro6').content_en
        section1_intro7 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro7').content_en
        section1_intro8 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro8').content_en
        intro1_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro1_link1').content_en
        intro2_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro2_link1').content_en
        intro3_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro3_link1').content_en
        intro4_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro4_link1').content_en
        intro5_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro5_link1').content_en
        intro7_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro7_link1').content_en
        intro7_link2 = Content_item.objects.get(section='ps', page='expertise', role='intro7_link2').content_en
        intro8_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link1').content_en
        intro8_link2 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link2').content_en
        intro8_link3 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link3').content_en

    elif lang == "FR":
        section1_title = Content_item.objects.get(section='ps', page='expertise', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro2').content_fr
        section1_intro3 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro3').content_fr
        section1_intro4 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro4').content_fr
        section1_intro5 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro5').content_fr
        section1_intro6 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro6').content_fr
        section1_intro7 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro7').content_fr
        section1_intro8 = Content_item.objects.get(section='ps', page='expertise', role='section1_intro8').content_fr
        intro1_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro1_link1').content_fr
        intro2_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro2_link1').content_fr
        intro3_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro3_link1').content_fr
        intro4_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro4_link1').content_fr
        intro5_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro5_link1').content_fr
        intro7_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro7_link1').content_fr
        intro7_link2 = Content_item.objects.get(section='ps', page='expertise', role='intro7_link2').content_fr
        intro8_link1 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link1').content_fr
        intro8_link2 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link2').content_fr
        intro8_link3 = Content_item.objects.get(section='ps', page='expertise', role='intro8_link3').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_expertise_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ps/expertise.html', locals())

def ps_practice_leaders(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = ps_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title').content_en
        section1_title1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title1').content_en
        section1_intro1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1').content_en
        section1_intro1_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1_box1').content_en
        section1_intro1_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1_box2').content_en
        section1_title2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title2').content_en
        section1_intro2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2').content_en
        section1_intro2_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2_box1').content_en
        section1_intro2_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2_box2').content_en
        section1_title3 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title3').content_en
        section1_intro3 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3').content_en
        section1_intro3_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3_box1').content_en
        section1_intro3_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3_box2').content_en
        section1_title4 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title4').content_en
        section1_intro4 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4').content_en
        section1_intro4_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4_box1').content_en
        section1_intro4_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4_box2').content_en
        section1_title5 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title5').content_en
        section1_intro5 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5').content_en
        section1_intro5_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5_box1').content_en
        section1_intro5_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5_box2').content_en
        section1_title6 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title6').content_en
        section1_intro6 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6').content_en
        section1_intro6_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6_box1').content_en
        section1_intro6_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6_box2').content_en
        section1_title7 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title7').content_en
        section1_intro7 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7').content_en
        section1_intro7_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7_box1').content_en
        section1_intro7_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7_box2').content_en
        section1_title8 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title8').content_en
        section1_intro8 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8').content_en
        section1_intro8_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8_box1').content_en
        section1_intro8_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8_box2').content_en
        section1_title9 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title9').content_en
        section1_intro9 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9').content_en
        section1_intro9_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9_box1').content_en
        section1_intro9_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9_box2').content_en
    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title').content_fr
        section1_title1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title1').content_fr
        section1_intro1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1').content_fr
        section1_intro1_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1_box1').content_fr
        section1_intro1_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro1_box2').content_fr
        section1_title2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title2').content_fr
        section1_intro2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2').content_fr
        section1_intro2_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2_box1').content_fr
        section1_intro2_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro2_box2').content_fr
        section1_title3 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title3').content_fr
        section1_intro3 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3').content_fr
        section1_intro3_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3_box1').content_fr
        section1_intro3_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro3_box2').content_fr
        section1_title4 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title4').content_fr
        section1_intro4 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4').content_fr
        section1_intro4_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4_box1').content_fr
        section1_intro4_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro4_box2').content_fr
        section1_title5 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title5').content_fr
        section1_intro5 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5').content_fr
        section1_intro5_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5_box1').content_fr
        section1_intro5_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro5_box2').content_fr
        section1_title6 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title6').content_fr
        section1_intro6 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6').content_fr
        section1_intro6_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6_box1').content_fr
        section1_intro6_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro6_box2').content_fr
        section1_title7 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title7').content_fr
        section1_intro7 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7').content_fr
        section1_intro7_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7_box1').content_fr
        section1_intro7_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro7_box2').content_fr
        section1_title8 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title8').content_fr
        section1_intro8 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8').content_fr
        section1_intro8_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8_box1').content_fr
        section1_intro8_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro8_box2').content_fr
        section1_title9 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_title9').content_fr
        section1_intro9 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9').content_fr
        section1_intro9_box1 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9_box1').content_fr
        section1_intro9_box2 = Content_item.objects.get(section='ps', page='practice_leaders', role='section1_intro9_box2').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_practice_leaders_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/ps/practice_leaders.html', locals())

def ps_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'ps_sales_support' : 'Sales support',
            'ps_contact_thps' : 'Contact TELUS Health',
            'ps_call_us' : 'Call us',
            'ps_tel' : '1 888 709-8759',
            'ps_hours' : '8:00 a.m. to 8:00 p.m. (EST)',

            }

    elif lang == 'FR':

        short_copy = {

            'ps_sales_support' : 'Soutien aux ventes',
            'ps_contact_thps' : 'Contactez TELUS Santé',
            'ps_call_us' : 'Appelez-nous',
            'ps_tel' : '1 888 709-8759',
            'ps_hours' : "8 h à 20 h, heure de l'Est",

            }

    #Get base generic context
    context = ps_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'show_carousel'                 : False,
        'menu_sales_class' : 'current_page_item',
        'show_solutions_cta'            : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/ps/sales.html', locals())

#########################################################################################
# TELUS in Health
#########################################################################################


def tih_base_context(request):

    #Get base generic context
    context = base_context(request)

    #TODO: Make solutions CTA dynamic

    #Set base context dictionary
    tih_base_context = {

        #Set menu classes
        'menu_latest_thinking_class'            : '',
        'menu_making_difference_class'          : '',
        'menu_communities_matter_class'         : '',
        'menu_proven_leadership_class'          : '',

        #Show carousel
        'show_carousel'                         : True,

    }

    #Set context dictionary
    context.update(tih_base_context)

    return context

def tih_home (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'learn_more' : 'Learn more',

            'health_solutions' : {
                'text' : 'Health Solutions',
                'url' : '/health-solutions/'
            },

            'professional_services' : {
                'text' : 'Professional Services',
                'url' : '/professional-services/overview/'
            },

           'contact_us' : 'Contact us',

            'general_enquiries' : {
                'text' : 'General enquiries',
                'url' : '/contact-telus-health/'
            },

            'tih_support' : {
                'text' : 'Support',
                'url' : '/contact-telus-health/support/'
            },

            'tih_sales' : {
                'text' : 'Sales',
                'url' : '/contact-telus-health/sales/'
            },

            'tih_solutions_for' : 'Solutions for...',


        }

    elif lang == 'FR':

        short_copy = {

            'learn_more' : 'En savoir plus',

            'health_solutions' : {
                'text' : 'Solutions en sante',
                'url' : '/solutions-en-sante/'
            },

            'professional_services' : {
                'text' : 'Professional Services',
                'url' : '/services-professionnels/apercu/'
            },

           'contact_us' : 'Contactez-nous',

            'general_enquiries' : {
                'text' : 'Renseignements généraux',
                'url' : '/contacter-telus-sante/'
            },

            'tih_support' : {
                'text' : 'Support',
                'url' : '/contacter-telus-sante/soutien/'
            },

            'tih_sales' : {
                'text' : 'Ventes',
                'url' : '/contacter-telus-sante/ventes/'
            },

            'tih_solutions_for' : 'Solutions pour...',


        }

    #Get base generic context
    context = tih_base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/tih/home.html', locals())

def tih_making_difference (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = tih_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title1 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title1').content_en
        section1_title2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title2').content_en
        section1_intro1 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro1').content_en
        section1_title2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title2').content_en
        section1_intro2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro2').content_en
        section1_title3 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title3').content_en
        section1_intro3 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro3').content_en
        section1_title4 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title4').content_en
        section1_intro4 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro4').content_en
        section1_title5 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title5').content_en
        section1_intro6 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro6').content_en
    elif lang == "FR":
        section1_title1 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title1').content_fr
        section1_title2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title2').content_fr
        section1_intro1 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro1').content_fr
        section1_title2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title2').content_fr
        section1_intro2 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro2').content_fr
        section1_title3 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title3').content_fr
        section1_intro3 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro3').content_fr
        section1_title4 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title4').content_fr
        section1_intro4 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro4').content_fr
        section1_title5 = Content_item.objects.get(section='tih', page='making_difference', role='section1_title5').content_fr
        section1_intro6 = Content_item.objects.get(section='tih', page='making_difference', role='section1_intro6').content_fr

    #Set context dictionary
    context.update({
        'menu_making_difference_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/tih/making_difference.html', locals())

def tih_communities_matter (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = tih_base_context(request)

    #Get page specific content
    if lang == "EN":
        #
        section1_title = Content_item.objects.get(section='tih', page='communities_matter', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section1_intro1').content_en
        section1_box1 = Content_item.objects.get(section='tih', page='communities_matter', role='section1_box1').content_en
        section2_title = Content_item.objects.get(section='tih', page='communities_matter', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section2_intro1').content_en
        section2_box2 = Content_item.objects.get(section='tih', page='communities_matter', role='section2_box2').content_en
        section3_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section3_intro1').content_en
        section3_box1 = Content_item.objects.get(section='tih', page='communities_matter', role='section3_box1').content_en
        section4_title = Content_item.objects.get(section='tih', page='communities_matter', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section4_intro1').content_en
        section5_title = Content_item.objects.get(section='tih', page='communities_matter', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section5_intro1').content_en
        section6_title = Content_item.objects.get(section='tih', page='communities_matter', role='section6_title').content_en
        section6_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section6_intro1').content_en
        #read = Content_item.objects.get(section='tih', page='communities_matter', role='read').content_en
        video = Content_item.objects.get(section='tih', page='communities_matter', role='video').content_en

    elif lang == "FR":
        #
        section1_title = Content_item.objects.get(section='tih', page='communities_matter', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section1_intro1').content_fr
        section1_box1 = Content_item.objects.get(section='tih', page='communities_matter', role='section1_box1').content_fr
        section2_title = Content_item.objects.get(section='tih', page='communities_matter', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section2_intro1').content_fr
        section2_box2 = Content_item.objects.get(section='tih', page='communities_matter', role='section2_box2').content_fr
        section3_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section3_intro1').content_fr
        section3_box1 = Content_item.objects.get(section='tih', page='communities_matter', role='section3_box1').content_fr
        section4_title = Content_item.objects.get(section='tih', page='communities_matter', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section4_intro1').content_fr
        section5_title = Content_item.objects.get(section='tih', page='communities_matter', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section5_intro1').content_fr
        section6_title = Content_item.objects.get(section='tih', page='communities_matter', role='section6_title').content_fr
        section6_intro1 = Content_item.objects.get(section='tih', page='communities_matter', role='section6_intro1').content_fr
        #read = Content_item.objects.get(section='tih', page='communities_matter', role='read').content_fr
        video = Content_item.objects.get(section='tih', page='communities_matter', role='video').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_communities_matter_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/tih/communities_matter.html', locals())

def tih_executive_team (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = tih_base_context(request)

    #Get page specific content
    if lang == "EN":
        section1_title = Content_item.objects.get(section='tih', page='executive_team', role='section1_title').content_en
        section1_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section1_intro1').content_en
        section1_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section1_intro2').content_en
        section2_title = Content_item.objects.get(section='tih', page='executive_team', role='section2_title').content_en
        section2_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section2_intro1').content_en
        section2_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section2_intro2').content_en
        section3_title = Content_item.objects.get(section='tih', page='executive_team', role='section3_title').content_en
        section3_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section3_intro1').content_en
        section3_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section3_intro2').content_en
        section4_title = Content_item.objects.get(section='tih', page='executive_team', role='section4_title').content_en
        section4_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section4_intro1').content_en
        section4_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section4_intro2').content_en
        section5_title = Content_item.objects.get(section='tih', page='executive_team', role='section5_title').content_en
        section5_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section5_intro1').content_en
        section5_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section5_intro2').content_en
        section6_title = Content_item.objects.get(section='tih', page='executive_team', role='section6_title').content_en
        section6_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section6_intro1').content_en
        section6_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section6_intro2').content_en
        section7_title = Content_item.objects.get(section='tih', page='executive_team', role='section7_title').content_en
        section7_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section7_intro1').content_en
        section7_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section7_intro2').content_en
        section8_title = Content_item.objects.get(section='tih', page='executive_team', role='section8_title').content_en
        section8_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section8_intro1').content_en
        section8_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section8_intro2').content_en
    elif lang == "FR":
        section1_title = Content_item.objects.get(section='tih', page='executive_team', role='section1_title').content_fr
        section1_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section1_intro1').content_fr
        section1_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section1_intro2').content_fr
        section2_title = Content_item.objects.get(section='tih', page='executive_team', role='section2_title').content_fr
        section2_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section2_intro1').content_fr
        section2_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section2_intro2').content_fr
        section3_title = Content_item.objects.get(section='tih', page='executive_team', role='section3_title').content_fr
        section3_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section3_intro1').content_fr
        section3_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section3_intro2').content_fr
        section4_title = Content_item.objects.get(section='tih', page='executive_team', role='section4_title').content_fr
        section4_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section4_intro1').content_fr
        section4_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section4_intro2').content_fr
        section5_title = Content_item.objects.get(section='tih', page='executive_team', role='section5_title').content_fr
        section5_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section5_intro1').content_fr
        section5_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section5_intro2').content_fr
        section6_title = Content_item.objects.get(section='tih', page='executive_team', role='section6_title').content_fr
        section6_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section6_intro1').content_fr
        section6_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section6_intro2').content_fr
        section7_title = Content_item.objects.get(section='tih', page='executive_team', role='section7_title').content_fr
        section7_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section7_intro1').content_fr
        section7_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section7_intro2').content_fr
        section8_title = Content_item.objects.get(section='tih', page='executive_team', role='section8_title').content_fr
        section8_intro1 = Content_item.objects.get(section='tih', page='executive_team', role='section8_intro1').content_fr
        section8_intro2 = Content_item.objects.get(section='tih', page='executive_team', role='section8_intro2').content_fr

    #Set context dictionary
    context.update({
        #
        'menu_executive_team_class' : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/tih/executive_team.html', locals())

#################################################################################################################################
# General
#################################################################################################################################

def home (request):

    #Home is not dynamic. Must set page id
    request.session['page_id'] = 1

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'interested_in' : 'Interested in solutions for …',

            'workers_compensation_boards' : {
                    'text' : 'Workers Compensation Boards',
                    'url' : '/solutions-for/workers-compensation-boards/'
                },

            'health_regions_hospitals' : {
                    'text' : 'Health Regions and Hospitals',
                    'url' : '/solutions-for/health-regions-hospitals/'
                },

            'allied_healthcare_providers' : {
                    'text' : 'Allied Healthcare Providers',
                    'url' : '/solutions-for/allied-healthcare-providers/'
                },

            'physicians' : {
                    'text' : 'Physicians',
                    'url' : '/solutions-for/physicians/'
                },

            'pharmacists' : {
                    'text' : 'Pharmacists',
                    'url' : '/solutions-for/pharmacists/'
                },

            'consumers' : {
                    'text' : 'Consumers',
                    'url' : '/solutions-for/consumers/'
                },

            'insurers_employers' : {
                    'text' : 'Insurers & Employers',
                    'url' : '/solutions-for/insurers-employers/'
                },

            'pharmaceutical' : {
                    'text' : 'Pharmaceutical',
                    'url' : '/solutions-for/pharmaceutical/'
                },

            'media_releases_title' : 'Media releases',
            'mr_show_more' : {
                    'text' : 'Show more',
                    'url' : '/news-events/media-releases/'
                },
            'latest_thinking_title' : 'Latest Thinking',
            'lt_show_more' : {
                    'text' : 'Show more',
                    'url' : '/telus-in-health/latest-thinking/articles/'
                }

        }

    elif lang == 'FR':

        short_copy = {

            'interested_in' : 'Intéressé par les solutions pour…',

            'workers_compensation_boards' : {
                    'text' : 'Commissions des accidents de travail',
                    'url' : '/solutions-pour/commissions-des-accidents-de-travail/'
                },

            'health_regions_hospitals' : {
                    'text' : 'Régie régionales et hôpitaux',
                    'url' : '/solutions-pour/regie-regionales-et-hopitaux/'
                },

            'allied_healthcare_providers' : {
                    'text' : 'Prestataires de soins de santé affiliés',
                    'url' : '/solutions-pour/prestataires-de-soins-de-sante-affilies/'
                },

            'physicians' : {
                    'text' : 'Médecins',
                    'url' : '/solutions-pour/medecins/'
                },

            'pharmacists' : {
                    'text' : 'Pharmaciens',
                    'url' : '/solutions-pour/pharmaciens/'
                },

            'consumers' : {
                    'text' : 'Grand public',
                    'url' : '/solutions-pour/grand-public/'
                },

            'insurers_employers' : {
                    'text' : 'Assureurs et employeurs',
                    'url' : '/solutions-pour/assureurs-et-employeurs/'
                },

            'pharmaceutical' : {
                    'text' : 'Pharmaceutiques',
                    'url' : '/solutions-pour/pharmaceutiques/'
                },

            'media_releases_title' : 'Communiqués de presse',
            'mr_show_more' : {
                    'text' : 'En voir plus',
                    'url' : '/nouvelles-evenements/communiques-de-presse/'
                },
            'latest_thinking_title' : 'Récentes réflexions',
            'lt_show_more' : {
                    'text' : 'En voir plus',
                    'url' : '/telus-en-sante/recentes-reflexions/articles/'
                }

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass

    elif lang == "FR":
        pass

    latest_thinking_items = Latest_Thinking_item.objects.all().order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.all().order_by('-media_release_date')[:2]

    #Set context dictionary
    context.update({

        'lang':lang,
        'region':region,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/general/home.html', locals())

def privacy (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='general', page='privacy', role='page_title').content_en
        privacy = Content_item.objects.get(section='general', page='privacy', role='privacy').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='general', page='privacy', role='page_title').content_fr
        privacy = Content_item.objects.get(section='general', page='privacy', role='privacy').content_fr


    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/privacy.html', locals())

def accessibility (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='general', page='accessibility', role='page_title').content_en
        section1_privacy = Content_item.objects.get(section='general', page='accessibility', role='section1_privacy').content_en
        section1_feedback = Content_item.objects.get(section='general', page='accessibility', role='section1_feedback').content_en
        section1_services1 = Content_item.objects.get(section='general', page='accessibility', role='section1_services1').content_en
        section1_services2 = Content_item.objects.get(section='general', page='accessibility', role='section1_services2').content_en
        section1_pay = Content_item.objects.get(section='general', page='accessibility', role='section1_pay').content_en
        section1_solutions = Content_item.objects.get(section='general', page='accessibility', role='section1_solutions').content_en
        section1_customer = Content_item.objects.get(section='general', page='accessibility', role='section1_customer').content_en
        section1_access = Content_item.objects.get(section='general', page='accessibility', role='section1_access').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='general', page='accessibility', role='page_title').content_fr
        section1_privacy = Content_item.objects.get(section='general', page='accessibility', role='section1_privacy').content_fr
        section1_feedback = Content_item.objects.get(section='general', page='accessibility', role='section1_feedback').content_fr
        section1_services1 = Content_item.objects.get(section='general', page='accessibility', role='section1_services1').content_fr
        section1_services2 = Content_item.objects.get(section='general', page='accessibility', role='section1_services2').content_fr
        section1_pay = Content_item.objects.get(section='general', page='accessibility', role='section1_pay').content_fr
        section1_solutions = Content_item.objects.get(section='general', page='accessibility', role='section1_solutions').content_fr
        section1_customer = Content_item.objects.get(section='general', page='accessibility', role='section1_customer').content_fr
        section1_access = Content_item.objects.get(section='general', page='accessibility', role='section1_access').content_fr

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/accessibility.html', locals())

def legal (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        #page_title = Content_item.objects.get(section='general', page='legal', role='page_title').content_en
        head1 = Content_item.objects.get(section='general', page='legal', role='head1').content_en
        head2 = Content_item.objects.get(section='general', page='legal', role='head2').content_en
        toc = Content_item.objects.get(section='general', page='legal', role='toc').content_en

    elif lang == "FR":
        #page_title = Content_item.objects.get(section='general', page='legal', role='page_title').content_fr
        head1 = Content_item.objects.get(section='general', page='legal', role='head1').content_fr
        head2 = Content_item.objects.get(section='general', page='legal', role='head2').content_fr
        toc = Content_item.objects.get(section='general', page='legal', role='toc').content_fr

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/legal.html', locals())

def provider_registration (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/provider_registration.html', locals())

def health_solutions (request):

    lang = set_lang(request)
    region = set_region(request)

    #Set section to_show
    if request.method == 'GET' and 'id' in request.GET:

        to_show = request.GET['id']

    else:

        if lang == 'EN':
            to_show = "pharmacists"
        if lang == 'FR':
            to_show = "pharmaciens"


    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'interested_in' : 'Interested in solutions for …',

            'hs_workers_compensation_boards' : {
                    'text' : 'Workers Compensation Boards',
                    'url' : '/health-solutions/?id=workers-compensation-boards#section'
                },

            'hs_health_regions_hospitals' : {
                    'text' : 'Health Regions and Hospitals',
                    'url' : '/health-solutions/?id=health-regions-hospitals#section'
                },

            'hs_allied_healthcare_providers' : {
                    'text' : 'Allied Healthcare Providers',
                    'url' : '/health-solutions/?id=allied-healthcare-providers#section'
                },

            'hs_physicians' : {
                    'text' : 'Physicians',
                    'url' : '/health-solutions/?id=physicians#section'
                },

            'hs_pharmacists' : {
                    'text' : 'Pharmacists',
                    'url' : '/health-solutions/?id=pharmacists#section'
                },

            'hs_consumers' : {
                    'text' : 'Consumers',
                    'url' : '/health-solutions/?id=consumers#section'
                },

            'hs_insurers_employers' : {
                    'text' : 'Insurers & Employers',
                    'url' : '/health-solutions/?id=insurers-employers#section'
                },

            'hs_pharmaceutical' : {
                    'text' : 'Pharmaceutical',
                    'url' : '/health-solutions/?id=pharmaceutical#section'
                },

        }

    elif lang == 'FR':

        short_copy = {

            'interested_in' : 'Intéressé par les solutions pour…',

            'hs_allied_healthcare_providers' : {

                'text' : "Prestataires de soins de santé affiliés",
                'url' :  "/solutions-en-sante/?id=prestataires-de-soins-de-sante-affilies#section"

            },

            'hs_consumers' : {

                'text' : "Grand public",
                'url' :  "/solutions-en-sante/?id=grand-public#section"

            },

            'hs_health_regions_hospitals' : {

                'text' : "Régie régionales et hôpitaux",
                'url' :  "/solutions-en-sante/?id=regie-regionales-et-hopitaux#section"

            },

            'hs_insurers_employers' : {

                'text' : "Assureurs et employeurs",
                'url' :  "/solutions-en-sante/?id=assureurs-et-employeurs#section"

            },

            'hs_pharmaceutical' : {

                'text' : "Pharmaceutiques",
                'url' :  "/solutions-en-sante/?id=pharmaceutiques#section"

            },

            'hs_pharmacists' : {

                'text' : "Pharmaciens",
                'url' :  "/solutions-en-sante/?id=pharmaciens#section"

            },

            'hs_physicians' : {

                'text' : "Médecins",
                'url' :  "/solutions-en-sante/?id=medecins#section"

            },

            'hs_workers_compensation_boards' : {

                'text' : "Commissions des accidents de travail",
                'url' :  "/solutions-en-sante/?id=commissions-des-accidents-de-travail#section"

            },

        }

    #TODO: Fix show/hide js
    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        template_name = "/en/"+to_show
    elif lang == "FR":
        template_name = "/fr/"+to_show

    #Set context dictionary
    context.update({
        'template_name' : template_name,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/general/health_solutions.html', locals())

def products (request):

    lang = set_lang(request)
    region = set_region(request)

    #TODO: Fix show/hide js
    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        page_title = Content_item.objects.get(section='general', page='products', role='page_title').content_en
        links1 = Content_item.objects.get(section='general', page='products', role='links1').content_en
        links2 = Content_item.objects.get(section='general', page='products', role='links2').content_en
        links3 = Content_item.objects.get(section='general', page='products', role='links3').content_en
        list1 = Content_item.objects.get(section='general', page='products', role='list1').content_en
        linksA = Content_item.objects.get(section='general', page='products', role='linksA').content_en
        linksC = Content_item.objects.get(section='general', page='products', role='linksC').content_en
        linksD = Content_item.objects.get(section='general', page='products', role='linksD').content_en
        linksE = Content_item.objects.get(section='general', page='products', role='linksE').content_en
        linksF = Content_item.objects.get(section='general', page='products', role='linksF').content_en
        linksH = Content_item.objects.get(section='general', page='products', role='linksH').content_en
        linksI = Content_item.objects.get(section='general', page='products', role='linksI').content_en
        linksK = Content_item.objects.get(section='general', page='products', role='linksK').content_en
        linksM = Content_item.objects.get(section='general', page='products', role='linksM').content_en
        linksO = Content_item.objects.get(section='general', page='products', role='linksO').content_en
        linksP = Content_item.objects.get(section='general', page='products', role='linksP').content_en
        linksR = Content_item.objects.get(section='general', page='products', role='linksR').content_en
        linksS = Content_item.objects.get(section='general', page='products', role='linksS').content_en
        linksT = Content_item.objects.get(section='general', page='products', role='linksT').content_en
        linksU = Content_item.objects.get(section='general', page='products', role='linksU').content_en
        linksW = Content_item.objects.get(section='general', page='products', role='linksW').content_en
        linksX = Content_item.objects.get(section='general', page='products', role='linksX').content_en
        head1 = Content_item.objects.get(section='general', page='products', role='head1').content_en
        head2 = Content_item.objects.get(section='general', page='products', role='head2').content_en
        results = Content_item.objects.get(section='general', page='products', role='results').content_en

    elif lang == "FR":
        page_title = Content_item.objects.get(section='general', page='products', role='page_title').content_fr
        links1 = Content_item.objects.get(section='general', page='products', role='links1').content_fr
        links2 = Content_item.objects.get(section='general', page='products', role='links2').content_fr
        links3 = Content_item.objects.get(section='general', page='products', role='links3').content_fr
        list1 = Content_item.objects.get(section='general', page='products', role='list1').content_fr
        linksA = Content_item.objects.get(section='general', page='products', role='linksA').content_fr
        linksC = Content_item.objects.get(section='general', page='products', role='linksC').content_fr
        linksD = Content_item.objects.get(section='general', page='products', role='linksD').content_fr
        linksE = Content_item.objects.get(section='general', page='products', role='linksE').content_fr
        linksF = Content_item.objects.get(section='general', page='products', role='linksF').content_fr
        linksH = Content_item.objects.get(section='general', page='products', role='linksH').content_fr
        linksI = Content_item.objects.get(section='general', page='products', role='linksI').content_fr
        linksK = Content_item.objects.get(section='general', page='products', role='linksK').content_fr
        linksM = Content_item.objects.get(section='general', page='products', role='linksM').content_fr
        linksO = Content_item.objects.get(section='general', page='products', role='linksO').content_fr
        linksP = Content_item.objects.get(section='general', page='products', role='linksP').content_fr
        linksR = Content_item.objects.get(section='general', page='products', role='linksR').content_fr
        linksS = Content_item.objects.get(section='general', page='products', role='linksS').content_fr
        linksT = Content_item.objects.get(section='general', page='products', role='linksT').content_fr
        linksU = Content_item.objects.get(section='general', page='products', role='linksU').content_fr
        linksW = Content_item.objects.get(section='general', page='products', role='linksW').content_fr
        linksX = Content_item.objects.get(section='general', page='products', role='linksX').content_fr
        head1 = Content_item.objects.get(section='general', page='products', role='head1').content_fr
        head2 = Content_item.objects.get(section='general', page='products', role='head2').content_fr
        results = Content_item.objects.get(section='general', page='products', role='results').content_fr


    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/products.html', locals())

def support_documents_pharmacists (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/support_documents_pharmacists.html', locals())

def prior_authorization_forms (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/prior_authorization_forms.html', locals())

def find_eclaims_enabled_provider (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/find_eclaims_enabled_provider.html', locals())

def newsletters_subscription (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/newsletters_subscription.html', locals())


def support_information_nightingale_users (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/support_information_nightingale_users.html', locals())

def training (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/general/training.html', locals())

##############################################################################################################################
# Latest Thinking
##############################################################################################################################

def lt_home (request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        key_health_issue_get = int(request.GET['key_health_issue']) if 'key_health_issue' in request.GET else 0
        solution_category_get = int(request.GET['solution_category']) if 'solution_category' in request.GET else 0
        content_type_get = int(request.GET['content_type']) if 'content_type' in request.GET else 0
        solutions_for_get = int(request.GET['solutions_for']) if 'solutions_for' in request.GET else 0

    else:

        key_health_issue_get = 0
        solution_category_get = 0
        content_type_get = 0
        solutions_for_get = 0

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'reset_url' : '/telus-in-health/latest-thinking/',
            'all_results' : "All results",
            'category_url' : "/telus-in-health/latest-thinking/category/",
            'item_url' : "/telus-in-health/latest-thinking/item/",
            'show_more_button' : "Show more",
            'see_all' : {
                'text' : 'See all',
                'url' : '/telus-in-health/latest-thinking/articles/'
                }

        }

    elif lang == 'FR':

        short_copy = {

            'reset_url' : '/telus-en-sante/recentes-reflexions/',
            'all_results' : "Tous les résultats",
            'category_url' : "/telus-en-sante/recentes-reflexions/categorie/",
            'item_url' : "/telus-en-sante/recentes-reflexions/item/",
            'show_more_button' : "En voir plus",
            'see_all' : {
                'text' : 'Voir tous les résultats',
                'url' : '/telus-en-sante/recentes-reflexions/articles/'
                }

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    filter_list = []
    if lang == "EN":

        if key_health_issue_get !=0 :
            key_health_issue_get_name = KeyHealthIssue.objects.get(id=key_health_issue_get).issue_en
            filter_list.append(key_health_issue_get_name)

        if solution_category_get !=0 :
            solution_category_get_name = SolutionsCategory.objects.get(id=solution_category_get).category_en
            filter_list.append(solution_category_get_name)

        if content_type_get !=0 :
            content_type_get_name = ContentType.objects.get(id=content_type_get).content_type_en
            filter_list.append(content_type_get_name)

        if solutions_for_get !=0 :
            solutions_for_get_name = SolutionsFor.objects.get(id=solutions_for_get).solutions_for_en
            filter_list.append(solutions_for_get_name)

    elif lang == "FR":

        if key_health_issue_get !=0 :
            key_health_issue_get_name = KeyHealthIssue.objects.get(id=key_health_issue_get).issue_fr
            filter_list.append(key_health_issue_get_name)

        if solution_category_get !=0 :
            solution_category_get_name = SolutionsCategory.objects.get(id=solution_category_get).category_fr
            filter_list.append(solution_category_get_name)

        if content_type_get !=0 :
            content_type_get_name = ContentType.objects.get(id=content_type_get).content_type_fr
            filter_list.append(content_type_get_name)

        if solutions_for_get !=0 :
            solutions_for_get_name = SolutionsFor.objects.get(id=solutions_for_get).solutions_for_fr
            filter_list.append(solutions_for_get_name)

    all_key_health_issues = KeyHealthIssue.objects.all()
    all_solution_categories = SolutionsCategory.objects.all()
    all_content_types = ContentType.objects.all()
    all_solutions_for = SolutionsFor.objects.all()

    featured_items = Latest_Thinking_item.objects.filter(featured_article=True).order_by('-publication_date')[:5]
    first_featured_item_id = featured_items[0].id
    featured_items_count = featured_items.count()
    featured_items_range = range(0, featured_items_count)

    home_items = Latest_Thinking_item.objects

    if key_health_issue_get != 0:
        home_items = home_items.filter(key_health_issue__id__exact=key_health_issue_get)

    if solution_category_get != 0:
        home_items = home_items.filter(solutions_category__id__exact=solution_category_get)

    if content_type_get != 0:
        home_items = home_items.filter(content_type__id__exact=content_type_get)

    if solutions_for_get != 0:
        home_items = home_items.filter(solutions_for__id__exact=solutions_for_get)

    home_items = home_items.order_by('-publication_date')[:25]

    #Set context dictionary
    context.update({

        'menu_latest_thinking_class' : 'current_page_item',
    })

    locals().update(context)
    locals().update(short_copy)

    if request.method == "POST":
        client_data = json.loads(request.POST["client_data"])
        data = {}
        data["render"] = query_lt_home(request, client_data)
        return JsonResponse(data)

    #Return the view
    return render(request, 'core/lt/home.html', locals())

def lt_item (request, item_name):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'h1_title' : 'Latest Thinking',
            'back_to_publications' : {
                'text' : 'Back to publications',
                'url' : '/telus-in-health/latest-thinking/articles/'
                },
            'continue_button' : "Click here to continue reading",
            'article_options' : 'Article options',
            "download_pdf" : "Download PDF version",

            'related' : 'Related Publications'

        }

    elif lang == 'FR':

        short_copy = {

            'h1_title' : 'Récentes réflexions',
            'back_to_publications' : {
                'text' : 'Retour aux publications',
                'url' : '/telus-en-sante/recentes-reflexions/articles/'
                },
            'continue_button' : "Cliquez ici pour poursuivre votre lecture",
            'article_options' : "Options de l'article",
            "download_pdf" : "Télécharger la version PDF",

            'related' : 'Publications connexes'


        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":

        item_content = Latest_Thinking_item.objects.get(item_name_en=item_name)
        title = item_content.title_en
        date = item_content.date_en
        full_text = item_content.full_text_en
        pdf = item_content.pdf_en
        menu_url_fr = "/telus-en-sante/recentes-reflexions/item/{}/".format(item_content.item_name_fr)

    elif lang == "FR":

        item_content = Latest_Thinking_item.objects.get(item_name_fr=item_name)
        title = item_content.title_fr
        date = item_content.date_fr
        full_text = item_content.full_text_fr
        pdf = item_content.pdf_fr
        menu_url_en = "/telus-in-health/latest-thinking/item/{}/".format(item_content.item_name_en)

    #Set context dictionary
    context.update({

        'menu_latest_thinking_class' : 'current_page_item',
        'item_name':item_name,
    })

    related_items = Latest_Thinking_item.objects.filter(key_health_issue__in=item_content.key_health_issue.all()).exclude(id=item_content.id).order_by('-publication_date')[:4]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/lt/item.html', locals())

def lt_category (request, key_health_issue_link):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'all_results' : 'All results',
            'category' : 'Category',

        }

    elif lang == 'FR':

        short_copy = {

            'all_results' : 'Tous les résultats',
            'category' : 'Catégories',

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        key_health_issue = KeyHealthIssue.objects.get(issue_link_en =key_health_issue_link)
        h1_title = key_health_issue.issue_en
        menu_url_fr = "/telus-en-sante/recentes-reflexions/categorie/{}/".format(key_health_issue.issue_link_fr)
    elif lang == "FR":
        key_health_issue = KeyHealthIssue.objects.get(issue_link_fr =key_health_issue_link)
        h1_title = key_health_issue.issue_fr
        menu_url_en = "/telus-in-health/latest-thinking/category/{}/".format(key_health_issue.issue_link_en)

    #Set context dictionary
    context.update({

        'menu_latest_thinking_class' : 'current_page_item',
    })

    all_key_health_issues = KeyHealthIssue.objects.all()
    all_items_list = Latest_Thinking_item.objects.filter(key_health_issue__id=key_health_issue.id).order_by('-publication_date')
    paginator = Paginator(all_items_list, 10)

    page = request.GET.get('page')

    try:
        all_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        all_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        all_items = paginator.page(paginator.num_pages)

    #Set context dictionary
    context.update({

        'menu_latest_thinking_class' : 'current_page_item',
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/lt/category.html', locals())

def lt_articles (request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        key_health_issue_get = int(request.GET['key_health_issue']) if 'key_health_issue' in request.GET else 0
        solution_category_get = int(request.GET['solution_category']) if 'solution_category' in request.GET else 0
        content_type_get = int(request.GET['content_type']) if 'content_type' in request.GET else 0
        solutions_for_get = int(request.GET['solutions_for']) if 'solutions_for' in request.GET else 0

    else:

        key_health_issue_get = 0
        solution_category_get = 0
        content_type_get = 0
        solutions_for_get = 0

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'all_results' : 'All results',

            'category' : 'Category',

            'long_wait_times' : {
                'text' : 'Access and care continuity',
                'url' : '/telus-in-health/latest-thinking/category/long-wait-times/'
                },

            'chronic_disease_management' : {
                'text' : 'Chronic disease management',
                'url' : '/telus-in-health/latest-thinking/category/chronic-disease-management/'
                },

            'general_subject' : {
                'text' : 'General subject',
                'url' : '/telus-in-health/latest-thinking/category/general-subject/'
                },

            'medication_errors_and_non_compliance' : {
                'text' : 'Medication Management',
                'url' : '/telus-in-health/latest-thinking/category/medication-errors-and-non-compliance/'
                },

            'performance_improvement' : {
                'text' : 'Performance management',
                'url' : '/telus-in-health/latest-thinking/category/the-need-for-performance-improvement/'
                },

            'lack_focus' : {
                'text' : 'Prevention and self-management',
                'url' : '/telus-in-health/latest-thinking/category/lack-of-focus/'
                }

        }

    elif lang == 'FR':

        short_copy = {

            'all_results' : 'Tous les résultats',

            'category' : 'Catégories',

            'long_wait_times' : {
                'text' : 'Accès et continuité des soins',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/acces-et-continuite-des-soins/'
                },

            'chronic_disease_management' : {
                'text' : 'Gestion des maladies chroniques',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/gestion-des-maladies-chroniques/'
                },

            'general_subject' : {
                'text' : 'Sujet général',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/sujet-general/'
                },

            'medication_errors_and_non_compliance' : {
                'text' : 'Gestion de la médication',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/gestion-de-la-medication/'
                },

            'performance_improvement' : {
                'text' : 'Gestion de la performance',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/gestion-de-la-performance/'
                },

            'lack_focus' : {
                'text' : 'Prévention et autogestion',
                'url' : '/telus-en-sante/recentes-reflexions/categorie/prevention-et-autogestion/'
                }

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        h1_title = "Latest Thinking"
    elif lang == "FR":
        h1_title = "Récentes réflexions"

    all_key_health_issues = KeyHealthIssue.objects.all()
    all_solution_categories = SolutionsCategory.objects.all()
    all_content_types = ContentType.objects.all()
    all_solutions_for = SolutionsFor.objects.all()

    all_items_list = Latest_Thinking_item.objects.all()

    if key_health_issue_get != 0:
        all_items_list = all_items_list.filter(key_health_issue__id__exact=key_health_issue_get)

    if solution_category_get != 0:
        all_items_list = all_items_list.filter(solutions_category__id__exact=solution_category_get)

    if content_type_get != 0:
        all_items_list = all_items_list.filter(content_type__id__exact=content_type_get)

    if solutions_for_get != 0:
        all_items_list = all_items_list.filter(solutions_for__id__exact=solutions_for_get)

    all_items_list = all_items_list.order_by('-publication_date')

    paginator = Paginator(all_items_list, 10)
    page = request.GET.get('page')

    try:
        all_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        all_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        all_items = paginator.page(paginator.num_pages)

    #Set context dictionary
    context.update({

        'menu_latest_thinking_class' : 'current_page_item',
    })

    locals().update(context)
    locals().update(short_copy)
    if request.method == "POST":
        client_data = json.loads(request.POST["client_data"])
        data = {}
        data["render"] = query_upcoming_events(request, client_data)
        return JsonResponse(data)
    #Return the view
    return render(request, 'core/lt/articles.html', locals())

##############################################################################################################################
# News and events
##############################################################################################################################

def news_events (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'news_events_mr' : 'Media releases',

            'news_events_see_more_news' : {
                'text' : 'See more news',
                'url' : '/news-events/media-releases/'
                },

            'news_events_ue' : 'Upcoming Events',

            'news_events_see_more_events' : {
                'text' : 'See more events',
                'url' : '/news-events/events/'
                },

        }

    elif lang == 'FR':

        short_copy = {

            'news_events_mr' : 'Communiqués de presse',

            'news_events_see_more_news' : {
                'text' : 'Voir plus de nouvelles',
                'url' : '/nouvelles-evenements/communiques-de-presse/'
                },

            'news_events_ue' : 'Événements à venir',

            'news_events_see_more_events' : {
                'text' : "Voir plus d'événements",
                'url' : '/nouvelles-evenements/evenements/'
                },

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass


    #Set context dictionary
    context.update({

    })

    news_items = Media_Release_item.objects.all().order_by('-media_release_date')[:2]
    events_items = Event_item.objects.all().order_by('-date_time')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/news_events/home.html', locals())

def media_releases (request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        solution_category_get = int(request.GET['solution_category']) if 'solution_category' in request.GET else 0
        solutions_for_get = int(request.GET['solutions_for']) if 'solutions_for' in request.GET else 0
        publication_year_get = int(request.GET['publication_year']) if 'publication_year' in request.GET else 0

    else:

        solution_category_get = 0
        solutions_for_get = 0
        publication_year_get = 0

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'media_releases_tab' : {
                'text' : 'Recent media releases',
                'url' : '/news-events/media-releases/'
            },
            'a_media_release_url' : '/news-events/media-release/'

        }

    elif lang == 'FR':

        short_copy = {

            'media_releases_tab' : {
                'text' : 'Derniers communiqués de presse',
                'url' : '/nouvelles-evenements/communiques-de-presse/'
            },
            'a_media_release_url' : '/nouvelles-evenements/nouvelle/'

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    all_solution_categories = SolutionsCategory.objects.all()
    all_solutions_for = SolutionsFor.objects.all()
    publication_years = [2017, 2016, 2015, 2014, 2013, 2012]

    all_items_list = Media_Release_item.objects.all()

    if solution_category_get != 0:
        all_items_list = all_items_list.filter(solutions_category__id__exact=solution_category_get)

    if solutions_for_get != 0:
        all_items_list = all_items_list.filter(solutions_for__id__exact=solutions_for_get)

    if publication_year_get != 0:
        all_items_list = all_items_list.filter(media_release_date__year=publication_year_get)

    all_items_list = all_items_list.order_by('-media_release_date')
    paginator = Paginator(all_items_list, 6)

    page = request.GET.get('page')

    try:
        all_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        all_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        all_items = paginator.page(paginator.num_pages)

    #Set context dictionary
    context.update({

        'show_carousel' : True,
        'show_navbar' : True,
    })


    locals().update(context)
    locals().update(short_copy)
    if request.method == "POST":
        client_data = json.loads(request.POST["client_data"])
        data = {}
        data["render"] = query_media_releases(request, client_data)
        return JsonResponse(data)

    #Return the view
    return render(request, 'core/news_events/media_releases.html', locals())


def a_media_release (request, item_name):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'back_to_news' : {
                'text' : 'Back to News',
                'url' : '/news-events/media-releases/'
            },

        }

    elif lang == 'FR':

        short_copy = {

            'back_to_news' : {
                'text' : 'Retour aux nouvelles',
                'url' : '/nouvelles-evenements/communiques-de-presse/'
            },

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":

        item = Media_Release_item.objects.get(item_name_en=item_name)
    elif lang == "FR":

        item = Media_Release_item.objects.get(item_name_fr=item_name)

    #Set context dictionary
    context.update({

        'show_carousel' : False,
        'show_navbar' : False,
    })

    related_news = Media_Release_item.objects.filter(solutions_category__in=item.solutions_category.all()).order_by('-media_release_date').exclude(id=item.id)[:2]
    related_publications = Latest_Thinking_item.objects.filter(solutions_category__in=item.solutions_category.all()).order_by('-publication_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/news_events/a_media_release.html', locals())

def upcoming_events (request):

    lang = set_lang(request)
    region = set_region(request)

    if request.method == 'GET':

        solution_category_get = int(request.GET['solution_category']) if 'solution_category' in request.GET else 0
        solutions_for_get = int(request.GET['solutions_for']) if 'solutions_for' in request.GET else 0
        province_get = str(request.GET['province']) if 'province' in request.GET else ""

    else:

        solution_category_get = 0
        solutions_for_get = 0
        province_get = ""

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'featured_events_tab' : {
                'text' : 'Featured Events',
                'url' : '/news-events/events/'
            },

            'an_event_url' : '/news-events/event/'

        }

    elif lang == 'FR':

        short_copy = {

            'featured_events_tab' : {
                'text' : 'Evénements sélectionnés',
                'url' : '/nouvelles-evenements/evenements/'
            },

            'an_event_url' : '/nouvelles-evenements/evenement/'

        }

    #Get page specific content
    if lang == "EN":
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))
    elif lang == "FR":
        all_provinces = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))

    all_solution_categories = SolutionsCategory.objects.all()
    all_solutions_for = SolutionsFor.objects.all()

    today = datetime.date.today()
    all_items_list = Event_item.objects.all().filter(event_date__gte=today)

    if solution_category_get != 0:
        all_items_list = all_items_list.filter(solutions_category__id__exact=solution_category_get)

    if solutions_for_get != 0:
        all_items_list = all_items_list.filter(solutions_for__id__exact=solutions_for_get)

    if province_get != "":
        all_items_list = all_items_list.filter(event_province=province_get)

    #all_items_list = all_items_list.filter(event_date__gte=today).order_by('-event_date')
    all_items_list = all_items_list.order_by('-event_date')

    paginator = Paginator(all_items_list, 6)
    page = request.GET.get('page')

    try:
        all_items = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        all_items = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        all_items = paginator.page(paginator.num_pages)

    #Set context dictionary
    context.update({

        'show_carousel' : True,
        'show_navbar' : True,
    })

    locals().update(context)
    locals().update(short_copy)
    if request.method == "POST":
        client_data = json.loads(request.POST["client_data"])
        data = {}
        data["render"] = query_upcoming_events(request, client_data)
        return JsonResponse(data)

    #Return the view
    return render(request, 'core/news_events/upcoming_events.html', locals())

def an_event (request, item_name):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'back_to_events' : {
                'text' : 'Back to Events',
                'url' : '/news-events/events/'
            }

        }

    elif lang == 'FR':

        short_copy = {

            'back_to_events' : {
                'text' : 'Retour aux événements',
                'url' : '/nouvelles-evenements/evenements/'
            }

        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":

        item = Event_item.objects.get(item_name_en=item_name)
    elif lang == "FR":

        item = Event_item.objects.get(item_name_fr=item_name)

    #Set context dictionary
    context.update({

        'show_carousel' : False,
        'show_navbar' : False,
    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/news_events/an_event.html', locals())

##############################################################################################################################
# Contact
##############################################################################################################################

def contact_telus_health (request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'call_us' : 'Call us',
            'call_us_phone' : '1-888-709-8759',
            'other_contact_methods' : 'Other Contact Methods',
            'contact_page_support' : {
                        'text' : 'Support',
                        'url' : '/contact-telus-health/support/'
                },
            'contact_page_sales' : {
                        'text' : 'Sales',
                        'url' : '/contact-telus-health/sales/'
                },
            'our_offices_inc' : "en/our_offices",
        }

    elif lang == 'FR':

        short_copy = {

            'call_us' : 'Appelez-nous',
            'call_us_phone' : '1-888-709-8759',
            'other_contact_methods' : 'Autres moyens de contact',
            'contact_page_support' : {
                        'text' : 'Soutien technique',
                        'url' : '/contacter-telus-sante/soutien/'
                },
            'contact_page_sales' : {
                        'text' : 'Ventes',
                        'url' : '/contacter-telus-sante/ventes/'
                },
            'our_offices_inc' : "fr/our_offices"
        }

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass


    #Set context dictionary
    context.update({

    })

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/contact_us/contact_telus_health.html', locals())

def contact_telus_health_sales (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        sales_or_support =  "sales"
    elif lang == "FR":
        sales_or_support =  "ventes"


    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/contact_us/contact_telus_health_sales_support.html', locals())

def contact_telus_health_support (request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content
    if lang == "EN":
        sales_or_support =  "support"
    elif lang == "FR":
        sales_or_support =  "soutien-technique"

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/contact_us/contact_telus_health_sales_support.html', locals())

######################################################################################################################
# Professional Services
######################################################################################################################

def pshcp_base_context(request):

    #Get base generic context
    context = base_context(request)

    short_copy= {}
    lang = set_lang(request)
    if lang == 'EN':
        short_copy = {

            'overview' : {
                        'text' : 'Overview',
                        'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/overview/'
                },
            'registration' : {
                        'text' : 'Registration',
                        'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/registration/'
                },
            'faq' : {
                        'text' : 'FAQ',
                        'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/faq/'
                },
            'information' : {
                        'text' : 'Information',
                        'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/information/'
                },
            'pseudo_din_list' : {
                        'text' : 'Medical Supplies Pseudo-DIN List',
                        'url' : '/health-solutions/claims-and-benefits-management/pshcp-provider-information/medical-supplies-pseudo-din-list/'
                }
        }

    elif lang == 'FR':
        short_copy = {

            'overview' : {
                        'text' : 'Aperçu',
                        'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/apercu/'
                },
            'registration' : {
                        'text' : 'Inscription',
                        'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/inscription/'
                },
            'faq' : {
                        'text' : 'Foire aux questions',
                        'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/foire-aux-questions/'
                },
            'information' : {
                        'text' : 'Renseignements',
                        'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/renseignements/'
                },
            'pseudo_din_list' : {
                        'text' : 'Liste de pseudo-DIN pour fournitures médicales',
                        'url' : '/solutions-en-sante/gestion-des-demandes-de-reglement-en-sante/renseignements-sur-le-fournisseur-du-rssfp/liste-de-pseudo-din-pour-fournitures-medicales/'
                }
        }

    #Set base context dictionary
    ps_base_context = {

        #Set menu classes
        'menu_overview_class'           : '',
        'menu_registration_class'       : '',
        'menu_faq_class'                : '',
        'menu_information_class'        : '',
        'menu_pseudo_din_list_class'          : '',

        #Show carousel
        'show_carousel'                 : False,
        'show_latest_thinking'          : False,
        'show_media_releases'           : False,
        'show_solutions_cta'            : False,

    }

    #Set context dictionary
    context.update(ps_base_context)
    context.update(short_copy)

    return context

def pshcp_overview(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pshcp_base_context(request)

    #Get page specific content
    if lang == "EN":
        intro = Content_item.objects.get(section='pshcp', page='overview', role='intro').content_en
        box_left = Content_item.objects.get(section='pshcp', page='overview', role='box_left').content_en
        box_right = Content_item.objects.get(section='pshcp', page='overview', role='box_right').content_en
    elif lang == "FR":
        intro = Content_item.objects.get(section='pshcp', page='overview', role='intro').content_fr
        box_left = Content_item.objects.get(section='pshcp', page='overview', role='box_left').content_fr
        box_right = Content_item.objects.get(section='pshcp', page='overview', role='box_right').content_fr

    #Set context dictionary
    context.update({
        'menu_overview_class'           : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pshcp/pshcp_overview.html', locals())

def pshcp_registration(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pshcp_base_context(request)

    short_copy= {}
    if lang == 'EN':
        short_copy = {

            'contact' : {
                    'tel' : '1-800-668-1608',
                    'hours' : '8:00am to 12:00am (EST)'
                }
        }

    elif lang == 'FR':
        short_copy = {

            'contact' : {
                    'tel' : '1 800 668-1608',
                    'hours' : "8 h à 24 h, heure de l'Est"
                }
        }

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'menu_registration_class'           : 'current_page_item',
    })

    locals().update(context)
    context.update(short_copy)

    #Return the view
    return render(request, 'core/pshcp/pshcp_registration.html', locals())

def pshcp_faq(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pshcp_base_context(request)

    short_copy= {}
    if lang == 'EN':
        short_copy = {

            'faq' : "Frequently Asked Questions"
        }

    elif lang == 'FR':
        short_copy = {

            'faq' : "Foire aux questions"
        }

    #Get page specific content
    if lang == "EN":
        pass
    elif lang == "FR":
        pass

    #Set context dictionary
    context.update({
        'menu_faq_class'           : 'current_page_item',
    })

    locals().update(context)
    context.update(short_copy)

    #Return the view
    return render(request, 'core/pshcp/pshcp_faq.html', locals())

def pshcp_information(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pshcp_base_context(request)

    #Get page specific content
    if lang == "EN":
        intro = Content_item.objects.get(section='pshcp', page='information', role='intro').content_en
        box_left = Content_item.objects.get(section='pshcp', page='information', role='box_left').content_en
        box_right = Content_item.objects.get(section='pshcp', page='information', role='box_right').content_en
    elif lang == "FR":
        intro = Content_item.objects.get(section='pshcp', page='information', role='intro').content_fr
        box_left = Content_item.objects.get(section='pshcp', page='information', role='box_left').content_fr
        box_right = Content_item.objects.get(section='pshcp', page='information', role='box_right').content_fr

    #Set context dictionary
    context.update({
        'menu_information_class'           : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pshcp/pshcp_information.html', locals())

def pshcp_pseudo_din_list(request):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = pshcp_base_context(request)

    #Get page specific content
    if lang == "EN":
        intro = Content_item.objects.get(section='pshcp', page='pseudo_din_list', role='intro').content_en
    elif lang == "FR":
        intro = Content_item.objects.get(section='pshcp', page='pseudo_din_list', role='intro').content_fr

    #Set context dictionary
    context.update({
        'menu_pseudo_din_list_class'           : 'current_page_item',
    })

    locals().update(context)

    #Return the view
    return render(request, 'core/pshcp/pshcp_pseudo_din_list.html', locals())



def search(request, query):

    lang = set_lang(request)
    region = set_region(request)

    #Get base generic context
    context = base_context(request)

    #Get page specific content

    #Set context dictionary
    context.update({

    })

    locals().update(context)

    #Return the view
    return render(request, 'core/search/result.html', locals())


def pharmacists_home(request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Download claims documents ",
                    'url' : "/support-documents-pharmacists/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Order online ",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Training",
                    'url' : "/training/"
                },

            'receipt' : {
                'title' : "Receipts",
                'text' : "Personalised and non-personalised receipts"
            },

            'labels': {
                'title' : "Labels",
                'text': "Personalised and non-personalised labels"
            },

            'cartridges': {
                'title' : "Cartridges",
                'text': "Refurbished printer cartridges and photo conductors"
            },

            'order_start': {
                'text': "Start a new order"
            },

            'links' : {

                'network' : "/health-solutions/pharmacy-management/our-solutions/assyst-network/",
                'pos' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/",
                'posqc' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/",
                'dopill' : "/health-solutions/pharmacy-management/our-solutions/do-pill/",
                'ps' : "/health-solutions/pharmacy-management/our-solutions/pharma-space/",
                'rxvigi' : "/health-solutions/pharmacy-management/our-solutions/rx-vigilance/",
                'ubik' : "/health-solutions/pharmacy-management/our-solutions/telus-ubik/",
                'xpill' : "/health-solutions/pharmacy-management/our-solutions/xpill-pharma/",
                },

            'page_title': "Order online Solutions for Pharmacists",

            'nav' : {
                '1' : "1. Select Your Product",
                '2' : "2. Review Order",
                '3' : "3. Tell Us About Yourself"
            }

        }



    elif lang == 'FR':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Documents de Demandes de règlement",
                    'url' : "/documents-soutien-pharmaciens/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Commande en ligne",
                    'url' : "/solutions-pour/pharmaciens/commande-en-ligne/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Formation",
                    'url' : "/formation/"
                },

            'receipt': {
                'title': "Reçus",
                'text': "Reçus personnalisés et non-personnalisés."
            },

            'labels': {
                'title': "Étiquettes",
                'text': "Étiquettes personnalisées et non-personnalisées."
            },

            'cartridges': {
                'title': "Cartouches d’impression",
                'text': "Cartouches d’imprimante ré-usinées et photo conducteurs."
            },

            'order_start' : {
                'text' : "Débuter une nouvelle commande"
            },

            'links' : {

                'network' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/",
                'pos' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/",
                'posqc' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/",
                'dopill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/",
                'ps' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/",
                'rxvigi' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/",
                'ubik' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/",
                'xpill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/",

                },

            'page_title' : 'Solutions pour Pharmaciens',

            'nav': {
                '1': "1. Sélection",
                '2': "2. Revoir la commande",
                '3': "3. Entrez vos Coordinees"
            }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":
        carousel_title = Content_item.objects.get(section='pharmacists', page='pharmacists_home', role='carousel_title').content_en
        carousel_content = Content_item.objects.get(section='pharmacists', page='pharmacists_home', role='carousel_content').content_en
    elif lang == "FR":
        carousel_title = Content_item.objects.get(section='pharmacists', page='pharmacists_home', role='carousel_title').content_fr
        carousel_content = Content_item.objects.get(section='pharmacists', page='pharmacists_home', role='carousel_content').content_fr

    #Set context dictionary
    context.update({
        'show_carousel' : True,
        'show_media_releases' : False,
        'show_events' : False,
        'show_latest_thinking' : False,
        'show_solutions_cta' : False,

    })
    latest_thinking_items = Latest_Thinking_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-publication_date')[:3]
    media_releases_items = Media_Release_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-media_release_date')[:2]
    event_items = Event_item.objects.filter(solutions_for__id=context['solutions_for']['pharmacists']).order_by('-event_date')[:2]

    locals().update(context)
    locals().update(short_copy)

    #Return the view
    return render(request, 'core/pharmacists_order_online/pharmacists_home.html', locals())

@csrf_exempt
def pharmacists_order_online(request):

    lang = set_lang(request)
    region = set_region(request)

    short_copy= {}
    if lang == 'EN':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Download claims documents ",
                    'url' : "/support-documents-pharmacists/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Order online ",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Training",
                    'url' : "/training/"
                },

            'receipt': {
                'title': "Receipts",
                'text': "Personalised and non-personalised receipts"
                },

            'labels': {
                'title': "Labels",
                'text': "Personalised and non-personalised labels"
                },

            'cartridges': {
                'title': "Cartridges",
                'text': "Refurbished printer cartridges and photo conductors"
                },

            'page_title': "Order online Solutions for Pharmacists",

            'links' : {

                'network' : "/health-solutions/pharmacy-management/our-solutions/assyst-network/",
                'pos' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale/",
                'posqc' : "/health-solutions/pharmacy-management/our-solutions/assyst-point-sale-quebec/",
                'dopill' : "/health-solutions/pharmacy-management/our-solutions/do-pill/",
                'ps' : "/health-solutions/pharmacy-management/our-solutions/pharma-space/",
                'rxvigi' : "/health-solutions/pharmacy-management/our-solutions/rx-vigilance/",
                'ubik' : "/health-solutions/pharmacy-management/our-solutions/telus-ubik/",
                'xpill' : "/health-solutions/pharmacy-management/our-solutions/xpill-pharma/",

                },

            'nav' : {
                '1': "1. Select Your Product",
                '2': "2. Review Order",
                '3': "3. Tell Us About Yourself"
            },

            'product_mics' : {
                '1' : 'Select the appropriate logo for your pharmacy.',
                '2' : 'Per box',
                '3' : 'Quantity',
                '4' : 'Total',
                '5' : 'Add to Order',
                '6' : 'Order Updated',
                '7' : 'Contact Us',
                '8' : 'Update Order'
            },

            'footer_mics' : {
                '1' : 'Products',
                '2' : 'Subtotal',
                '3' : "Next"
            }

        }

    elif lang == 'FR':

        short_copy = {

            'sf_pharmacists_docs' : {
                    'text' : "Documents de Demandes de règlement",
                    'url' : "/documents-soutien-pharmaciens/"
                },

            'sf_pharmacists_order' : {
                    'text' : "Commande en ligne",
                    'url' : "/solutions-for/pharmacists/order-online/"
                },

            'sf_pharmacists_training' : {
                    'text' : "Formation",
                    'url' : "/formation/"
                },

            'page_title': 'Solutions pour Pharmaciens',

            'receipt': {
                'title': "Reçus",
                'text': "Reçus personnalisés et non-personnalisés."
            },

            'labels': {
                'title': "Étiquettes",
                'text': "Étiquettes personnalisées et non-personnalisées."
            },

            'cartridges': {
                'title': "Cartouches d’impression",
                'text': "Cartouches d’imprimante ré-usinées et photo conducteurs."
            },

            'links' : {

                'network' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-reseau/",
                'pos' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente/",
                'posqc' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/assyst-point-de-vente-quebec/",
                'dopill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/do-pill/",
                'ps' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/espace-pharma/",
                'rxvigi' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions//rx-vigilance/",
                'ubik' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/ubik/",
                'xpill' : "/solutions-sante/solutions-de-gestion-de-pharmacies/nos-solutions/xpill-pharma/",

                },

            'nav': {
                '1': "1. Sélection",
                '2': "2. Revoir la commande",
                '3': "3. Entrez vos Coordinees"
            },

            'product_mics': {
                '1' : 'Sélectionnez le logo approprié pour votre pharmacie.',
                '2' : 'Par boîte',
                '3' : 'Quantité',
                '4' : 'Total',
                '5' : 'Ajouter',
                '6' : 'Mise à jour',
                '7' : 'Contactez-nous à',
                '8' : 'Mise à jour de la commande'
            },

            'footer_mics': {
                '1': 'Des produits',
                '2': 'Soustotal',
                '3': "Prochain"
            }

        }

    #Get base generic context
    context = sf_base_context(request)

    #Get page specific content
    if lang == "EN":

        contact_us = Content_item.objects.get(section='pharmacists', page='order_online', role='contact').content_en

    elif lang == "FR":
        contact_us = Content_item.objects.get(section='pharmacists', page='order_online', role='contact').content_fr



    total = 0
    totalqty = 0

    #Get page specific content
    #page_title = Content_item.objects.get(section='emr', page='emr_welcome_overview', role='page_title')

    #Get all pharmacy products that are active
    pharmacy_products = Pharmacy_Product.objects.filter(active=True)

    #Get categories
    categories = Pharmacy_Product_Category.objects.filter(active=True)
        #Get page info

    page_id = request.session.get('page_id')
    page = Page.objects.get(id=page_id)

    #Get lang and region
    lang = set_lang(request)
    region = set_region(request)

    #Get copy
    copy = Copy(lang, region, page)
    dictionary = copy.base_dictionary()

    try:
        order = request.get_signed_cookie('order', salt='th1sw2bs3t4nam5')
    except KeyError:
        order = {}
    if type(order) is str:
        order = ast.literal_eval(order)
    xx = [x for x in order.keys()]
    ordered_products = Pharmacy_Product.objects.filter(id__in=xx)

    responsedata = {}
    productpk = {}
    for product in ordered_products:
        productdata = {}
        qty = order[product.id]
        price = qty * product.price
        productdata['min_qty'] = product.minimum_order
        productdata['price'] = product.price
        if lang == 'EN':
            productdata['title'] = product.title_en
            productdata['description'] = product.description_en
        else:
            productdata['title'] = product.title_fr
            productdata['description'] = product.description_fr
        productdata['ptotal'] = price
        productdata['qty'] = order[product.id]
        productdata['id'] = product.id
        productdata['image'] = static("images/default_image.jpg")
        if product.image:
            productdata['image'] = product.image.url
            print("product image url is", product.image.url)
        total += price
        totalqty += qty
        productpk[product.id] = productdata

    totalmain = 0
    totalsub = "00"
    if total != 0:
        total = str(total).split('.')
        totalmain = total[0]
        totalsub = total[1]
    if request.is_ajax():
        responsedata['products'] = productpk
        responsedata['extras'] = {'total': total, "totalmain":totalmain, 'totalqty':totalqty, "totalsub":totalsub}
        if request.method == 'POST':
            json_str =  (request.body).decode('utf-8')
            json_obj = json.loads(json_str)
            print("Yesy",json_obj, total, totalsub)
            thisorder = PharmacyProduct_Order.objects.create(
                            firstname = json_obj['FirstName'],
                            lastname = json_obj['LastName'],
                            email = json_obj['Email'],
                            phone = json_obj['Phone'],
                            company = json_obj['Company'],
                            address = json_obj['Address'],
                            address2 = json_obj['BillingStreet'],
                            city = json_obj['City'],
                            state = json_obj['province'],
                            country = json_obj['Country'],
                            postalcode = json_obj['PostalCode'],
                            region = json_obj['customMarketoRegion'],
                            total = float(int(total[0])+(int(total[1])*0.01))
                        )
            for product in ordered_products:
                carty = CartItem.objects.create(order= thisorder,
                                    product = product,
                                    quantity = order[product.id],
                                    )
            order_dic_data = {
                'firstname': json_obj['FirstName'],
                'lastname':json_obj['LastName'],
                'email': json_obj['Email'],
                'order': order,
                'ordered_products': ordered_products,
                "total": (int(total[0]) + (float(total[1]) * 0.01)),
                "totalqty": totalqty,
                "order_date": carty.dateCreated,
                "order_id": carty.id,
                }
            client_feedback = render_to_string('includes/product_order_client.html', order_dic_data)
            seller_feedback = render_to_string('includes/product_order_seller.html', order_dic_data)
            print("this", strip_tags(seller_feedback), client_feedback)
            send_mail('Your Order Was Received', strip_tags(client_feedback), settings.DEFAULT_FROM_EMAIL, [json_obj['Email']], html_message=client_feedback)
            send_mail('New Order Received', strip_tags(seller_feedback), settings.DEFAULT_FROM_EMAIL, [settings.DEFAULT_TO_EMAIL], html_message=client_feedback)
            responsedata['products'] = {}
            responsedata['extras'] = {'total': '0', "totalmain":0, 'totalqty':0, "totalsub":"00"}
            response = JsonResponse(responsedata)
            response.delete_cookie('order')
            return response
        response = JsonResponse(responsedata)
        return response


    #print('copy is', copy.base_dictionary())


    #Set context dictionary
    context.update({
        'show_carousel' : False,
        'show_media_releases' : False,
        'show_events' : False,
        'show_latest_thinking' : False,
        'show_solutions_cta' : False,
        'pharmacy_products': pharmacy_products,
        'categories': categories,
        'totalmain': totalmain,
        'totalsub': totalsub,
        'totalqty': totalqty,

    })
    locals().update(context)
    locals().update(short_copy)
    print("SDF", short_copy.get('product_mics'))
    #Return the view
    # return render(request, 'core/sf/sf_pharmacists.html', locals())
    #Return the view
        #Get page specific content

    return render(request, 'core/pharmacists_order_online/pharmacists_order_online.html', locals())
