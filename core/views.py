from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import AdminLoginSerializer, AdminUserSerializer, AdminGroupsSerializer, TodoTitleSerializer, SubTaskSerializer
from django.core.files.base import ContentFile
import io
from PyPDF2 import PdfMerger
from .models import AdminUser,TodoTitle, SubTask, AdminGroups
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


class AdminVerifierLoginView(APIView):
    print("🔹 AdminVerifierLoginView Initialized")  # Debugging print

    def post(self, request):
        print("🔹 Received POST request to /admin-verifier-login/")
        print("🔹 Raw Request Data:", request.data)
        
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data.get("user")
            print(f"🔹 Authenticated User: {user.email}")
            return Response({"message": "Login successful"}, status=status.HTTP_200_OK)
        
        print("🔸 Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class AdminUserRegistrationView(APIView):
    """
    Handles admin user registration, merging uploaded identity documents.
    On success, broadcasts the new admin info via Channels.
    """
    def post(self, request):
        mobile_number = request.data.get("mobile_number", "unknown")
        
        # Retrieve identity documents (all 5 expected documents)
        identity_documents = [
            request.FILES.get("identity_document1"),
            request.FILES.get("identity_document2"),
            request.FILES.get("identity_document3"),
            request.FILES.get("disaster_management_training_certificate"),
            request.FILES.get("authorization_letter"),
        ]
        identity_documents = [doc for doc in identity_documents if doc]
        
        if identity_documents:
            merger = PdfMerger()
            for doc in identity_documents:
                merger.append(doc)
            output_stream = io.BytesIO()
            merger.write(output_stream)
            merger.close()
            output_stream.seek(0)
            merged_file = ContentFile(output_stream.read(), name=f"{mobile_number}_iddocs.pdf")
            if hasattr(request.data, '_mutable') and not request.data._mutable:
                request.data._mutable = True
            request.data["merged_documents"] = merged_file

        # Rename additional file fields
        file_fields = {
            "live_selfie_capture": "selfie",
            "signature_upload": "signature",
            "disaster_management_training_certificate": "training",
            "authorization_letter": "authletter",
        }
        for field, suffix in file_fields.items():
            file_obj = request.FILES.get(field)
            if file_obj:
                ext = file_obj.name.split('.')[-1]
                file_obj.name = f"{mobile_number}_{suffix}.{ext}"
        
        # Process additional fields for job and gender (if present)
        if request.data.get("job"):
            request.data["job"] = request.data["job"]
        if request.data.get("gender"):
            request.data["gender"] = request.data["gender"]
        
        serializer = AdminUserSerializer(data=request.data)
        if serializer.is_valid():
            admin_user = serializer.save()
            # Broadcast the new admin info via Channels
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "new_admin_users",
                {
                    "type": "new_admin",
                    "admin": serializer.data,
                }
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminUserSummaryView(APIView):
    """
    Retrieves summary details of an admin user for the UserProgressHeader component.
    """

    def get(self, request, pk):
        user = get_object_or_404(AdminUser, pk=pk)
        
        # Count the number of groups this admin is managing
        no_of_groups = user.admin_groups.count()

        # Extract only the required fields based on your model
        user_data = {
            "name": user.name,
            "job": user.job,  
            "email": user.email,
            "mobile_number": user.mobile_number,
            "profile_picture":  request.build_absolute_uri(user.live_selfie_capture.url) if user.live_selfie_capture else None,
            "address": user.address,
            "city": user.city,
            "state": user.state,
            "pincode": user.pincode,
            "admin_since": user.created_at.strftime("%d/%m/%Y"),  # Formatted date
            "no_of_groups": no_of_groups,  # Number of groups the admin manages
        }
        
        return Response(user_data, status=status.HTTP_200_OK)


class AdminUserListView(APIView):
    def get(self, request):
        screen = request.query_params.get("screen", "")
        if screen == "home":
            queryset = AdminUser.objects.filter(verified=False)
        else:
            queryset = AdminUser.objects.filter(verified=True)
        
        data = []
        for user in queryset:
            user_data = {
                "id": user.id,
                "name": user.name,
                "job": user.job,
                "gender": user.gender,
            }
            # If a profile image is available, build its absolute URL
            if user.live_selfie_capture:
                user_data["live_selfie_capture"] = request.build_absolute_uri(user.live_selfie_capture.url)
            else:
                user_data["live_selfie_capture"] = ""  # or a default image URL
            data.append(user_data)
        
        return Response(data, status=status.HTTP_200_OK)

class AdminUserDetailView(APIView):
    """
    GET a single admin user by ID.
    """
    def get(self, request, pk):
        user = get_object_or_404(AdminUser, pk=pk)
        serializer = AdminUserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class AdminUserUpdateStatusView(APIView):
    """
    PATCH to update the verified status of an admin user.
    Expects a JSON payload with an "action" field:
      - "approve": sets verified=True and returns a message with the username and serialized data.
      - "decline": deletes the user and returns a message with the username.
    """
    def patch(self, request, pk):
        action = request.data.get("action")
        user = get_object_or_404(AdminUser, pk=pk)
        username = user.name  # Save the username for the response
        
        if action == "approve":
            user.verified = True
            user.save()
            serializer = AdminUserSerializer(user)
            return Response(
                {"message": f"{username} Request Accepted", "user": serializer.data},
                status=status.HTTP_200_OK
            )
        elif action == "decline":
            user.delete()
            return Response(
                {"message": f"{username} Request Declined"},
                status=status.HTTP_200_OK
            )
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        
@csrf_exempt  # Disable CSRF if needed
@xframe_options_exempt  # Allow embedding in iframe
def serve_pdf(request, file_path):
    response = FileResponse(open(f"uploads/{file_path}", "rb"), content_type="application/pdf")
    response["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response["Access-Control-Allow-Credentials"] = "true"
    return response

class RevokeAdminPrivilegesView(APIView):
    """
    Receives a POST request with a revocation message and admin user ID,
    prints the message (for now), and deletes the admin user record.
    """
    def post(self, request, pk):
        message = request.data.get("message", "")
        # For now, just print the message and admin ID to the console
        print(f"Revoking privileges for admin id {pk}: {message}")
        
        # Delete the admin user record
        admin_user = get_object_or_404(AdminUser, pk=pk)
        admin_user.delete()
        
        return Response({"detail": f"Admin {pk} privileges revoked"}, status=status.HTTP_200_OK)
    
class AdminGroupsListView(APIView):
    """
    Retrieves a list of groups (id and group_name) for a specific admin.
    """
    def get(self, request, admin_id):
        admin = get_object_or_404(AdminUser, pk=admin_id)
        groups_qs = admin.admin_groups.all()  # using the related_name 'admin_groups'
        groups_data = [{"id": group.id, "groupName": group.group_name} for group in groups_qs]
        return Response(groups_data, status=status.HTTP_200_OK)

class AdminTodosView(APIView):
    """
    Retrieves tasks (TodoTitles) along with subtasks for a given admin for a selected date.
    Filtering is done on the subtasks’ created_on date.
    """
    def get(self, request, admin_id):
        date_str = request.query_params.get("date")
        if not date_str:
            return Response({"error": "Date parameter required"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        
        todos = TodoTitle.objects.filter(created_by__id=admin_id)
        tasks_data = []
        for todo in todos:
            # Filter subtasks whose created_on date equals the selected date.
            subtasks = todo.subtasks.filter(created_on__date=date_obj)
            if subtasks.exists():
                # Determine task status: if all subtasks are completed (both flags true) then "Finished", else "In Progress"
                task_status = "Finished" if all(s.completed and s.completion_approved for s in subtasks) else "In Progress"
                tasks_data.append({
                    "id": todo.id,
                    "taskName": todo.title,
                    "status": task_status,
                    "date": date_str,
                    "subTasks": [{
                        "id": sub.id,
                        "name": sub.description,
                        "status": "Completed" if (sub.completed and sub.completion_approved) else "In Progress",
                        # For time values, we use created_on as start and completed_on as end (if available)
                        "start": sub.created_on.isoformat(),
                        "end": sub.completed_on.isoformat() if sub.completed_on else sub.created_on.isoformat()
                    } for sub in subtasks]
                })
        return Response(tasks_data, status=status.HTTP_200_OK)

def broadcast_progress_update(admin_id):
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        "progress_updates",
        {
            "type": "progress_update",
            "admin": admin_id,
        }
    )

# ----- AdminGroups Views -----

class AdminGroupsCreateView(APIView):
    """
    POST endpoint to create a new AdminGroups record.
    Expects JSON with: group_name, admin (ID), allowed_volunteers (optional list)
    """
    def post(self, request):
        serializer = AdminGroupsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            broadcast_progress_update(serializer.data.get("admin"))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AdminGroupsUpdateView(APIView):
    """
    POST endpoint to update an existing AdminGroups record.
    Expects JSON with fields to update.
    """
    def post(self, request, pk):
        group = get_object_or_404(AdminGroups, pk=pk)
        serializer = AdminGroupsSerializer(group, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            broadcast_progress_update(serializer.data.get("admin"))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----- TodoTitle (Task) Views -----

class TodoTitleCreateView(APIView):
    """
    POST endpoint to create a new TodoTitle (task) record.
    Expects JSON with: title, created_by (ID)
    """
    def post(self, request):
        serializer = TodoTitleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            broadcast_progress_update(serializer.data.get("created_by"))
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class TodoTitleUpdateView(APIView):
    """
    POST endpoint to update an existing TodoTitle record.
    Expects JSON with fields to update.
    """
    def post(self, request, pk):
        todo = get_object_or_404(TodoTitle, pk=pk)
        serializer = TodoTitleSerializer(todo, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            broadcast_progress_update(serializer.data.get("created_by"))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ----- SubTask Views -----

class SubTaskCreateView(APIView):
    """
    POST endpoint to create a new SubTask record.
    Expects JSON with: todo_title (ID), description, completed (boolean),
    completion_approved (boolean), assigned_volunteer (optional)
    """
    def post(self, request):
        serializer = SubTaskSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            # Retrieve admin id from parent TodoTitle.
            todo_id = serializer.data.get("todo_title")
            from .models import TodoTitle  # Import here to avoid circular imports.
            todo = TodoTitle.objects.get(pk=todo_id)
            broadcast_progress_update(todo.created_by_id)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubTaskUpdateView(APIView):
    """
    POST endpoint to update an existing SubTask record.
    Expects JSON with fields to update.
    """
    def post(self, request, pk):
        subtask = get_object_or_404(SubTask, pk=pk)
        serializer = SubTaskSerializer(subtask, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            from .models import TodoTitle
            todo = TodoTitle.objects.get(pk=subtask.todo_title_id)
            broadcast_progress_update(todo.created_by_id)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)