from email.mime import application
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.mail import send_mail, BadHeaderError
from django.conf import settings
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from .models import ChefProfile, EmployerProfile, VerificationCode, Job, Subscription, NewsletterSubscriber, Candidate, JobEngagement, TestimonyLog, NeedChefSubmission, Notification, NeedStaffEngagement, JobApplication, CVSubmission, JobVacancySubmission, DishPhoto, UserOTP
import random
import requests
import traceback
from django.shortcuts import redirect
from django.core.management.base import BaseCommand
import json
import ast
import threading
from django.http import HttpResponse
from django.http import JsonResponse, StreamingHttpResponse
from django.contrib.admin.models import LogEntry, CHANGE
from cities_light.models import Country, Region, City
from smtplib import SMTPException
from django.views.decorators.http import require_POST
from django.core.mail import mail_admins
from datetime import timedelta
from django.utils import timezone
from django.db.models import Count,  Q
from .forms import CandidateRegistrationForm, NeedStaffForm, CVSubmissionForm, JobVacancySubmissionForm, ReliefChefRequestForm, PermanentChefRequestForm, PrivateChefRequestForm, CulinaryAgentRegistrationForm, ContactForm, CompleteProfileForm
from django.urls import reverse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE, DELETION
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.db.models import F, Value, CharField
from django.db.models.functions import Coalesce
from django.contrib.auth.views import PasswordChangeView, PasswordResetView
from django.urls import reverse_lazy
from .utils import send_otp_email
from django.core.mail import BadHeaderError
from .forms import EmailBasedPasswordResetForm
from django.db.models import Prefetch
import uuid
import os
from huggingface_hub import InferenceClient
from django.db.models import F
import feedparser
from django.core.cache import cache
from main.tasks import fetch_career_advice
from django.utils.timezone import now
# Create your views here.


def fetch_feed(url, cache_key, limit=3):
    """Fetch and cache RSS feed entries."""
    cached = cache.get(cache_key)
    if cached:
        return cached

    try:
        feed = feedparser.parse(url)
        items = []

        for entry in feed.entries[:limit]:
            items.append({
                "title": entry.get("title", "Untitled"),
                "link": entry.get("link", "#"),
                "published": entry.get("published", "Unknown date"),
                "summary": entry.get("summary", "")[:180] + "...",
                "image": (
                    entry.media_thumbnail[0]["url"]
                    if hasattr(entry, "media_thumbnail")
                    else "/static/pictures/default-blog.jpg"
                ),
            })
    except Exception:
        items = []

    cache.set(cache_key, items, 95000)  # cache 15 mins
    return items


def convert_to_string(value):
    """
    Converts a value to a clean comma-separated string.
    Works for list, tuple, MultiSelectField, or strings.
    Removes brackets and quotes if present.
    """
    if not value:
        return "Not specified"
    
    # Handle list or tuple
    if isinstance(value, (list, tuple)):
        return ", ".join([str(v).strip() for v in value if v])
    
    # If string, remove brackets/quotes if mistakenly stored
    value_str = str(value).strip()
    if value_str.startswith("[") and value_str.endswith("]"):
        value_str = value_str[1:-1]  # remove brackets
    value_str = value_str.replace("'", "").replace('"', "")
    return value_str




def home(request):
    # Counts
    total_companies = EmployerProfile.objects.filter(is_verified=True).count()
    total_applications = JobApplication.objects.all().count()
    total_jobs = JobVacancySubmission.objects.filter(is_approved=True).count() + Candidate.objects.filter(is_approved=True).count()
    total_members = User.objects.filter(is_active=True).count()

    # Testimonies
    testimonies_raw = TestimonyLog.objects.select_related('user').all().order_by('-created_at')[:50]
    testimonies = []
    for t in testimonies_raw:
        user = t.user
        profile_pic = None
        if hasattr(user, 'chefprofile') and user.chefprofile.profile_picture:
            profile_pic = user.chefprofile.profile_picture.url
        elif hasattr(user, 'employerprofile') and user.employerprofile.profile_picture:
            profile_pic = user.employerprofile.profile_picture.url
        testimonies.append({
            "id": t.id,
            "user": user,
            "message": t.testimony,
            "created_at": t.created_at,
            "profile_pic": profile_pic,
        })

    # Career advice
    career_advices = cache.get("career_advice_feed")
    if not career_advices:
        career_advices = fetch_career_advice()

    # Fetch jobs
    cv_jobs = NeedChefSubmission.objects.filter(is_approved=True)
    candidate_jobs = JobVacancySubmission.objects.filter(is_approved=True)

    all_jobs = []

    # Map NeedChefSubmission jobs
    for job in cv_jobs:
        profile_pic = None
        if job.user and hasattr(job.user, "employerprofile") and job.user.employerprofile.profile_picture:
            profile_pic = job.user.employerprofile.profile_picture.url

        all_jobs.append({
            "id": job.id,
            "job_title": convert_to_string(getattr(job, "job_positions", "Job Title")),
            "establishment": convert_to_string(getattr(job, "company_name", "Private Employer")),
            "preferred_locations": convert_to_string(getattr(job, "state_of_residence", "Not specified")),
            "salary": convert_to_string(getattr(job, "salary_range", "Not specified")),
            "experience_years": convert_to_string(getattr(job, "years_experience", "Not specified")),
            "job_type": convert_to_string(getattr(job, "employment_type", "Full Time")),
            "expertise": convert_to_string(getattr(job, "skills_cuisine", "Not specified")),
            "apply_link": f"/apply/needchef/{job.id}/",
            "date": getattr(job, "submitted_at", now()),
            "is_candidate_job": False,
            "show_naira": False,  # No Naira for NeedChef jobs
            "profile_pic": profile_pic,
        })

    # Map JobVacancySubmission jobs
    for job in candidate_jobs:
        profile_pic = None
        if job.user and hasattr(job.user, "employerprofile") and job.user.employerprofile.profile_picture:
            profile_pic = job.user.employerprofile.profile_picture.url

        all_jobs.append({
            "id": job.id,
            "job_title": convert_to_string(getattr(job, "job_category", "Job Title")),
            "establishment": convert_to_string(getattr(job, "establishment", getattr(job, "employer_name", "Private Employer"))),
            "preferred_locations": convert_to_string(getattr(job, "job_locations", getattr(job, "preferred_location_other", "Nigeria"))),
            "salary": convert_to_string(getattr(job, "salary_range", getattr(job, "experience_years", "Not specified"))),
            "experience_years": convert_to_string(getattr(job, "experience_level", getattr(job, "years_experience", "Not specified"))),
            "job_type": convert_to_string(getattr(job, "get_preferred_job_types_display", lambda: "Full Time")()),
            "expertise": convert_to_string(getattr(job, "required_skills", getattr(job, "additional_skills", "Not specified"))),
            "apply_link": f"/apply/job/{job.id}/",
            "date": getattr(job, "date_submitted", now()),
            "is_candidate_job": True,
            "show_naira": True,  # Show Naira for JobVacancySubmission
            "profile_pic": profile_pic,
        })

    # Sort jobs by date (latest first)
    all_jobs.sort(key=lambda x: x["date"], reverse=True)

    context = {
        "total_companies": total_companies,
        "total_applications": total_applications,
        "total_jobs": total_jobs,
        "total_members": total_members,
        "testimonies": testimonies,
        "career_advices": career_advices,
        "jobs": all_jobs,
    }

    return render(request, "home.html", context)






# @login_required
# def complete_profile(request):
#     if request.method == "POST":
#         form = CompleteProfileForm(request.POST)
#         if form.is_valid():
#             user = request.user
#             data = form.cleaned_data
#             user.set_password(data["password1"])
#             user.save()

#             profile, created = ChefProfile.objects.get_or_create(user=user)
#             profile.phone = data["phone"]
#             profile.country = data["country"]
#             profile.save()

#             messages.success(request, "✅ Profile completed successfully! Please log in again.")
#             return redirect("login")
#     else:
#         form = CompleteProfileForm()

#     return render(request, "complete_profile.html", {"form": form})



@login_required
def redirect_after_login(request):
    redirect_url = request.session.pop('redirect_after_login', None)
    if redirect_url:
        return redirect(redirect_url)
    return redirect('chef_dashboard')



def candidate_register(request):
    if request.method == "POST":
        form = CandidateRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.user = request.user
            candidate.save()
            messages.success(request, "✅ Registration successful!")
            return redirect("login")
    else:
        form = CandidateRegistrationForm()
    return render(request, "candidate_register.html", {"form": form})



def job_vacancies(request):

    # -------------------------------
    # NEED A CHEF JOBS
    # -------------------------------
    need_chef_jobs = NeedChefSubmission.objects.filter(
        is_approved=True
    ).exclude(
        status__iexact="completed"
    )

    completed_needchef_from_applications = JobApplication.objects.filter(
        need_chef__isnull=False,
        status="Completed"
    ).values_list("need_chef_id", flat=True)

    need_chef_jobs = need_chef_jobs.exclude(id__in=completed_needchef_from_applications)



    # -------------------------------
    # JOB VACANCY SUBMISSION JOBS
    # -------------------------------
    submitted_jobs = JobVacancySubmission.objects.filter(
        is_approved=True
    )

    completed_vacancies = JobApplication.objects.filter(
        job_vacancy__isnull=False,
        status="Completed"
    ).values_list("job_vacancy_id", flat=True)

    submitted_jobs = submitted_jobs.exclude(id__in=completed_vacancies)



    context = {
        "need_chef_jobs": need_chef_jobs,
        "submitted_jobs": submitted_jobs,
    }

    return render(request, "job_vacancies.html", context)




    context = {
        "need_chef_jobs": need_chef_jobs,
        "submitted_jobs": submitted_jobs,
    }

    return render(request, "job_vacancies.html", context)








# ✅ Helper to fetch the correct application type
def get_application_for_user(app_id, user):
    try:
        return JobApplication.objects.get(
            id=app_id,
            # either this user posted a Job or a NeedChefSubmission
            # NOTE: Using OR logic properly to cover both sides
            # We'll use a Q() object for that
        )
    except JobApplication.DoesNotExist:
        return None




@login_required(login_url='login')
def accept_application(request, app_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    app = JobApplication.objects.filter(id=app_id).first()
    if not app:
        return JsonResponse({"success": False, "message": "Application not found."})

    # Ownership check
    if app.job and app.job.employer != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})
    if app.need_chef and app.need_chef.user != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})

    app.status = "Accepted"
    app.save()

    # If it's a NeedChef application, handle NeedStaffEngagement
    if app.need_chef:
        candidate_instance = getattr(app.chef, "chefprofile", None)
        if not candidate_instance:
            return JsonResponse({"success": False, "message": "Chef profile not found."})

        engagement, created = NeedStaffEngagement.objects.get_or_create(
            submission=app.need_chef,
            candidate=candidate_instance,
            defaults={"status": "accepted"}
        )
        if not created:
            engagement.status = "accepted"
            engagement.save()

        app.need_chef.status = "accepted"
        app.need_chef.save()

    # Send email notification
    if app.chef.email:
        job_title = app.job.title if app.job else (app.need_chef.job_positions or "Chef Request")
        send_mail(
            subject=f"Application Accepted: {job_title}",
            message=f"Congratulations! Your application for '{job_title}' has been accepted.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[app.chef.email],
            fail_silently=True,
        )

    return JsonResponse({"success": True, "message": "Application accepted successfully."})


@login_required(login_url='login')
def reject_application(request, app_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    app = JobApplication.objects.filter(id=app_id).first()
    if not app:
        return JsonResponse({"success": False, "message": "Application not found."})

    # Ownership check
    if app.job and app.job.employer != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})
    if app.need_chef and app.need_chef.user != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})

    app.status = "Rejected"
    app.save()

    if app.need_chef:
        candidate_instance = getattr(app.chef, "candidateprofile", None)
        if candidate_instance:
            NeedStaffEngagement.objects.filter(submission=app.need_chef, candidate=candidate_instance).update(status="rejected")

        app.need_chef.status = "rejected"
        app.need_chef.save()

    return JsonResponse({"success": True, "message": "Application rejected successfully."})


