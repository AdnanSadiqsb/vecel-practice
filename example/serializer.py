from rest_framework import serializers

from .models import User



# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        exclude = ["groups", "user_permissions"]

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
class EmptySerializer(serializers.Serializer):
    pass
