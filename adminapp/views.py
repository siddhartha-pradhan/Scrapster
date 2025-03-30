# adminapp/views.py
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required

from adminapp.forms import WasteTipForm, CommunityInitiativeForm
from wasteapp.models import WasteRequest, Complaint, Payment, WasteTip, CommunityInitiative, UserCommunityInitiative
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from account_app.decorators import role_required
from driverapp.models import DriverProfile
from django.core.mail import send_mail
from django.conf import settings

from django.db.models import Count, Sum

# View for the admin dashboard
@role_required(allowed_roles=['admin'])
def admin_dashboard(request):
    # Count total, pending, rejected, and completed waste requests
    total_requests = WasteRequest.objects.count()  # Total number of waste requests
    pending_requests = WasteRequest.objects.filter(status="Pending").count()  # Number of pending requests
    rejected_requests = WasteRequest.objects.filter(status="Rejected").count()  # Number of rejected requests
    completed_requests = WasteRequest.objects.filter(status="Completed").count()  # Number of completed requests
    # Count total users
    total_users = User.objects.filter(is_superuser=False).exclude(driver_profile__isnull=False).count()
    assigned_requests = WasteRequest.objects.filter(driver=request.user, status="Assigned").order_by("collection_time")
    # Create a context dictionary to pass data to the template
    context = {
        "total_requests": total_requests,
        "pending_requests": pending_requests,
        "rejected_requests": rejected_requests,
        "completed_requests": completed_requests,
        "total_users": total_users,
        "assigned_requests": assigned_requests,
    }

    # Add data for waste type distribution
    waste_type_counts = WasteRequest.objects.values('waste_type').annotate(count=Count('id'))
    waste_quantity_by_type = WasteRequest.objects.values('waste_type').annotate(total=Sum('quantity'))
    waste_type_data = {item['waste_type']: item['count'] for item in waste_type_counts}
    waste_quantity_data = {item['waste_type']: item['total'] for item in waste_quantity_by_type}

    # Add data for collection trends (last 7 days)
    from datetime import datetime, timedelta
    last_7_days = []
    collection_counts = []

    for i in range(6, -1, -1):
        day = datetime.now().date() - timedelta(days=i)
        count = WasteRequest.objects.filter(created_at__date=day).count()
        last_7_days.append(day.strftime('%a'))
        collection_counts.append(count)

    context.update({
        "waste_type_data": waste_type_data,
        "waste_quantity_data": waste_quantity_data,
        "last_7_days": last_7_days,
        "collection_counts": collection_counts,
        "waste_type_data_keys": list(waste_type_data.keys()),
        "waste_type_data_values": list(waste_type_data.values()),
        "waste_quantity_data_keys": list(waste_quantity_data.keys()),
        "waste_quantity_data_values": list(waste_quantity_data.values()),
    })

    return render(request, "adminapp/dashboard.html", context)



# View for managing pending waste requests
@role_required(allowed_roles=['admin'])
def manage_pending_requests(request):
    # Fetch all pending requests
    pending_requests = WasteRequest.objects.filter(status="Pending").order_by("-created_at")

    # Separate requests into unassigned and assigned categories
    unassigned_requests = pending_requests.filter(driver__isnull=True)
    assigned_requests = pending_requests.filter(driver__isnull=False)

    for waste_request in unassigned_requests:
        complaint = Complaint.objects.filter(waste_request=waste_request).first()
        waste_request.complaint = complaint  # will be None if not found

    for waste_request in assigned_requests:
        complaint = Complaint.objects.filter(waste_request=waste_request).first()
        waste_request.complaint = complaint  # will be None if not found

    # Prepare context to pass to the template
    context = {
        "unassigned_requests": unassigned_requests,
        "assigned_requests": assigned_requests,
    }

    # Render the template with context data
    return render(request, "adminapp/pending_requests.html", context)



# View for approving a waste request
@role_required(allowed_roles=['admin'])
def approve_request(request, request_id):
    # Get the waste request by ID and update its status to Completed
    waste_request = get_object_or_404(WasteRequest, id=request_id)  # Get the waste request object
    waste_request.status = "Completed"  # Update the status to Completed
    waste_request.save()  # Save the changes
    # Redirect to the manage pending requests page
    return redirect("adminapp:manage_pending_requests")


