from rest_framework import serializers
from .models import AdminVerifierUser, AdminUser, AdminGroups, TodoTitle, SubTask, GeneralUser, VolunteerRequests

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
    
class GroupSerializer(serializers.ModelSerializer):
    # Use a SerializerMethodField to compute if the logged-in user (by phone) is in allowed_volunteers.
    isvolunteer = serializers.SerializerMethodField()
    
    class Meta:
        model = AdminGroups
        # Use the admin field directly (it will be represented as the admin's primary key)
        fields = ('id', 'group_name', 'created_on', 'admin', 'isvolunteer', 'city')
    
    def get_isvolunteer(self, obj):
        phone = self.context.get('phone')
        # Returns True if a volunteer with the given phone exists in allowed_volunteers
        return obj.allowed_volunteers.filter(mobile_number=phone).exists()

class VolunteerRequestsSerializer(serializers.ModelSerializer):
    volunteer_id = serializers.IntegerField(source='volunteer.id', read_only=True)
    group_id = serializers.IntegerField(source='group.id', read_only=True)
    
    class Meta:
        model = VolunteerRequests
        fields = ('id', 'volunteer_id', 'group_id', 'requested_at')

    
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
        
class GeneralUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneralUser
        # Only include the fields you expect from the registration form
        fields = ['full_name', 'email', 'mobile_number', 'street_address', 'city', 'state', 'is_volunteer']

