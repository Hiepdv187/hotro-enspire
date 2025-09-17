from django.contrib import admin
from .models import Department, Asset, District, School, LabRoom


class DepartmentAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id','name' ),
        }),
    )
    
    list_display = ('id','name' )
    list_filter = ('id','name' )
    search_fields = ('id','name' )
admin.site.register(Department , DepartmentAdmin)

class AssetAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id','district_id','department_id','lab_room_id', 'school_id','name', 'asset_amount', 'asset_status'),
        }),
    )
    
    list_display = ('id','district_id','department_id','lab_room_id', 'school_id','name', 'asset_amount', 'asset_status')
    list_filter = ('id','district_id','department_id','lab_room_id', 'school_id','name', 'asset_amount', 'asset_status')
    search_fields = ('id','district_id','department_id','lab_room_id', 'school_id','name', 'asset_amount', 'asset_status')
admin.site.register(Asset , AssetAdmin)

class DistrictAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('id', 'department_id', 'name'),
        }),
    )
    
    list_display = ('id','department_id','name',)
    list_filter = ('id','department_id','name',)
    search_fields = ('id','department_id','name',)
admin.site.register(District, DistrictAdmin)

class SchoolAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('district_id', 'id','name'),
        }),
    )
    
    list_display = ('district_id', 'id','name')
    list_filter = ('district_id', 'id','name')
    search_fields = ('district_id', 'id','name')
admin.site.register(School, SchoolAdmin)

class LabRoomAdmin(admin.ModelAdmin):
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('school_id', 'id','name'),
        }),
    )
    
    list_display = ('school_id', 'id','name')
    list_filter = ('school_id', 'id','name')
    search_fields = ('school_id', 'id','name')
admin.site.register(LabRoom, LabRoomAdmin)
