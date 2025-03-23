from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DriverProfileForm
from .models import DriverProfile
from account_app.decorators import role_required  # Import the existing role-based decorator
from wasteapp.models import WasteRequest
from django.shortcuts import get_object_or_404


@role_required(allowed_roles=['driver'])  # Allow only users with the 'driver' role
def driver_profile(request):
    # Check if the driver already has a profile
    try:
        profile = request.user.driver_profile
        form = DriverProfileForm(instance=profile)
    except DriverProfile.DoesNotExist:
        form = DriverProfileForm()

    if request.method == 'POST':
        form = DriverProfileForm(request.POST, instance=request.user.driver_profile if hasattr(request.user, 'driver_profile') else None)
        if form.is_valid():
            driver_profile = form.save(commit=False)
            driver_profile.user = request.user
            driver_profile.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('driverapp:dashboard')

    return render(request, 'driverapp/driver_profile.html', {'form': form})


from django.utils.timezone import now

@role_required(allowed_roles=['driver'])
def driver_dashboard(request):
    # Fetch the driver's assigned tasks, sorted by nearest collection time
    assigned_tasks = WasteRequest.objects.filter(
        driver=request.user, status="Pending"
    ).order_by("collection_time")

    # Fetch the tasks completed by the driver
    completed_tasks = WasteRequest.objects.filter(
        driver=request.user, status="Completed"
    )  # Most recently completed tasks first

    context = {
        "assigned_tasks": assigned_tasks,
        "completed_tasks": completed_tasks,
    }
    return render(request, "driverapp/driver_dashboard.html", context)




@role_required(allowed_roles=['user'])
def view_driver_details(request, driver_id):
    # Fetch the driver's profile using their ID
    driver_profile = get_object_or_404(DriverProfile, user_id=driver_id)

    return render(request, 'driverapp/driver_details.html', {
        'driver_profile': driver_profile
    })
