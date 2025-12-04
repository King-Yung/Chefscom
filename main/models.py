from django.db import models
from django.contrib.auth.models import User
import random
from datetime import timedelta
from django.utils import timezone
from django.utils.timezone import now
now()
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.text import slugify
from multiselectfield import MultiSelectField
from cities_light.models import Country, Region
from django_countries.fields import CountryField

import string, datetime




def generate_verification_code():
    """Generate a 6-digit random code"""
    return random.randint(100000, 999999)

class UserOTP(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return (datetime.datetime.now(datetime.timezone.utc) - self.created_at).seconds > 300  # 5 minutes


class ChefProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='chef_pics/', blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    is_verified_2 = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Chef - {str(self.user.username)}"



class EmployerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    organization = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField( )
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    is_verified = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    profile_picture = models.ImageField(upload_to='employers/', blank=True, null=True)
    is_subscribed = models.BooleanField(default=False)
    is_verified_2 = models.BooleanField(default=False) 
    profile_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Employer - {str(self.user.username)}"
    

class VerificationCode(models.Model):
    """Stores verification codes for phone or email verification."""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    is_used = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.expires_at:
            # Code expires after 10 minutes
            self.expires_at = timezone.now() + timedelta(minutes=10)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"Verification code for {self.user.username} - {self.code}"


# class Job(models.Model):
#     EMPLOYMENT_TYPES = [
#         ('full-time', 'Full-Time'),
#         ('part-time', 'Part-Time'),
#         ('contract', 'Contract'),
#     ]

#     employer = models.ForeignKey(EmployerProfile, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     description = models.TextField()
#     location = models.CharField(max_length=255)
#     address = models.CharField(max_length=255, blank=True, null=True)
#     employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES)
#     posted_at = models.DateTimeField(auto_now_add=True)
#     min_experience = models.IntegerField(default=0)  # in years
#     max_experience = models.IntegerField(default=0)
#     preferred_gender = models.CharField(max_length=10, choices=[('male','Male'),('female','Female'),('any','Any')], default='any')
#     is_active = models.BooleanField(default=True)  # NEW field to track active job postings

#     def __str__(self):
#         return f"{self.title} at {self.employer.organization}"



EXPERIENCE_CHOICESS = [
    ('0-1', '0–1'),
    ('2-4', '2–4'),
    ('5-7', '5–7'),
    ('8-10', '8–10'),
    ('10+', '10+'),
]

EMPLOYMENT_STATUS = [
    ('employed', 'Employed'),
    ('self-employed', 'Self-employed'),
    ('unemployed', 'Unemployed'),
    ('student', 'Student'),
]

YES_NO = [
    ('yes', 'Yes'),
    ('no', 'No'),
]



SPECIALTIES = [
    ('continental', 'Continental Cuisine'),
    ('african', 'African Cuisine'),
    ('pastry', 'Pastry/Bakery'),
    ('catering', 'Catering/Event Service'),
    ('grill', 'Grill/Barbecue'),
    ('other', 'Other'),
]

ESTABLISHMENT_TYPES = [
    ('hotel', 'Hotel/Resort'),
    ('restaurant', 'Restaurant/Eatery'),
    ('private_catering', 'Private Catering'),
    ('event_company', 'Event Company'),
    ('school', 'School/Institution'),
    ('other', 'Other'),
]

PREFERRED_LOCATIONS = [
    ('kano', 'Kano'),
    ('abuja', 'Abuja'),
    ('lagos', 'Lagos'),
    ('ph', 'Port Harcourt'),
    ('kaduna', 'Kaduna'),
    ('makurdi', 'Makurdi'),
    ('open', 'Open to Relocation'),
    ('other', 'Other'),
]

ALERT_CHANNELS = [
    ('email', 'Email'),
    ('whatsapp', 'WhatsApp'),
    ('sms', 'SMS'),
]

CONTRACT_TERM = [
    ('temporary', 'Temporary'),
    ('permanent', 'Permanent'),
    ('both', 'Both'),
]

GENDER_CHOICESS = [
    ('male', 'Male'),
    ('female', 'Female'),
    ('prefer_not', 'Prefer not to say'),
    ]


def cv_upload_to(instance, filename):
    # store under media/cvs/<timestamp>_<filename>
    import time
    safe_name = filename.replace(' ', '_')
    return f'cvs/{int(time.time())}_{safe_name}'


class Candidate(models.Model):
    
    # personal info
    
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    # ... rest of fields ...

    full_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICESS)
    date_of_birth = models.DateField(blank=True, null=True)
    phone = models.CharField(max_length=30)
    email = models.EmailField()
    residential_address = models.TextField(blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state_of_residence = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)

    # professional
    current_employment_status = models.CharField(max_length=30, choices=EMPLOYMENT_STATUS, blank=True)
    current_last_job_title = models.CharField(max_length=255, blank=True)
    years_experience = models.CharField(max_length=10, choices=EXPERIENCE_CHOICESS, blank=True)
    specialty = models.CharField(max_length=40, choices=SPECIALTIES, blank=True)
    specialty_other = models.CharField(max_length=255, blank=True)
    establishment_preference = models.CharField(max_length=40, choices=ESTABLISHMENT_TYPES, blank=True)
    establishment_other = models.CharField(max_length=255, blank=True)
    preferred_locations = models.CharField(max_length=255, blank=True)
    preferred_location_other = models.CharField(max_length=255, blank=True)

    highest_qualification = models.CharField(max_length=255, blank=True)
    culinary_school = models.CharField(max_length=255, blank=True)
    additional_skills = models.TextField(blank=True)

    last_employer = models.CharField(max_length=255, blank=True)
    last_position = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    key_responsibilities = models.TextField(blank=True)

    contract_term = models.CharField(max_length=20, choices=CONTRACT_TERM, blank=True)

    cv = models.FileField(upload_to=cv_upload_to, blank=True, null=True)

    # reference
    referee_name = models.CharField(max_length=255, blank=True)
    referee_relationship = models.CharField(max_length=255, blank=True)
    referee_contact = models.CharField(max_length=255, blank=True)

    # alerts
    alert_email = models.BooleanField(default=False)
    alert_whatsapp = models.BooleanField(default=False)
    alert_sms = models.BooleanField(default=False)

    message = models.TextField(blank=True)

    # Exclusive job preferences (checkboxes)
    EXCLUSIVE_JOB_CHOICES = [
        ("Relief Chef", "Relief Chef"),
        ("Permanent Chef", "Permanent Chef"),
        ("Private Chef", "Private Chef"),
        ("All of the above", "All of the above"),
    ]
    preferred_job_types = MultiSelectField(choices=EXCLUSIVE_JOB_CHOICES, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("engaged", "Engaged"),  # Employer has hired the chef
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def get_preferred_job_types_display(self):
        if not self.preferred_job_types:
            return "—"
        return ", ".join([job.strip() for job in self.preferred_job_types if job.strip()])

    def __str__(self):
        return f"{self.full_name} — {self.phone}"

    

    


class Subscription(models.Model):
    PAYMENT_GATEWAYS = [
        ("paystack", "Paystack"),
        ("flutterwave", "Flutterwave"),
    ]

    PLAN_CHOICES = [
        ("candidate_monthly", "Candidate - Monthly"),
        ("candidate_3month", "Candidate - 3 Months"),
        ("candidate_6month", "Candidate - 6 Months"),
        ("candidate_12month", "Candidate - 12 Months"),
        ("employer_monthly", "Employer - Monthly"),
        ("employer_3month", "Employer - 3 Months"),
        ("employer_6month", "Employer - 6 Months"),
        ("employer_12month", "Employer - 12 Months"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    plan_name = models.CharField(max_length=50, choices=PLAN_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=False)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    paystack_reference = models.CharField(max_length=100, blank=True, null=True)
    flutterwave_reference = models.CharField(max_length=100, blank=True, null=True)
    payment_gateway = models.CharField(max_length=20, choices=PAYMENT_GATEWAYS, default="paystack")
    created_at = models.DateTimeField(auto_now_add=True)

    def activate(self, duration_days=30):
        """Mark subscription as active and set dates if missing."""
        now = timezone.now()
        if not self.start_date:
            self.start_date = now
        if not self.end_date:
            self.end_date = now + timedelta(days=duration_days)
        self.is_active = True
        self.save()

    def deactivate(self):
        """Deactivate subscription."""
        self.is_active = False
        self.save()

    def has_active_subscription(self):
        """
        Return True if:
        - Subscription is_active=True, and
        - Either no end_date (manual admin subscription) OR end_date > now.
        """
        if not self.is_active:
            return False
        if not self.end_date:
            return True  # admin-added subscription with no expiry
        return self.end_date > timezone.now()

    def __str__(self):
        status = "Active" if self.has_active_subscription() else "Inactive"
        return f"{self.user.username} - {self.get_plan_name_display()} ({status})"



class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    date_subscribed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    

    
class JobEngagement(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("engaged", "Engaged"),  # Employer has hired the chef
    ]

    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_engagements")
    candidate = models.ForeignKey(User, on_delete=models.CASCADE, related_name="job_engagements_as_candidate")
    cv_submission = models.ForeignKey("CVSubmission", on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    application = models.ForeignKey("JobApplication", on_delete=models.CASCADE, null=True, blank=True)
    candidate_phone = models.CharField(max_length=30, blank=True, null=True)
    candidate_country = models.CharField(max_length=100, blank=True, null=True)
    
    # === New Fields for testimony tracking ===
    hired_at = models.DateTimeField(blank=True, null=True)

    # Employer side
    employer_testimony = models.TextField(blank=True, null=True)
    employer_testimony_submitted = models.BooleanField(default=False)

    # Chef side
    chef_testimony = models.TextField(blank=True, null=True)
    chef_testimony_submitted = models.BooleanField(default=False)


    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Track when hired
    hired_at = models.DateTimeField(blank=True, null=True)

    def mark_engaged(self):
        """Call when employer officially hires a chef."""
        self.status = "engaged"
        self.hired_at = timezone.now()
        self.save()

    def disable_unresponsive_users(self):
        """Disable employer or chef accounts if no testimony within 7 days."""
        if not self.hired_at:
            return  # No hire date yet, nothing to check

        deadline = self.hired_at + timedelta(days=7)

        if timezone.now() > deadline:
            # Disable employer if no testimony
            if not self.employer_testimony_submitted:
                employer_user = self.employer
                employer_user.is_active = False
                employer_user.save()

            # Disable chef if no testimony
            if not self.chef_testimony_submitted:
                chef_user = self.candidate.user
                chef_user.is_active = False
                chef_user.save()


    def chef_testimony_due(self):
        """Returns True if more than 7 days since hire and chef testimony missing."""
        if self.status == "engaged" and not self.chef_testimony and self.hired_at:
            return timezone.now() > self.hired_at + timedelta(days=7)
        return False

    def __str__(self):
        employer_name = self.employer.get_full_name() or self.employer.username
        candidate_name = self.candidate.get_full_name() or self.candidate.username
        return f"{employer_name} → {candidate_name} ({self.status})"




class TestimonyLog(models.Model):
    ROLE_CHOICES = [
        ("employer", "Employer"),
        ("chef", "Chef"),
    ]

    engagement = models.ForeignKey(JobEngagement, on_delete=models.CASCADE, related_name="testimonies", null=True, blank=True )
    application = models.ForeignKey("JobApplication", on_delete=models.CASCADE, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    
    testimony = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role.capitalize()} testimony by {self.user.get_full_name()} on {self.created_at.date()}"


JOB_POSITION_CHOICES = [
    ('executive_chef','Executive Chef'),
    ('sous_chef','Sous Chef'),
    ('pastry_chef','Pastry Chef'),
    ('cook','Cook'),
    ('kitchen_assistant','Kitchen Assistant')
]

EMPLOYMENT_TYPE_CHOICES = [
    ('full_time','Full-time'),
    ('part_time','Part-time'),
    ('contract','Contract'),
    ('temporary','Temporary')
]

MEALS_CHOICES = [('yes','Yes'),('no','No'),('partly','Partly')]

def cv_upload_to(instance, filename):
    safe_name = filename.replace(' ', '_')
    return f'needchef_cvs/{int(time.time())}_{safe_name}'

class NeedChefSubmission(models.Model):

    STATUS_CHOICES = [
        ("pending", "Pending"),       # Candidate hasn’t responded
        ("accepted", "Accepted"),     # Candidate accepted the engagement
        ("rejected", "Rejected"),     # Candidate rejected
        ("completed", "Completed"),       # Employer officially hired
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    nationality = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    state_of_residence = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    
    company_name = models.CharField(max_length=255, default="")
    establishment_type = models.CharField(max_length=255, default="")
    company_address = models.TextField(default="")
    state_of_residence = models.CharField(max_length=255, default="")
    website = models.URLField(blank=True)
    contact_person = models.CharField(max_length=255, default="")
    contact_position = models.CharField(max_length=255, default="")
    contact_email = models.EmailField(default="")
    contact_phone = models.CharField(max_length=20, default="")

    job_positions = models.CharField(max_length=255, blank=True)
    employment_type = models.CharField(max_length=255, blank=True)
    work_location = models.CharField(max_length=255, default="")
    
    start_date = models.DateField(blank=True, null=True)  # allow null
    salary_range = models.CharField(max_length=50, default="")
    working_hours = models.CharField(max_length=50, default="")
    meals_accommodation = MultiSelectField(max_length=20, choices=MEALS_CHOICES, default="no")
    preferred_qualification = models.CharField(max_length=255, blank=True)
    years_experience = models.IntegerField(blank=True, null=True)  # allow null
    skills_cuisine = models.TextField(blank=True)
    language_preference = models.CharField(max_length=255, blank=True)
    additional_notes = models.TextField(blank=True)
    message = models.TextField(blank=True)
    cv = models.FileField(upload_to=cv_upload_to, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    is_approved = models.BooleanField(default=False)

    submitted_at = models.DateTimeField(auto_now_add=True)

    # keep any custom methods here if you had them
    def __str__(self):
        return f"{self.company_name} ({self.contact_email})"
    def get_job_positions_display(self):
        if self.job_positions:
            return ", ".join([pos.strip() for pos in self.job_positions.split(",")])
        return "—"

    def get_employment_type_display(self):
        if self.employment_type:
            return ", ".join([et.strip() for et in self.employment_type.split(",")])
        return "—"

    def __str__(self):
        return f"{self.company_name} ({self.contact_email})"
    

class NeedStaffEngagement(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),       # Candidate hasn’t responded
        ("accepted", "Accepted"),     # Candidate accepted the engagement
        ("rejected", "Rejected"),     # Candidate rejected
        ("engaged", "Engaged"),       # Employer officially hired
    ]

    submission = models.ForeignKey(
        'NeedChefSubmission', 
        on_delete=models.CASCADE, 
        related_name="engagements"
    )
    candidate = models.ForeignKey(
        'Candidate', 
        on_delete=models.CASCADE, 
        related_name="needstaff_engagements"
    )
    message = models.TextField(blank=True, null=True)  # Optional custom message
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Track official hire
    hired_at = models.DateTimeField(blank=True, null=True)

    # Testimony / feedback fields
    employer_testimony = models.TextField(blank=True, null=True)
    employer_testimony_submitted = models.BooleanField(default=False)

    chef_testimony = models.TextField(blank=True, null=True)
    chef_testimony_submitted = models.BooleanField(default=False)

    is_viewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def mark_engaged(self):
        """Call when employer officially hires a candidate."""
        self.status = "engaged"
        self.hired_at = timezone.now()
        self.save()

    def disable_unresponsive_users(self):
        """
        Disable employer or candidate accounts if testimony is not submitted
        within 7 days of hiring.
        """
        if not self.hired_at:
            return

        deadline = self.hired_at + timezone.timedelta(days=7)

        if timezone.now() > deadline:
            # Disable employer if testimony missing
            if not self.employer_testimony_submitted:
                self.submission.user.is_active = False
                self.submission.user.save()
            # Disable candidate if testimony missing
            if not self.chef_testimony_submitted:
                self.candidate.user.is_active = False
                self.candidate.user.save()

    def chef_testimony_due(self):
        """Check if chef testimony is overdue."""
        if self.status == "engaged" and not self.chef_testimony and self.hired_at:
            return timezone.now() > self.hired_at + timezone.timedelta(days=7)
        return False

    def __str__(self):
        return f"{self.submission.company_name} → {self.candidate.full_name} ({self.status})"
    


class Job(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_jobs")
    title = models.CharField(max_length=255)  # e.g., position name
    slug = models.SlugField(unique=True, blank=True, null=True)
    description = models.TextField(blank=True, null=True)  # additional info or message
    need_chef = models.ForeignKey(NeedChefSubmission, null=True, blank=True, on_delete=models.CASCADE)

    # New fields for detailed job info
    company_name = models.CharField(max_length=255, blank=True, null=True)
    establishment_type = models.CharField(max_length=255, blank=True, null=True)
    job_positions = models.CharField(max_length=255, blank=True, null=True)
    employment_type = models.CharField(max_length=255, blank=True, null=True)
    work_location = models.CharField(max_length=255, blank=True, null=True)
    state_of_residence = models.CharField(max_length=255, blank=True, null=True)
    salary_range = models.CharField(max_length=255, blank=True, null=True)
    skills_cuisine = models.TextField(blank=True, null=True)
    preferred_qualification = models.CharField(max_length=255, blank=True, null=True)
    language_preference = models.CharField(max_length=255, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    working_hours = models.CharField(max_length=255, blank=True, null=True)
    meals_accommodation = models.TextField(blank=True, null=True)
    message = models.TextField(blank=True, null=True)  # any additional employer message

    # Application-related fields
    applicant = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications", null=True, blank=True)
    applied_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="applied_jobs")
    application_message = models.TextField(blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Accepted", "Accepted"), ("Rejected", "Rejected")],
        default="Pending",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    posted_at = models.DateTimeField(default=timezone.now)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.title)
            new_slug = base_slug
            counter = 1

            # Ensure slug is unique
            while Job.objects.filter(slug=new_slug).exists():
                new_slug = f"{base_slug}-{counter}"
                counter += 1

            self.slug = new_slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} at {self.company_name or 'Unknown Company'}"
    


class JobApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='applications_as_user' ) 
    job = models.ForeignKey(Job, on_delete=models.CASCADE, null=True, blank=True)
    chef = models.ForeignKey(User, on_delete=models.CASCADE, related_name='applications_as_chef')
    email = models.EmailField(default="")
    job_vacancy = models.ForeignKey("JobVacancySubmission", on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(blank=True, null=True)
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name="received_applications", null=True, blank=True)
    need_chef = models.ForeignKey(NeedChefSubmission, on_delete=models.CASCADE, null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=[
        ('Pending', 'Pending'),
        ('Accepted', 'Accepted'),
        ('Rejected', 'Rejected'),
        ("Completed", "Completed")
    ], default='Pending')
    date_applied = models.DateTimeField(auto_now_add=True)

     # testimonies
    chef_testimony = models.TextField(null=True, blank=True)
    employer_testimony = models.TextField(null=True, blank=True)
    chef_testimony_date = models.DateTimeField(null=True, blank=True)
    employer_testimony_date = models.DateTimeField(null=True, blank=True)
    is_viewed = models.BooleanField(default=False, null=True, blank=True)

    

    def __str__(self):
        if self.job:
            return f"{self.chef.get_full_name()} → {self.job.title} ({self.status})"
        elif self.need_chef:
            return f"{self.chef.get_full_name()} → {self.need_chef.job_positions} ({self.status})"
        return f"{self.chef.get_full_name()} → Unknown ({self.status})"




class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.title}"
    

class CVSubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)

     # Link to JobEngagement
    engagement = models.ForeignKey('JobEngagement', on_delete=models.CASCADE, related_name='cv_submissions', null=True, blank=True)
    full_name = models.CharField(max_length=200)
    gender = models.CharField(max_length=30, blank=True)
    dob = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=50)
    email = models.EmailField()
    address = models.TextField(blank=True)
    # ✅ Use Cities Light dropdowns for country and state
    nationality = models.ForeignKey(
        Country, on_delete=models.SET_NULL, null=True, blank=True, related_name="cv_country"
    )
    state = models.ForeignKey(
        Region, on_delete=models.SET_NULL, null=True, blank=True, related_name="cv_state"
    )

    employment_status = models.CharField(max_length=50, blank=True)
    job_title = models.CharField(max_length=200, blank=True)
    experience_years = models.CharField(max_length=20, blank=True)
    expertise = models.TextField(blank=True)
    expertise_other = models.TextField(blank=True)
    establishment = models.TextField(blank=True)
    establishment_other = models.TextField(blank=True)
    preferred_locations = models.TextField(blank=True)
    preferred_locations_other = models.TextField(blank=True)

    qualification = models.CharField(max_length=200, blank=True)
    culinary_school = models.CharField(max_length=200, blank=True)
    skills = models.TextField(blank=True)

    last_employer = models.CharField(max_length=200, blank=True)
    position_held = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    responsibilities = models.TextField(blank=True)

    contract = models.CharField(max_length=50, blank=True)
    cv = models.FileField(upload_to="cv_uploads/", blank=True, null=True)

    referee_name = models.CharField(max_length=200, blank=True)
    relationship = models.CharField(max_length=100, blank=True)
    referee_contact = models.CharField(max_length=200, blank=True)

    alerts = models.TextField(blank=True)
    job_type = models.TextField(blank=True)
    signature = models.CharField(max_length=200, blank=True)
    date = models.DateField(null=True, blank=True)
    message = models.TextField(blank=True)

    submitted_at = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False)

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("engaged", "Engaged"),  # Employer has hired the chef
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    def __str__(self):
        return f"{self.full_name} - {self.email}"
    

