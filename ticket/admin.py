from django.contrib import admin
from .models import Ticket
# Register your models here.

class TicketAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('ticket_id','ticket_title','ticket_description', 'customer', 'engineer', 'status' ),
        }),
    )
    
    list_display = ('ticket_id','ticket_title','ticket_description', 'customer', 'engineer', 'status' )
    list_filter = ('ticket_id','ticket_title','ticket_description', 'customer', 'engineer', 'status' )
    search_fields = ('ticket_id','ticket_title','ticket_description', 'customer', 'engineer', 'status')
admin.site.register(Ticket , TicketAdmin)