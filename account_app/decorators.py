from django.shortcuts import redirect
from django.http import HttpResponseForbidden

def role_required(allowed_roles=[]):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if request.user.is_authenticated:
                if request.user.is_superuser:
                    if 'admin' in allowed_roles:
                        return view_func(request, *args, **kwargs)
                    else:
                        return HttpResponseForbidden("Admins cannot access this page.")
                
                if hasattr(request.user, 'userprofile') and request.user.userprofile.role in allowed_roles:
                    return view_func(request, *args, **kwargs)
                else:
                    return HttpResponseForbidden("You do not have permission to access this page.")
            else:
                return redirect('login_user')
        return _wrapped_view
    return decorator