@login_required(login_url='login')
def hire_application(request, app_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    app = JobApplication.objects.filter(id=app_id).first()
    if not app:
        return JsonResponse({"success": False, "message": "Application not found."})

    # Ownership check
    if app.job and app.job.employer != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})
    if app.need_chef and app.need_chef.user != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})

    if app.status != "Accepted":
        return JsonResponse({"success": False, "message": "Only accepted applications can be hired."})

    app.status = "Hired"
    app.save()

    if app.need_chef:
        candidate_instance = getattr(app.chef, "candidateprofile", None)
        if candidate_instance:
            engagement = NeedStaffEngagement.objects.filter(submission=app.need_chef, candidate=candidate_instance).first()
            if engagement:
                engagement.status = "hired"
                engagement.save()

        app.need_chef.status = "engaged"
        app.need_chef.save()

    return JsonResponse({"success": True, "message": "🎉 Chef successfully hired!"})


@login_required(login_url='login')
def delete_application(request, app_id):
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    app = JobApplication.objects.filter(id=app_id).first()
    if not app:
        return JsonResponse({"success": False, "message": "Application not found."})

    # Ownership check
    if app.job and app.job.employer != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})
    if app.need_chef and app.need_chef.user != request.user:
        return JsonResponse({"success": False, "message": "Application not found."})

    app.delete()
    return JsonResponse({"success": True, "message": "Application deleted successfully."})





@login_required(login_url='login')
def apply_for_job(request, job_id=None, needchef_id=None, next_page=None):
    user = request.user
    redirect_url = reverse(next_page) if next_page else reverse("job_vacancies")

    # Ensure user is a Chef
    if not ChefProfile.objects.filter(user=user).exists():
        return HttpResponse(f"""
            <script>
                alert("Only chef accounts can apply for this job.");
                window.location.href = "{redirect_url}";
            </script>
        """)

    job = None
    need_chef = None
    employer = None
    employer_name = None
    job_title = None

    if job_id:
        job = JobVacancySubmission.objects.filter(id=job_id).first() or Job.objects.filter(id=job_id).first()
        if not job:
            return HttpResponse(f"""
                <script>
                    alert("No job matches the given query.");
                    window.location.href = "{redirect_url}";
                </script>
            """)
        employer = getattr(job, 'user', None) or getattr(job, 'employer', None)
        employer_name = getattr(job, 'user', None) and getattr(job.user, 'get_full_name', None) and job.user.get_full_name() or getattr(job, 'user', None) and job.user.username or "Unknown"
        job_title = getattr(job, 'title', None) or getattr(job, 'job_category', None) or "Not specified"

        if JobApplication.objects.filter(job_vacancy=job, chef=user).exists():
            return HttpResponse(f"""
                <script>
                    alert("You already applied for '{job_title}'.");
                    window.location.href = "{redirect_url}";
                </script>
            """)

    elif needchef_id:
        need_chef = get_object_or_404(NeedChefSubmission, id=needchef_id)
        employer = need_chef.user
        employer_name = need_chef.company_name or need_chef.user.get_full_name() or need_chef.user.username
        job_title = None
        if JobApplication.objects.filter(need_chef=need_chef, chef=user).exists():
            return HttpResponse(f"""
                <script>
                    alert("You have already applied for this Need a Chef request!");
                    window.location.href = "{redirect_url}";
                </script>
            """)
    else:
        return redirect(redirect_url)

    if request.method == "POST":
        message = request.POST.get("message", "I am interested in this position.")

        application = JobApplication.objects.create(
            job=job if isinstance(job, Job) else None,
            job_vacancy=job if isinstance(job, JobVacancySubmission) else None,
            need_chef=need_chef,
            chef=user,
            employer=employer,
            
            message=message,
            email=user.email,
            status="Pending",
        )

        # Admin emails
        admin_emails = [email for name, email in getattr(settings, 'ADMINS', [])]

        # Send emails to employer + admins
        recipient_list = []
        if employer and hasattr(employer, 'email'):
            recipient_list.append(employer.email)
        recipient_list.extend(admin_emails)

        send_async_email(
            send_mail,
            subject="New Application Received",
            message=f"A chef ({user.get_full_name() or user.username}) has applied for '{job_title or 'a Need a Chef request'}'.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=recipient_list,
            fail_silently=True,
        )

        # Send confirmation email to chef
        send_async_email(
            send_mail,
            subject="Application Submitted Successfully",
            message="Your application has been submitted successfully.",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )

        return HttpResponse(f"""
            <script>
                alert("Application submitted successfully!");
                window.location.href = "{redirect_url}";
            </script>
        """)

    return redirect(redirect_url)



@login_required
def applied(request):
    user = request.user

    # Fetch applications where user is the employer
    job_apps = JobApplication.objects.filter(
        Q(job__employer=user) | 
        Q(job_vacancy__user=user) | 
        Q(need_chef__user=user)
    ).select_related(
        'chef', 'chef__chefprofile', 'job', 'job_vacancy', 'need_chef'
    )

    applications = []
    for app in job_apps:
        # Get chef full name if profile exists, else username
        chef_full_name = getattr(app.chef.chefprofile, 'full_name', None)
        if not chef_full_name:
            chef_full_name = f"{app.chef.first_name} {app.chef.last_name}".strip()
            if not chef_full_name.strip():
                chef_full_name = app.chef.username

        # Employer / company name
        employer_name = "Unknown"
        if app.job and getattr(app.job, 'employer', None):
            employer_name = app.job.employer.get_full_name() or app.job.employer.username
        elif app.job_vacancy and getattr(app.job_vacancy, 'user', None):
            employer_name = app.job_vacancy.user.get_full_name() or app.job_vacancy.user.username
        elif app.need_chef and getattr(app.need_chef, 'user', None):
            employer_name = app.need_chef.user.get_full_name() or app.need_chef.user.username

        # Handle job_positions for need-a-chef
        request_type = []
        if app.need_chef and app.need_chef.job_positions:
            try:
                request_type = ast.literal_eval(app.need_chef.job_positions)
            except Exception:
                request_type = [app.need_chef.job_positions]

        # Determine job title and position
        job_title = None
        job_position = None

        if app.job:
            job_title = getattr(app.job, "title", None)
            job_position = getattr(app.job, "job_position", None)

        elif app.job_vacancy:
            job_title = getattr(app.job_vacancy, "title", None)
            job_position = getattr(app.job_vacancy, "job_category", None)

        # Determine type
        app_type = (
            "job" if app.job else
            "job_vacancy" if app.job_vacancy else 
            "need_chef"
        )

        applications.append({
            "id": app.id,
            "chef_username": app.chef.username,
            "chef_full_name": chef_full_name,
            "chef_phone": getattr(app.chef.chefprofile, 'phone_number', 'Not provided'),
            "chef_email": getattr(app.chef.chefprofile, 'email', app.chef.email),
            "employer_name": employer_name,

            "job_title": job_title,
            "job_position": job_position,   # ✅ FIXED — NOW INCLUDED

            "request_type": request_type,
            "type": app_type,
            "applied_date": app.date_applied,
            "status": app.status,
            "message": app.message,
            "employer_testimony": getattr(app, 'employer_testimony', None),
        })

    return render(request, 'dashboard/applied.html', {"applications": applications})







@login_required(login_url='login')
def manage_applications(request):
    """Employer sees all applications for their jobs"""
    
    # Applications linked to Job objects owned by employer
    job_apps = JobApplication.objects.filter(job__employer=request.user).select_related('chef__user')
    
    # Applications linked to NeedChef objects owned by employer
    needchef_apps = JobApplication.objects.filter(need_chef__user=request.user).select_related('need_chef__user')
    
    # Combine in Python
    applications = list(job_apps) + list(needchef_apps)
    
    return render(request, "dashboard/applied.html", {"applications": applications})




@login_required(login_url='login')
def update_application_status(request, application_id, action):
    """Employer accepts, rejects, hires, or deletes an application (AJAX-compatible)"""
    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    try:
        application = get_object_or_404(JobApplication, id=application_id, job__employer=request.user)
    except:
        return JsonResponse({"success": False, "message": "Application not found."})

    chef_user = application.chef

    if action == "accept":
        application.status = "Accepted"
        msg = f"✅ You accepted {chef_user.username}'s application."
        email_subject = "Job Application Accepted"
        email_body = f"Congratulations {chef_user.get_full_name() or chef_user.username}!\n\nYour application for '{application.job.title}' has been accepted by the employer."

    elif action == "reject":
        application.status = "Rejected"
        msg = f"❌ You rejected {chef_user.username}'s application."
        email_subject = "Job Application Rejected"
        email_body = f"Dear {chef_user.get_full_name() or chef_user.username},\n\nYour application for '{application.job.title}' was not accepted. We wish you better luck next time."

    elif action == "hire":
        application.status = "Hired"
        msg = f"🤝 You hired {chef_user.username}."
        email_subject = "Congratulations — You’ve Been Hired!"
        email_body = f"Dear {chef_user.get_full_name() or chef_user.username},\n\nThe employer has officially hired you for '{application.job.title}'."

    elif action == "delete":
        application.delete()
        return JsonResponse({"success": True, "message": "Application deleted successfully."})

    else:
        return JsonResponse({"success": False, "message": "Invalid action."})

    application.save()

    # send email
    send_mail(
        subject=email_subject,
        message=email_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[chef_user.email],
        fail_silently=True,
    )

    return JsonResponse({"success": True, "message": msg})




@login_required(login_url='login')
@csrf_exempt
def submit_testimonyy(request, application_id):
    """
    Handles submission of chef or employer testimony.
    Marks JobApplication and NeedChefSubmission as 'Completed' if both testimonies exist.
    Saves a copy in Testimony model.
    Deactivates related jobs from listings.
    """
    

    try:
        application = JobApplication.objects.get(id=application_id)
    except JobApplication.DoesNotExist:
        return JsonResponse({"success": False, "message": "Application not found."})

    if request.method != "POST":
        return JsonResponse({"success": False, "message": "Invalid request method."})

    # Get testimony from form or JSON
    testimony = request.POST.get("testimony")
    if not testimony:
        try:
            data = json.loads(request.body)
            testimony = data.get("testimony")
        except Exception:
            testimony = None

    if not testimony:
        return JsonResponse({"success": False, "message": "Please write a testimony."})

    # Identify user role
    if request.user == application.employer:
        application.employer_testimony = testimony
        role = "Employer"
    elif request.user == application.chef:
        application.chef_testimony = testimony
        role = "Chef"
    else:
        return JsonResponse({"success": False, "message": "You are not authorized for this action."})

    # Save testimony in the JobApplication
    application.save()

    # Save a copy in Testimony model
    TestimonyLog.objects.create(
        user=request.user,
        application=application,
        role=role,
        testimony=testimony
    )

    # Check if both testimonies exist
    if application.employer_testimony and application.chef_testimony:
        application.status = "Completed"
        application.save()

        if application.need_chef:
            application.need_chef.status = "completed"
            application.need_chef.is_approved = False
            application.need_chef.save()

        if application.job_vacancy:
            application.job_vacancy.is_approved = False
            application.job_vacancy.save()

        return JsonResponse({
            "success": True,
            "message": f"{role} testimony submitted."
        })

    # Only one testimony submitted so far
    return JsonResponse({
        "success": True,
        "message": f"{role} testimony submitted successfully!"
    })





def disable_users_without_testimony():
    overdue = JobApplication.objects.filter(
        status="Hired",
        deadline__lt=timezone.now()
    ).filter(
        chef_testimony__isnull=True
    ) | JobApplication.objects.filter(
        status="Hired",
        deadline__lt=timezone.now()
    ).filter(
        employer_testimony__isnull=True
    )

    for app in overdue:
        app.chef.is_active = False
        app.job.employer.is_active = False
        app.chef.save()
        app.job.employer.save()



