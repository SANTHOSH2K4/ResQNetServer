from rest_framework import serializers
from .models import AdminVerifierUser, AdminUser, AdminGroups, TodoTitle, SubTask

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get("email")
        password = data.get("password")
        try:
            user = AdminVerifierUser.objects.get(email=email)
            print("🔹 User:", user)
        except AdminVerifierUser.DoesNotExist:
            raise serializers.ValidationError("Invalid email or password.")
        
        # Manual validation: compare plain text password values
        if user.password != password:
            raise serializers.ValidationError("Invalid email or password.")

        data["user"] = user
        return data
    
class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminUser
        fields = "__all__"
        
    def create(self, validated_data):
        return AdminUser.objects.create(**validated_data)

class AdminGroupsSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdminGroups
        fields = "__all__"

class TodoTitleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TodoTitle
        fields = "__all__"

class SubTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubTask
        fields = "__all__"
