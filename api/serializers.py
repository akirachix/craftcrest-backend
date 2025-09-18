from django.core.validators import validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from rest_framework.authtoken.models import Token
from users.models import User, ArtisanPortfolio, Profile, PortfolioImage
from users.utils import send_otp_email


class PortfolioImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioImage
        fields = ["id", "image"]
        read_only_fields = ["id"]

class ArtisanPortfolioSerializer(serializers.ModelSerializer):
    image_files = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True,
        required=True,
        min_length=10 
    )
    images = PortfolioImageSerializer(many=True, read_only=True)

    class Meta:
        model = ArtisanPortfolio
        fields = ["id", "title", "description", "created_at", "image_files", "images", "artisan"]
        read_only_fields = ["id", "created_at", "images", "artisan"]

    def create(self, validated_data):
        image_files = validated_data.pop("image_files", [])
        artisan = validated_data.pop("artisan", None)  
        if artisan is None:
            raise serializers.ValidationError({"artisan": "Artisan is required to create a portfolio."})
        portfolio = ArtisanPortfolio.objects.create(artisan=artisan, **validated_data)
        for image_file in image_files:
            PortfolioImage.objects.create(portfolio=portfolio, image=image_file)
        return portfolio

    def validate(self, attrs):
        if not attrs.get("title"):
            raise serializers.ValidationError({"title": "Title is required."})
        if not attrs.get("description"):
            raise serializers.ValidationError({"description": "Description is required."})
        image_files = attrs.get("image_files", [])
        if len(image_files) < 10:
            raise serializers.ValidationError({
                "image_files": "At least 10 images are required for the portfolio."
            })
        return attrs


class UserRegistrationSerializer(serializers.ModelSerializer):
    token = serializers.SerializerMethodField(read_only=True)
    password = serializers.CharField(write_only=True, required=True)
    portfolio = ArtisanPortfolioSerializer(write_only=True, required=False)
    latitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    longitude = serializers.DecimalField(
        max_digits=9, decimal_places=6, required=False, allow_null=True
    )
    national_id = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="National ID already exists.")]
    )
    phone_number = serializers.CharField(
        required=True,
        validators=[UniqueValidator(queryset=User.objects.all(), message="Phone number already exists.")]
    )
    image = serializers.ImageField(required=False, allow_null=True)
    
    class Meta:
        model = User
        fields = [
            "id", "token", "email", "password", "first_name", "last_name",
            "user_type", "phone_number", "image",
            "latitude", "longitude", "national_id", "portfolio"
        ]
        read_only_fields = ["id", "token"]

    def get_token(self, obj):
        token, _ = Token.objects.get_or_create(user=obj)
        return token.key

    def validate_email(self, value):
        validate_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_phone_number(self, value):
        if not value.isdigit() or len(value) != 10:
            raise serializers.ValidationError("Phone number must be exactly 10 digits.")
        return value

    def validate(self, attrs):
        user_type = attrs.get("user_type")
        required_fields = ["email", "password", "first_name", "last_name", "phone_number", "user_type"]
        missing = [f for f in required_fields if not attrs.get(f)]
        if missing:
            raise serializers.ValidationError({f: "This field is required." for f in missing})
        if user_type == User.ARTISAN:
            portfolio_data = attrs.get("portfolio")
            if not portfolio_data:
                raise serializers.ValidationError({
                    "portfolio": "Artisans must provide a portfolio with at least 10 images."
                })
            portfolio_serializer = ArtisanPortfolioSerializer(data=portfolio_data)
            portfolio_serializer.is_valid(raise_exception=True)
            attrs["portfolio"] = portfolio_serializer.validated_data
            if not attrs.get("national_id"):
                raise serializers.ValidationError({"national_id": "National ID is required for artisans."})
            if attrs.get("latitude") is None or attrs.get("longitude") is None:
                raise serializers.ValidationError({
                    "latitude": "Latitude is required for artisans.",
                    "longitude": "Longitude is required for artisans."
                })
        elif user_type == User.BUYER:
            attrs["portfolio"] = None
            attrs["national_id"] = None
            attrs["latitude"] = None
            attrs["longitude"] = None
        return attrs

    def create(self, validated_data):
        portfolio_data = validated_data.pop("portfolio", None)
        password = validated_data.pop("password")
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.is_active = False
        user.save()
        if user.user_type == User.ARTISAN and portfolio_data:
            portfolio_serializer = ArtisanPortfolioSerializer(data=portfolio_data)
            portfolio_serializer.is_valid(raise_exception=True)
            portfolio_serializer.save(artisan=user)   
        user.generate_otp()
        send_otp_email(user.email, user.otp, purpose='verify')
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        phone_number = data.get("phone_number")
        password = data.get("password")

        if (email and phone_number) or (not email and not phone_number):
            raise serializers.ValidationError({"non_field_errors": "Must provide either email or phone number, but not both."})

        if not password:
            raise serializers.ValidationError({"non_field_errors": "Must provide password."})

        try:
            if email:
                user = User.objects.get(email=email)
            else:
                user = User.objects.get(phone_number=phone_number)
        except User.DoesNotExist:
            raise serializers.ValidationError({"non_field_errors": "Invalid email/phone or password."})

        if not user.is_active or not user.check_password(password):
            raise serializers.ValidationError({"non_field_errors": "Invalid email/phone or password."})

        token, _ = Token.objects.get_or_create(user=user)
        data["user"] = user
        data["token"] = token.key
        return data

class CustomUserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    image = serializers.ImageField(read_only=True)

    class Meta:
        model = User
        fields = ["email", "full_name", "phone_number", "image", "user_type"]
        read_only_fields = ["email", "user_type", "image"]

    def get_full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip()

class ProfileSerializer(serializers.ModelSerializer):
    user = CustomUserSerializer(read_only=True)
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = Profile
        fields = ["id", "user", "image"]
        read_only_fields = ["id", "user"]

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        try:
            user.generate_otp()
            send_otp_email(user.email, user.otp, purpose='reset')
        except Exception as e:
            raise serializers.ValidationError(f"Failed to send OTP email: {str(e)}")
        return value

class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if not user.otp or user.otp != data["otp"]:
            raise serializers.ValidationError({"otp": "Invalid OTP."})
        if not user.otp_exp or user.otp_exp < timezone.now():
            raise serializers.ValidationError({"otp": "OTP has expired."})
        user.otp_verified = True
        user.is_active = True
        user.otp = None
        user.otp_exp = None
        user.save(update_fields=["otp_verified", "is_active", "otp", "otp_exp"])
        return data

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User not found."})
        if user.is_active:
            raise serializers.ValidationError({"email": "This account is already verified."})
        user.generate_otp()
        send_otp_email(user.email, user.otp, purpose='verify')
        return {"message": "A new OTP has been sent to your email."}

class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data.get("new_password") != data.get("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords must match."})
        try:
            user = User.objects.get(email=data["email"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"email": "User with this email does not exist."})
        if not user.otp_verified:
            raise serializers.ValidationError({"email": "OTP not verified."})
        try:
            validate_password(data["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return data

    def save(self, **kwargs):
        user = User.objects.get(email=self.validated_data["email"])
        user.set_password(self.validated_data["new_password"])
        user.otp = None
        user.otp_exp = None
        user.otp_verified = False
        user.save()
        return user