class JobVacancySubmission(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    # ==============================
    # SECTION 1: EMPLOYER INFORMATION
    # ==============================
    BUSINESS_TYPES = [
        ("Hotel", "Hotel"),
        ("Restaurant", "Restaurant"),
        ("Eatery / Quick Service Restaurant", "Eatery / Quick Service Restaurant"),
        ("Event Catering Company", "Event Catering Company"),
        ("Private Residence", "Private Residence"),
        ("Other", "Other (please specify)"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("accepted", "Accepted"),
        ("rejected", "Rejected"),
        ("engaged", "Engaged"),
        ("completed", "Completed"),  # Employer has hired the chef
    ]
    
    employer_name = models.CharField("Business / Organization Name", max_length=255)
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPES)
    other_business_type = models.CharField(max_length=100, blank=True, null=True)
    contact_person_name = models.CharField("Contact Person Name", max_length=150, blank=True, null=True)
    position_title = models.CharField("Position / Title", max_length=150, blank=True, null=True)
    business_address = models.TextField("Business Address")
    state = models.CharField(max_length=100)
    business_phone = models.CharField("Business Phone Number", max_length=20)
    official_email = models.EmailField("Official Email Address")
    website_or_social = models.CharField("Website / Social Media Handle", max_length=255, blank=True, null=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    # ==============================
    # SECTION 2: JOB DETAILS
    # ==============================
    JOB_CATEGORIES = [
        ("Chef (Executive / Head Chef)", "Chef (Executive / Head Chef)"),
        ("Sous Chef", "Sous Chef"),
        ("Cook / Line Cook", "Cook / Line Cook"),
        ("Pastry / Bakery Chef", "Pastry / Bakery Chef"),
        ("Continental / Local Cuisine Chef", "Continental / Local Cuisine Chef"),
        ("Private Chef", "Private Chef"),
        ("Relief / Temporary Chef", "Relief / Temporary Chef"),
        ("Kitchen Assistant", "Kitchen Assistant"),
        ("Waiter / Hospitality Staff", "Waiter / Hospitality Staff"),
        ("Other", "Other"),
    ]

    EMPLOYMENT_TYPES = [
        ("Full-Time", "Full-Time"),
        ("Part-Time", "Part-Time"),
        ("Temporary", "Temporary"),
        ("Relief", "Relief"),
        ("Internship", "Internship"),
        ("Contract", "Contract"),
        ("Trainee", "Trainee"),
        ("Live-In", "Live-In"),
        ("Live-Out", "Live-Out"),
    ]

    SALARY_RANGES = [
        ("Below ₦70,000", "Below ₦70,000"),
        ("₦70,000–₦150,000", "₦70,000–₦150,000"),
        ("₦150,000–₦250,000", "₦150,000–₦250,000"),
        ("₦250,000–₦350,000", "₦250,000–₦350,000"),
        ("Above ₦350,000", "Above ₦350,000"),
        ("Negotiable", "Negotiable"),
    ]

    job_category = models.CharField(max_length=100, choices=JOB_CATEGORIES)
    number_of_positions = models.PositiveIntegerField("Number of Positions Available", blank=True, null=True)
    employment_type = models.CharField(max_length=100, choices=EMPLOYMENT_TYPES)
    job_location = models.CharField(max_length=255)
    expected_start_date = models.DateField(blank=True, null=True)
    work_schedule = models.TextField("Work Schedule (Days, Hours, Shifts)", blank=True, null=True)
    salary_range = models.CharField(max_length=100, choices=SALARY_RANGES, blank=True, null=True)

    # ==============================
    # SECTION 3: JOB DESCRIPTION
    # ==============================
    duties_responsibilities = models.TextField("Key Duties & Responsibilities", blank=True, null=True)
    required_skills = models.TextField("Required Skills & Experience", blank=True, null=True)

    MIN_QUALIFICATION = [
        ("Culinary School Graduate", "Culinary School Graduate"),
        ("Professional Certification", "Professional Certification"),
        ("OND / HND", "OND / HND"),
        ("SSCE", "SSCE"),
        ("Any with Proven Experience", "Any with Proven Experience"),
    ]

    EXPERIENCE_LEVEL = [
        ("Entry-Level (0–2 years)", "Entry-Level (0–2 years)"),
        ("Mid-Level (3–5 years)", "Mid-Level (3–5 years)"),
        ("Senior-Level (6+ years)", "Senior-Level (6+ years)"),
    ]

    GENDER_PREF = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("No Preference", "No Preference"),
    ]

    AGE_RANGES = [
        ("18–25", "18–25"),
        ("26–35", "26–35"),
        ("36–45", "36–45"),
        ("46+", "46+"),
    ]


    BENEFITS = [
            ("Feeding Included", "Feeding Included"),
            ("Accommodation Provided", "Accommodation Provided"),
            ("Transportation Support", "Transportation Support"),
            ("Reference Letter", "Reference Letter"),
            ("Medical / Health Benefits", "Medical / Health Benefits"),
            ("Paid Leave", "Paid Leave"),
            ("Performance Bonus", "Performance Bonus"),
            (" Uniforms Provided", " Uniforms Provided"),
    ]

    min_qualification = models.CharField(max_length=100, choices=MIN_QUALIFICATION, blank=True, null=True)
    experience_level = models.CharField(max_length=100, choices=EXPERIENCE_LEVEL, blank=True, null=True)
    preferred_gender = models.CharField(max_length=50, choices=GENDER_PREF, blank=True, null=True)
    age_range = models.CharField(max_length=50, choices=AGE_RANGES, blank=True, null=True)

    # ==============================
    # SECTION 4: COMPENSATION & BENEFITS
    # ==============================
    salary_from = models.PositiveIntegerField("Salary From (₦)", blank=True, null=True)
    salary_to = models.PositiveIntegerField("Salary To (₦)", blank=True, null=True)
    
    benefits = models.CharField(max_length=50, choices=BENEFITS, blank=True, null=True)

   

    PAYMENT_FREQUENCY = [
        ("Weekly", "Weekly"),
        ("Bi-weekly", "Bi-weekly"),
        ("Monthly", "Monthly"),
    ]

    payment_frequency = models.CharField(max_length=50, choices=PAYMENT_FREQUENCY, blank=True, null=True)

    # ==============================
    # SECTION 5: DOCUMENTATION & VERIFICATION
    # ==============================
    REQUIRED_DOCS = [
        ("CV / Resume", "CV / Resume"),
        ("Valid ID", "Valid ID"),
        ("Food Handler’s Certificate", "Food Handler’s Certificate"),
        ("Reference Letter", "Reference Letter"),
        ("Passport Photograph", "Passport Photograph"),
        ("Other", "Other"),
    ]

    VERIFICATION_LEVELS = [
        ("Basic Screening (CV + Phone Interview)", "Basic Screening (CV + Phone Interview)"),
        ("Standard Verification (ID + References)", "Standard Verification (ID + References)"),
        ("Premium Verification (Full Background Check)", "Premium Verification (Full Background Check)"),
    ]

    required_documents = models.CharField(max_length=255, choices=REQUIRED_DOCS, blank=True, null=True)
    verification_level = models.CharField(max_length=100, choices=VERIFICATION_LEVELS, blank=True, null=True)

    # ==============================
    # SECTION 6: APPLICATION MANAGEMENT
    # ==============================
    INTERVIEW_MODES = [
        ("Physical Interview", "Physical Interview"),
        ("Virtual / Online Interview", "Virtual / Online Interview"),
        ("Either", "Either"),
    ]

    application_deadline = models.DateField(blank=True, null=True)
    interview_mode = models.CharField(max_length=100, choices=INTERVIEW_MODES, blank=True, null=True)
    notes = models.TextField("Additional Notes / Special Instructions", blank=True, null=True)

    # ==============================
    # SECTION 7: EMPLOYER DECLARATION
    # ==============================
    declaration_agreed = models.BooleanField(
        "The information provided is accurate to the best of my knowledge.",
        default=False
    )

    declaration_agreed_2 = models.BooleanField(
        "I authorize Chef James & Associates (CJA) to list and promote this job vacancy.",
        default=False
    )

    declaration_agreed_3 = models.BooleanField(
        "I understand that Chefs.com.ng/CJA will shortlist and recommend only verified candidates.",
        default=False
    )
    date_submitted = models.DateTimeField(auto_now_add=True)

    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.employer_name} — {self.job_category}"



