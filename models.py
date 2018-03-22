#!/usr/bin/python
# -*- coding: latin-1 -*-
from django.db import models
from django.shortcuts import HttpResponse

from unittest.util import _MAX_LENGTH
from django.template.defaultfilters import title
#from blinker._utilities import text
#from Onboard.WindowUtils import Orientation
from django.utils.translation import ugettext_lazy as _

class Page(models.Model):
    
    section_name_en = models.CharField(max_length=255)
    page_name_en = models.CharField(max_length=255)
    url_en = models.CharField(max_length=255)
    section_name_fr = models.CharField(max_length=255)
    page_name_fr = models.CharField(max_length=255)
    url_fr = models.CharField(max_length=255)
    view = models.CharField(max_length=255)
    
    def __str__(self):
            return self.page_name_en

class KeyHealthIssue(models.Model):
    
    issue_en = models.CharField(max_length=250, default="", null=True, blank=True)
    issue_link_en = models.CharField(max_length=250, default="", null=True, blank=True)
    
    issue_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    issue_link_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    def __str__(self):
            return self.issue_en
    
class SolutionsCategory (models.Model):
    
    category_en = models.CharField(max_length=250, default="", null=True, blank=True)
    category_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    def __str__(self):
            return self.category_en
    
class ContentType (models.Model):
    
    content_type_en = models.CharField(max_length=250, default="", null=True, blank=True)
    content_type_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    def __str__(self):
            return self.content_type_en
    
class SolutionsFor (models.Model):
    
    solutions_for_en = models.CharField(max_length=250, default="", null=True, blank=True)
    solutions_for_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    def __str__(self):
            return self.solutions_for_en
       
class Content_item(models.Model):
    
    #Where content goes
    section = models.CharField(max_length=200)
    page = models.CharField(max_length=200)
    role = models.CharField(max_length=50)
    
    #The content itself
    content_en = models.TextField(default="")
    content_fr = models.TextField(default="")
    
class Latest_Thinking_item(models.Model):
    
    date_time = models.DateTimeField(auto_now_add=True)  
    publication_date = models.DateField(null=True, blank=True)
    
    image = models.CharField(max_length=250, default="", null=True, blank=True)
    show_pdf_button_in_article = models.BooleanField()
    featured_article = models.BooleanField(default=False)
    
    #Classification
    solutions_category = models.ManyToManyField(SolutionsCategory)
    solutions_for = models.ManyToManyField(SolutionsFor)
    content_type = models.ManyToManyField(ContentType)
    key_health_issue = models.ManyToManyField(KeyHealthIssue)
    
    date_en = models.CharField(max_length=30, default="", null=True, blank=True) #April 21, 2017
    item_name_en = models.CharField(max_length=250, default="", null=True, blank=True)
    title_en = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_en = models.TextField(default="", null=True, blank=True)
    full_text_en = models.TextField(default="", null=True, blank=True)
    pdf_en = models.CharField(max_length=250, default="", null=True, blank=True)
    
    date_fr = models.CharField(max_length=30, default="", null=True, blank=True) #28 juillet 2017
    item_name_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    title_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_fr = models.TextField(default="", null=True, blank=True)
    full_text_fr = models.TextField(default="", null=True, blank=True)
    pdf_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
class Media_Release_item(models.Model):
    
    date_time = models.DateTimeField(auto_now_add=True) 
    media_release_date = models.DateField(null=True, blank=True)
     
    image = models.CharField(max_length=250, default="", null=True, blank=True)
    featured = models.BooleanField(default=False)
    
    #Classification
    solutions_category = models.ManyToManyField(SolutionsCategory)
    solutions_for = models.ManyToManyField(SolutionsFor)
    
    date_en = models.CharField(max_length=30, default="", null=True, blank=True) #April 21, 2017
    item_name_en = models.CharField(max_length=250, default="", null=True, blank=True)
    title_en = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_en = models.TextField(default="", null=True, blank=True)
    full_text_en = models.TextField(default="", null=True, blank=True)
    
    date_fr = models.CharField(max_length=30, default="", null=True, blank=True) #28 juillet 2017
    item_name_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    title_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_fr = models.TextField(default="", null=True, blank=True)
    full_text_fr = models.TextField(default="", null=True, blank=True)
    
