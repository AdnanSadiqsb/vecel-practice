from rest_framework import serializers

from .models import User


# Serializers define the API representation.
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"
