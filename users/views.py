from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import render
from django.contrib.auth import get_user_model, authenticate, login
from django.views.decorators.csrf import csrf_exempt
from .utils import generate_otp, send_verification_email, send_forgot_password_email
import json
from datetime import datetime, timedelta
from rest_framework.authtoken.models import Token

User = get_user_model()

def current_time_view(request):
   
    current_time = timezone.now().time()
    if request.user.is_authenticated:
        user_type = request.user.get_type_display()
        return HttpResponse(f"Current server time: {current_time} for {user_type} user")
    return HttpResponse(f"Current server time: {current_time}")

@csrf_exempt
def register_user(request):
   
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            email = data.get('email')
            password = data.get('password')
            user_type = data.get('type')
            name = data.get('name')

            if not phone_number or not email or not password or not user_type:
                return JsonResponse({'error': 'Missing required fields'}, status=400)
            
            if user_type not in ['artisan', 'buyer']:
                return JsonResponse({'error': 'Invalid user type. Must be artisan or buyer'}, status=400)
            
            if User.objects.filter(phone_number=phone_number).exists():
                return JsonResponse({'error': 'Phone number already exists'}, status=400)
            
            if User.objects.filter(email=email).exists():
                return JsonResponse({'error': 'Email already exists'}, status=400)

            user = User.objects.create_user(
                phone_number=phone_number,
                email=email,
                password=password,
                type=user_type,
                name=name,
                is_active=False  
            )

            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()

            send_verification_email(email, otp)
            return JsonResponse({'message': 'User registered. Verification email sent'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def login_user(request):
   
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            phone_number = data.get('phone_number')
            password = data.get('password')

            if not phone_number or not password:
                return JsonResponse({'error': 'Missing phone_number or password'}, status=400)

            user = authenticate(request, phone_number=phone_number, password=password)
            if user is None:
                return JsonResponse({'error': 'Invalid phone number or password'}, status=401)
            
            if not user.is_active:
                return JsonResponse({'error': 'Account not verified. Please verify your email'}, status=403)

            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return JsonResponse({
                'message': 'Login successful',
                'token': token.key,
                'user': {
                    'phone_number': user.phone_number,
                    'email': user.email,
                    'type': user.type,
                    'name': user.name
                }
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def request_verification_email(request):
  
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'User with this email does not exist'}, status=404)
            
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            send_verification_email(email, otp)
            return JsonResponse({'message': 'Verification email sent'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def verify_email(request):
  
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            otp = data.get('otp')
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'User with this email does not exist'}, status=404)
            
            if user.otp != otp or (timezone.now() - user.otp_created_at) > timedelta(minutes=5):
                return JsonResponse({'error': 'Invalid or expired OTP'}, status=400)
            
            user.is_active = True
            user.otp = None
            user.otp_created_at = None
            user.save()
            return JsonResponse({'message': 'Email verified successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def request_password_reset(request):
  
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'User with this email does not exist'}, status=404)
            
            otp = generate_otp()
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            
            send_forgot_password_email(email, otp)
            return JsonResponse({'message': 'Password reset email sent'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
def reset_password(request):
   
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            otp = data.get('otp')
            new_password = data.get('new_password')
            user = User.objects.filter(email=email).first()
            if not user:
                return JsonResponse({'error': 'User with this email does not exist'}, status=404)
            
            if user.otp != otp or (timezone.now() - user.otp_created_at) > timedelta(minutes=5):
                return JsonResponse({'error': 'Invalid or expired OTP'}, status=400)
            
            user.set_password(new_password)
            user.otp = None
            user.otp_created_at = None
            user.save()
            return JsonResponse({'message': 'Password reset successfully'})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Invalid request method'}, status=405)