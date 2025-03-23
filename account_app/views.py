from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, LoginView
from profileapp.models import UserProfile
from django.urls import reverse_lazy
# Create your views here.

def home(request):
    return render(request, 'index.html')

class CustomLoginView(LoginView):
    template_name = 'login.html'


    def get_success_url(self):
        messages.success(self.request, "Login successful!")
        if self.request.user.is_superuser:
            return reverse_lazy('adminapp:dashboard')
        
        try:
            user_profile = UserProfile.objects.get(user=self.request.user)
            print(f"Logged-in user role: {user_profile.role}")
            
            if user_profile.role == 'driver':
                return reverse_lazy('driverapp:dashboard')
            else:
                return reverse_lazy('profileapp:user_profile')


        except UserProfile.DoesNotExist:
            print("No UserProfile found for the user.")
            return reverse_lazy('profileapp:user_profile')

    def form_invalid(self, form):
        messages.error(self.request, "Invalid username or password.")
        return super().form_invalid(form)

def RegisterView(request):
    # if request.method == "POST":
    #     username = request.POST.get('username')
    #     email = request.POST.get('email')
    #     first_name = request.POST.get('first_name')
    #     last_name = request.POST.get('last_name')
    #     password = request.POST.get('password')
    #     password_confirm = request.POST.get('password_confirm')
    #     role = request.POST.get('role')  # Capture the role field
    #
    #     print(f"Role selected: {role}")  # Debugging
    #
    #     if role == "admin":
    #         messages.error(request, "You cannot register as an admin.")
    #         return redirect('register_user')
    #
    #     if password != password_confirm:
    #         messages.error(request, "Passwords do not match.")
    #         return redirect('register_user')
    #
    #     if User.objects.filter(username=username).exists():
    #         messages.error(request, "Username already exists.")
    #         return redirect('register_user')
    #
    #     if User.objects.filter(email=email).exists():
    #         messages.error(request, "Email already exists.")
    #         return redirect('register_user')
    #
    #     # Create user
    #     try:
    #         user = User.objects.create_user(
    #             username=username,
    #             email=email,
    #             first_name=first_name,
    #             last_name=last_name,
    #             password=password
    #         )
    #
    #         # Ensure role is correctly set in the UserProfile
    #         user_profile, created = UserProfile.objects.get_or_create(user=user)
    #         user_profile.role = role
    #         user_profile.save()
    #
    #         messages.success(request, "Registration successful. Please log in.")
    #         return redirect('login_user')
    #
    #     except Exception as e:
    #         messages.error(request, f"Error: {e}")
    #         return redirect('register_user')

    return render(request, 'register.html')

def register_resident(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = "user"  # Capture the role field

        print(f"Role selected: {role}")  # Debugging

        if role == "admin":
            messages.error(request, "You cannot register as an admin.")
            return redirect('register_resident')

        if password != password_confirm:
            messages.error(request, "Passwords do not match.")
            return redirect('register_resident')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect('register_resident')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect('register_resident')

        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password
            )

            user_profile, created = UserProfile.objects.get_or_create(user=user)
            user_profile.role = role
            user_profile.save()

            messages.success(request,'Your resident account has been created successfully.')
            return redirect('login_user')

        except Exception as e:
            messages.error(request, f"Error: {e}")
            return redirect('register_user')


    return render(request, 'register_resident.html')

def register_employee(request):
    if request.method == 'POST':
        messages.success(request, 'Your employee application has been submitted! Our team will review it shortly.')
        return redirect('login_user')
    return render(request, 'register_employee.html')


def LogoutView(request):
    logout(request)
    return redirect("/login_user")

