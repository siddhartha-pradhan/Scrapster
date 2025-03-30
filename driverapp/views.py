from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import DriverProfileForm
from .models import DriverProfile
from account_app.decorators import role_required
from wasteapp.models import WasteRequest
from django.shortcuts import get_object_or_404

@role_required(allowed_roles=['driver'])
def driver_profile(request):
    try:
        profile = request.user.driver_profile
        form = DriverProfileForm(instance=profile)
    except DriverProfile.DoesNotExist:
        form = DriverProfileForm()

    if request.method == 'POST':
        form = DriverProfileForm(request.POST, instance=request.user.driver_profile if hasattr(request.user, 'driver_profile') else None)
        if form.is_valid():
            driver_profile_details = form.save(commit=False)
            driver_profile_details.user = request.user
            driver_profile_details.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('driverapp:dashboard')

    return render(request, 'driverapp/profile.html', {'form': form})

from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum
from datetime import datetime, timedelta

@role_required(allowed_roles=['driver'])
def driver_dashboard(request):
    driver = request.user

    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)
    yesterday = today - timedelta(days=1)

    assigned_requests = WasteRequest.objects.filter(
        driver=driver,
        status='Pending'
    ).order_by('collection_time')

    todays_pickups = assigned_requests.filter(
        collection_time__date=today
    )

    upcoming_pickups = assigned_requests.filter(
        collection_time__date__gt=today
    )

    completed_pickups = WasteRequest.objects.filter(
        driver=driver,
        status='Completed'
    ).order_by('-updated_at')[:5]

    total_assigned = assigned_requests.count()
    total_completed = WasteRequest.objects.filter(
        driver=driver,
        status='Completed'
    ).count()

    total_waste_collected = WasteRequest.objects.filter(
        driver=driver,
        status='Completed'
    ).aggregate(total=Sum('quantity'))['total'] or 0

    waste_by_type = WasteRequest.objects.filter(
        driver=driver,
        status='Completed'
    ).values('waste_type').annotate(
        total=Sum('quantity')
    ).order_by('-total')

    last_week = today - timedelta(days=7)
    pickups_by_day = WasteRequest.objects.filter(
        driver=driver,
        status='Completed',
        updated_at__date__gte=last_week
    ).values('updated_at__date').annotate(
        count=Count('id')
    ).order_by('updated_at__date')

    pickups_by_day_formatted = []
    for pickup in pickups_by_day:
        date = pickup['updated_at__date']
        pickups_by_day_formatted.append({
            'date': date.strftime('%a'),
            'count': pickup['count']
        })

    context = {
        'assigned_requests': assigned_requests,
        'todays_pickups': todays_pickups,
        'upcoming_pickups': upcoming_pickups,
        'completed_pickups': completed_pickups,
        'total_assigned': total_assigned,
        'total_completed': total_completed,
        'total_waste_collected': total_waste_collected,
        'waste_by_type': waste_by_type,
        'pickups_by_day': pickups_by_day_formatted,
        'today': today,
    }

    return render(request, 'driverapp/dashboard.html', context)

@role_required(allowed_roles=['driver'])
def request_details(request):
    return render(request, 'driverapp/request_details.html')