@login_required(login_url='login')
def view_applications(request):
    user = request.user  # logged-in employer

    # Applications for standard job vacancies
    job_apps = JobVacancySubmission.objects.filter(job__user=user).select_related('chef', 'job')

    # Applications for Need a Chef submissions
    need_chef_apps = JobApplication.objects.filter(need_chef__user=user).select_related('chef', 'need_chef')

    # Combine both into a unified list for template
    applications = []

    for app in job_apps:
        applications.append({
            "id": app.id,
            "chef_full_name": app.chef.get_full_name() or app.chef.username,
            "chef_username": app.chef.email,
            "chef_phone": getattr(app.chef.chefprofile, 'phone', ''),
            "job_title": getattr(app.job, 'job_category', '—'),
            "message": app.message,
            "status": app.status,
            "applied_date": app.created_at if hasattr(app, 'created_at') else app.id,
            "type": "job vacancy",
            "request_type": None,
            "employer_testimony": getattr(app, 'employer_testimony', None),
        })

    for app in need_chef_apps:
        positions = getattr(app.need_chef, 'job_positions', [])
        formatted_positions = [pos.replace("_", " ").title() for pos in positions]

        applications.append({
            "id": app.id,
            "chef_full_name": app.chef.get_full_name() or app.chef.username,
            "chef_username": app.chef.email,
            "chef_phone": getattr(app.chef.chefprofile, 'phone', ''),
            "job_title": None,
            "message": app.message,
            "status": app.status,
            "applied_date": app.created_at if hasattr(app, 'created_at') else app.id,
            "type": "needchef",
            "request_type": formatted_positions,  # send formatted string list
            "employer_testimony": getattr(app, 'employer_testimony', None),
        })

    # Sort by applied date descending (most recent first)
    applications = sorted(applications, key=lambda x: x['applied_date'], reverse=True)

    context = {
        "applications": applications
    }
    return render(request, "employer_applications.html", context)





def send_async_email(func, *args, **kwargs):
    """Run send_mail in a background thread."""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs)
    thread.start()


def send_notification(subject, message, recipients):
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )



@login_required(login_url='login')
def need_job(request):
    user = request.user
    # Fetch candidate for this user, if exists
    candidate = Candidate.objects.filter(user=user).first()

    # Check if they already submitted the form (key field is filled)
    already_submitted = candidate and candidate.preferred_job_types

    if request.method == 'POST':
        if already_submitted:
            messages.warning(request, "⚠️ You have already used the Submit CV feature.")
            return redirect('need_job')

        form = CandidateRegistrationForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            candidate = form.save(commit=False)
            candidate.user = user

            # Combine selected job types into CSV string
            job_types = form.cleaned_data.get("preferred_job_types")
            if job_types:
                candidate.preferred_job_types = ", ".join(job_types)

            candidate.save()

            # === ADMIN LOG ENTRY ===
            LogEntry.objects.log_action(
                user_id=user.id,
                content_type_id=ContentType.objects.get_for_model(candidate).pk,
                object_id=candidate.id,
                object_repr=f"{candidate.full_name} (pending approval)",
                action_flag=ADDITION,
                change_message="New candidate registration pending approval."
            )

            # === EMAIL ADMIN ===
            send_async_email(
                mail_admins,
                subject="🆕 New Candidate Registration Pending Approval",
                message=(f"A new candidate has registered and is awaiting approval:\n\n"
                         f"Full Name: {candidate.full_name}\n"
                         f"Gender: {candidate.gender}\n"
                         f"Years of Experience: {candidate.years_experience}\n"
                         f"Specialty: {candidate.specialty}\n"
                         f"Preferred Establishment: {candidate.establishment_preference}\n\n"
                         f"Please log in to the admin panel to review and approve.")
            )

            # === EMAIL USER ===
            send_async_email(
                send_mail,
                subject="🎉 Your Chef.com I Need A Job Registration Was Successful",
                message=(f"Hello {candidate.full_name},\n\n"
                         "Thank you for registering with Chef.com!\n"
                         "Your profile has been submitted and is pending admin approval.\n\n"
                         "Once approved, you'll start receiving job opportunities matching your profile.\n\n"
                         "Best regards,\nThe Chef.com Team"),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[candidate.email]
            )

            messages.success(request, "✅ Registration successful! You will receive job notifications soon.")
            return redirect('candidate_register_success')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = CandidateRegistrationForm(instance=candidate)

    context = {
        'form': form,
    }

    return render(request, 'need_job.html', context)




def candidate_register_success(request):
    return render(request, "candidate_register_success.html")


@login_required(login_url='login')
def my_jobs(request):
    chef = get_object_or_404(ChefProfile, user=request.user)

    job_applications_qs = JobApplication.objects.filter(
        chef=request.user
    ).select_related('job', 'need_chef', 'job_vacancy', 'chef', 'chef__chefprofile')

    job_applications = []
    for app in job_applications_qs:
        # Chef full name
        chef_full_name = getattr(app.chef.chefprofile, 'full_name', None)
        if not chef_full_name:
            chef_full_name = f"{app.chef.first_name} {app.chef.last_name}".strip()
            if not chef_full_name:
                chef_full_name = app.chef.username

        # Employer name
        employer_name = "Unknown"
        if app.job and getattr(app.job, 'employer_name', None):
            employer_name = app.job.employer_name
        elif app.job_vacancy and getattr(app.job_vacancy, 'employer_name', None):
            employer_name = app.job_vacancy.employer_name
        elif app.need_chef and getattr(app.need_chef, 'company_name', None):
            employer_name = app.need_chef.company_name

        # Job title or request type
        job_title = None
        request_type = []
        if app.job:
            job_title = getattr(app.job, 'title', None)
        elif app.job_vacancy:
            job_title = getattr(app.job_vacancy, 'job_category', 'N/A')
        elif app.need_chef:
            try:
                request_type = ast.literal_eval(app.need_chef.job_positions)
            except Exception:
                request_type = [app.need_chef.job_positions]

        job_applications.append({
            "id": app.id,
            "chef_username": app.chef.username,
            "chef_full_name": chef_full_name,
            "chef_phone": getattr(app.chef.chefprofile, 'phone_number', 'Not provided'),
            "chef_email": getattr(app.chef.chefprofile, 'email', app.chef.email),

            "employer_name": employer_name,
            "request_type": request_type,
            "job_title": job_title,
            "type": "job" if app.job else "need_chef" if app.need_chef else "job_vacancy",
            "applied_date": app.date_applied,
            "status": app.status,
            "message": app.message,

            # 🔥 ADD THESE TWO LINES
            "chef_testimony": app.chef_testimony,
            "employer_testimony": app.employer_testimony,
        })

    job_vacancys = JobVacancySubmission.objects.filter(user=request.user).select_related('job_vacancy')

    return render(request, "chef_my_jobs.html", {
        'chef': chef,
        'job_applications': job_applications,
        'job_vacancys': job_vacancys,
    })




def load_states(request):
    country_id = request.GET.get("country_id")
    if not country_id:
        return JsonResponse([], safe=False)

    try:
        country_id = int(country_id)
    except ValueError:
        return JsonResponse([], safe=False)

    states = Region.objects.filter(country_id=country_id).order_by("name")
    data = list(states.values("id", "name"))
    return JsonResponse(data, safe=False)



def get_country_code(request):
    country_id = request.GET.get("country_id")
    if country_id:
        try:
            country = Country.objects.get(id=country_id)
            return JsonResponse({"iso_code": country.code2.lower()})
        except Country.DoesNotExist:
            pass
    return JsonResponse({"iso_code": None})



class Command(BaseCommand):
    help = "Disable chefs who did not submit testimony within 7 days of being hired."

    def handle(self, *args, **kwargs):
        engagements = JobEngagement.objects.filter(status="engaged", hired_at__isnull=False, chef_testimony__isnull=True)
        count = 0

        for engagement in engagements:
            if engagement.chef_testimony_due():
                chef_profile = ChefProfile.objects.filter(user=engagement.candidate.user).first()
                if chef_profile and chef_profile.user.is_active:
                    chef_profile.user.is_active = False
                    chef_profile.user.save()
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Disabled {count} chef account(s) without testimony."))



@require_POST
@login_required
def submit_testimony(request, engagement_id):
    import traceback
    try:
        # Parse JSON request body
        data = json.loads(request.body)
        testimony_text = data.get("testimony", "").strip()

        if not testimony_text:
            return JsonResponse({"success": False, "message": "Testimony cannot be empty."}, status=400)

        # Identify user type and get engagement
        if hasattr(request.user, "employerprofile"):
            try:
                engagement = JobEngagement.objects.get(id=engagement_id, employer=request.user)
                engagement.employer_testimony = testimony_text
                testimony_by = "Employer"
            except JobEngagement.DoesNotExist:
                return JsonResponse({"success": False, "message": "Engagement not found."}, status=404)

        elif hasattr(request.user, "chefprofile"):
            try:
                engagement = JobEngagement.objects.get(id=engagement_id, candidate=request.user)
                engagement.chef_testimony = testimony_text
                testimony_by = "Chef"
            except JobEngagement.DoesNotExist:
                return JsonResponse({"success": False, "message": "Engagement not found."}, status=404)

        else:
            return JsonResponse({"success": False, "message": "User type not recognized."}, status=403)

        # Save testimony in JobEngagement
        engagement.save()

        # Log testimony for admin panel
        try:
            TestimonyLog.objects.create(
                user=request.user,
                application=engagement.application,  # Ensure this is a JobApplication instance
                testimony=testimony_text
            )
        except Exception as e:
            print("❌ Failed to log testimony:", e)
            traceback.print_exc()
            return JsonResponse({"success": False, "message": f"Failed to log testimony: {str(e)}"})

        # Notify admin by email
        try:
            subject = f"📝 Testimony Submitted by {testimony_by} {request.user.get_full_name()}"
            message = (
                f"{testimony_by} {request.user.get_full_name()} submitted a testimony "
                f"for candidate {engagement.candidate.get_full_name()}:\n\n{testimony_text}"
            )
            mail_admins(subject, message)
        except (BadHeaderError, SMTPException, Exception) as e:
            print("⚠️ Failed to send admin email:", e)
            traceback.print_exc()

        return JsonResponse({"success": True, "message": "✅ Testimony submitted successfully."})

    except json.JSONDecodeError:
        return JsonResponse({"success": False, "message": "Invalid JSON."}, status=400)

    except Exception as e:
        print("❌ Error in submit_testimony:", e)
        traceback.print_exc()
        return JsonResponse({"success": False, "message": "Something went wrong."}, status=500)




