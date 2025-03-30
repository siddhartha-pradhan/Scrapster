from django.db import models
from django.contrib.auth.models import User
from profileapp.models import Address

WASTE_TYPES = [
    ('Plastic', 'Plastic'),
    ('Organic', 'Organic'),
    ('Electronic', 'Electronic'),
    ('Metal', 'Metal'),
    ('Paper', 'Paper'),
]

class WasteRequest(models.Model):
    user = models.ForeignKey(User, related_name='waste_requests', on_delete=models.CASCADE)
    waste_type = models.CharField(max_length=50, choices=WASTE_TYPES)
    quantity = models.PositiveIntegerField(help_text="Enter quantity in kg")
    collection_time = models.DateTimeField()
    collection_location = models.ForeignKey('profileapp.Address', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, default='Pending', choices=[('Pending', 'Pending'), ('Completed', 'Completed')])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(null=True, blank=True,)
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_tasks")

    def __str__(self):
        return f"{self.user.username} - {self.waste_type} - ({self.status})"

class Complaint(models.Model):
    COMPLAINT_CATEGORIES = [
        ('Delay', 'Delay in collection'),
        ('Missed', 'Missed pickup'),
        ('Rude', 'Rude behavior'),
        ('Other', 'Other'),
    ]

    COMPLAINT_STATUS = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, related_name='complaints', on_delete=models.CASCADE)
    waste_request = models.ForeignKey('WasteRequest', related_name='complaints', on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=COMPLAINT_CATEGORIES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=COMPLAINT_STATUS, default='Pending')
    response = models.TextField(blank=True, null=True, help_text="Admin/driver response to the complaint.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Complaint by {self.user.username} - {self.get_category_display()} ({self.status})"