class ReliefChefRequest(models.Model):
    # Section 1: Company Information
    business_name = models.CharField(max_length=255)
    establishment_type = models.CharField(max_length=100)
    company_address = models.CharField(max_length=255)
    state = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    position_role = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    email = models.EmailField()

    # Section 2: Relief Chef Requirement Details
    POSITION_REQUIRED = [
            ("Executive Chef", "Executive Chef"),
            ("Sous Chef", "Sous Chef"),
            ("Cook", "Cook"),
            ("Kitchen Assistant", "Kitchen Assistant"),
            ("BBQ/Grill Chef", "BBQ/Grill Chef"),
            ("Other", "Other"),
    ]

    
    position_required = models.CharField(max_length=100, choices=POSITION_REQUIRED, null=True)
    position_required_other = models.CharField(max_length=100, blank=True)

    REASON_FOR_REQUEST = [
            ("Staff Absence", "Staff Absence"),
            ("Seasonal Deman", "Seasonal Deman"),
            ("Special Event", "Special Event"),
            ("New Opening", "New Opening"),
            ("Other", "Other"),
    ]

    reason_for_request = models.CharField(max_length=100, choices=REASON_FOR_REQUEST, null=True)
    reason_for_request_other = models.CharField(max_length=100, blank=True)

    DURATION = [
            ("1 - 3 Days", "1 - 3 Days"),
            ("1 Week", "1 Week"),
            ("2 - 4 Weeks", "2 - 4 Weeks"),
            ("1 - 3 Months", "1 - 3 Months"),
            ("Other", "Other"),
    ]
    duration_of_assignment = models.CharField(max_length=50, choices=DURATION, null=True)
    duration_other = models.CharField(max_length=100, blank=True)
    expected_start_date = models.DateField()
    work_schedule = models.CharField(max_length=100)
    work_location = models.CharField(max_length=255)

    MEALS_ACCOMODATION = [
            ("Yes", "Yes"),
            ("No", "No"),
            ("Partly", "Partly"),
            
    ]
    meals_accommodation = models.CharField(max_length=50, choices=MEALS_ACCOMODATION, null=True)

    # Section 3: Skill & Experience Preference

    EXPERIENCE_LEVEL = [
            ("Entry Level", "Entry Level"),
            ("Mid Level", "Mid Level"),
            ("Senior/Executive", "Senior/Executive"),
            
    ]
    experience_level = models.CharField(max_length=50, choices=EXPERIENCE_LEVEL, null=True)
    
    CUISINE_TYPE = [
            ("African Cuisine", "African Cuisine"),
            ("Continental", "Continental"),
            ("Pastry/Bakery", "Pastry/Bakery"),
            ("BBQ/Grill", "BBQ/Grill"),
            ("intercontinental", "intercontinental"),
            ("Other", "other"),
            
    ]
    cuisine_type = models.CharField(max_length=100, choices=CUISINE_TYPE, null=True)
    cuisine_type_other = models.CharField(max_length=100, blank=True)
    additional_skills = models.TextField(blank=True)
    languages_preferred = models.CharField(max_length=100, blank=True)

    # Section 4: Payment & Terms
    PAYMENT_ARRANGEMENT = [
            ("Daily Rate", "Daily Rate"),
            ("Weekly Rate", "Weekly Rate"),
            ("Project/Event-Based", "Project/Event-Based"),
            ("To Be Discussed", "To Be Discussed"),
    ]
    payment_arrangement = models.CharField(max_length=50, choices=PAYMENT_ARRANGEMENT, null=True)
    budget_range = models.CharField(max_length=50)

    PAYMENT_MODE = [
            ("Bank Transfer", "Bank Transfer"),
            ("Cash", "Cash"),
            ("Other", "Other"),
    ]
    payment_mode = models.CharField(max_length=50, choices=PAYMENT_MODE, null=True)
    payment_mode_other = models.CharField(max_length=50, blank=True)
    # Section 5: Additional Notes
    additional_notes = models.TextField(blank=True)

    # Section 6: Declaration & Consent
    full_name = models.CharField(max_length=100)
    signature = models.CharField(max_length=100)  # could be digital signature or typed name
    date_submitted = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.business_name} - {self.contact_person}"
    


class PermanentChefRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    company_name = models.CharField(max_length=255)

    BUSINESS_TYPE = [
            ("Hotel", "Hotel"),
            ("Restaurant", "Restaurant"),
            ("Eatry", "Eatry"),
            ("Catering", "Catering"),
            ("Event Company", "Event Company"),
            ("Other", "Other"),
            
    ]
    
    business_type = models.CharField(max_length=100, choices=BUSINESS_TYPE, null=True)
    business_type_other = models.CharField(max_length=100, blank=True)
    business_location = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    website = models.CharField(max_length=255, blank=True, null=True)
    
    POSITION_TITLE = [
            ("Head Chef", "Head Chef"),
            ("Sous Chef", "Sous Chef"),
            ("Pastry Chef", "Pastry Chef"),
            ("Continental Chef", "Continental Chef"),
            ("Other", "Other"),
            
    ]
    position_title = models.CharField(max_length=255, choices=POSITION_TITLE, null=True)
    position_title_other = models.CharField(max_length=255, blank=True)

    EMPLOYMENT_TYPE = [
            ("Full-time", "Full-time"),
            ("Contract", "Contract"),
            ("Live-in", "Live-in"),
    ]
    employment_type = models.CharField(max_length=100, choices=EMPLOYMENT_TYPE, null=True)

    WORK_SCHEDULE = [
            ("6 days per week", "6 days per week"),
            ("Shifts", "Shifts"),
            ("Flexible", "Flexible"),
            ("Other", "Other"),
    ]
    work_schedule = models.CharField(max_length=255, choices=WORK_SCHEDULE, null=True)
    work_schedule_other = models.CharField(max_length=255, blank=True)
    start_date = models.DateField(blank=True, null=True)
    job_location = models.CharField(max_length=255)
    number_of_chefs = models.IntegerField(default="")

    DURATION = [
            ("Permanent /Minimum 12 months", "Permanent /Minimum 12 months"),
            ("Renewable", "Renewable"),
            
    ]
    duration = models.CharField(max_length=255, choices=DURATION, null=True)
    salary_range = models.CharField(max_length=100)

    ACCOMODATION = [
            ("Yes", "Yes"),
            ("No", "No"),
            ("Partial", "Partial"),
    ]
    accommodation_meals = models.CharField(max_length=100, choices=ACCOMODATION, null=True)


    CUISINE_SPECIALTY = [
            ("Local", "Local"),
            ("Continental", "Continental"),
            ("Pastry", "Pastry"),
            ("Grill", "Grill"),
            ("Fusion", "Fusion"),
            ("African", "African"),
            ("Other", "Other"),
    ]
    cuisine_specialty = models.CharField(max_length=255, choices=CUISINE_SPECIALTY, null=True)
    cuisine_specialty_other = models.CharField(max_length=255, blank=True)
    responsibilities = models.TextField()


    EXPERIENCE_LEVEL = [
            ("Entry Level (1–2 years)", "Entry Level (1–2 years)"),
            ("Mid-Level (3–5 years)", "Mid-Level (3–5 years)"),
            ("Senior / Executive (6+ years)", "Senior / Executive (6+ years)"),
    ]
    experience_level = models.CharField(max_length=100, choices=EXPERIENCE_LEVEL, null=True)
    certifications = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=255, blank=True, null=True)
    preferences = models.TextField(blank=True, null=True)



    HIRING_TIMELINE = [
            ("Immediately", "Immediately"),
            ("Within 2 weeks", "Within 2 weeks"),
            ("Within a month", "Within a month"),
            ("Other", "Other"),
    ]
    hiring_timeline = models.CharField(max_length=100, choices=HIRING_TIMELINE, null=True)
    hiring_timeline_other = models.CharField(max_length=100, blank=True)




    CONTACT_METHOD = [
            ("Email", "Email"),
            ("Phone / WhatsApp", "Phone / WhatsApp"),
    ]
    contact_method = models.CharField(max_length=50, choices=CONTACT_METHOD, null=True)
    job_spec_file = models.FileField(upload_to="permanent_chefs/specs/", blank=True, null=True)

    declaration_signed = models.BooleanField(default=False)
    full_name = models.CharField(max_length=100)
    signature = models.CharField(max_length=100)  # could be digital signature or typed name
    date_submitted = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.company_name} - {self.position_title}"
    