class Event_item(models.Model):
    
    date_time = models.DateTimeField(auto_now_add=True)      
    event_date = models.DateField(null=True, blank=True)
    
    CHOICES = (('AB', 'Alberta'), ('BC', 'British Columbia'), ('MB', 'Manitoba'), ('NB', 'New Brunswick'), ('NL', 'Newfoundland'), ('NT', 'Northwest Territories'), ('NS', 'Nova Scotia'), ('NU', 'Nunavut'), ('ON', 'Ontario'), ('PE', 'Prince Edward Island'), ('QC', 'Quebec'), ('SK', 'Saskatchewan'), ('YT', 'Yukon'))
    event_province = models.CharField(max_length=25, choices=CHOICES, default='ON')
    
    #Classification
    solutions_category = models.ManyToManyField(SolutionsCategory)
    solutions_for = models.ManyToManyField(SolutionsFor)
    
    date_en = models.CharField(max_length=100, default="", null=True, blank=True) #August 25th to August 27th, 2017
    place_name_en = models.CharField(max_length=100, default="", null=True, blank=True)  
    street_address_en = models.CharField(max_length=100, default="", null=True, blank=True) 
    city_state_en = models.CharField(max_length=100, default="", null=True, blank=True)
    postal_code_en = models.CharField(max_length=100, default="", null=True, blank=True)
    map_link_en = models.CharField(max_length=250, default="", null=True, blank=True)  
    item_name_en = models.CharField(max_length=250, default="", null=True, blank=True)
    event_name_en = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_en = models.TextField(default="", null=True, blank=True)
    full_text_en = models.TextField(default="", null=True, blank=True)
    
    date_fr = models.CharField(max_length=100, default="", null=True, blank=True) #25 août au 27 août 2017
    place_name_fr = models.CharField(max_length=100, default="", null=True, blank=True)  
    street_address_fr = models.CharField(max_length=100, default="", null=True, blank=True) 
    city_state_fr = models.CharField(max_length=100, default="", null=True, blank=True)
    postal_code_fr = models.CharField(max_length=100, default="", null=True, blank=True)
    map_link_fr = models.CharField(max_length=250, default="", null=True, blank=True)  
    item_name_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    event_name_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    intro_fr = models.TextField(default="", null=True, blank=True)
    full_text_fr = models.TextField(default="", null=True, blank=True)
    
class Carousel_item(models.Model):
    
    date_time = models.DateTimeField(auto_now_add=True)  
    
    CHOICES = (('left', 'Left'), ('right', 'Right'))
    image_or_video_placement = models.CharField(max_length=5, choices=CHOICES)
    use_video_instead_of_image = models.BooleanField(default=False)
    show_button = models.BooleanField(default=True)
    
    title_en = models.CharField(max_length=250, default="", null=True, blank=True)
    text_en = models.TextField(default="", null=True, blank=True)
    button_text_en = models.CharField(max_length=100, default="", null=True, blank=True)
    image_en = models.CharField(max_length=250, default="", null=True, blank=True)
    video_url_en = models.CharField(max_length=250, default="", null=True, blank=True)
    video_id_en = models.CharField(max_length=250, default="", null=True, blank=True)
    link_en = models.CharField(max_length=250, default="", null=True, blank=True)
    
    title_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    text_fr = models.TextField(default="", null=True, blank=True)
    button_text_fr = models.CharField(max_length=100, default="", null=True, blank=True)
    image_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    video_url_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    video_id_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    link_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    pages = models.ManyToManyField(Page)
    
class EmrResources (models.Model):
    
    category = models.CharField(max_length=250, default="", null=True, blank=True)
    solution = models.CharField(max_length=250, default="", null=True, blank=True)
    type = models.CharField(max_length=250, default="", null=True, blank=True)
    type_en = models.CharField(max_length=250, default="", null=True, blank=True)
    type_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    
    image_en = models.CharField(max_length=250, default="", null=True, blank=True)
    title_en = models.CharField(max_length=250, default="", null=True, blank=True)
    link_en = models.CharField(max_length=250, default="", null=True, blank=True)
    description_en = models.CharField(max_length=250, default="", null=True, blank=True)
    
    image_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    title_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    link_fr = models.CharField(max_length=250, default="", null=True, blank=True)
    description_fr = models.CharField(max_length=250, default="", null=True, blank=True)

