from django import forms
from .models import GENDER_CHOICESS, Candidate, SPECIALTIES, PREFERRED_LOCATIONS, ESTABLISHMENT_TYPES, EXPERIENCE_CHOICESS, EMPLOYMENT_STATUS, CONTRACT_TERM, GENDER_CHOICESS, JOB_POSITION_CHOICES, EMPLOYMENT_TYPE_CHOICES, MEALS_CHOICES, CVSubmission, JobVacancySubmission, ReliefChefRequest, PermanentChefRequest
from cities_light.models import Country, Region
from django.db import models
from .models import NeedChefSubmission, PrivateChefRequest, CulinaryAgentRegistration, ContactMessage
from django.contrib.auth.models import User
from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Fieldset
from django.contrib.auth.forms import PasswordResetForm
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget



# ------------------ Candidate Form ------------------ #
class CandidateRegistrationForm(forms.ModelForm):
    EXCLUSIVE_JOB_CHOICES = [
        ("Relief Chef", "Relief Chef"),
        ("Permanent Chef", "Permanent Chef"),
        ("Private Chef", "Private Chef"),
        ("All of the above", "All of the above"),
    ]

    preferred_job_types = forms.MultipleChoiceField(
        choices=EXCLUSIVE_JOB_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Preferred Job Type(s)"
    )

    preferred_locations = forms.MultipleChoiceField(
        choices=PREFERRED_LOCATIONS,
        required=False,
        widget=forms.CheckboxSelectMultiple
    )

    specialty = forms.ChoiceField(
        choices=SPECIALTIES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    establishment_preference = forms.ChoiceField(
        choices=ESTABLISHMENT_TYPES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    years_experience = forms.ChoiceField(
        choices=EXPERIENCE_CHOICESS,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    gender = forms.ChoiceField(
        choices=GENDER_CHOICESS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    current_employment_status = forms.ChoiceField(
        choices=EMPLOYMENT_STATUS,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    contract_term = forms.ChoiceField(
        choices=CONTRACT_TERM,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    nationality = forms.ModelChoiceField(
        queryset=Country.objects.all().order_by("name"),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    state_of_residence = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())
    
    class Meta:
        model = Candidate
        fields = [
            'full_name', 'gender', 'date_of_birth', 'phone', 'email', 'residential_address',
            'state_of_residence', 'nationality', 'current_employment_status', 'current_last_job_title',
            'years_experience', 'specialty', 'specialty_other', 'establishment_preference', 'establishment_other',
            'preferred_locations', 'preferred_location_other', 'highest_qualification', 'culinary_school',
            'additional_skills', 'last_employer', 'last_position', 'start_date', 'end_date', 'key_responsibilities',
            'contract_term', 'cv', 'referee_name', 'referee_relationship', 'referee_contact',
            'alert_email', 'alert_whatsapp', 'alert_sms', 'message'
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class':'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'phone': forms.TextInput(attrs={'class':'form-control'}),
            'email': forms.EmailInput(attrs={'class':'form-control'}),
            'residential_address': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'current_last_job_title': forms.TextInput(attrs={'class':'form-control'}),
            'specialty_other': forms.TextInput(attrs={'class':'form-control'}),
            'establishment_other': forms.TextInput(attrs={'class':'form-control'}),
            'preferred_location_other': forms.TextInput(attrs={'class':'form-control'}),
            'highest_qualification': forms.TextInput(attrs={'class':'form-control'}),
            'culinary_school': forms.TextInput(attrs={'class':'form-control'}),
            'additional_skills': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'last_employer': forms.TextInput(attrs={'class':'form-control'}),
            'last_position': forms.TextInput(attrs={'class':'form-control'}),
            'start_date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'end_date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'key_responsibilities': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'cv': forms.ClearableFileInput(attrs={'class':'form-control'}),
            'referee_name': forms.TextInput(attrs={'class':'form-control'}),
            'referee_relationship': forms.TextInput(attrs={'class':'form-control'}),
            'referee_contact': forms.TextInput(attrs={'class':'form-control'}),
            'message': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'nationality' in self.data:
            try:
                country_id = int(self.data.get('nationality'))
                self.fields['state_of_residence'].queryset = Region.objects.filter(country_id=country_id).order_by('name')
            except (ValueError, TypeError):
                self.fields['state_of_residence'].queryset = Region.objects.none()
        elif self.instance.pk and self.instance.nationality:
            self.fields['state_of_residence'].queryset = Region.objects.filter(country=self.instance.nationality).order_by('name')

    def clean_cv(self):
        cv = self.cleaned_data.get('cv')
        if cv:
            if cv.size > 4 * 1024 * 1024:
                raise forms.ValidationError("CV file too large (max 4MB).")
            ext = cv.name.split('.')[-1].lower()
            if ext not in ['pdf', 'doc', 'docx']:
                raise forms.ValidationError("Upload a PDF or Word document (doc, docx).")
        return cv

    def clean_preferred_locations(self):
        locations = self.cleaned_data.get('preferred_locations')
        return ','.join(locations) if locations else ''


class CompleteProfileForm(forms.Form):
    phone = forms.CharField(max_length=20, required=True)
    country = CountryField().formfield(widget=CountrySelectWidget())
    password1 = forms.CharField(widget=forms.PasswordInput, label="Password", required=True)
    password2 = forms.CharField(widget=forms.PasswordInput, label="Confirm Password", required=True)

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
    

    

class NeedStaffForm(forms.ModelForm):
    job_positions = forms.MultipleChoiceField(
        choices=[
            ('executive_chef','Executive Chef'),
            ('sous_chef','Sous Chef'),
            ('pastry_chef','Pastry Chef'),
            ('cook','Cook'),
            ('kitchen_assistant','Kitchen Assistant'),
            ('other','Other'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Position(s) Available"
    )
    job_positions_other = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Fill if other Position selected'}),
        label="Other Position"
    )

    employment_type = forms.MultipleChoiceField(
        choices=[
            ('full_time','Full-time'),
            ('part_time','Part-time'),
            ('contract','Contract'),
            ('temporary','Temporary')
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Employment Type"
    )

    meals_accommodation = forms.MultipleChoiceField(
        choices=MEALS_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Meals / Accommodation Provided?"
    )

    years_experience = forms.IntegerField(
        required=True,
        widget=forms.NumberInput(attrs={'class':'form-control', 'min':0, 'placeholder':'Enter years of experience'}),
        label="Years of Experience Required"
    )

    nationality = forms.ModelChoiceField(
        queryset=Country.objects.none(),  # temporarily empty
        widget=forms.Select(attrs={'class':'form-select','readonly':'readonly'}),
        label="Country"
    )

    state_of_residence = forms.ModelChoiceField(
        queryset=Region.objects.none(),
        widget=forms.Select(attrs={'class':'form-select'}),
        required=True,
        label="State of Residence"
    )

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = NeedChefSubmission
        fields = [
            'company_name', 'establishment_type', 'company_address', 'state_of_residence', 'website',
            'contact_person', 'contact_position', 'contact_email', 'contact_phone',
            'job_positions', 'job_positions_other', 'employment_type', 'work_location', 'start_date',
            'salary_range', 'working_hours', 'meals_accommodation',
            'preferred_qualification', 'years_experience', 'skills_cuisine', 'language_preference',
            'message'
        ]
        widgets = {
            'company_name': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter company name'}),
            'establishment_type': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter establishment type'}),
            'company_address': forms.Textarea(attrs={'class':'form-control','rows':2,'placeholder':'Enter address'}),
            'website': forms.URLInput(attrs={'class':'form-control','placeholder':'Enter website'}),
            'contact_person': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter contact person'}),
            'contact_position': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter contact position'}),
            'contact_email': forms.EmailInput(attrs={'class':'form-control','placeholder':'Enter email address'}),
            'contact_phone': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter phone number'}),
            'work_location': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter work location'}),
            'start_date': forms.DateInput(attrs={'type':'date','class':'form-control'}),
            'salary_range': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter salary range'}),
            'working_hours': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter working hours'}),
            'preferred_qualification': forms.TextInput(attrs={'class':'form-control','placeholder':'Enter preferred qualification'}),
            'skills_cuisine': forms.Textarea(attrs={'class':'form-control','rows':2}),
            'language_preference': forms.TextInput(attrs={'class':'form-control'}),
            'message': forms.Textarea(attrs={'class':'form-control','rows':3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            nigeria = Country.objects.get(name__iexact="Nigeria")
            self.fields['nationality'].queryset = Country.objects.filter(name__iexact="Nigeria")
            self.fields['nationality'].initial = nigeria
            self.fields['state_of_residence'].queryset = Region.objects.filter(country=nigeria).order_by('name')
        except Exception:
            # Ignore errors before migrations or when DB is empty
            self.fields['nationality'].queryset = Country.objects.none()
            self.fields['state_of_residence'].queryset = Region.objects.none()



class CVSubmissionForm(forms.ModelForm):
    nationality = forms.ModelChoiceField(
        queryset=Country.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "country-select"})
    )

    state = forms.ModelChoiceField(
        queryset=Region.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-select", "id": "state-select"})
    )

    phone = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "id": "phone",
            "placeholder": "WhatsApp preferred",
        })
    )

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = CVSubmission
        fields = "__all__"
        exclude = ["date_submitted", "is_approved", "status"]
        

        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your full name"}),

            "gender": forms.Select(attrs={"class": "form-select"}, choices=[
                ("Male", "Male"),
                ("Female", "Female"),
                ("Prefer not to say", "Prefer not to say")
            ]),

            "dob": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),

            "employment_status": forms.TextInput(attrs={"class": "form-control"}),
            "job_title": forms.TextInput(attrs={"class": "form-control"}),
            "experience_years": forms.TextInput(attrs={"class": "form-control"}),
            "expertise": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "establishment": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "preferred_locations": forms.Textarea(attrs={"class": "form-control", "rows": 2}),

            "qualification": forms.TextInput(attrs={"class": "form-control"}),
            "culinary_school": forms.TextInput(attrs={"class": "form-control"}),
            "skills": forms.Textarea(attrs={"class": "form-control", "rows": 2}),

            "last_employer": forms.TextInput(attrs={"class": "form-control"}),
            "position_held": forms.TextInput(attrs={"class": "form-control"}),
            "start_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "end_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "responsibilities": forms.Textarea(attrs={"class": "form-control", "rows": 2}),

            "contract": forms.Select(attrs={"class": "form-select"}, choices=[
                ("Full-time", "Full-time"),
                ("Part-time", "Part-time"),
                ("Contract", "Contract"),
            ]),

            "cv": forms.ClearableFileInput(attrs={"class": "form-control"}),

            "referee_name": forms.TextInput(attrs={"class": "form-control"}),
            "relationship": forms.TextInput(attrs={"class": "form-control"}),
            "referee_contact": forms.TextInput(attrs={"class": "form-control"}),

            "alerts": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "job_type": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "signature": forms.TextInput(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "message": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }



# class JobVacancySubmissionForm(forms.ModelForm):
#     captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

#     class Meta:
#         model = JobVacancySubmission
#         fields = "__all__"
#         widgets = {
#             "expected_start_date": forms.DateInput(attrs={"type": "date"}),
#             "application_deadline": forms.DateInput(attrs={"type": "date"}),
#             "business_address": forms.Textarea(attrs={"rows": 1}),
#             "work_schedule": forms.Textarea(attrs={"rows": 1}),
#             "duties_responsibilities": forms.Textarea(attrs={"rows": 1}),
#             "required_skills": forms.Textarea(attrs={"rows": 1}),
#             "notes": forms.Textarea(attrs={"rows": 1}),
#         }


class JobVacancySubmissionForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = JobVacancySubmission
        exclude = ["status", "is_approved", "date_submitted"]
        fields = "__all__"
        widgets = {
            "expected_start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "application_deadline": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "business_address": forms.Textarea(attrs={
                "rows": 1,
                "placeholder": "Enter full business address",
                "class": "form-control",
            }),
            "work_schedule": forms.Textarea(attrs={
                "rows": 1,
                "placeholder": "e.g. Monday–Saturday, 8am–6pm",
                "class": "form-control",
            }),
            "duties_responsibilities": forms.Textarea(attrs={
                "rows": 1,
                "placeholder": "List the main duties and responsibilities",
                "class": "form-control",
            }),
            "required_skills": forms.Textarea(attrs={
                "rows": 1,
                "placeholder": "e.g. Culinary skills, teamwork, communication, etc.",
                "class": "form-control",
            }),
            "notes": forms.Textarea(attrs={
                "rows": 1,
                "placeholder": "Add any extra notes or instructions for applicants",
                "class": "form-control",
            }),
            "employer_name": forms.TextInput(attrs={
                "placeholder": "Business / Organization Name",
                "class": "form-control",
            }),
            "other_business_type": forms.TextInput(attrs={
                "placeholder": "Specify other business type (if applicable)",
                "class": "form-control",
            }),
            "contact_person_name": forms.TextInput(attrs={
                "placeholder": "Enter full name of contact person",
                "class": "form-control",
            }),
            "position_title": forms.TextInput(attrs={
                "placeholder": "e.g. HR Manager, Owner, Supervisor",
                "class": "form-control",
            }),
            "state": forms.TextInput(attrs={
                "placeholder": "State where the business is located",
                "class": "form-control",
            }),
            "business_phone": forms.TextInput(attrs={
                "placeholder": "e.g. +234 801 234 5678",
                "class": "form-control",
            }),
            "official_email": forms.EmailInput(attrs={
                "placeholder": "e.g. info@business.com",
                "class": "form-control",
            }),
            "website_or_social": forms.TextInput(attrs={
                "placeholder": "e.g. www.business.com or @businesshandle",
                "class": "form-control",
            }),
            "number_of_positions": forms.NumberInput(attrs={
                "placeholder": "e.g. 2",
                "class": "form-control",
            }),
            "job_location": forms.TextInput(attrs={
                "placeholder": "City or area where the job is located",
                "class": "form-control",
            }),
            "salary_from": forms.NumberInput(attrs={
                "placeholder": "Minimum salary in ₦",
                "class": "form-control",
            }),
            "salary_to": forms.NumberInput(attrs={
                "placeholder": "Maximum salary in ₦",
                "class": "form-control",
            }),
            # "benefits": forms.Textarea(attrs={
            #     "rows": 1,
            #     "placeholder": "e.g. Accommodation, meals, bonuses, etc.",
            #     "class": "form-control",
            # }),
        }


class ReliefChefRequestForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    expected_start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    phone_number = forms.CharField(
        label="Phone Number",
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'type': 'tel',        # Important for intl-tel-input
            'id': 'phone',        # Must match JS selector
            'placeholder': '+234 ...'
        })
    )

    class Meta:
        model = ReliefChefRequest
        fields = '__all__'
        widgets = {
            'additional_notes': forms.Textarea(attrs={'rows':4}),
            'additional_skills': forms.Textarea(attrs={'rows':4}),
            'signature': forms.TextInput(attrs={'placeholder': 'Type your name as signature'}),
        }


class PermanentChefRequestForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    start_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    class Meta:
        model = PermanentChefRequest
        fields = "__all__"
        exclude = ["user", "date_submitted", "is_approved"]
        widgets= {
            'responsibilities': forms.Textarea(attrs={'rows':1}),
            'certifications': forms.Textarea(attrs={'rows':1}),
            'preferences': forms.Textarea(attrs={'rows':1}),
        }


class PrivateChefRequestForm(forms.ModelForm):

    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())


    event_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )

    meal_frequency = forms.MultipleChoiceField(
        choices=[
            ("Breakfast", "Breakfast"),
            ("Lunch", "Lunch"),
            ("Dinner", "Dinner"),
            ("Special Diet / Occasional Service", "Special Diet / Occasional Service"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="Meal Frequency",
        required=True,
    )

    class Meta:
        model = PrivateChefRequest
        exclude = ["user", "is_approved", "date_submitted"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
            "specific_dishes": forms.Textarea(attrs={"rows": 1}),
            "dietary_restrictions": forms.Textarea(attrs={"rows": 1}),
            }

    
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class CulinaryAgentRegistrationForm(forms.ModelForm):
    
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    culinary_opportunities = forms.MultipleChoiceField(
        choices=[
            ("Local Placements", "Local Placements (within Nigeria)"),
            ("International Opportunities", "International Opportunities"),
            ("Celebrity Chef Opportunities", "Celebrity Chef Opportunities"),
            ("Brand Collaboration", "Brand Collaboration / Endorsements"),
            ("Culinary Competitions", "Culinary Competitions & Events"),
            ("Private Chef Engagements", "Private Chef Engagements"),
            ("Culinary Training", "Culinary Training / Mentorship Opportunities"),
        ],
        widget=forms.CheckboxSelectMultiple,
        label="What type of culinary opportunities are you seeking?",
        required=True,
    )
    stage_name = forms.CharField(
        label="Stage/Professional name",
        required=True,
    
    )

    photo = forms.ImageField(
        label="Upload Professional Photo",
        required=True,
        widget=forms.ClearableFileInput()
    )

    cv = forms.FileField(
        label="Upload Your CV / Resume",
        required=True,
        widget=forms.ClearableFileInput()
    )
    

    current_employer = forms.CharField(
        label="Current/Most Recent Employer",
        required=False,
    
    )

    previous_employers = forms.CharField(
        label="Previous Employers/Placements",
        required=False,
    
    )


    full_name_lower = forms.CharField(
        label="Full Name",
        required=True,
    
    )
    manage_bookings = forms.BooleanField(
        label="Would you like us to manage your professional bookings and brand deals?",
        required=False,
    
    )


    career_goals = forms.CharField(
    label="What Are Your Career Goals as a Chef?",
    required=False,
    widget=forms.Textarea(attrs={"rows": 3, "placeholder": "Describe your career goals..."}),
    )


    
    # 

    portfolio_link = forms.URLField(
    label="Instagram or Portfolio Link",
    required=False,
    )

    feature_link = forms.URLField(
    label="Link to Your feature Video/Culinary Portfolio / Instagram / YouTube (if any)",
    required=False,
    )

 
    currently_available = forms.TypedChoiceField(
    label="Are You Currently Available?",
    choices=[("True", "Yes"), ("False", "No")],
    coerce=lambda x: x == 'True',
    widget=forms.RadioSelect,
    required=True
    )

    has_travel_doc = forms.TypedChoiceField(
    label="Do You Have a Valid Travel Document (for international placements)?",
    choices=[("True", "Yes"), ("False", "No")],
    coerce=lambda x: x == 'True',
    widget=forms.RadioSelect,
    required=True
    )

    available_from = forms.DateField(
        label="Available to Start New Engagements From",
        required=True,
        widget= forms.DateInput(attrs={"type": "date"}),
    
    )


    agreed_to_terms = forms.BooleanField(
    label="By submitting this form, I authorize Chef James & Associates Nig. Ltd to review, represent, and promote my culinary profile for potential engagements and collaborations under the agency’s terms and conditions.",
    required=True
    )

    agreed_to_terms_2 = forms.BooleanField(
    label="I confirm that the information provided above is true and accurate. I authorize Chef James & Associates (CJA) to act as my culinary representative and to share my professional profile with verified clients for placement or promotional purposes.",
    required=True
    )

    agreed_to_terms_main = forms.BooleanField(
    label="I Agree to the Terms of Representation",
    required=True
    )

    class Meta:
        model = CulinaryAgentRegistration
        
        exclude = ["user", "date_submitted"]
        widgets = {
            "date_of_birth": forms.DateInput(attrs={"type": "date"}),
            
            "address": forms.Textarea(attrs={"rows": 1, "placeholder": "Enter address..."}),
            "education": forms.Textarea(attrs={"rows": 1, "placeholder": "Education level..."}),
            "certifications": forms.Textarea(attrs={"rows": 1, "placeholder": "Enter certification..."}),
            "key_responsibilities": forms.Textarea(attrs={"rows": 1, "placeholder": "What are your key responsibilities..."}),
            "previous_employers": forms.Textarea(attrs={"rows": 1}),
            "reason_for_representation": forms.Textarea(attrs={"rows": 2, "placeholder": "Enter reason for representation..."}),
            "short_bio": forms.Textarea(attrs={"rows": 2, "placeholder": "Enter short bio. Not less than 30 words..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = "post"
        self.helper.add_input(Submit("submit", "Submit Application", css_class="btn btn-primary w-100"))


class ContactForm(forms.ModelForm):
    captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox())

    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']


class EmailBasedPasswordResetForm(PasswordResetForm):
    def get_users(self, email):
        """Return users who match the given email address."""
        active_users = User.objects.filter(email__iexact=email, is_active=True)
        return (u for u in active_users)