class PrivateChefRequest(models.Model):
    # ---------- Section 1: Client Info ----------
    CONTACT_METHOD_CHOICES = [
        ("Phone", "Phone"),
        ("Email", "Email"),
        ("WhatsApp", "WhatsApp"),
    ]

    CLIENT_TYPE_CHOICES = [
        ("Individual / Family", "Individual / Family"),
        ("Corporate / Executive Household", "Corporate / Executive Household"),
        ("Event / Occasion-Based", "Event / Occasion-Based"),
        ("Other", "Other"),
    ]

    # ---------- Section 2: Service Details ----------
    SERVICE_TYPE_CHOICES = [
        ("Full-time Live-in Private Chef", "Full-time Live-in Private Chef"),
        ("Part-time Private Chef", "Part-time Private Chef"),
        ("Event-Based (One-off Service)", "Event-Based (One-off Service)"),
        ("Weekly / Occasional Service", "Weekly / Occasional Service"),
    ]

    DURATION_CHOICES = [
        ("One-time Event", "One-time Event"),
        ("Short-term (1 week – 3 months)", "Short-term (1 week – 3 months)"),
        ("Long-term (6 months – 1 year)", "Long-term (6 months – 1 year)"),
        ("Permanent / Renewable", "Permanent / Renewable"),
    ]

    MEAL_FREQUENCY_CHOICES = [
        ("Breakfast", "Breakfast"),
        ("Lunch", "Lunch"),
        ("Dinner", "Dinner"),
        ("Special Diet / Occasional Service", "Special Diet / Occasional Service"),
    ]

    # ---------- Section 3: Cuisine ----------
    CUISINE_CHOICES = [
        ("Nigerian / African", "Nigerian / African"),
        ("Continental", "Continental"),
        ("Pastry / Dessert", "Pastry / Dessert"),
        ("Fusion / Gourmet", "Fusion / Gourmet"),
        ("Healthy / Diet-Specific", "Healthy / Diet-Specific"),
        ("Other", "Other"),
    ]

    CHEF_GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("No Preference", "No Preference"),
    ]

    PERSONALITY_TRAITS_CHOICES = [
        ("Professionalism", "Professionalism"),
        ("Creativity", "Creativity"),
        ("Cleanliness & Hygiene", "Cleanliness & Hygiene"),
        ("Communication", "Communication"),
        ("Discretion", "Discretion"),
        ("Punctuality", "Punctuality"),
    ]

    INGREDIENT_PROVIDER_CHOICES = [
        ("Client", "Client"),
        ("Chef", "Chef"),
        ("To Be Agreed", "To Be Agreed"),
    ]

    YES_NO_CHOICES = [
        ("Yes", "Yes"),
        ("No", "No"),
    ]

    # ---------- Fields ----------
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES)
    client_type = models.CharField(max_length=50, choices=CLIENT_TYPE_CHOICES)
    client_type_other = models.CharField(max_length=50, blank=True)

    service_type = models.CharField(max_length=50, choices=SERVICE_TYPE_CHOICES)
    duration = models.CharField(max_length=50, choices=DURATION_CHOICES)
    start_date = models.DateField(null=True, blank=True)
    service_location = models.CharField(max_length=255)
    number_of_people = models.PositiveIntegerField()
    meal_frequency = MultiSelectField(max_length=50, choices=MEAL_FREQUENCY_CHOICES)

    cuisine_type = models.CharField(max_length=50, choices=CUISINE_CHOICES)
    cuisine_type_other = models.CharField(max_length=50, blank=True)
    specific_dishes = models.TextField(blank=True, null=True)
    dietary_restrictions = models.TextField(blank=True, null=True)
    chef_gender = models.CharField(max_length=20, choices=CHEF_GENDER_CHOICES)
    personality_traits = models.CharField(max_length=100, choices=PERSONALITY_TRAITS_CHOICES)


    EVENT_TYPE = [
        ("Birthday", "Birthday"),
        ("Corporate Dinner", "Corporate Dinner"),
        ("Wedding", "Wedding"),
        ("Housewarming", "Housewarming"),
    ]
    event_type = models.CharField(max_length=100, choices=EVENT_TYPE, null=True)
    event_type_other = models.CharField(max_length=100, blank=True)
    event_date = models.CharField(blank=True, null=True)
    event_venue = models.CharField(max_length=255, blank=True, null=True)
    number_of_guests = models.PositiveIntegerField(blank=True, null=True)

    
    ADDITIONAL_SERVICES = [
        ("Waiters / Service Staff", "Waiters / Service Staff"),
        ("Kitchen Assistants", "Kitchen Assistants"),
        ("Food Plating & Presentation", "Food Plating & Presentation"),
        ("Event Menu Design", "Event Menu Design"),
    ]
    additional_services = models.CharField(max_length=100, choices=ADDITIONAL_SERVICES, null=True)

    budget = models.CharField(max_length=100)
    ingredient_provider = models.CharField(max_length=20, choices=INGREDIENT_PROVIDER_CHOICES)
    accommodation_provided = models.CharField(max_length=5, choices=YES_NO_CHOICES)
    transportation_support = models.CharField(max_length=5, choices=YES_NO_CHOICES)

    client_name = models.CharField(max_length=100)
    signature = models.CharField(max_length=100)

    date_submitted = models.DateTimeField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.full_name} - {self.service_type}"
    