class Pharmacy_Product_Category(models.Model):
    title_en = models.CharField(max_length=50)
    description_en = models.TextField(null=True, blank=True)
    title_fr = models.CharField(max_length=50, default="")
    description_fr = models.TextField(null=True, default="", blank=True)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(auto_now=True)
    

    def __str__(self):
        return self.title_en


class Pharmacy_Product_Company(models.Model):
    title = models.CharField(max_length=20)
    logo = models.ImageField(upload_to='pharmacy/product/company/', null=True, blank=True)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


    def get_thumb(self):
        if self.logo:
            return self.logo.url
        else:
            return False



class Pharmacy_Product(models.Model):
    title_en = models.CharField(max_length =50)
    description_en = models.TextField()
    title_fr = models.CharField(max_length=50, blank=True, default="")
    description_fr = models.TextField(blank=True, default="")
    image = models.ImageField(upload_to='pharmacy_product_images', null=True, blank=True)
    category = models.ForeignKey(Pharmacy_Product_Category)
    company = models.ForeignKey(Pharmacy_Product_Company, null=True)
    price = models.DecimalField(decimal_places=2, max_digits=6, default=0)
    contact_to_order = models.BooleanField(default=False)
    minimum_order = models.PositiveIntegerField(default=1)
    active = models.BooleanField(default=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return ('%s (%s)' % (self.title_en, self.company.title))

    def get_thumb(self):
        if self.image:
            return self.image.url
        else:
            return False


class PharmacyProduct_Order(models.Model):
    firstname = models.CharField(max_length = 150, null=True)
    lastname = models.CharField(max_length = 150, null=True)
    email = models.EmailField()
    phone = models.CharField(max_length = 150, null=True)
    company = models.CharField(max_length = 150, null=True, blank=True)
    address = models.CharField(max_length = 150, null=True)
    address2 = models.CharField(max_length = 50, null=True, blank=True)
    city = models.CharField(max_length = 150, null=True)
    state = models.CharField(max_length = 150, null=True)
    country = models.CharField(max_length = 150, null=True)
    postalcode = models.CharField(max_length = 9, null=True)
    region = models.CharField(max_length = 150, null=True)
    total = models.DecimalField(default=10.99, max_digits=10, decimal_places=2, null=True)
    date_created = models.DateTimeField(auto_now_add=True, editable=False)
    date_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return 'TELUSPHAR%s' % self.id
    '''
    def save(self, *args, **kwargs):
        summedval = self.cartitem_set.all().aggregate(models.Sum('sub_total'))
        self.total = summedval['sub_total__sum']
        super(PharmacyProduct_Order, self).save(*args, **kwargs)
    '''


class CartItem(models.Model):
    product = models.ForeignKey(Pharmacy_Product)
    quantity = models.IntegerField(default=1)
    sub_total = models.DecimalField(default=1.99, max_digits=10, decimal_places=2)
    order = models.ForeignKey(PharmacyProduct_Order)
    dateCreated = models.DateTimeField(auto_now = True)

    def save(self, *args, **kwargs):
        if self.quantity < self.product.minimum_order:
            self.quantity = self.product.minimum_order
        self.sub_total = self.quantity * self.product.minimum_order
        super(CartItem, self).save(*args, **kwargs)

class ProductContact (models.Model):
    
    product_name = models.CharField(max_length=250, default="", null=True, blank=True)
    product_link_name = models.CharField(max_length=250, default="", null=True, blank=True)
    
    CHOICES1 = (('sales', 'Sales'), ('support', 'Support'))
    sales_or_support = models.CharField(max_length=7, choices=CHOICES1)

    CHOICES2 = (('EN', 'EN'), ('FR', 'FR'))
    language = models.CharField(max_length=2, choices=CHOICES2)

    marketo_form_id = models.CharField(max_length=250, default="", null=True, blank=True)

upload_choice = (
    ('A', 'Append Upload'),
    ('C', 'Clean Upload')
)

class UploadRedirect(models.Model):
    fileObj = models.FileField()
    options = models.CharField(max_length=1, choices=upload_choice)


    def save(self, force_insert=False, force_update=False, using=None,
             update_fields=None):
        from core.redirectlinks import redirectIt
        which = self.options
        if which == 'C':
            status = redirectIt(self.fileObj, 2)
        else:
            status = redirectIt(self.fileObj, 1)
        if status == 1:
            pass
        else:
            return HttpResponse("<h1>Opps! Not working.</h1> <p>Most likely wrong format</p>")
