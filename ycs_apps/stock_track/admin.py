from django.contrib import admin
from ycs_apps.stock_track.models import *
from django.forms.models import BaseInlineFormSet

# Register your models here.
class RequiredInlineFormSet(BaseInlineFormSet):
    """
    Generates an inline formset that is required
    """

    def _construct_form(self, i, **kwargs):
        """
        Override the method to change the form attribute empty_permitted
        """
        form = super(RequiredInlineFormSet, self)._construct_form(i, **kwargs)
        form.empty_permitted = False
        return form
        
        
        
        
class DailyInline(admin.TabularInline):
    """ Creates a FormSet for the status foreign_key """
    model = Daily
    extra = 1
    formset = RequiredInlineFormSet
    
    
class CompanyAdmin(admin.ModelAdmin):
    """ Creates a FormSet for the RMA Model """
    fieldsets = [
        (None, {'fields': ['ticker']}),
        (None, {'fields': ['long_name']}),
    ]
    inlines = (DailyInline,)
    list_display = ('ticker','long_name')
    list_filter = ['long_name']
    search_fields = ['ticker','long_name']
    

admin.site.register(Company, CompanyAdmin)
admin.site.register(UserProfile)

# class ChoiceInline(admin.TabularInline):
    # model = Choice
    # extra = 3

# class PollAdmin(admin.ModelAdmin):
    # fieldsets = [
        # (None,               {'fields': ['question']}),
        # ('Date information', {'fields': ['pub_date'], 'classes': ['collapse']}),
    # ]
    # inlines = [ChoiceInline]
    # list_display = ('question', 'pub_date', 'was_published_recently')
    # list_filter = ['pub_date']
    # search_fields = ['question']

# admin.site.register(Poll, PollAdmin)
