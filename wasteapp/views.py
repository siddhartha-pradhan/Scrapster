from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import WasteRequestForm
from .models import WasteRequest
from profileapp.models import Address
from account_app.decorators import role_required

# wasteapp/views.py
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse




@role_required(allowed_roles=['user'])
def submit_waste_request(request):
    # Check if the user has at least one saved address
    user_addresses = Address.objects.filter(user=request.user)
    if not user_addresses.exists():
        messages.error(request, "Please add at least one address before submitting a waste request.")
        return redirect('profileapp:add_address')  # Redirect to the "Add Address" page

    if request.method == 'POST':
        form = WasteRequestForm(request.POST, user=request.user)  # Pass user context to the form
        if form.is_valid():
            waste_request = form.save(commit=False)
            waste_request.user = request.user  # Associate the request with the logged-in user

            # Check if an address was selected
            if not form.cleaned_data.get('collection_location'):
                default_address = user_addresses.filter(default=True).first()
                if default_address:
                    waste_request.collection_location = default_address
                else:
                    messages.error(request, "No default address found. Please select an address.")
                    return redirect('wasteapp:submit_request')
            else:
                waste_request.collection_location = form.cleaned_data.get('collection_location')

            waste_request.save()

            # Send email notification to admin
            pending_requests_url = request.build_absolute_uri(reverse('adminapp:manage_pending_requests'))
            admin_email = "k9907485@gmail.com"  # Replace with admin email address
            send_mail(
                subject="New Waste Collection Request Submitted",
                message=f"A new waste collection request has been submitted. Check pending requests at {pending_requests_url}",
                from_email=settings.EMAIL_HOST_USER,
                recipient_list=[admin_email],
                fail_silently=False,
            )

            messages.success(request, 'Waste collection request submitted successfully!')
            return redirect('wasteapp:my_requests')
    else:
        form = WasteRequestForm(user=request.user)

    context = {'form': form}
    return render(request, 'wasteapp/submit_request.html', context)



@role_required(allowed_roles=['user'])
def my_requests(request):
    # Fetch only the pending requests of the logged-in user
    pending_requests = WasteRequest.objects.filter(user=request.user, status='Pending').order_by('-created_at')
    
    context = {'pending_requests': pending_requests}
    return render(request, 'wasteapp/my_requests.html', context)

@role_required(allowed_roles=['user'])
def mark_as_completed(request, request_id):
    try:
        # Fetch the specific request by ID and verify it belongs to the logged-in user
        waste_request = WasteRequest.objects.get(id=request_id, user=request.user, status='Pending')
        waste_request.status = 'Completed'
        waste_request.save()
        messages.success(request, 'Request marked as completed.')
    except WasteRequest.DoesNotExist:
        messages.error(request, 'Request not found or already completed.')

    return redirect('wasteapp:my_requests')


@role_required(allowed_roles=['user'])
def my_history(request):
    # Fetch only the completed requests of the logged-in user
    completed_requests = WasteRequest.objects.filter(user=request.user, status='Completed').order_by('-created_at')
    
    context = {'completed_requests': completed_requests}
    return render(request, 'wasteapp/my_history.html', context)