# View for rejecting a waste request
@role_required(allowed_roles=['admin'])
def reject_request(request, request_id):
    # Get the waste request by ID and update its status to Rejected
    waste_request = get_object_or_404(WasteRequest, id=request_id)  # Get the waste request object
    waste_request.status = "Rejected"  # Update the status to Rejected
    waste_request.save()  # Save the changes
    # Redirect to the manage pending requests page
    return redirect("adminapp:manage_pending_requests")


# View for viewing completed waste requests
@role_required(allowed_roles=['admin'])
def view_completed_requests(request):
    completed_requests = WasteRequest.objects.filter(status="Completed").order_by("-created_at")  # Get completed requests in descending order of creation date
    context = {"completed_requests": completed_requests}
    return render(request, "adminapp/completed_requests.html", context)

@role_required(allowed_roles=['admin'])
def manage_users(request):
    users = User.objects.filter(is_superuser=False).exclude(driver_profile__isnull=False)
    context = {"users": users}
    return render(request, "adminapp/manage_users.html", context)

@role_required(allowed_roles=['admin'])
def toggle_user_status(request, user_id):
    # Toggle the active status of a user
    user = get_object_or_404(User, id=user_id)  # Get the user object
    if user.is_active:
        user.is_active = False  # Deactivate the user
        messages.success(request, f"User {user.username} has been deactivated.")  # Display a success message
    else:
        user.is_active = True  # Activate the user
        messages.success(request, f"User {user.username} has been reactivated.")  # Display a success message
    user.save()  # Save the changes
    # Redirect to the manage users page
    return redirect("adminapp:manage_users")



# View for deleting a user
@role_required(allowed_roles=['admin'])
def delete_user(request, user_id):
    # Delete a user by ID
    user = get_object_or_404(User, id=user_id)  # Get the user object
    messages.success(request, f"User {user.username} has been deleted.")  # Display a success message
    user.delete()  # Delete the user
    # Redirect to the manage users page
    return redirect("adminapp:manage_users")

@role_required(allowed_roles=['admin'])
def assign_driver(request, request_id):
    waste_request = get_object_or_404(WasteRequest, id=request_id)
    drivers = DriverProfile.objects.filter(user__is_active=True)  # Fetch active drivers

    if request.method == "POST":
        driver_id = request.POST.get("driver")
        driver = get_object_or_404(User, id=driver_id)

        # Ensure the driver has a DriverProfile
        try:
            driver_profile = driver.driver_profile
        except DriverProfile.DoesNotExist:
            messages.error(request, f"Driver {driver.username} does not have a profile. Assign another driver.")
            return redirect("adminapp:manage_pending_requests")

        # Assign the driver to the waste request
        waste_request.driver = driver
        waste_request.save()  # Save the change without altering the status

        # Send an email notification to the driver
        subject_for_driver = "New Waste Collection Task Assigned"
        message_for_driver = (
            f"Hello {driver.username},\n\n"
            f"You have been assigned a new waste collection task.\n\n"
            f"Details:\n"
            f"Type of Waste: {waste_request.waste_type}\n"
            f"Quantity: {waste_request.quantity}\n"
            f"Collection Location: {waste_request.collection_location}\n"
            f"Collection Time: {waste_request.collection_time}\n\n"
            f"Click the link below to view the task in your dashboard:\n"
            f"{request.build_absolute_uri('/driverapp/dashboard/')}\n\n"
            f"Thank you,\n"
            f"Waste Management Team"
        )
        recipient_list_for_driver = [driver.email]

        subject_for_resident = "Waste Collection Request Accepted"
        message_for_resident = (
            f"Hey {waste_request.user.first_name},\n\n"
            f"Your request for {waste_request.waste_type} of {waste_request.quantity} at {waste_request.collection_location} on {waste_request.collection_time} has been accepted and assigned with a driver.\n\n"
            f"Driver Details: \n"
            f"Driver Name: {driver.get_full_name()} \n"
            f"Driver Email: {driver.email} \n"
            f"Click the link below to view the task in your dashboard:\n"
            f"{request.build_absolute_uri('/waste/my_requests/')}\n\n"
            f"Thank you,\n"
            f"Waste Management Team"
        )

        recipient_list_for_resident = [waste_request.user.email]

        from_email = settings.DEFAULT_FROM_EMAIL

        try:
            send_mail(subject_for_driver, message_for_driver, from_email, recipient_list_for_driver)
            send_mail(subject_for_resident, message_for_resident, from_email, recipient_list_for_resident)
            messages.success(request, f"Driver {driver.username} assigned successfully. Email notification sent.")
        except Exception as e:
            messages.error(request, f"Driver {driver.username} assigned successfully, but email failed to send. Error: {e}")

        return redirect("adminapp:manage_pending_requests")

    context = {"waste_request": waste_request, "drivers": drivers}
    return render(request, "adminapp/assign_driver.html", context)


