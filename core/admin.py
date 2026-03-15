from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, CHVProfile, AdolescentProfile, CycleEntry, SymptomEntry

# 1. Custom User Admin
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_chv', 'is_adolescent', 'is_staff')
    list_filter = ('is_chv', 'is_adolescent', 'is_staff', 'is_superuser', 'is_active')
    # Add our custom boolean fields to the default Django User admin form
    fieldsets = UserAdmin.fieldsets + (
        ('HerCycle Role Attributes', {'fields': ('is_chv', 'is_adolescent')}),
    )

# 2. CHV Profile Admin with Bulk Approval Action
@admin.register(CHVProfile)
class CHVProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'is_approved')
    list_filter = ('is_approved', 'organization')
    search_fields = ('user__username', 'organization')
    actions = ['approve_chvs']

    @admin.action(description='Approve selected Community Health Volunteers')
    def approve_chvs(self, request, queryset):
        # This allows you to select multiple CHVs and approve them all at once
        updated = queryset.update(is_approved=True)
        self.message_user(request, f'Successfully approved {updated} CHV(s).')

# 3. Adolescent Profile Admin
@admin.register(AdolescentProfile)
class AdolescentProfileAdmin(admin.ModelAdmin):
    list_display = ('anonymous_id', 'get_username', 'chv')
    search_fields = ('anonymous_id', 'user__username', 'chv__user__username')
    list_filter = ('chv',) # Easily filter girls by which CHV is managing them

    # Helper to display the username from the linked User model
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'

# 4. Cycle Entry Admin
@admin.register(CycleEntry)
class CycleEntryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'start_date', 'end_date', 'flow_intensity', 'last_modified', 'is_deleted')
    list_filter = ('flow_intensity', 'start_date', 'is_deleted')
    search_fields = ('profile__anonymous_id',)
    readonly_fields = ('id', 'last_modified')

# 5. Symptom Entry Admin
@admin.register(SymptomEntry)
class SymptomEntryAdmin(admin.ModelAdmin):
    list_display = ('profile', 'date', 'symptom_type', 'severity', 'last_modified', 'is_deleted')
    list_filter = ('symptom_type', 'severity', 'is_deleted')
    search_fields = ('profile__anonymous_id', 'symptom_type')
    readonly_fields = ('id', 'last_modified')