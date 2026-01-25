from users.models import CV

def user_cv(request):
    # Dodaje CV użytkownika do kontekstu szablonu, jeśli jest zalogowany
    if request.user.is_authenticated:
        try:
            return {"user_cv": CV.objects.get(user=request.user)}
        except CV.DoesNotExist:
            return {"user_cv": None}
    return {"user_cv": None}
