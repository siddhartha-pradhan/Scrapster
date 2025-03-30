from django.urls import path
from .views import submit_waste_request, my_requests, mark_as_completed, user_initiative_list, toggle_initiative_participation, my_history, submit_complaint, payment_details, tip_details, khalti_payment_success, initiate_payment

app_name = 'wasteapp'

urlpatterns = [
    path('submit/', submit_waste_request, name='submit_request'),
    path('my_requests/', my_requests, name='my_requests'),
    path('mark_as_completed/<int:request_id>/', mark_as_completed, name='mark_as_completed'),
    path('my_history/', my_history, name='my_history'),
    path('submit-complaint/', submit_complaint, name='submit_complaint'),
    path('payment-details/', payment_details, name='payment_details'),
    path('tip-details/', tip_details, name='tip_details'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('initiate-payment/', initiate_payment, name='initiate_payment'),
    path('khalti-payment-success/', khalti_payment_success, name='khalti_payment_success'),
    path('initiatives/', user_initiative_list, name='user_initiative_list'),
    path('initiatives/<int:initiative_id>/toggle/', toggle_initiative_participation, name='toggle_initiative_participation'),

]
