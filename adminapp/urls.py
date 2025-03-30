from django.urls import path
from . import views
from .views import manage_users, toggle_user_status, delete_user

app_name = "adminapp"

urlpatterns = [
    # Dashboard
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    
    # Pending Requests
    path("pending-requests/", views.manage_pending_requests, name="manage_pending_requests"),
    path("pending-requests/approve/<int:request_id>/", views.approve_request, name="approve_request"),
    path("pending-requests/reject/<int:request_id>/", views.reject_request, name="reject_request"),
    
    # Completed Requests
    path("completed-requests/", views.view_completed_requests, name="view_completed_requests"),
    path("manage_users/", manage_users, name="manage_users"),
    path("toggle_user_status/<int:user_id>/", toggle_user_status, name="toggle_user_status"),
    path("delete_user/<int:user_id>/", delete_user, name="delete_user"),
    path("assign-driver/<int:request_id>/", views.assign_driver, name="assign_driver"),
    path('mark_as_completed/<int:request_id>/', views.mark_as_completed, name='mark_as_completed'),
    path("manage_drivers/", views.manage_drivers, name="manage_drivers"),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('update-complaint-status/', views.update_complaint_status, name='update_complaint_status'),
    path('tips/', views.tip_list, name='tip_list'),
    path('tips/create/', views.tip_create, name='tip_create'),
    path('tips/<int:pk>/edit/', views.tip_edit, name='tip_edit'),
    path('tips/<int:pk>/delete/', views.tip_delete, name='tip_delete'),
    path('initiatives/', views.initiative_list, name='initiative_list'),
    path('initiatives/create/', views.initiative_create, name='initiative_create'),
    path('initiatives/<int:initiative_id>/', views.initiative_detail, name='initiative_detail'),
]