# ===== EMPLOYER ENGAGES CANDIDATE =====
@require_POST
@login_required(login_url='login')
def engage_candidate(request):
    """
    Allows an employer to engage a candidate or CV submission.
    Stores candidate phone and country at the time of engagement.
    """
    # Only employers can engage
    if not hasattr(request.user, "employerprofile"):
        return JsonResponse({"success": False, "message": "Unauthorized: Only employers can engage."}, status=403)

    try:
        data = json.loads(request.body)
        candidate_id = data.get("candidate_id")
        cv_id = data.get("cv_id")
        message = data.get("message", "")

        if not candidate_id and not cv_id:
            return JsonResponse({"success": False, "message": "Missing candidate or CV ID."}, status=400)

        # --- CASE 1: Candidate engagement ---
        if candidate_id:
            candidate = Candidate.objects.get(id=candidate_id)
            candidate_user = candidate.user  # must be a User instance

            # Prevent duplicate engagements
            if JobEngagement.objects.filter(candidate=candidate_user, employer=request.user).exists():
                return JsonResponse({"success": False, "message": "You’ve already engaged this candidate."}, status=400)

            # Get phone and country from Candidate profile
            candidate_phone = getattr(candidate, 'phone', 'Not provided')
            candidate_country = getattr(candidate.nationality, 'name', 'Not provided')

            engagement = JobEngagement.objects.create(
                employer=request.user,
                candidate=candidate_user,
                message=message or f"{request.user.get_full_name()} engaged you for a job.",
                candidate_phone=candidate_phone,
                candidate_country=candidate_country
            )

            target_user = candidate_user
            target_name = candidate.full_name or candidate_user.get_full_name() or candidate_user.username

        # --- CASE 2: CV engagement ---
        elif cv_id:
            cv = CVSubmission.objects.get(id=cv_id)
            if not cv.user:
                return JsonResponse({"success": False, "message": "CV submission has no associated user."}, status=400)

            candidate_user = cv.user

            # Prevent duplicate engagements
            if JobEngagement.objects.filter(candidate=candidate_user, employer=request.user).exists():
                return JsonResponse({"success": False, "message": "You’ve already engaged this CV submission."}, status=400)

            # Optional: create Candidate record if missing
            candidate, _ = Candidate.objects.get_or_create(
                user=candidate_user,
                defaults={
                    "full_name": cv.full_name,
                    "gender": cv.gender or "Prefer not to say"
                }
            )

            candidate_phone = cv.phone or 'Not provided'
            candidate_country = cv.nationality.name if cv.nationality else 'Not provided'

            engagement = JobEngagement.objects.create(
                employer=request.user,
                candidate=candidate_user,
                message=message or f"{request.user.get_full_name()} engaged you via your CV submission.",
                candidate_phone=candidate_phone,
                candidate_country=candidate_country
            )

            target_user = candidate_user
            target_name = cv.full_name or candidate_user.get_full_name() or candidate_user.username

        # --- Send notification email asynchronously ---
        email_subject = "📢 New Job Engagement"
        email_msg = (
            f"Hello {target_name},\n\n"
            f"You have been engaged for a job by {request.user.get_full_name()}.\n\n"
            f"Message: {engagement.message}\n\n"
            "Please check your account for more details.\n\n— Chef.Com"
        )

        try:
            if target_user.email:
                send_async_email(email_subject, email_msg, [target_user.email])
            # Optionally notify admins asynchronously
            send_async_email(
                "New Job Engagement",
                f"Employer {request.user.email} engaged {target_name}.",
                [admin[1] for admin in settings.ADMINS]
            )
        except Exception as mail_error:
            print(f"⚠️ Async mail failed: {mail_error}")
            traceback.print_exc()

        return JsonResponse({"success": True, "message": "Engagement processed successfully."})

    except Candidate.DoesNotExist:
        return JsonResponse({"success": False, "message": "Candidate not found."}, status=404)
    except CVSubmission.DoesNotExist:
        return JsonResponse({"success": False, "message": "CV submission not found."}, status=404)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        traceback.print_exc()
        return JsonResponse({"success": False, "message": f"Something went wrong: {e}"}, status=500)





@login_required(login_url='login')
def manage_chef(request):
    """
    Employer dashboard: list all engaged chefs with contact details.
    Uses phone & country stored directly in JobEngagement.
    Prepopulates employer organization name.
    """
    engagements_qs = JobEngagement.objects.filter(employer=request.user).select_related('candidate')

    # Get organization name from employer profile
    try:
        employer_organization = request.user.employerprofile.organization
    except EmployerProfile.DoesNotExist:
        employer_organization = request.user.get_full_name()  # fallback

    engagements = []

    for e in engagements_qs:
        engagements.append({
            "id": e.id,
            "candidate_full_name": e.candidate.get_full_name() or e.candidate.username,
            "candidate_email": e.candidate.email,
            "candidate_phone": getattr(e, "candidate_phone", "Not provided"),
            "candidate_country": getattr(e, "candidate_country", "Not provided"),
            "message": e.message,
            "status": e.status,
            "employer_testimony": e.employer_testimony,
            "employer_organization": employer_organization,  # <-- added
        })

    return render(request, "dashboard/manage_chef.html", {"engagements": engagements})






@login_required(login_url='login')
def job_alerts(request):
    user = request.user  # Chef user

    # Prefetch employer profile to get company_name efficiently
    employer_profiles = EmployerProfile.objects.all()
    job_engagements = JobEngagement.objects.filter(
        candidate=user
    ).select_related('employer').prefetch_related(
        Prefetch('employer__employerprofile', queryset=employer_profiles, to_attr='profile')
    ).order_by('-created_at')

    # Mark new alerts as viewed
    JobEngagement.objects.filter(candidate=user, is_viewed=False).update(is_viewed=True)

    # Pass job engagements to template
    return render(request, "dashboard/job_alerts.html", {
        "job_engagements": job_engagements
    })








# ===== CANDIDATE ACCEPTS =====
# ===== CANDIDATE ACCEPT =====
@require_POST
@login_required
def accept_engagement(request, engagement_id):
    try:
        engagement = JobEngagement.objects.get(id=engagement_id, candidate=request.user)
        engagement.status = "accepted"
        engagement.is_viewed = True
        engagement.save()

        return JsonResponse({
            "success": True,
            "message": "Engagement accepted successfully."
        })

    except JobEngagement.DoesNotExist:
        return JsonResponse({"success": False, "message": "Engagement not found."}, status=404)
    except Exception:
        return JsonResponse({"success": False, "message": "Something went wrong."}, status=500)


# ===== CANDIDATE REJECT =====
@require_POST
@login_required
def reject_engagement(request, engagement_id):
    try:
        engagement = JobEngagement.objects.get(id=engagement_id, candidate=request.user)
        engagement.status = "rejected"
        engagement.is_viewed = True
        engagement.save()

        return JsonResponse({
            "success": True,
            "message": "Engagement rejected successfully."
        })

    except JobEngagement.DoesNotExist:
        return JsonResponse({"success": False, "message": "Engagement not found."}, status=404)
    except Exception:
        return JsonResponse({"success": False, "message": "Something went wrong."}, status=500)


# ===== EMPLOYER MARKS ENGAGED =====
@require_POST
@login_required
def mark_engaged(request, engagement_id):
    try:
        engagement = JobEngagement.objects.get(id=engagement_id, employer=request.user)
        engagement.status = "engaged"
        engagement.save()

        subj = "🎉 Engagement Confirmed"
        msg = f"You have been officially hired by {engagement.employer.get_full_name()}."

        # Send candidate email asynchronously
        send_async_email(subj, msg, settings.DEFAULT_FROM_EMAIL, [engagement.candidate.email])

        # Notify admins asynchronously
        admin_msg = f"{engagement.employer.email} hired {engagement.candidate.email}"
        send_async_email(f"Admin Notification: {subj}", admin_msg, settings.DEFAULT_FROM_EMAIL, [admin[1] for admin in settings.ADMINS])

        return JsonResponse({"success": True, "message": "Engagement marked as engaged."})

    except JobEngagement.DoesNotExist:
        return JsonResponse({"success": False, "message": "Engagement not found."}, status=404)
    except Exception as e:
        import traceback
        print("❌ Error in mark_engaged:", e)
        traceback.print_exc()
        return JsonResponse({"success": False, "message": "Something went wrong."}, status=500)


# ===== DELETE ENGAGEMENT =====
@login_required
def delete_engagement(request, engagement_id):
    engagement = get_object_or_404(JobEngagement, id=engagement_id, employer=request.user)

    if request.method == "POST":
        engagement.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"success": False}, status=400)



def subscribe_newsletter(request):
    if request.method == 'POST':
        email = request.POST.get('email')

        if email:
            # Check if already subscribed
            if NewsletterSubscriber.objects.filter(email=email).exists():
                messages.info(request, "⚠️ You're already subscribed to our newsletter.")
            else:
                # Save subscriber
                NewsletterSubscriber.objects.create(email=email)

                # Send welcome email
                subject = "Welcome to Chefs.com Newsletter 🍽️"
                message = (
                    "Hello Food Lover!\n\n"
                    "Thank you for subscribing to the Chefs.com newsletter.\n"
                    "You'll now receive updates about our top chefs, latest food events, and culinary tips straight to your inbox!\n\n"
                    "Bon Appétit!\n"
                    "— The Chefs.com Team"
                )
                from_email = settings.DEFAULT_FROM_EMAIL
                recipient_list = [email]

                try:
                    send_mail(subject, message, from_email, recipient_list)
                    messages.success(request, "🎉 You’ve successfully subscribed! Check your email for confirmation.")
                except Exception as e:
                    messages.warning(request, "✅ Subscription saved, but we couldn’t send the welcome email.")
                    print(f"Email sending failed: {e}")
        else:
            messages.error(request, "⚠️ Please enter a valid email address.")
        
        return redirect(request.META.get('HTTP_REFERER', '/'))

    return redirect('/')



# def subscription_page(request):
#     candidate_plans = Subscription.objects.filter(category='candidate')
#     employer_plans = Subscription.objects.filter(category='employer')
#     return render(request, 'subscription.html', {
#         'candidate_plans': candidate_plans,
#         'employer_plans': employer_plans,
#         'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
#         'flutterwave_public_key': settings.FLUTTERWAVE_PUBLIC_KEY,
#     })


@login_required
def verify_payment(request):
    user = request.user

    # get the email of the user for Paystack/Flutterwave
    email = user.email

    # AMOUNT (₦10,000 example)
    amount = 10000 * 100  # Paystack uses kobo

    context = {
        "email": email,
        "amount": amount,
        "public_key_paystack": "PAYSTACK_PUBLIC_KEY",
        "public_key_flutterwave": "FLUTTERWAVE_PUBLIC_KEY",
    }

    return render(request, "upgrade_verified.html", context)



@login_required
def subscription_page(request):
    candidate_plans = [
        {"title": "Monthly Plan", "price": "₦2,000", "duration": "1 Month", "amount": 2000, "plan_name": "Candidate Monthly"},
        {"title": "3-Month Plan", "price": "₦5,000", "duration": "3 Months", "amount": 5000, "plan_name": "Candidate 3-Month"},
        {"title": "6-Month Plan", "price": "₦10,000", "duration": "6 Months", "amount": 10000, "plan_name": "Candidate 6-Month"},
        {"title": "12-Month Plan", "price": "₦19,500", "duration": "12 Months", "amount": 19500, "plan_name": "Candidate 12-Month"},
    ]

    employer_plans = [
        {"title": "Monthly Plan", "price": "₦10,000", "duration": "1 Month", "amount": 10000, "plan_name": "Employer Monthly"},
        {"title": "3-Month Plan", "price": "₦25,000", "duration": "3 Months", "amount": 25000, "plan_name": "Employer 3-Month"},
        {"title": "6-Month Plan", "price": "₦50,000", "duration": "6 Months", "amount": 50000, "plan_name": "Employer 6-Month"},
        {"title": "12-Month Plan", "price": "₦90,000", "duration": "12 Months", "amount": 90000, "plan_name": "Employer 12-Month"},
    ]

    user = request.user
    context = {}

    # ✅ Detect user type and show only the correct plans
    if hasattr(user, "chefprofile"):
        context["candidate_plans"] = candidate_plans
        context["user_type"] = "chef"
    elif hasattr(user, "employerprofile"):
        context["employer_plans"] = employer_plans
        context["user_type"] = "employer"
    else:
        messages.error(request, "Your account type could not be determined.")
        return redirect("chefs_hub")

    return render(request, "subscription_page.html", context)




@login_required
def start_subscription(request):
    if request.method != "POST":
        return redirect("subscription_page")

    user = request.user
    email = user.email
    amount = int(request.POST.get("amount", 0)) * 100  # convert to kobo
    gateway = request.POST.get("gateway")
    plan_name = request.POST.get("plan_name", "Basic")

    callback_url = request.build_absolute_uri("/subscription/verify/")

    if gateway == "paystack":
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        data = {"email": email, "amount": amount, "callback_url": callback_url}
        r = requests.post("https://api.paystack.co/transaction/initialize", json=data, headers=headers)
        res = r.json()
        print("Paystack response:", res)
        if res.get("status"):
            return redirect(res["data"]["authorization_url"])
        messages.error(request, "Paystack payment initialization failed.")
        return redirect("subscription_page")

    elif gateway == "flutterwave":
        headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
        data = {
            "tx_ref": f"FLW-{user.id}-{timezone.now().timestamp()}",
            "amount": str(amount / 100),
            "currency": "NGN",
            "redirect_url": callback_url,
            "customer": {"email": email, "name": user.get_full_name()},
            "customizations": {"title": plan_name, "description": "ChefsCom Subscription"},
        }
        r = requests.post("https://api.flutterwave.com/v3/payments", json=data, headers=headers)
        res = r.json()
        print("Flutterwave response:", res)
        if res.get("status") == "success":
            return redirect(res["data"]["link"])
        messages.error(request, "Flutterwave payment initialization failed.")
        return redirect("subscription_page")

    messages.error(request, "Invalid payment gateway selected.")
    return redirect("subscription_page")


