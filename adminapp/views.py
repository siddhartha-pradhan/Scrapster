# adminapp/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from wasteapp.models import WasteRequest
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.models import User
from account_app.decorators import role_required
from driverapp.models import DriverProfile
from django.core.mail import send_mail
from django.conf import settings


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
    # Render the admin dashboard template with the context data
    return render(request, "adminapp/dashboard.html", context)



# View for managing pending waste requests
@role_required(allowed_roles=['admin'])
def manage_pending_requests(request):
    # Fetch all pending requests
    pending_requests = WasteRequest.objects.filter(status="Pending").order_by("-created_at")

    # Separate requests into unassigned and assigned categories
    unassigned_requests = pending_requests.filter(driver__isnull=True)
    assigned_requests = pending_requests.filter(driver__isnull=False)

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
    # Fetch all completed waste requests ordered by creation date
    completed_requests = WasteRequest.objects.filter(status="Completed").order_by("-created_at")  # Get completed requests in descending order of creation date
    # Create a context dictionary to pass data to the template
    context = {"completed_requests": completed_requests}
    # Render the completed requests template with the context data
    return render(request, "adminapp/completed_requests.html", context)




# View for managing users
# View for managing users (excluding superusers and drivers)
@role_required(allowed_roles=['admin'])
def manage_users(request):
    # Fetch all users excluding superusers and drivers
    users = User.objects.filter(is_superuser=False).exclude(driver_profile__isnull=False)
    # Prepare context
    context = {"users": users}
    # Render the manage_users template
    return render(request, "adminapp/manage_users.html", context)



# View for toggling a user's active status
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
        subject = "New Waste Collection Task Assigned"
        message = (
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
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [driver.email]
        print(driver.email)
        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, f"Driver {driver.username} assigned successfully. Email notification sent.")
        except Exception as e:
            messages.error(request, f"Driver {driver.username} assigned successfully, but email failed to send. Error: {e}")

        return redirect("adminapp:manage_pending_requests")

    context = {"waste_request": waste_request, "drivers": drivers}
    return render(request, "adminapp/assign_driver.html", context)



# View for managing drivers
@role_required(allowed_roles=['admin'])
def manage_drivers(request):
    # Fetch all drivers with an associated DriverProfile
    drivers = DriverProfile.objects.select_related('user').all()
    # Prepare context
    context = {"drivers": drivers}
    # Render the manage_drivers template
    return render(request, "adminapp/manage_drivers.html", context)


# adminapp/views.py




def user_detail(request, user_id):
    """Fetch and return user details."""
    user = get_object_or_404(User, id=user_id)
    return render(request, 'adminapp/user_detail.html', {'user': user})
