from rest_framework import serializers
from Users.models import CustomUser
from django.contrib.auth import get_user_model

class RegisterAdminSerializer(serializers.ModelSerializer):

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
        validated_data.setdefault("is_admin", True)
        return CustomUser.objects.create(**validated_data)


class UserAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'first_name', 'last_name',]

User = get_user_model()

class ChangeAnyUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'password', 'is_admin']

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
