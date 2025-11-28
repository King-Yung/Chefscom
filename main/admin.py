# admin.py
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html
from django.utils import timezone
from datetime import timedelta
from django.urls import path
from django.template.response import TemplateResponse
from django.shortcuts import redirect, get_object_or_404
from .models import ChefProfile, EmployerProfile, Subscription, TestimonyLog, VerificationCode, CVSubmission, Candidate, Job, NewsletterSubscriber, JobEngagement, NeedChefSubmission, JobApplication, JobVacancySubmission, ReliefChefRequest, PermanentChefRequest, PrivateChefRequest, CulinaryAgentRegistration, DishPhoto, ContactMessage, UserOTP

# Inline for Subscription (linked to User)
class SubscriptionInline(admin.StackedInline):
    model = Subscription
    can_delete = False
    extra = 0
    fields = ('plan_name', 'amount', 'is_active', 'start_date', 'end_date', 'paystack_reference')
    readonly_fields = ('start_date', 'end_date', 'paystack_reference')

# Custom UserAdmin with Subscription inline
class CustomUserAdmin(BaseUserAdmin):
    inlines = [SubscriptionInline]

admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)

# Helper function to toggle subscription
def toggle_subscription_for_user(user):
    sub, created = Subscription.objects.get_or_create(user=user)
    sub.is_active = not sub.is_active
    if sub.is_active and not sub.start_date:
        sub.start_date = timezone.now()
    sub.save()



# ChefProfile admin with clickable subscription
@admin.register(ChefProfile)
class ChefProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'nationality', 'is_verified', 'is_verified_2', 'is_subscribed', 'date_created')
    search_fields = ('user__username', 'phone_number', 'is_verified_2', 'nationality')
    list_filter = ('is_verified', 'is_verified_2', 'nationality', 'date_created')
    ordering = ('-date_created',)

    def is_subscribed(self, obj):
        sub = getattr(obj.user, 'subscription', None)
        status = sub.is_active if sub else False
        color = "green" if status else "red"
        return format_html('<a href="{}" style="color:{};">{}</a>',
            f"/admin/main/chefprofile/{obj.id}/toggle-subscription/", color, "Yes" if status else "No")
    is_subscribed.short_description = "Subscribed"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:profile_id>/toggle-subscription/', self.admin_site.admin_view(self.toggle_subscription_view),
                 name='chefprofile-toggle-subscription'),
        ]
        return custom_urls + urls

    def toggle_subscription_view(self, request, profile_id):
        profile = get_object_or_404(ChefProfile, id=profile_id)
        toggle_subscription_for_user(profile.user)
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))



# EmployerProfile admin with clickable subscription
# Helper function to toggle subscription
def toggle_subscription_for_user(user, duration_days=30):
    """
    Toggle subscription for a user.
    If activating, sets end_date to duration_days from now if not set.
    """
    sub, created = Subscription.objects.get_or_create(user=user)

    if sub.is_active:
        # Deactivate subscription
        sub.is_active = False
    else:
        # Activate subscription
        sub.is_active = True
        sub.start_date = timezone.now()
        if not sub.end_date or sub.end_date < timezone.now():
            sub.end_date = timezone.now() + timedelta(days=duration_days)
    sub.save()


@admin.register(EmployerProfile)
class EmployerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'organization', 'phone_number', 'nationality', 'is_verified', 'is_verified_2', 'is_subscribed', 'date_created')
    search_fields = ('user__username', 'organization', 'phone_number', 'is_verified_2', 'nationality')
    list_filter = ('is_verified', 'is_verified_2', 'nationality', 'date_created')
    ordering = ('-date_created',)

    # Display subscribed status with clickable toggle
    def is_subscribed(self, obj):
        sub = getattr(obj.user, 'subscription', None)
        status = sub.is_active if sub else False
        color = "green" if status else "red"
        return format_html(
            '<a href="{}" style="color:{};">{}</a>',
            f"/admin/main/employerprofile/{obj.id}/toggle-subscription/", 
            color, 
            "Yes" if status else "No"
        )
    is_subscribed.short_description = "Subscribed"

    # Add custom admin URLs
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<int:profile_id>/toggle-subscription/', 
                self.admin_site.admin_view(self.toggle_subscription_view),
                name='employerprofile-toggle-subscription'
            ),
        ]
        return custom_urls + urls

    # Admin view that toggles subscription
    def toggle_subscription_view(self, request, profile_id):
        profile = get_object_or_404(EmployerProfile, id=profile_id)
        toggle_subscription_for_user(profile.user)
        return redirect(request.META.get('HTTP_REFERER', '/admin/'))



