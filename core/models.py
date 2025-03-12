from django.db import models
from django.utils import timezone

class VolunteerRequests(models.Model):

    volunteer = models.ForeignKey(
        'GeneralUser',
        on_delete=models.CASCADE,
        related_name='volunteer_requests'
    )
    group = models.ForeignKey(
        'AdminGroups',
        on_delete=models.CASCADE,
        related_name='group_requests'
    )
    phone = models.CharField(max_length=20)
    address = models.TextField()
    requested_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.volunteer.email} - {self.group.group_name} "


class AdminVerifierUser(models.Model):
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128)  # Store hashed passwords

    def __str__(self):
        return self.email
    
class AdminUser(models.Model):
    name = models.CharField(max_length=255)  # User's name
    mobile_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    
    # New fields
    job = models.CharField(max_length=255, blank=True, null=True)
    gender = models.CharField(max_length=20, blank=True, null=True)
    
    dob = models.DateField(blank=True, null=True)  # Added Date of Birth field
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    
    address = models.TextField(blank=True, null=True)
    
    # Identity Verification (Merged Documents)
    merged_documents = models.FileField(upload_to='identity_documents/', blank=True, null=True)
    
    # Disaster Response Role
    reason_for_admin_request = models.TextField()
    past_experience = models.TextField()
    affiliation = models.CharField(max_length=255, blank=True, null=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=255, blank=True, null=True)
    emergency_contact_relationship = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True, null=True)
    emergency_contact_address = models.TextField(blank=True, null=True)
    emergency_contact_alternate_number = models.CharField(max_length=15, blank=True, null=True)  # New field for alternate number
    
    # Digital Verification
    live_selfie_capture = models.ImageField(upload_to='selfie_verification/', blank=True, null=True)
    signature_upload = models.ImageField(upload_to='signatures/', blank=True, null=True)
    
    # Verified field
    verified = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.email
    
class GeneralUser(models.Model):
    full_name = models.CharField(max_length=255, help_text="User's full name")
    email = models.EmailField(unique=True, help_text="User's email address")
    mobile_number = models.CharField(max_length=15, unique=True, help_text="Mobile number with country code")
    street_address = models.CharField(max_length=255, help_text="Street address")
    city = models.CharField(max_length=100, help_text="City")
    state = models.CharField(max_length=100, help_text="State")
    is_volunteer = models.BooleanField(default=False, help_text="Flag to mark user as volunteer")
    
    created_at = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.email

class AdminGroups(models.Model):
    group_name = models.CharField(max_length=255, unique=True, help_text="Unique group name")
    created_on = models.DateTimeField(default=timezone.now, help_text="Timestamp of creation")
    admin = models.ForeignKey('AdminUser', on_delete=models.CASCADE, related_name='admin_groups', help_text="Group admin")
    city = models.CharField(max_length=100, help_text="City")
    # Change Many-to-Many linking to the new GeneralUser model
    allowed_volunteers = models.ManyToManyField(GeneralUser, related_name='accessible_groups', blank=True, help_text="Volunteers allowed in this group")
    
    def __str__(self):
        return self.group_name
    
class TodoTitle(models.Model):
    title = models.CharField(max_length=255, unique=True)  # Unique task title
    created_by = models.ForeignKey('AdminUser', on_delete=models.CASCADE, related_name='todos')  # Who created it
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of creation

    def __str__(self):
        return self.title

class SubTask(models.Model):
    todo_title = models.ForeignKey(TodoTitle, on_delete=models.CASCADE, related_name='subtasks')  # Parent title
    description = models.TextField()  # Description of the subtask
    completed = models.BooleanField(default=False)  # Status of the subtask
    completion_approved = models.BooleanField(default=False)  # Status
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of creation
    completed_on = models.DateTimeField(null=True, blank=True)  # Timestamp of completion    
    # Assigned Volunteer (optional)
    assigned_volunteer = models.ForeignKey(
        'GeneralUser', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subtasks'
    )

    def __str__(self):
        return f"{self.todo_title.title} - {self.description[:30]}..."  # Show title + subtask description