@role_required(allowed_roles=['admin'])
def mark_as_completed(request, request_id):
    try:
        # Fetch the specific request by ID and verify it belongs to the logged-in user
        waste_request = WasteRequest.objects.get(id=request_id, status='Pending')
        waste_request.updated_at = timezone.now()
        waste_request.status = 'Completed'
        waste_request.save()
        messages.success(request, 'Request marked as completed.')
    except WasteRequest.DoesNotExist:
        messages.error(request, 'Request not found or already completed.')

    return redirect('adminapp:view_completed_requests')

# View for managing drivers
@role_required(allowed_roles=['admin'])
def manage_drivers(request):
    drivers = DriverProfile.objects.select_related('user').all()
    assigned_requests_count = WasteRequest.objects.filter(status="Assigned").count()
    context = {
        "drivers": drivers,
        "assigned_requests_count": assigned_requests_count
    }
    return render(request, "adminapp/manage_drivers.html", context)


def user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    unassigned_pending_count = user.waste_requests.filter(driver=None, status='Pending').count()
    completed_count = user.waste_requests.filter(status='Completed').count()

    recent_requests = user.waste_requests.order_by('-created_at')[:3]
    recent_payments = Payment.objects.filter(user=user).order_by('-paid_at')[:3]

    return render(request, 'adminapp/user_detail.html', {
        'user': user,
        'unassigned_pending_count': unassigned_pending_count,
        'completed_count': completed_count,
        'recent_requests': recent_requests,
        'recent_payments': recent_payments,
    })

def update_complaint_status(request):
    if request.method == 'POST':
        complaint_id = request.POST.get('complaint_id')
        status = request.POST.get('status')
        response = request.POST.get('response')
        complaint = get_object_or_404(Complaint, id=complaint_id)
        complaint.status = status
        complaint.response = response
        complaint.save()
        messages.success(request, "Complaint status updated successfully.")
    return redirect('adminapp:manage_pending_requests')  # or wherever you want

def is_admin(user):
    return user.is_staff or user.is_superuser

def tip_list(request):
    tips = WasteTip.objects.all().order_by('-created_at')
    return render(request, 'adminapp/tips/list.html', {'tips': tips})

@login_required
@user_passes_test(is_admin)
def tip_create(request):
    form = WasteTipForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Tip created successfully.")
        return redirect('adminapp:tip_list')
    return render(request, 'adminapp/tips/form.html', {'form': form, 'title': 'Create Tip'})

@login_required
@user_passes_test(is_admin)
def tip_edit(request, pk):
    tip = get_object_or_404(WasteTip, pk=pk)
    form = WasteTipForm(request.POST or None, instance=tip)
    if form.is_valid():
        form.save()
        messages.success(request, "Tip updated successfully.")
        return redirect('adminapp:tip_list')
    return render(request, 'adminapp/tips/form.html', {'form': form, 'title': 'Edit Tip'})

@login_required
@user_passes_test(is_admin)
def tip_delete(request, pk):
    tip = get_object_or_404(WasteTip, pk=pk)
    if request.method == 'POST':
        tip.delete()
        return redirect('adminapp:tip_list')
    return render(request, 'adminapp/tips/confirm_delete.html', {'tip': tip})


@login_required
@user_passes_test(is_admin)
def initiative_create(request):
    form = CommunityInitiativeForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('adminapp:initiative_list')
    return render(request, 'adminapp/initiatives/form.html', {'form': form, 'title': 'Create Initiative'})

@login_required
def initiative_list(request):
    initiatives = CommunityInitiative.objects.order_by('-start_date')
    return render(request, 'adminapp/initiatives/list.html', {'initiatives': initiatives})

def initiative_detail(request, initiative_id):
    initiative = get_object_or_404(CommunityInitiative, pk=initiative_id)
    attendees = UserCommunityInitiative.objects.filter(community_initiative=initiative).select_related('user')

    context = {
        'initiative': initiative,
        'attendees': attendees
    }

    return render(request, 'adminapp/initiatives/detail.html', context)
