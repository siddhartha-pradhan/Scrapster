from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.template.loader import render_to_string

from .forms import WasteRequestForm
from .models import WasteRequest, Complaint, Payment
from profileapp.models import Address
from account_app.decorators import role_required

# wasteapp/views.py
from django.core.mail import send_mail, EmailMessage
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
            admin_email = "siddhartha.pradhan.ix@gmail.com"  # Replace with admin email address
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

from django.utils import timezone

@role_required(allowed_roles=['user'])
def my_requests(request):
    pending_requests = WasteRequest.objects.filter(user=request.user, status='Pending').order_by('-created_at')

    for waste_request in pending_requests:
        waste_request.can_mark_complete = waste_request.driver is not None
        waste_request.is_overdue = waste_request.collection_time < timezone.now()

        complaint = Complaint.objects.filter(waste_request=waste_request).first()
        waste_request.complaint = complaint  # will be None if not found

    context = {'pending_requests': pending_requests}
    return render(request, 'wasteapp/my_requests.html', context)

from django.utils import timezone

@role_required(allowed_roles=['user'])
def mark_as_completed(request, request_id):
    try:
        # Fetch the specific request by ID and verify it belongs to the logged-in user
        waste_request = WasteRequest.objects.get(id=request_id, user=request.user, status='Pending')
        waste_request.updated_at = timezone.now()
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

    for waste_request in completed_requests:
        complaint = Complaint.objects.filter(waste_request=waste_request).first()
        waste_request.complaint = complaint  # will be None if not found

    total_waste = 0
    total_collections = completed_requests.count()
    total_co2_saved = 0
    total_trees_saved = 0
    total_water_saved = 0
    total_oil_saved = 0
    prevented_toxic = False

    for req in completed_requests:
        qty = req.quantity
        total_waste += qty

        if req.waste_type == 'Paper':
            total_trees_saved += qty * 1.0  # Let's say 1kg paper = 1 tree saved
            total_water_saved += qty * 1.0  # 1kg = 1 gallon water
        elif req.waste_type == 'Plastic':
            total_oil_saved += qty * 1.0  # 1kg = 1 gallon of oil
            total_co2_saved += qty * 1.0
        elif req.waste_type in ['Metal', 'Glass']:
            total_co2_saved += qty * 1.0
        elif req.waste_type == 'E-waste':
            total_co2_saved += qty * 1.0
            prevented_toxic = True

    context = {
        'completed_requests': completed_requests,
        'total_collections': total_collections,
        'total_waste': total_waste,
        'total_co2_saved': total_co2_saved,
        'total_trees_saved': total_trees_saved,
        'total_water_saved': total_water_saved,
        'total_oil_saved': total_oil_saved,
        'prevented_toxic': prevented_toxic,
    }

    return render(request, 'wasteapp/my_history.html', context)

