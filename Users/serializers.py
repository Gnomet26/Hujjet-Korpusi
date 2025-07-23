from rest_framework import serializers
from .models import CustomUser

class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'username', 'password')

    def create(self, validated_data):

        if not validated_data.get('first_name'):
            raise serializers.ValidationError("Ism kiritilishi kerak")
        if not validated_data.get('last_name'):
            raise serializers.ValidationError("Familya kiritilishi kerak")
        if not validated_data.get('username'):
            raise serializers.ValidationError("Username kiritilishi kerak")
        if not validated_data.get('password'):
            raise serializers.ValidationError("Parol kiritilishi kerak")

        validated_data.setdefault("is_staff", False)
        validated_data.setdefault("is_superuser", False)
        validated_data.setdefault("is_active", True)
        return CustomUser.objects.create(**validated_data)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=20)
    password = serializers.CharField(max_length = 20)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')

        if username:
            user = CustomUser.objects.filter(username = username).first()
            if user:
                if user.check_password(password):
                    return user
                raise serializers.ValidationError("Parol xato, qaytadan urinib ko'ring")
            raise serializers.ValidationError("Bunday foydalanuvchi mavjud emas")
        raise serializers.ValidationError("Usernameni kiriting")
    
class ReadUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'username']

class ChangeUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'password']

    def update(self, instance, validated_data):
        
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
