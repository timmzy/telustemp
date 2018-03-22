from django.contrib import admin

from .models import Page
from .models import Content_item
from .models import Latest_Thinking_item
from .models import Media_Release_item
from .models import Event_item
from .models import Carousel_item
from .models import KeyHealthIssue
from .models import SolutionsCategory
from .models import ContentType
from .models import SolutionsFor
from .models import EmrResources
from .models import Content_item, Pharmacy_Product_Category, Pharmacy_Product, Pharmacy_Product_Company, UploadRedirect
from .models import PharmacyProduct_Order, CartItem
from .models import ProductContact

class ContentItemAdmin (admin.ModelAdmin):
    list_display = ['section', 'page', 'role', 'content_en', 'content_fr']
    search_fields = ['section', 'page','role','content_en','content_fr']
    list_filter = ['section', 'page', 'role']
    
class LatestThinkingItemAdmin (admin.ModelAdmin):
    list_display = ['date_en', 'title_en']
    search_fields = ['title_en', 'title_fr']
    filter_horizontal = ('solutions_category', 'solutions_for', 'content_type', 'key_health_issue',)
    
class MediaReleaseItemAdmin (admin.ModelAdmin):
    list_display = ['date_en', 'title_en']
    search_fields = ['title_en', 'intro_en', 'title_fr', 'intro_fr']
    filter_horizontal = ('solutions_category', 'solutions_for',)
    
class EventItemAdmin (admin.ModelAdmin):
    list_display = ['date_en', 'event_name_en']
    search_fields = ['event_name_en', 'event_name_fr']
    filter_horizontal = ('solutions_category', 'solutions_for',)
    
class CarouselItemAdmin (admin.ModelAdmin):
    list_display = ['title_en', 'title_fr']
    filter_horizontal = ('pages',)
    search_fields = ['title_en', 'title_fr']
 
class PageAdmin (admin.ModelAdmin):
    list_display = ['page_name_en', 'page_name_fr', 'url_en']
    search_fields = ['page_name_en', 'page_name_fr']
    list_filter = ['view', 'page_name_en', 'page_name_fr']

class KeyHealthIssueAdmin (admin.ModelAdmin):
    list_display = ['issue_en', 'issue_fr']

class SolutionsCategoryAdmin (admin.ModelAdmin):
    list_display = ['category_en', 'category_fr']

class ContentTypeAdmin (admin.ModelAdmin):
    list_display = ['content_type_en', 'content_type_fr']

class SolutionsForAdmin (admin.ModelAdmin):
    list_display = ['solutions_for_en', 'solutions_for_fr']
    
class EmrResourcesAdmin (admin.ModelAdmin):
    list_display = ['title_en', 'description_en']

def disable_item(modeladmin, request, queryset):
    queryset.update(active = False)
disable_item.short_description = 'Unpublish item or make the selected item Inactive'

def enable_item(modeladmin, request, queryset):
    queryset.update(active = True)
enable_item.short_description = 'Publish item or make the selected item Active'


class Pharmacy_Products_CategoryInline(admin.TabularInline):
    model = Pharmacy_Product_Category
    extra = 5

@admin.register(Pharmacy_Product_Category)
class Pharmacy_Products_CategoryAdmin(admin.ModelAdmin):
    list_display  = ('title_en', 'description_en', 'no_of_products', 'active')
    actions = [enable_item, disable_item]

    def no_of_products(self,obj):
        pcount = Pharmacy_Product.objects.filter(category=obj)
        pc = pcount.count()
        return pc
    no_of_products.empty_value_display = '0 Products'



@admin.register(Pharmacy_Product)
class Pharmacy_ProductAdmin(admin.ModelAdmin):
    list_display = ('__str__','thumb', 'category', 'price', 'minimum_order', 'company', 'active')
    list_filter = ('category', 'company', 'price', ('active', admin.BooleanFieldListFilter))
    actions = [enable_item, disable_item]

    def thumb(self, obj):
        if obj.get_thumb():
            return "<img src='{}' width='20' height='20' />".format(obj.get_thumb())

    thumb.allow_tags = True
    thumb.__name__ = 'Image'
    thumb.empty_value_display = "No Image"


@admin.register(Pharmacy_Product_Company)
class Pharmacy_Product_CompanyAdmin(admin.ModelAdmin):
    list_display = ('title', 'thumb', 'active')
    actions = [enable_item, disable_item]

    def thumb(self, obj):
        if obj.get_thumb():
            return "<img src='{}' width='20' height='20' />".format(obj.get_thumb())

    thumb.allow_tags = True
    thumb.__name__ = 'Logo'
    thumb.empty_value_display = "No Logo"

    
class ProductContactAdmin (admin.ModelAdmin):
    list_display = ['product_name', 'sales_or_support', 'language', 'marketo_form_id']

class ProductOrderDetailsAdmin (admin.ModelAdmin):
    list_display = ['firstname', 'lastname', 'email']
            
admin.site.register(Content_item, ContentItemAdmin)
admin.site.register(Latest_Thinking_item, LatestThinkingItemAdmin)
admin.site.register(Media_Release_item, MediaReleaseItemAdmin)
admin.site.register(Event_item, EventItemAdmin)
admin.site.register(Carousel_item, CarouselItemAdmin)
admin.site.register(Page, PageAdmin)

admin.site.register(KeyHealthIssue, KeyHealthIssueAdmin)
admin.site.register(SolutionsCategory, SolutionsCategoryAdmin)
admin.site.register(ContentType, ContentTypeAdmin)
admin.site.register(SolutionsFor, SolutionsForAdmin)
admin.site.register(EmrResources, EmrResourcesAdmin)
admin.site.register(ProductContact, ProductContactAdmin)
admin.site.register(PharmacyProduct_Order, ProductOrderDetailsAdmin)
admin.site.register(UploadRedirect)