@login_required
def verify_subscription(request):
    reference = request.GET.get("reference")
    tx_ref = request.GET.get("tx_ref")
    user = request.user

    # ✅ Paystack Verification
    if reference:
        headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}
        url = f"https://api.paystack.co/transaction/verify/{reference}"
        r = requests.get(url, headers=headers)
        res = r.json()

        if res.get("status") and res["data"]["status"] == "success":
            amount = res["data"]["amount"] / 100
            plan_name = "employer_monthly"  # or map dynamically
            sub = Subscription.objects.filter(user=user).order_by('-created_at').first()

            if not sub:
                sub = Subscription(user=user)

            sub.plan_name = plan_name
            sub.amount = amount
            sub.paystack_reference = reference
            sub.payment_gateway = "paystack"
            sub.save()
            sub.activate(duration_days=30)

            # Mark employer subscribed
            if hasattr(user, "employerprofile"):
                employer = user.employerprofile
                employer.is_subscribed = True
                employer.save()

            messages.success(request, "✅ Paystack subscription activated successfully!")
            return redirect("chefs_hub")

        messages.error(request, "❌ Paystack verification failed.")
        return redirect("subscription_page")

    # ✅ Flutterwave Verification
    elif tx_ref:
        headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
        url = f"https://api.flutterwave.com/v3/transactions/verify_by_reference?tx_ref={tx_ref}"
        r = requests.get(url, headers=headers)
        res = r.json()

        if res.get("status") == "success":
            amount = res["data"]["amount"]
            plan_name = "employer_monthly"
            sub = Subscription.objects.filter(user=user).order_by('-created_at').first()

            if not sub:
                sub = Subscription(user=user)

            sub.plan_name = plan_name
            sub.amount = amount
            sub.flutterwave_reference = tx_ref
            sub.payment_gateway = "flutterwave"
            sub.save()
            sub.activate(duration_days=30)

            if hasattr(user, "employerprofile"):
                employer = user.employerprofile
                employer.is_subscribed = True
                employer.save()

            messages.success(request, "✅ Flutterwave subscription activated successfully!")
            return redirect("chefs_hub")

        messages.error(request, "❌ Flutterwave verification failed.")
        return redirect("subscription_page")

    messages.error(request, "Invalid verification request.")
    return redirect("subscription_page")




@login_required(login_url='login')
def need_staff(request):
    if request.method == "POST":
        form = NeedStaffForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            if request.user.is_authenticated:
                submission.user = request.user
            submission.save()

            # === Create a Job entry from this submission ===
            Job.objects.create(
                employer=submission.user if submission.user else None,
                title=submission.job_positions or "Chef Needed",
                description=submission.message or "No description provided",
                company_name=submission.company_name if submission.user else "Unknown Company",
                establishment_type=submission.establishment_type,
                job_positions=submission.job_positions,
                employment_type=submission.employment_type,
                work_location=submission.work_location,
                state_of_residence=getattr(submission.state_of_residence, 'name', submission.state_of_residence),
                salary_range=submission.salary_range,
                skills_cuisine=submission.skills_cuisine,
                preferred_qualification=submission.preferred_qualification,
                language_preference=submission.language_preference,
                start_date=submission.start_date,
                working_hours=submission.working_hours,
                meals_accommodation=submission.meals_accommodation,
                message=submission.message,
            )

            # === Send email to employer in background ===
            if submission.user and submission.user.email:
                subject = "Need Staff Submission Successful"
                message = (
                    f"Dear {submission.user.get_full_name() or submission.user.username},\n\n"
                    "Your staff request has been submitted successfully and saved as a job listing.\n"
                    "You can view and manage it from your dashboard."
                )
                # Assuming your send_mail function can handle async/background sending
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [submission.user.email])

            messages.success(request, "Your request has been submitted successfully!")
            return redirect('thank_you')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = NeedStaffForm()

    return render(request, 'need_staff.html', {'form': form})




# New view for the thank-you page
def thank_you(request):
    return render(request, 'thank_you.html')



