from django.contrib import admin
from .models import Stage, StageItem


class StageItemInline(admin.TabularInline):
    model = StageItem
    extra = 0
    fields = ['item_type', 'position_x', 'position_y', 'rotation', 'width', 'height', 'custom_ammo_count']


@admin.register(Stage)
class StageAdmin(admin.ModelAdmin):
    list_display = ['name', 'width', 'height', 'created_by', 'created_at', 'get_total_ammo_count']
    list_filter = ['created_at', 'created_by']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'get_total_ammo_count', 'get_item_summary']
    inlines = [StageItemInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'created_by')
        }),
        ('Dimensions', {
            'fields': ('width', 'height')
        }),
        ('Statistics', {
            'fields': ('get_total_ammo_count', 'get_item_summary', 'created_at', 'updated_at')
        }),
    )

    def get_total_ammo_count(self, obj):
        return obj.get_total_ammo_count()
    get_total_ammo_count.short_description = 'Total Ammo'

    def get_item_summary(self, obj):
        summary = obj.get_item_summary()
        return ', '.join([f"{count}x {item}" for item, count in summary.items()])
    get_item_summary.short_description = 'Items'


@admin.register(StageItem)
class StageItemAdmin(admin.ModelAdmin):
    list_display = ['stage', 'item_type', 'position_x', 'position_y', 'get_ammo_count']
    list_filter = ['item_type', 'stage']
    search_fields = ['stage__name', 'notes']

    fieldsets = (
        ('Item Information', {
            'fields': ('stage', 'item_type', 'notes')
        }),
        ('Position & Size', {
            'fields': ('position_x', 'position_y', 'rotation', 'width', 'height')
        }),
        ('Ammunition', {
            'fields': ('custom_ammo_count',)
        }),
    )