# Register other models
@admin.register(VerificationCode)
class VerificationCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'code', 'is_used', 'created_at', 'expires_at')
    search_fields = ('user__username', 'code')
    list_filter = ('is_used', 'created_at')
    ordering = ('-created_at',)



@admin.register(Candidate)
class CandidateAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'gender', 'years_experience', 'specialty', 'is_approved', 'status')
    list_filter = ('is_approved', 'gender', 'specialty', 'years_experience', 'specialty_other', 'establishment_preference', 'establishment_other', 'preferred_locations', 'preferred_location_other', 'highest_qualification', 'contract_term', 'preferred_job_types')
    search_fields = ('full_name', 'email', 'phone')
    actions = ['approve_candidates']

    @admin.action(description="Approve selected candidates")
    def approve_candidates(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} candidate(s) approved successfully.", level=messages.SUCCESS)

    def changelist_view(self, request, extra_context=None):
        """Add a banner on top of the Candidate list page if approvals are pending."""
        pending_count = Candidate.objects.filter(is_approved=False).count()
        extra_context = extra_context or {}
        extra_context['pending_count'] = pending_count
        return super().changelist_view(request, extra_context=extra_context)
    
    def __str__(self):
            return f"{self.full_name} — {self.phone}"

    def get_preferred_job_types_display(self):
        """
        Returns a nicely formatted, comma-separated string of job types.
        """
        if not self.preferred_job_types:
            return "—"
        return ", ".join([job.strip() for job in self.preferred_job_types.split(",") if job.strip()])
    


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan_name', 'amount', 'is_active', 'start_date', 'end_date')
    search_fields = ('user__username', 'user__email', 'plan_name')
    list_filter = ('is_active', 'plan_name', 'start_date')
    ordering = ('-start_date',)



@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'date_subscribed')
    search_fields = ('email',)


@admin.register(JobEngagement)
class JobEngagementAdmin(admin.ModelAdmin):
    list_display = (
        'candidate',
        'employer',
        'status',
        'hired_at',
        'created_at'
    )
    list_filter = ("status", "is_viewed", "created_at", "employer")
    search_fields = (
        "employer__username",
        "employer__email",
        "candidate__user__username",
        "candidate__user__email",
        "message",
    )
    readonly_fields = ("created_at", "updated_at")

    def short_employer_testimony(self, obj):
        return (obj.employer_testimony[:30] + "...") if obj.employer_testimony else "—"
    short_employer_testimony.short_description = "Employer Testimony"

    def short_chef_testimony(self, obj):
        return (obj.chef_testimony[:30] + "...") if obj.chef_testimony else "—"
    short_chef_testimony.short_description = "Chef Testimony"

    def save_model(self, request, obj, form, change):
        """Log any changes to JobEngagement in the admin."""
        super().save_model(request, obj, form, change)
        from django.contrib.admin.models import LogEntry, CHANGE
        from django.contrib.contenttypes.models import ContentType

        LogEntry.objects.log_action(
            user_id=request.user.id,
            content_type_id=ContentType.objects.get_for_model(obj).pk,
            object_id=obj.id,
            object_repr=str(obj),
            action_flag=CHANGE,
            change_message=f"Admin {request.user.username} changed engagement status to {obj.status}",
        )



@admin.register(TestimonyLog)
class TestimonyLogAdmin(admin.ModelAdmin):
    list_display = ("user_full_name", "role", "short_testimony", "created_at")
    list_filter = ("role", "created_at")
    search_fields = ("user__username", "user__first_name", "user__last_name", "testimony")
    ordering = ("-created_at",)

    def user_full_name(self, obj):
        """Return the user's full name, falling back to username."""
        full_name = f"{obj.user.first_name} {obj.user.last_name}".strip()
        return full_name if full_name else obj.user.username
    user_full_name.short_description = "User"

    def short_testimony(self, obj):
        """Show only the first few words in admin list view."""
        return (obj.testimony[:50] + "...") if len(obj.testimony) > 50 else obj.testimony
    short_testimony.short_description = "Testimony"