@login_required(login_url='login')
def submit_cv(request):
    specialties = [
        "Continental Cuisine",
        "African Cuisine",
        "Pastry/Bakery",
        "Catering/Event Service",
        "Grill/Barbecue",
    ]
    locations = ["Kano", "Abuja", "Lagos", "Port Harcourt", "Kaduna", "Makurdi"]

    user = request.user

    # 🔒 Prevent duplicate submissions
    if CVSubmission.objects.filter(user=user).exists():
        messages.warning(request, "⚠️ You have already used the Submit CV feature.")
        return redirect("home")   # ✔️ Redirect to home

    if request.method == "POST":
        form = CVSubmissionForm(request.POST, request.FILES)

        if form.is_valid():
            cv_entry = form.save(commit=False)
            cv_entry.user = user  # attach logged-in user
            cv_entry.is_approved = False
            cv_entry.save()

            full_name = cv_entry.full_name or user.get_full_name() or user.username
            specialty = getattr(cv_entry, "specialty", "Not specified")
            location = getattr(cv_entry, "location", "Not specified")

            # === Notify admin ===
            send_async_email(
                mail_admins,
                subject="🆕 New CV Submission Pending Approval",
                message=(
                    f"A new CV has been submitted:\n\n"
                    f"Full Name: {full_name}\n"
                    f"Specialty: {specialty}\n"
                    f"Location: {location}\n\n"
                    f"Login to admin panel to review."
                )
            )

            # === Notify user ===
            send_async_email(
                send_mail,
                subject="🎉 Your ChefHub CV Submission Was Successful",
                message=(
                    f"Hello {full_name},\n\n"
                    "Thank you for submitting your CV to ChefHub!\n"
                    "Your CV is pending admin approval.\n\n"
                    "Best regards,\nThe ChefHub Team"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[cv_entry.email or user.email],
            )

            messages.success(request, "✅ Your CV has been submitted successfully! Awaiting admin approval.")
            return redirect("home")  # ✔️ Redirect to home

        else:
            print("CV Submission Form errors:", form.errors)
            messages.error(request, "❌ Please correct the errors below.")

    else:
        form = CVSubmissionForm()

    return render(
        request,
        "submit_cv.html",
        {
            "form": form,
            "specialties": specialties,
            "locations": locations,
        }
    )




@login_required(login_url='login')
def submit_job(request):
    user = request.user
    form = JobVacancySubmissionForm()
    can_submit = hasattr(user, 'employerprofile')  # Only employers can submit

    if request.method == "POST":
        if not can_submit:
            messages.error(request, "❌ Only employers can submit job vacancies.")
        else:
            form = JobVacancySubmissionForm(request.POST)
            if form.is_valid():
                job = form.save(commit=False)

                # Link user to job
                job.user = user
                job.employer = user
                job.is_approved = False

                # Save additional fields
                job.company_name = form.cleaned_data.get('company_name')
                job.establishment_type = form.cleaned_data.get('establishment_type')
                job.job_positions = form.cleaned_data.get('job_positions')
                job.employment_type = form.cleaned_data.get('employment_type')
                job.work_location = form.cleaned_data.get('work_location')
                job.state_of_residence = form.cleaned_data.get('state_of_residence')
                job.salary_range = form.cleaned_data.get('salary_range')
                job.skills_cuisine = form.cleaned_data.get('skills_cuisine')
                job.preferred_qualification = form.cleaned_data.get('preferred_qualification')
                job.language_preference = form.cleaned_data.get('language_preference')
                job.start_date = form.cleaned_data.get('start_date')
                job.working_hours = form.cleaned_data.get('working_hours')
                job.meals_accommodation = form.cleaned_data.get('meals_accommodation')
                job.message = form.cleaned_data.get('message')

                job.save()

                # Send emails asynchronously
                employer_email = user.email
                admin_email = settings.DEFAULT_FROM_EMAIL

                subject_user = "✅ Job Vacancy Submitted - Awaiting Approval"
                message_user = (
                    f"Dear {user.username},\n\n"
                    "Your job vacancy has been received successfully.\n"
                    "Our admin team will review and approve it shortly.\n\n"
                    "Best regards,\nChef.com Team"
                )

                subject_admin = f"🆕 New Job Vacancy Pending Approval - {user.username}"
                message_admin = (
                    f"A new job vacancy has been submitted by {user.username}.\n\n"
                    f"Job Title: {job.position_title}\n"
                    f"Company Name: {job.company_name}\n"
                    f"Employment Type: {job.employment_type}\n\n"
                    "Please log in to the admin panel to approve or reject it."
                )

                try:
                    send_async_mail(subject_user, message_user, admin_email, [employer_email])
                    send_async_mail(subject_admin, message_admin, admin_email, [admin_email])
                except Exception as e:
                    messages.warning(request, f"⚠️ Job saved but email could not be sent: {e}")

                messages.success(request, "✅ Job Vacancy submitted successfully! Awaiting admin approval.")
                return redirect("submit_job")
            else:
                messages.error(request, "❌ Please correct the errors below.")

    return render(request, 'submit_job.html', {
        "form": form,
        "can_submit": can_submit
    })




def about(request):
    # ✅ Count total verified companies (assuming EmployerProfile model)
    total_companies = EmployerProfile.objects.filter(is_verified=True).count()

    # ✅ Count total job applications
    total_applications = JobApplication.objects.all().count()

    # ✅ Count total approved jobs
    total_jobs = JobVacancySubmission.objects.filter(is_approved=True).count()

    # ✅ Count total registered members (chefs)
    total_members = User.objects.filter(is_active=True).count()

    context = {
        "total_companies": total_companies,
        "total_applications": total_applications,
        "total_jobs": total_jobs,
        "total_members": total_members,
    }

    return render(request, "about.html", context)


def services(request):
    return render(request, 'services.html')

def team(request):
    return render(request, 'team.html')

def faq(request):
    return render(request, 'faq.html')

def subscribe(request):
    return render(request, 'subscribe.html')


def employers_list(request):
    return render(request, 'employers_list.html')

def company_detail(request):
    return render(request, 'company_detail.html')




def user_login(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # 🔹 Step 1: Check if user exists
        try:
            user = User.objects.get(email=email)  # ✅ Query by email
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

        # 🔹 Step 2: If account is unverified (if you use this logic)
        if not user.is_active:
            otp = str(random.randint(100000, 999999))

            VerificationCode.objects.filter(user=user, is_used=False).update(is_used=True)
            VerificationCode.objects.create(
                user=user,
                code=otp,
                expires_at=timezone.now() + timezone.timedelta(minutes=10)
            )

            send_mail(
                "Verify your Chefs.com.ng account",
                f"Your verification code is {otp}. It expires in 10 minutes.",
                "ChefHub <atechincc@gmail.com>",
                [user.email],
                fail_silently=False,
            )

            request.session["pending_user_email"] = email
            messages.info(request, "Your account is not verified. A new verification code has been sent.")
            return redirect("verify_code")

        # 🔹 Step 3: Normal authentication (now correct)
        auth_user = authenticate(request, username=user.username, password=password)

        if auth_user is not None:
            # 🔹 OTP on Login
            otp = str(random.randint(100000, 999999))
            UserOTP.objects.update_or_create(
                user=user,
                defaults={"otp_code": otp, "created_at": timezone.now()}
            )

            send_mail(
                "Your chefs.com.ng Login OTP",
                f"Your OTP code is: {otp}",
                "noreply@chefs.com.ng",
                [user.email],
                fail_silently=False,
            )

            request.session["otp_user_id"] = user.id
            messages.info(request, "Enter the OTP sent to your email.")
            return redirect("verify_otp")

        else:
            messages.error(request, "Invalid email or password.")
            return redirect("login")

    return render(request, "login.html")




def set_role(request, role):
    request.session["signup_role"] = role
    return redirect("account_signup") 




def verify_otp_view(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        user_id = request.session.get("otp_user_id")

        if not user_id:
            messages.error(request, "Session expired. Please log in again.")
            return redirect("login")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            messages.error(request, "User not found.")
            return redirect("login")

        try:
            otp_record = UserOTP.objects.get(user=user)
        except UserOTP.DoesNotExist:
            messages.error(request, "No OTP record found.")
            return redirect("login")

        if otp_record.otp_code == otp_entered:
            # ✅ Activate and log in the user
            user.is_active = True
            user.save()
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            auth_login(request, user)

            # ✅ Add login success message
            messages.success(request, "Login successful!")

            # ✅ Redirect based on profile type
            if hasattr(user, 'chefprofile'):
                return redirect("chef_dashboard")
            elif hasattr(user, 'employerprofile'):
                return redirect("employer_dashboard")
            else:
                messages.warning(request, "No profile found. Please contact support.")
                return redirect("home")  # fallback

        else:
            messages.error(request, "Invalid OTP. Please try again.")
            return redirect("verify_otp")

    return render(request, "verify_otp.html")



def resend_otp_view(request):
    user_id = request.session.get("otp_user_id")
    if not user_id:
        messages.error(request, "Session expired. Please log in again.")
        return redirect("login")

    user = User.objects.get(id=user_id)
    new_otp = str(random.randint(100000, 999999))

    # Update or create OTP
    UserOTP.objects.update_or_create(
        user=user,
        defaults={"otp_code": new_otp, "created_at": timezone.now()}
    )

    # Send email
    send_mail(
        "Your chefs.com.ng Login OTP",
        f"Your new OTP code is: {new_otp}",
        "noreply@chefs.com.ng",
        [user.email],
        fail_silently=False,
    )

    messages.success(request, "✅ A new OTP has been sent to your email.")
    return redirect("verify_otp")


def logout_view(request):
    auth_logout(request)
    return redirect("home")



def signup(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")
        nationality_id = request.POST.get("nationality")
        phone_number = request.POST.get("phone_number")

        # === Validate Passwords ===
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup")

        # === Prevent Duplicate User ===
        if User.objects.filter(username=email).exists():
            messages.error(request, "User already exists.")
            return redirect("signup")

        # === Create User ===
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_active = False
        user.save()

        # ✅ Fetch the Country instance
        nationality = Country.objects.filter(id=nationality_id).first()

        # === Create Chef Profile ===
        chef_profile = ChefProfile.objects.create(
            user=user,
            phone_number=phone_number,
            nationality=nationality
        )

        # === Create Candidate Profile linked to this user ===
        candidate_profile = Candidate.objects.create(
            user=user,
            full_name=f"{first_name} {last_name}",
            email=email,
            is_approved=False  # initially pending
        )

        # === Generate Verification Code ===
        code = random.randint(100000, 999999)
        VerificationCode.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timezone.timedelta(minutes=10)
        )

        # === Send Verification Email ===
        send_mail(
            "Verify Your Chef Account",
            f"Your verification code is {code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )

        # === Store Session Info ===
        request.session["pending_user_email"] = email
        request.session["signup_category"] = "chef"

        messages.success(request, "Account created! Please check your email for the verification code.")
        return redirect("verify_code")

    countries = Country.objects.all().order_by("name")
    return render(request, "signup.html", {"countries": countries})




def signup_employer(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        confirm_password = request.POST.get("confirm_password", "")
        organization = request.POST.get("organization", "").strip()
        nationality_id = request.POST.get("nationality", "").strip()  # changed from country to nationality
        full_phone = request.POST.get("phone_number", "").strip()
        terms_accepted = request.POST.get("terms")

        # === Validate Terms ===
        if not terms_accepted:
            messages.error(request, "You must accept the terms and conditions.")
            return redirect("signup_employer")

        # === Check for Empty Fields ===
        if not all([first_name, last_name, email, password, confirm_password, organization, nationality_id, full_phone]):
            messages.error(request, "All fields are required.")
            return redirect("signup_employer")

        # === Validate Passwords ===
        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect("signup_employer")

        # === Check for Existing User ===
        if User.objects.filter(username=email).exists():
            messages.error(request, "User with this email already exists.")
            return redirect("signup_employer")

        # === Create User ===
        user = User.objects.create_user(
            username=email,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_active = False
        user.save()

        # ✅ Fetch Country instance from cities_light
        nationality = Country.objects.filter(id=nationality_id).first()

        # === Create Employer Profile ===
        EmployerProfile.objects.create(
            user=user,
            organization=organization,
            phone_number=full_phone,
            nationality=nationality,  # use FK instance instead of string
        )

        # === Generate and Save Verification Code ===
        code = str(random.randint(100000, 999999))
        VerificationCode.objects.create(
            user=user,
            code=code,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # === Send Verification Email ===
        send_mail(
            "Verify Your Employer Account",
            f"Your verification code is {code}",
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True,
        )

        # === Save Session Data ===
        request.session["pending_user_email"] = email
        request.session["signup_category"] = "employer"

        messages.success(request, "Account created! Please check your email for the verification code.")
        return redirect("verify_code")

    # === Load countries for dropdown ===
    countries = Country.objects.all().order_by("name")
    return render(request, "signup_employer.html", {"countries": countries})



User = get_user_model()

def verify_code(request):
    email = request.session.get("pending_user_email")
    category = request.session.get("signup_category")

    if not email:
        return redirect("login")

    try:
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect("signup")

    if request.method == "POST":
        code_entered = request.POST.get("code")

        try:
            record = VerificationCode.objects.filter(user=user, is_used=False).latest("created_at")
        except VerificationCode.DoesNotExist:
            messages.error(request, "No verification code found.")
            return redirect("verify_code")

        if record.is_expired():
            messages.error(request, "This verification code has expired.")
            return redirect("verify_code")

        if record.code == code_entered:
            record.is_used = True
            record.save()

            # ✅ Mark user and profile as verified
            user.is_active = True
            user.save()

            if category == "chef":
                ChefProfile.objects.filter(user=user).update(is_verified=True)
                redirect_to = "chef_dashboard"
            else:
                EmployerProfile.objects.filter(user=user).update(is_verified=True)
                redirect_to = "employer_dashboard"

            # ✅ Fix: specify backend for Django to log user in
            user.backend = "allauth.account.auth_backends.AuthenticationBackend"
            auth_login(request, user)

            messages.success(request, "✅ Verification successful!")
            return redirect(redirect_to)

        messages.error(request, "❌ Invalid verification code. Please try again.")

    return render(request, "verify_code.html")



def resend_code(request):
    # Try to get email from session first
    email = request.session.get("pending_user_email")

    if not email:
        email = request.POST.get("email")

    if not email:
        messages.error(request, "Session expired. Please sign up or log in again.")
        return redirect("signup")

    try:
        # ✅ Use username instead of email for lookup
        user = User.objects.get(username=email)
    except User.DoesNotExist:
        messages.error(request, "No account found with that email.")
        return redirect("signup")

    # Generate new 6-digit code
    new_code = str(random.randint(100000, 999999))

    # Deactivate previous unused codes
    VerificationCode.objects.filter(user=user, is_used=False).update(is_used=True)

    # Create new one
    VerificationCode.objects.create(
        user=user,
        code=new_code,
        expires_at=timezone.now() + timezone.timedelta(minutes=10)
    )

    # Send email
    send_mail(
        subject="Your Verification Code",
        message=f"Your new verification code is {new_code}. It expires in 10 minutes.",
        from_email="ChefHub <atechincc@gmail.com>",
        recipient_list=[email],
        fail_silently=False,
    )

    # Keep session alive
    request.session["pending_user_email"] = email

    messages.success(request, "✅ A new verification code has been sent to your email.")
    return redirect("verify_code")




@login_required
def complete_profile(request):
    user = request.user

    # Determine which profile to update
    profile = getattr(user, "chefprofile", None) or getattr(user, "employerprofile", None)

    if profile and profile.profile_completed:
        return redirect("dashboard")  # already completed

    if request.method == "POST":
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            # Set password for the user
            user.set_password(data["password1"])
            user.save()

            # Update profile info
            if profile:
                profile.phone_number = data["phone_number"]
                profile.country = data["country"]
                profile.profile_completed = True
                profile.save()

            messages.success(request, "🎉 Profile setup complete! You can now login to continue.")
            return redirect("chef_dashboard")
    else:
        form = CompleteProfileForm()

    return render(request, "complete_profile.html", {"form": form})



@login_required(login_url='login')
def chef_dashboard(request):
    chef, created = ChefProfile.objects.get_or_create(user=request.user)

    # ✅ Handle profile picture upload
    if request.method == "POST" and 'profile_picture' in request.FILES:
        chef.profile_picture = request.FILES['profile_picture']
        chef.save()
        return redirect('chef_dashboard')  # reload after upload

    # ✅ Get job engagements for the logged-in user
    job_engagements = JobEngagement.objects.filter(candidate=request.user).order_by('-created_at')

    return render(request, "chef_dashboard.html", {
        "chef": chef,
        "job_engagements": job_engagements
    })





@login_required
def employer_dashboard(request):
    try:
        employer_profile = EmployerProfile.objects.get(user=request.user)
    except EmployerProfile.DoesNotExist:
        messages.error(request, "Access denied. You are not registered as an employer.")
        return redirect("home")

    # ✅ Handle profile picture upload
    if request.method == "POST" and request.FILES.get("profile_picture"):
        employer_profile.profile_picture = request.FILES["profile_picture"]
        employer_profile.save()
        messages.success(request, "Profile picture updated successfully!")
        return redirect("employer_dashboard")  # Refresh to show the new image

    engagements = JobEngagement.objects.filter(
        employer=request.user
    ).select_related("candidate__user").order_by("-created_at")

    return render(request, "employer_dashboard.html", {
        "employer": employer_profile,
        "engagements": engagements,
    })




def recovery_password(request):
    return render(request, 'recovery_password.html')

def partners(request):
    return render(request, 'partners.html')



def contact(request):
    if request.method == "POST":
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "✅ Your message has been sent successfully!")
            return redirect('contact')
        else:
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = ContactForm()
    
    return render(request, "contact.html", {"form": form})




@login_required(login_url="login")
def culinary_agents(request):
    """
    Handles Culinary Agent registration.
    Only authenticated users with active subscriptions can submit.
    Sends formal confirmation email to candidate upon successful registration.
    """
    if request.method == "POST":
        user = request.user

        # ✅ Ensure active subscription
        subscription = Subscription.objects.filter(user=user, is_active=True).first()
        if not subscription:
            messages.warning(
                request,
                "🚫 You must have an active subscription to register as a Culinary Agent."
            )
            return redirect("subscription_page")

        # ✅ Process registration form
        form = CulinaryAgentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            agent = form.save(commit=False)
            agent.user = user
            agent.save()

            # ✅ Save multiple dish photos if uploaded
            for img in request.FILES.getlist("dish_photos"):
                DishPhoto.objects.create(agent=agent, image=img)

            # --- Admin Notification (unchanged) ---
            subject_admin = "New Culinary Agent Registration"
            message_admin = (
                f"A new Culinary Agent registration was submitted by {agent.full_name}.\n"
                f"Email: {agent.email}"
            )
            send_async_email(
                send_mail,
                subject_admin,
                message_admin,
                settings.DEFAULT_FROM_EMAIL,
                [settings.DEFAULT_FROM_EMAIL]
            )

            # --- Candidate Confirmation Email (formal detailed style) ---
            subject_user = "🎉 Thank You for Registering with CJA Recruitment Agency — Culinary Agent Program"
            message_user = f"""
Dear {agent.full_name},

Thank you for completing your registration to join the Culinary Agent Program with Chef James & Associates Nigeria Limited (CJA) — the premier representation platform for professional chefs and culinary talents across Nigeria and Africa.

We are delighted by your interest in joining our network. Our team will carefully review your submission and contact you shortly to discuss your culinary experience, professional goals, and next steps toward matching you with rewarding opportunities.

________________________________________
Key Information About the Culinary Agent Program
By joining the CJA Culinary Agent Program, you authorize CJA to act as your official representative in securing culinary engagements, brand partnerships, and professional contracts on your behalf.

Terms of Representation:
1. Commission
   - CJA earns a 20% commission on all successful deals, placements, or contracts secured through our agency.
   - All payments for CJA-facilitated opportunities are processed through CJA before disbursement to you.

2. Professional Conduct
   - You are expected to maintain professionalism, punctuality, and integrity in all engagements.
   - Any direct client engagement bypassing CJA constitutes a breach of representation terms.

3. Termination
   - Either party may terminate this agreement with written notice.
   - Commissions for any existing contracts or deals facilitated by CJA remain payable.

For a complete overview of your rights and obligations, please review our full Terms & Conditions of Representation here: [Insert Link to Full Terms]

________________________________________
Once your registration has been verified, a Talent Manager will reach out to confirm your profile. If approved, we will begin actively pitching you for available chef placements, brand partnerships, and other professional opportunities.

If you have any immediate questions, please contact us at hrchef@chef.com.ng or +234 (0) XXX XXX XXXX.

Warm regards,  
Chef James & Associates Nigeria Limited (CJA)  
Empowering Culinary Careers. Strengthening Hospitality Brands.
"""
            send_async_email(
                send_mail,
                subject_user,
                message_user,
                settings.DEFAULT_FROM_EMAIL,
                [agent.email]
            )

            messages.success(
                request,
                "✅ Registration submitted successfully! You’ll be contacted soon."
            )
            return redirect("culinary_agents")
        else:
            print("🧾 FORM ERRORS:", form.errors)
            messages.error(request, "❌ Please correct the errors below.")
    else:
        form = CulinaryAgentRegistrationForm()

    return render(request, "culinary_agents.html", {"form": form})





@login_required
def relief_chef(request):
    form = ReliefChefRequestForm()

    if request.method == "POST":
        form = ReliefChefRequestForm(request.POST, request.FILES)
        user = request.user

        # ✅ Must be employer
        if not EmployerProfile.objects.filter(user=user).exists():
            messages.error(request, "❌ Only employer accounts can submit a Relief Chef request.")
            return redirect("home")

        # ✅ Must have active subscription
        active_subscription = (
            user.subscriptions.filter(is_active=True)
            .order_by("-end_date")
            .first()
        )

        if not active_subscription or not active_subscription.has_active_subscription():
            messages.error(request, "⚠️ You must have an active subscription to submit this request.")
            return redirect("subscription_page")

        # ✅ Valid form
        if form.is_valid():
            chef_request = form.save(commit=False)
            chef_request.user = user
            chef_request.save()

            # ✅ Notify admin and user
            admin_email = settings.DEFAULT_FROM_EMAIL
            user_email = chef_request.email
            employer_name = chef_request.company_name

            # --- Admin Notification ---
            send_async_email(
                send_mail,
                "New Relief Chef Request Submitted",
                f"A new relief chef request was submitted by {employer_name}.",
                admin_email,
                [admin_email],
            )

            # --- Employer Confirmation ---
            subject = "Thank You for Your Request — Chef Placement Confirmation"
            message = f"""
Dear {employer_name},

Thank you for reaching out to Chef.com.ng, the recruitment arm of Chef James & Associates (CJA).

We have received your request for our ‘Find Relief Chef’ service, and we’re delighted to support you in finding the right culinary professional for your team.

Our Service Terms

To ensure fairness, transparency, and professionalism in all engagements, please review our standard placement terms below:

1. Payment Structure
   - The first month’s salary of any chef engaged through Chef.com.ng is to be paid through our agency.
   - Subsequent salary payments are made directly to the employed chef by the employer.

2. Agency Commission
   - Chef.com.ng earns a 15% service commission from the chef’s first month’s agreed salary.
   - Example: If a chef’s monthly salary is ₦250,000, Chef.com.ng’s commission is ₦37,500, and the chef receives the balance of ₦212,500.

3. Service Completion Clause
   - Once a chef has successfully completed 30 days (one full month) of work, Chef.com.ng’s commission for that placement is deemed fully earned.

4. Replacement Policy
   - If a placed chef discontinues the role within 14 days of engagement due to unforeseen circumstances, Chef.com.ng will provide a qualified replacement at no additional cost to the employer.

5. Candidate Vetting & Conduct
   - All chefs are screened, reference-checked, and verified before recommendation.
   - Employers are expected to provide safe working conditions, timely remuneration, and a respectful work environment.

6. Non-Circumvention Policy
   - Employers are kindly reminded not to engage any chef introduced by Chef.com.ng outside our process within the first 6 months of introduction.
   - Breach of this term may attract a penalty equivalent to one full month’s salary of the candidate.

We appreciate your cooperation and look forward to a successful recruitment process.
Our placement team will contact you shortly to confirm your request details and begin candidate matching.

Warm regards,  
The Recruitment Team  
Chef.com.ng — By Chef James & Associates (CJA)  
📧 hrchef@chef.com.ng | 🌐 www.chef.com.ng | 📞 +234 (0) xxx xxx xxxx  

Confidentiality Notice:  
All communications and candidate details shared by Chef.com.ng are strictly confidential and must not be disclosed or used outside the agreed recruitment purpose.
"""

            send_async_email(
                send_mail,
                subject,
                message,
                admin_email,
                [user_email],
            )

            messages.success(request, "✅ Your Relief Chef request has been submitted successfully!")
            return redirect("relief_chef")

        else:
            messages.error(request, "❌ Please correct the errors in your submission.")

    return render(request, "relief_chef.html", {"form": form})



@login_required
# -------------------------
# PERMANENT CHEF REQUEST
# -------------------------
def permanent_chef(request):
    form = PermanentChefRequestForm()

    if request.method == "POST":
        form = PermanentChefRequestForm(request.POST, request.FILES)
        user = request.user

        # ✅ Must be employer
        if not EmployerProfile.objects.filter(user=user).exists():
            messages.error(request, "❌ Only employer accounts can submit a Permanent Chef request.")
            return redirect("home")

        # ✅ Must have active subscription (manual or automatic)
        active_subscription = (
            user.subscriptions.filter(is_active=True)
            .order_by("-end_date")
            .first()
        )

        if not active_subscription or not active_subscription.has_active_subscription():
            messages.error(request, "⚠️ You must have an active subscription to submit this request.")
            return redirect("subscription_page")

        # ✅ Valid form
        if form.is_valid():
            chef_request = form.save(commit=False)
            chef_request.user = user
            chef_request.save()

            # ✅ Email setup
            admin_email = settings.DEFAULT_FROM_EMAIL
            employer_email = chef_request.email
            employer_name = chef_request.company_name

            # --- Admin Notification ---
            send_async_email(
                send_mail,
                "New Permanent Chef Request Submitted",
                f"A new permanent chef request has been submitted by {employer_name}.",
                admin_email,
                [admin_email],
            )

            # --- Employer Confirmation Email ---
            subject = "Thank You for Your Request — Chef Placement Confirmation"
            message = f"""
Dear {employer_name},

Thank you for reaching out to Chef.com.ng, the recruitment arm of Chef James & Associates (CJA).

We have received your request for our ‘Find Permanent Chef’ service, and we’re delighted to support you in finding the right culinary professional for your team.

Our Service Terms

1. Payment Structure
   - The first month’s salary of any chef engaged through Chef.com.ng is to be paid through our agency.
   - Subsequent salary payments are made directly to the employed chef by the employer.

2. Agency Commission
   - Chef.com.ng earns a 15% service commission from the chef’s first month’s agreed salary.
   - Example: If a chef’s monthly salary is ₦250,000, Chef.com.ng’s commission is ₦37,500, and the chef receives the balance of ₦212,500.

3. Service Completion Clause
   - Once a chef has successfully completed 30 days (one full month) of work, Chef.com.ng’s commission for that placement is deemed fully earned.

4. Replacement Policy
   - If a placed chef discontinues the role within 14 days of engagement due to unforeseen circumstances, Chef.com.ng will provide a qualified replacement at no additional cost to the employer.

5. Candidate Vetting & Conduct
   - All chefs are screened, reference-checked, and verified before recommendation.
   - Employers are expected to provide safe working conditions, timely remuneration, and a respectful work environment.

6. Non-Circumvention Policy
   - Employers are kindly reminded not to engage any chef introduced by Chef.com.ng outside our process within the first 6 months of introduction.
   - Breach of this term may attract a penalty equivalent to one full month’s salary of the candidate.

We appreciate your cooperation and look forward to a successful recruitment process.
Our placement team will contact you shortly to confirm your request details and begin candidate matching.

Warm regards,  
The Recruitment Team  
Chef.com.ng — By Chef James & Associates (CJA)  
📧 hrchef@chef.com.ng | 🌐 www.chef.com.ng | 📞 +234 (0) xxx xxx xxxx  

Confidentiality Notice:  
All communications and candidate details shared by Chef.com.ng are strictly confidential and must not be disclosed or used outside the agreed recruitment purpose.
"""
            send_async_email(
                send_mail,
                subject,
                message,
                admin_email,
                [employer_email],
            )

            messages.success(request, "✅ Your Permanent Chef request has been submitted successfully!")
            return redirect("permanent_chef")
        else:
            messages.error(request, "❌ Please correct the errors in your submission.")

    return render(request, "permanent_chef.html", {"form": form})


# -------------------------
# PRIVATE CHEF REQUEST
# -------------------------
@login_required
def private_chef(request):
    form = PrivateChefRequestForm()

    if request.method == "POST":
        user = request.user

        # ✅ Must be logged in
        if not user.is_authenticated:
            messages.error(request, "❌ You must be logged in to submit a private chef request.")
            return redirect("login")

        # ✅ Must be an employer
        if not EmployerProfile.objects.filter(user=user).exists():
            messages.error(request, "❌ Only employer accounts can submit a private chef request.")
            return redirect("home")

        # ✅ Must have active subscription (manual or automatic)
        active_subscription = (
            user.subscriptions.filter(is_active=True)
            .order_by("-end_date")
            .first()
        )

        if not active_subscription or not active_subscription.has_active_subscription():
            messages.error(request, "❌ You must be subscribed to submit a private chef request.")
            return redirect("subscription_page")

        # ✅ Valid form
        form = PrivateChefRequestForm(request.POST, request.FILES)
        if form.is_valid():
            chef_request = form.save(commit=False)
            chef_request.user = user
            chef_request.save()

            # ✅ Send notifications
            admin_email = settings.DEFAULT_FROM_EMAIL
            employer_email = chef_request.email
            employer_name = chef_request.full_name

            # --- Notify Admin ---
            send_async_email(
                send_mail,
                "New Private Chef Request Submitted",
                f"A new private chef request has been submitted by {employer_name}.",
                admin_email,
                [admin_email],
            )

            # --- Send Confirmation to Employer ---
            subject = "Thank You for Your Request — Chef Placement Confirmation"
            message = f"""
Dear {employer_name},

Thank you for reaching out to Chef.com.ng, the recruitment arm of Chef James & Associates (CJA).

We have received your request for our ‘Find Private Chef’ service, and we’re delighted to support you in finding the right culinary professional for your team.

Our Service Terms

To ensure fairness, transparency, and professionalism in all engagements, please review our standard placement terms below:

1. Payment Structure
   - The first month’s salary of any chef engaged through Chef.com.ng is to be paid through our agency.
   - Subsequent salary payments are made directly to the employed chef by the employer.

2. Agency Commission
   - Chef.com.ng earns a 15% service commission from the chef’s first month’s agreed salary.
   - Example: If a chef’s monthly salary is ₦250,000, Chef.com.ng’s commission is ₦37,500, and the chef receives the balance of ₦212,500.

3. Service Completion Clause
   - Once a chef has successfully completed 30 days (one full month) of work, Chef.com.ng’s commission for that placement is deemed fully earned.

4. Replacement Policy
   - If a placed chef discontinues the role within 14 days of engagement due to unforeseen circumstances, Chef.com.ng will provide a qualified replacement at no additional cost to the employer.

5. Candidate Vetting & Conduct
   - All chefs are screened, reference-checked, and verified before recommendation.
   - Employers are expected to provide safe working conditions, timely remuneration, and a respectful work environment.

6. Non-Circumvention Policy
   - Employers are kindly reminded not to engage any chef introduced by Chef.com.ng outside our process within the first 6 months of introduction.
   - Breach of this term may attract a penalty equivalent to one full month’s salary of the candidate.

We appreciate your cooperation and look forward to a successful recruitment process.
Our placement team will contact you shortly to confirm your request details and begin candidate matching.

Warm regards,  
The Recruitment Team  
Chef.com.ng — By Chef James & Associates (CJA)  
📧 hrchef@chef.com.ng | 🌐 www.chef.com.ng | 📞 +234 (0) xxx xxx xxxx  

Confidentiality Notice:  
All communications and candidate details shared by Chef.com.ng are strictly confidential and must not be disclosed or used outside the agreed recruitment purpose.
"""
            send_async_email(
                send_mail,
                subject,
                message,
                admin_email,
                [employer_email],
            )

            messages.success(request, "✅ Your Private Chef request has been submitted successfully!")
            return redirect("private_chef")
        else:
            messages.error(request, "❌ Please correct the errors in your submission.")

    return render(request, "private_chef.html", {"form": form})




def event_news(request):
    return render(request, 'event_news.html')

def testimonies(request):
    return render(request, 'testimonies.html')



def chefs_hub(request):
    # Only approved chefs and CV submissions should show
    approved_candidates = Candidate.objects.filter(is_approved=True)
    approved_cv_submissions = CVSubmission.objects.filter(is_approved=True)
    is_employer = hasattr(request.user, "employerprofile")

    # ✅ Get all engagements where status = 'engaged'
    engaged_or_hired = JobEngagement.objects.filter(status="engaged")

    # ✅ Exclude candidates tied to those engagements
    # Match via candidate.user because JobEngagement.candidate -> User
    approved_candidates = approved_candidates.exclude(
        user__job_engagements_as_candidate__in=engaged_or_hired
    )

    # ✅ Exclude CV submissions tied to engaged candidates
    approved_cv_submissions = approved_cv_submissions.exclude(
        user__job_engagements_as_candidate__in=engaged_or_hired
    )

    return render(request, "chefs_hub.html", {
        "candidates": approved_candidates,
        "cv_submissions": approved_cv_submissions,
        "is_employer": is_employer,
    })





def consultancy_services(request):
    return render(request, 'consultancy_services.html')  

def terms_condition(request):
    return render(request, 'terms_condition.html')

def privacy_policy(request):
    return render(request, 'privacy_policy.html')

def disclaimer(request):
    return render(request, 'disclaimer.html')



@login_required
def chef_settings(request):
    return render(request, "dashboard/chef_settings.html")



@login_required
def employer_settings(request):
    return render(request, "dashboard/employer_settings.html")



@login_required
def upgrade_subscription(request):
    if request.method == "POST":
        # Redirect to your subscription packages page
        return redirect("subscription_page")
    return redirect("chef_settings")



# @login_required
# def upgrade_verified(request):
#     if request.method == "POST":
#         chef = getattr(request.user, "chefprofile", None)
#         if chef:
#             chef.is_verified_2 = True
#             chef.save()
#             messages.success(request, "✅ Your account has been upgraded to Verified!")
#         else:
#             messages.error(request, "❌ Unable to find your chef profile.")
#     return redirect("chef_settings")

@login_required
def upgrade_verified(request):
    """
    When user clicks 'Upgrade to Verified' from Settings,
    redirect them to the Verified Handle information page.
    """
    return redirect("verified_handle_page")   # URL name for the page you provided

@login_required
def verified_handle_page(request):
    return render(request, "upgrade_verified.html")


@login_required
def verified_checkout(request):
    user_type = request.GET.get("type")      # 'chef' or 'employer'
    amount = request.GET.get("amount")       # amount passed from template buttons

    # Validate user_type
    if user_type not in ["chef", "employer"]:
        messages.error(request, "Invalid verification type.")
        return redirect("verified_handle_page")

    # Validate amount
    if not amount or not amount.isdigit():
        messages.error(request, "Invalid or missing payment amount.")
        return redirect("verified_handle_page")

    # Convert amount to integer
    amount = int(amount)

    # Create unique transaction reference
    txn_ref = str(uuid.uuid4())

    # Save to session
    request.session["verify_ref"] = txn_ref
    request.session["verify_type"] = user_type
    request.session["verify_amount"] = amount

    # Select the payment gateway (Paystack by default)
    gateway = "paystack"  # later you can let user choose

    if gateway == "paystack":
        return redirect(reverse("paystack_init") + f"?ref={txn_ref}&amount={amount}")

    else:  # Flutterwave
        return redirect(reverse("flutter_init") + f"?ref={txn_ref}&amount={amount}")

    

@login_required
def paystack_init(request):
    ref = request.GET.get("ref")
    amount = request.GET.get("amount")  # coming from verified_checkout

    # Validate
    if not ref or not amount:
        messages.error(request, "Invalid payment request.")
        return redirect("verified_handle_page")

    try:
        amount = int(amount) * 100  # convert Naira → Kobo
    except:
        messages.error(request, "Invalid amount value.")
        return redirect("verified_handle_page")

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    data = {
        "email": request.user.email,
        "amount": amount,
        "reference": ref,
        "callback_url": request.build_absolute_uri(reverse("paystack_callback")),
    }

    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        json=data,
        headers=headers
    ).json()

    if response.get("status") is True:
        return redirect(response["data"]["authorization_url"])
    else:
        messages.error(request, "Payment initialization failed. Try again.")
        return redirect("verified_handle_page")



@login_required
def paystack_callback(request):
    ref = request.GET.get("reference")

    verify_url = f"https://api.paystack.co/transaction/verify/{ref}"
    headers = {"Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}"}

    res = requests.get(verify_url, headers=headers).json()

    if res["data"]["status"] == "success":
        # Mark account as verified
        user = request.user
        chef = getattr(user, "chefprofile", None)
        employer = getattr(user, "employerprofile", None)

        if chef:
            chef.is_verified_2 = True
            chef.save()

        elif employer:
            employer.is_verified_2 = True
            employer.save()

        messages.success(request, "🎉 Payment Successful! Your account is now VERIFIED.")
        return redirect("chef_settings" if chef else "employer_settings")

    messages.error(request, "Payment verification failed.")
    return redirect("verified_handle_page")



@login_required
def flutter_init(request):
    import requests

    ref = request.GET.get("ref")
    amount = request.GET.get("amount")  # amount in Naira from button
    user = request.user

    if not ref or not amount:
        messages.error(request, "Invalid payment request.")
        return redirect("verified_handle_page")

    try:
        amount = float(amount)  # make sure it's a number
    except ValueError:
        messages.error(request, "Invalid amount value.")
        return redirect("verified_handle_page")

    data = {
        "tx_ref": ref,
        "amount": amount,
        "currency": "NGN",
        "redirect_url": request.build_absolute_uri(reverse("flutter_callback")),
        "customer": {
            "email": user.email,
            "name": user.get_full_name()
        },
        "customizations": {
            "title": "CJA Verified Handle",
            "description": "Payment for CJA Verified Handle subscription"
        }
    }

    headers = {
        "Authorization": f"Bearer {settings.FLUTTERWAVE_SECRET_KEY}",
        "Content-Type": "application/json"
    }

    res = requests.post("https://api.flutterwave.com/v3/payments",
                        json=data, headers=headers).json()

    if res.get("status") == "success":
        return redirect(res["data"]["link"])

    messages.error(request, "Flutterwave initialization failed.")
    return redirect("verified_handle_page")




@login_required
def flutter_callback(request):
    status = request.GET.get("status")
    ref = request.GET.get("tx_ref")

    if status == "successful":
        # Mark verified
        user = request.user
        chef = getattr(user, "chefprofile", None)
        employer = getattr(user, "employerprofile", None)

        if chef:
            chef.is_verified_2 = True
            chef.save()

        elif employer:
            employer.is_verified_2 = True
            employer.save()

        messages.success(request, "🎉 Payment Successful! Your account is now VERIFIED.")
        return redirect("chef_settings" if chef else "employer_settings")

    messages.error(request, "Payment failed or cancelled.")
    return redirect("verified_handle_page")





# Use Django built-in password views for these:
class change_password_view(PasswordChangeView):
    template_name = "dashboard/change_password.html"
    success_url = reverse_lazy("chef_settings")

    def form_valid(self, form):
        response = super().form_valid(form)
        
        # ✅ Success message
        messages.success(self.request, "✅ Your password has been changed successfully!")

        # ✅ Email user
        user = self.request.user
        send_mail(
            subject="🔐 Password Changed Successfully",
            message=(
                f"Hi {user.get_full_name() or user.username},\n\n"
                "Your password for your chefs.com.ng account was changed successfully.\n"
                "If you did not make this change, please reset your password immediately."
            ),
            from_email="noreply@chefs.com.ng",
            recipient_list=[user.email],
            fail_silently=True,
        )

        return response

    def form_invalid(self, form):
        messages.error(self.request, "❌ Please correct the errors below and try again.")
        return super().form_invalid(form)



class reset_password_view(PasswordResetView):
    template_name = "dashboard/password_reset.html"
    email_template_name = "dashboard/password_reset_verify.html"
    success_url = reverse_lazy("chef_settings")
    form_class = EmailBasedPasswordResetForm

    def form_valid(self, form):
        try:
            response = super().form_valid(form)
            messages.success(self.request, "✅ Password reset link has been sent to your email.")
            return response
        except Exception:
            messages.error(self.request, "❌ Failed to send reset email. Please check your email address and try again.")
            return self.form_invalid(form)




client = InferenceClient(token=os.getenv("HF_API_TOKEN"))

@csrf_exempt
def ask_ai(request):
    if request.method != "POST":
        return JsonResponse({"answer": "Invalid request method. Use POST."})

    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"answer": "Invalid JSON."})

    question = body.get("question")
    if not question:
        return JsonResponse({"answer": "Please ask a question."})

    user = request.user
    if hasattr(user, 'chefprofile'):
        profile_type = 'chef'
        profile = user.chefprofile
        is_verified = profile.is_verified_2
    elif hasattr(user, 'employerprofile'):
        profile_type = 'employer'
        profile = user.employerprofile
        is_verified = profile.is_verified_2
    else:
        profile_type = 'guest'
        is_verified = False

    subscription_info = ""
    if profile_type != 'guest':
        plan = getattr(profile, 'subscription_plan', 'No active plan')
        end_date = getattr(profile, 'subscription_end', 'N/A')
        subscription_info = f"Current Plan: {plan}, Expires: {end_date}"

    system_context = f"""
You are an AI assistant for Chef.com.ng, a platform for chefs and employers in Nigeria.
The site offers Verified Handle subscriptions for chefs and employers.

CHEF / CANDIDATE VERIFIED HANDLE
- Subscription Options:
  * Monthly: ₦2,000
  * 3 Months: ₦5,000
  * 6 Months: ₦10,000
  * 12 Months: ₦19,500
- Benefits: verified badge, priority job matching, visibility boost, CJA training & events, Top Verified Chefs directory.

EMPLOYER / BRAND VERIFIED HANDLE
- Subscription Options:
  * Monthly: ₦5,000
  * 3 Months: ₦13,500
  * 6 Months: ₦25,000
  * 12 Months: ₦47,500
- Benefits: verified badge, access to verified chef database, priority listing of vacancies, recruitment support, discounted commissions, partner spotlight.

Payment methods: Paystack or Flutterwave.

User Info:
Type: {profile_type}
Verified: {is_verified}
{subscription_info}
Answer questions as accurately as possible based on this information.
"""

    try:
        # Correct Hugging Face chat usage
        response = client.chat.model("meta-llama/Llama-2-7b-chat-hf")(
            messages=[
                {"role": "system", "content": system_context},
                {"role": "user", "content": question}
            ]
        )

        answer = response.get("generated_text", "No response from model.")
        return JsonResponse({"answer": answer})

    except Exception as e:
        return JsonResponse({"answer": f"Error contacting Hugging Face API: {str(e)}"})



def success_stories(request):
    # Get all testimonies (you can filter if needed)
    testimonies = TestimonyLog.objects.select_related('user').all().order_by('-created_at')

    return render(request, "home.html", {"testimonies": testimonies})