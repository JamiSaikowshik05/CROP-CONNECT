"""
Admin configuration for Procurement Portal.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Farmer, LandDetails, Crop, Slot, SlotBooking,
    Procurement, Bill, Payment, Announcement
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    search_fields = ('username', 'email')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Portal Role', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Portal Role', {'fields': ('role', 'phone')}),
    )


@admin.register(Farmer)
class FarmerAdmin(admin.ModelAdmin):
    list_display = ('user', 'aadhaar', 'district', 'verified', 'created_at')
    search_fields = ('aadhaar', 'user__username', 'district')
    list_filter = ('verified', 'district')


@admin.register(LandDetails)
class LandDetailsAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'survey_no', 'total_area_acres', 'verified')
    search_fields = ('survey_no', 'farmer__user__username')


@admin.register(Crop)
class CropAdmin(admin.ModelAdmin):
    list_display = ('name', 'msp_per_quintal', 'unit', 'is_active')


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('date', 'crop', 'total_capacity_quintals', 'booked_capacity', 'is_active')


@admin.register(SlotBooking)
class SlotBookingAdmin(admin.ModelAdmin):
    list_display = ('farmer', 'slot', 'estimated_quintals', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(Procurement)
class ProcurementAdmin(admin.ModelAdmin):
    list_display = ('booking', 'actual_weight_quintals', 'status', 'validated_at')


@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('bill_number', 'procurement', 'total_amount', 'created_at')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('bill', 'status', 'approved_at')


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'created_at')