@admin.register(NeedChefSubmission)
class NeedChefSubmissionAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'job_positions', 'submitted_at', 'is_approved', 'status')
    list_filter = ('is_approved', 'submitted_at', 'status')
    search_fields = ('company_name', 'job_positions', 'company_address', 'status')
    actions = ['approve_submissions']

    # ✅ Admin action to approve submissions
    def approve_submissions(self, request, queryset):
        updated = queryset.update(is_approved=True)
        self.message_user(request, f"{updated} submission(s) approved.")
    approve_submissions.short_description = "Approve selected submissions"



@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "company_name",
        "title", 
        "employer", 
        "posted_at", 
        "status", 
    )
    search_fields = (
        "title", 
        "company_name", 
        "employer__username", 
        "job_positions", 
    )
    list_filter = ("status", "establishment_type", "employment_type", "posted_at")
    readonly_fields = ("created_at", "posted_at")
    ordering = ("-posted_at",)

@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    # Use a method to display full name
    list_display = (
        "chef_full_name",  # <- replace chef with method
        "job",  
        "status", 
        "date_applied"
    )
    list_filter = ("status", "date_applied")
    search_fields = (
        "chef__username", 
        "chef__email", 
        "job__title", 
        "need_chef__job_positions"
    )
    ordering = ("-date_applied",)

    # Method to show full name
    def chef_full_name(self, obj):
        return obj.chef.get_full_name() if obj.chef else "N/A"
    
    chef_full_name.short_description = "Chef Full Name"


@admin.register(CVSubmission)
class CVSubmissionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "is_approved", "status", "experience_years", "submitted_at")
    search_fields = ("full_name", "email", "phone", "is_approved")
    list_filter = ("experience_years", "submitted_at")
    list_editable = ("is_approved",)



@admin.register(JobVacancySubmission)
class JobVacancySubmissionAdmin(admin.ModelAdmin):
    list_display = ("employer_name", "job_category", "employment_type", "state", "is_approved", "status", "application_deadline", "date_submitted",)

    list_filter = ("job_category", "employment_type", "state", "preferred_gender", "date_submitted", "application_deadline", "is_approved", "status")

    search_fields = ("employer_name", "business_phone", "official_email", "job_location", "position_title", "company_name", "status")

    ordering = ("-date_submitted",)


@admin.register(ReliefChefRequest)
class ReliefChefRequestAdmin(admin.ModelAdmin):
    list_display = (
        'business_name',
        'contact_person',
        'position_required',
        'expected_start_date',
        'work_location',
        'date_submitted',
    )
    list_filter = ('position_required', 'expected_start_date', 'work_location')
    search_fields = ('business_name', 'contact_person', 'phone_number', 'email')


@admin.register(PermanentChefRequest)
class PermanentChefRequestAdmin(admin.ModelAdmin):
    list_display = ("company_name", "position_title", "employment_type", "business_location", "date_submitted", "is_approved")
    list_filter = ("employment_type", "experience_level", "is_approved", "date_submitted")
    search_fields = ("company_name", "contact_person", "email", "phone_number", "position_title")
    readonly_fields = ("date_submitted",)
    ordering = ("-date_submitted",)


@admin.register(PrivateChefRequest)
class PrivateChefRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "service_type", "cuisine_type", "budget", "is_approved", "date_submitted")
    list_filter = ("service_type", "cuisine_type", "is_approved", "date_submitted")
    search_fields = ("full_name", "email", "phone_number")
    readonly_fields = ("date_submitted",)



class DishPhotoInline(admin.TabularInline):
    model = DishPhoto
    extra = 0


@admin.register(CulinaryAgentRegistration)
class CulinaryAgentRegistrationAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "professional_title", "experience_years", "date_submitted")
    search_fields = ("full_name", "email", "professional_title")
    list_filter = ("professional_title", "experience_years", "currently_available")
    inlines = [DishPhotoInline]



@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'date_sent')
    search_fields = ('name', 'email', 'subject', 'message')
    list_filter = ('date_sent',)
    ordering = ('-date_sent',)

@admin.register(UserOTP)
class UserOTPAdmin(admin.ModelAdmin):
    list_display = ('user', 'otp_code')
    search_fields = ('user', 'otp_code', )
    list_filter = ('otp_code',)
    ordering = ('created_at',)