# ======================= FOR CULINARY PAGE ==============================
# ===========================-------------------============================




GENDER_CHOICES = [
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
]

TITLE_CHOICES = [
    ("Private Chef", "Private Chef"),
    ("Executive Chef", "Executive Chef"),
    ("Pastry Chef", "Pastry Chef"),
    ("Sous Chef", "Sous Chef"),
    ("Other", "Other"),
]

EXPERIENCE_CHOICES = [
    ("1-3", "1–3 years"),
    ("4-7", "4–7 years"),
    ("8-10", "8–10 years"),
    ("10+", "10+ years"),
]

SPECIALTY_CHOICES = [
    ("Nigerian / African Cuisine", "Nigerian / African Cuisine"),
    ("Continental Cuisine", "Continental Cuisine"),
    ("Pastry / Bakery", "Pastry / Bakery"),
    ("Grill / Barbecue", "Grill / Barbecue"),
    ("Asian / Oriental", "Asian / Oriental"),
    ("Fusion / Creative Cuisine", "Fusion / Creative Cuisine"),
    ("Other", "Other"),
]

AVAILABILITY_CHOICES = [
    ("Full-Time", "Full-Time"),
    ("Contract", "Contract"),
    ("Private Service", "Private Service"),
    ("Temporary / Relief", "Temporary / Relief"),
]