import requests
from django.shortcuts import render
def fetch_environmental_tips():
    url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/NewsSearchAPI"
    querystring = {"q":"waste management tips","pageNumber":"1","pageSize":"5","autoCorrect":"true"}

    headers = {
        "X-RapidAPI-Key": "YOUR_RAPIDAPI_KEY",
        "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    if response.status_code == 200:
        data = response.json()
        return data.get("value", [])  # List of articles
    return []

def tips_page(request):
    tips = fetch_environmental_tips()
    return render(request, 'tips/tips_page.html', {'tips': tips})

@role_required(allowed_roles=['user'])
def submit_complaint(request):
    waste_request_id = request.POST.get('waste_request_id')
    category = request.POST.get('category')
    description = request.POST.get('description')

    try:
        waste_request = WasteRequest.objects.get(id=waste_request_id, user=request.user)
    except WasteRequest.DoesNotExist:
        messages.error(request, "Invalid waste request.")
        return redirect('wasteapp:my_requests')

    Complaint.objects.create(
        user=request.user,
        waste_request=waste_request,
        category=category,
        description=description
    )

    messages.success(request, "Complaint submitted successfully.")
    return redirect('wasteapp:my_requests')


@role_required(allowed_roles=['user'])
def payment_details(request):
    payments = Payment.objects.filter(user=request.user).order_by('-payment_for')

    if payments.exists():
        latest_payment_date = payments.first().payment_for
        next_payment_date = get_next_month(latest_payment_date)
    else:
        today = date.today()
        next_payment_date = date(today.year, today.month, 1)

    context = {
        'payments': payments,
        'next_payment_date': next_payment_date,
    }
    return render(request, 'wasteapp/payment_details.html', context)

from datetime import date

def get_next_month(first_of_month: date):
    year = first_of_month.year
    month = first_of_month.month
    if month == 12:
        return date(year + 1, 1, 1)
    else:
        return date(year, month + 1, 1)

def get_next_payment_date(user):
    payments = Payment.objects.filter(user=user).order_by('-payment_for')
    if payments.exists():
        last_payment = payments.first().payment_for
        return get_next_month(last_payment)
    else:
        today = date.today()
        return date(today.year, today.month, 1)

import uuid

@login_required
def initiate_payment(request):
    if request.method == 'POST':
        customer_name = f"{request.user.first_name} {request.user.last_name}".strip()
        customer_email = request.user.email

        url = "https://dev.khalti.com/api/v2/epayment/initiate/"
        payload = {
            "return_url": settings.KHALTI_RETURN_URL,
            "website_url": settings.KHALTI_WEBSITE_URL,
            "amount": int(float(500)),
            "purchase_order_id": str(uuid.uuid4()),
            "purchase_order_name": "Order Payment",
            "customer_info": {
                "name": customer_name,
                "email": customer_email,
                "phone": "9800000000",  # Replace with dynamic phone if available
            },
            "amount_breakdown": [
                {
                    "label": "Mark Price",
                    "amount": int(float(443))
                },
                {
                    "label": "VAT",
                    "amount": int(float(57))
                }
            ],
        }

        headers = {
            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers)
        response_data = response.json()

        if response.status_code == 200 and "payment_url" in response_data:
            return redirect(response_data["payment_url"])
        else:
            return JsonResponse({
                "success": False,
                "message": response_data.get("detail", "Error in payment initiation")
            })

def khalti_payment_success(request):
    pidx = request.GET.get("pidx")

    if not pidx:
        return JsonResponse({"error": "Missing pidx"}, status=400)

    response = requests.post(
        "https://dev.khalti.com/api/v2/epayment/lookup/",
        json={"pidx": pidx},
        headers={
            "Authorization": f"Key {settings.KHALTI_SECRET_KEY}",
            "Content-Type": "application/json"
        }
    )

    if response.status_code != 200:
        return JsonResponse({"error": "Khalti API call failed"}, status=500)

    payment_data = response.json()
    status = payment_data.get("status")
    order_id = request.GET.get("purchase_order_id")
    transaction_id = request.GET.get("transaction_id")

    if status == "Completed":
        user = request.user
        next_payment_date = get_next_payment_date(user)

        # Double-check to avoid duplicates
        if Payment.objects.filter(user=user, payment_for=next_payment_date).exists():
            messages.warning(request, f"Payment for {next_payment_date.strftime('%B %Y')} already exists.")
            return redirect('wasteapp:payment_details')

        # Create the payment (set amount as needed)
        Payment.objects.create(
            user=user,
            payment_for=next_payment_date,
            amount=500.00  # 👈 Replace with your actual logic or dynamic value
        )

        messages.success(request, f"Payment for {next_payment_date.strftime('%B %Y')} completed successfully.")

        mail_subject = f"Payment Received for {next_payment_date.strftime('%B %Y')}"
        message = (
            f"Dear {user.first_name or user.username},\n\n"
            f"We've successfully received your payment of रु500.00 for the month of {next_payment_date.strftime('%B %Y')}.\n\n"
            f"Thank you for staying up to date with your waste management payments.\n\n"
            f"Best regards,\n"
            f"The Waste Management Team"
        )
        to_email = user.email
        send_email = EmailMessage(mail_subject, message, to=[to_email], from_email=settings.EMAIL_ROOT_EMAIL)
        send_email.send()
        print("Sent mail success")

        return redirect('wasteapp:payment_details')
    elif status in ["Pending", "Initiated"]:
        return redirect('wasteapp:payment_details')
    else:
        return redirect('wasteapp:payment_details')
