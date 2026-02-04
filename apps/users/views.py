# apps/users/views.py
from django.http import JsonResponse

def user_list(request):
    """Простой view для тестирования"""
    return JsonResponse({'message': 'Users API works!'})