REPRESENTATION_CHOICES = [
    ("Local Placements", "Local Placements (within Nigeria)"),
    ("International Opportunities", "International Opportunities"),
    ("Celebrity Chef Opportunities", "Celebrity Chef Opportunities"),
    ("Brand Collaboration", "Brand Collaboration / Endorsements & Media Features"),
    ("Culinary Competitions", "Culinary Competitions & Events"),
    ("Private Chef Engagements", "Private Chef Engagements"),
    ("Culinary Training", "Culinary Training / Mentorship Opportunities"),
]

CONTRACT_CHOICES = [
    ("Permanent", "Permanent"),
    ("Temporary", "Temporary"),
    ("Freelance", "Freelance / Event-based"),
]

CURRENTLY_AVAILABLE= [
    ("True", "Yes"),
    ("False", "No"),
]

HAS_TRAVEL = [
    ("True", "Yes"),
    ("False", "No"),
]

class CulinaryAgentRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # SECTION 1
    full_name = models.CharField(max_length=150)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES)
    stage_name = models.CharField(max_length=150, blank=True, null=True)
    nationality = CountryField()
    state = models.CharField(max_length=150)
    address = models.TextField()
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    portfolio_link = models.URLField(blank=True, null=True)
    photo = models.ImageField(upload_to="culinary_agents/photos/")
    
    # SECTION 2
    professional_title = models.CharField(max_length=50, choices=TITLE_CHOICES)
    experience_years = models.CharField(max_length=10, choices=EXPERIENCE_CHOICES)
    culinary_specialty = models.CharField(max_length=100, choices=SPECIALTY_CHOICES)
    specialty_other = models.CharField(max_length=100, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    certifications = models.TextField(blank=True, null=True)
    languages = models.CharField(max_length=150, blank=True, null=True)
    availability_type = models.CharField(max_length=30, choices=AVAILABILITY_CHOICES)
    
    # SECTION 3
    current_employer = models.CharField(max_length=150, blank=True, null=True)
    position_held = models.CharField(max_length=150, blank=True, null=True)
    employment_duration = models.CharField(max_length=100, blank=True, null=True)
    key_responsibilities = models.TextField(blank=True, null=True)
    previous_employers = models.TextField(blank=True, null=True)
    
    # SECTION 4
    culinary_opportunities  = models.JSONField(default=list)
    preferred_location = models.CharField(max_length=150, blank=True, null=True)
    expected_pay = models.CharField(max_length=100, blank=True, null=True)
    manage_bookings = models.BooleanField(default=False)
    preferred_contract = models.CharField(max_length=50, choices=CONTRACT_CHOICES)
    career_goals = models.TextField(blank=True, null=True)
    reason_for_representation = models.TextField(blank=True, null=True)
    
    # SECTION 5
    cv = models.FileField(upload_to="culinary_agents/cv/")
    feature_link = models.URLField(blank=True, null=True)
    short_bio = models.TextField(max_length=150, null=True)
    
    # SECTION 6
    
    currently_available = models.CharField(max_length=50, choices=CURRENTLY_AVAILABLE, null=True)
    available_from = models.DateField(null=True, blank=True)
    has_travel_doc = models.CharField(max_length=50, choices=HAS_TRAVEL, null=True)
    
    # SECTION 7
    agreed_to_terms = models.BooleanField(default=False)
    agreed_to_terms_2 = models.BooleanField(default=False)
    agreed_to_terms_main = models.BooleanField(default=False)

    full_name_lower = models.CharField(max_length=200)
    signature = models.CharField(max_length=200)
    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name
    
class DishPhoto(models.Model):
    agent = models.ForeignKey(CulinaryAgentRegistration, on_delete=models.CASCADE, related_name="dish_photos")
    image = models.ImageField(upload_to="agents/dishes/")


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} - {self.email}"


class CareerAdvice(models.Model):
    title = models.CharField(max_length=500)
    link = models.URLField()
    summary = models.TextField(blank=True, null=True)
    image = models.URLField(blank=True, null=True)
    published = models.DateTimeField()
    source = models.CharField(max_length=255, default="Escoffier")

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-published']

    def __str__(self):
        return self.title