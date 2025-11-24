from users.models import CV

def user_cv(request):
    # Context processor to add the user's CV to the template context
    if request.user.is_authenticated:
        try:
            return {"user_cv": CV.objects.get(user=request.user)}
        except CV.DoesNotExist:
            return {"user_cv": None}
    return {"user_cv": None}
