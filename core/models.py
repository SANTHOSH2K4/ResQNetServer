from django.db import models
from django.utils import timezone

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
    
class Volunteer(models.Model):
    volunteer_id = models.CharField(max_length=50, unique=True)  # Unique Volunteer ID
    name = models.CharField(max_length=255)  # Name
    mobile_number = models.CharField(max_length=15, unique=True)  # Contact

    def __str__(self):
        return f"{self.name} ({self.volunteer_id})"
    
class AdminGroups(models.Model):
    group_name = models.CharField(max_length=255, unique=True)  # Unique group name
    created_on = models.DateTimeField(default=timezone.now)  # Timestamp of creation
    
    # One admin per group
    admin = models.ForeignKey('AdminUser', on_delete=models.CASCADE, related_name='admin_groups')

    # Many-to-Many for volunteer access (optional)
    allowed_volunteers = models.ManyToManyField(Volunteer, related_name='accessible_groups', blank=True)

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
        'Volunteer', on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_subtasks'
    )

    def __str__(self):
        return f"{self.todo_title.title} - {self.description[:30]}..."  # Show title + subtask description