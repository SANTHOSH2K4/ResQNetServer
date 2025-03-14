from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import VolunteerRequestsSerializer ,GroupSerializer,GeneralUserSerializer, AdminLoginSerializer, AdminUserSerializer, AdminGroupsSerializer, TodoTitleSerializer, SubTaskSerializer
from django.core.files.base import ContentFile
import io
from PyPDF2 import PdfMerger
from .models import AdminUser,TodoTitle, SubTask, AdminGroups, GeneralUser, VolunteerRequests, ChatMessage
from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.clickjacking import xframe_options_exempt
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
import json
import random
import requests
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone

import google.generativeai as genai
import base64
import os
from bing_image_downloader import downloader

otp_storage = {}

genai.configure(api_key="AIzaSyBMugtwcla3HhBCvYbf42BGHcalDyKQ5g0")
class SendMessageView(APIView):
    def post(self, request, format=None):
        data = request.data
        group_id = data.get("group_id")
        msg_type = data.get("type")  # Expected to be "msg"
        content = data.get("content")
        sender = data.get("sender")
        sender_id = data.get("sender_id")
        sender_name = data.get("sender_name")
        
        if not group_id or not content or not sender or not sender_id or not sender_name:
            return Response(
                {"error": "Missing required fields."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            group = AdminGroups.objects.get(id=group_id)
        except AdminGroups.DoesNotExist:
            return Response(
                {"error": "Group not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create a new ChatMessage record
        chat_message = ChatMessage.objects.create(
            group=group,
            type=msg_type,  # "msg"
            content=content,
            sender=sender,
            sender_id=sender_id,
            sender_name=sender_name,
            timestamp=timezone.now()
        )
        
        response_data = {
            "id": str(chat_message.id),
            "group": group.group_name,
            "group_id": group_id,  # Include group_id in response
            "type": chat_message.type,
            "content": chat_message.content,
            "timestamp": chat_message.timestamp,
            "sender": chat_message.sender,
            "sender_id": chat_message.sender_id,
            "sender_name": chat_message.sender_name,
        }
        
        # Identify receivers based on group city
        channel_layer = get_channel_layer()
        admin_receivers = AdminUser.objects.filter(city=group.city)
        general_receivers = GeneralUser.objects.filter(city=group.city)
        all_receivers = list(admin_receivers) + list(general_receivers)
        
        # Broadcast the new chat message to each receiver's group channel.
        for receiver in all_receivers:
            phone = getattr(receiver, 'mobile_number', None)
            if not phone:
                continue
            sanitized_phone = phone.replace("+", "plus")
            receiver_group_name = f"phone_updates_{sanitized_phone}"
            
            async_to_sync(channel_layer.group_send)(
                receiver_group_name,
                {
                    "type": "send_chat_update",  # This triggers PhoneConsumer.send_chat_update
                    "data": {
                        "action": "new_chat_message",
                        "id": str(chat_message.id),
                        "group": group.group_name,
                        "group_id": group_id,  # Include group_id
                        "type": chat_message.type,
                        "content": chat_message.content,
                        "timestamp": chat_message.timestamp.isoformat(),
                        "sender": chat_message.sender,
                        "sender_id": chat_message.sender_id,
                        "sender_name": chat_message.sender_name,
                    }
                }
            )
        
        return Response(response_data, status=status.HTTP_201_CREATED)

class ApproveVolunteerView(APIView):
    """
    API endpoint to approve a volunteer request.
    Updates the GeneralUser's is_volunteer status and adds them to the group's allowed_volunteers.
    Then broadcasts an update via the phone-number WebSocket.
    """
    def post(self, request):
        volunteer_id = request.data.get('volunteer_id')
        group_id = request.data.get('group_id')
        print(volunteer_id, "for that volunteer", group_id, "for this group")
        
        # Validate required fields
        if not volunteer_id or not group_id:
            return Response(
                {"error": "Both volunteer_id and group_id are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Find the GeneralUser
            volunteer = GeneralUser.objects.get(id=volunteer_id)
            print(volunteer)
        except GeneralUser.DoesNotExist:
            return Response(
                {"error": "Volunteer not found with the provided ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Find the AdminGroups
            group = AdminGroups.objects.get(id=group_id)
            print(group)
        except AdminGroups.DoesNotExist:
            return Response(
                {"error": "Group not found with the provided ID."},
                status=status.HTTP_404_NOT_FOUND
            )

        try:
            # Update the GeneralUser's is_volunteer status
            volunteer.is_volunteer = True
            volunteer.save()

            # Add the user to the group's allowed_volunteers
            group.allowed_volunteers.add(volunteer)

            # Broadcast the update to the volunteer's phone WebSocket.
            # Sanitize the phone number for the group name by replacing '+' with 'plus'
            channel_layer = get_channel_layer()
            sanitized_phone = volunteer.mobile_number.replace("+", "plus")
            group_name = f"phone_updates_{sanitized_phone}"
            
            message_data = {
                "action": "volunteer_approved",
                "volunteer_id": volunteer.id,
                "group_id": group.id,
                "volunteer_name": volunteer.full_name,
                "group_name": group.group_name,
                "isvolunteer": True  # Instruct the client to set session?.isvolunteer === true
            }
            
            async_to_sync(channel_layer.group_send)(
                group_name,
                {
                    "type": "send_phone_update",  # This calls PhoneConsumer.send_phone_update
                    "data": message_data
                }
            )

            return Response(
                {
                    "message": "Volunteer approved successfully.",
                    "volunteer_id": volunteer.id,
                    "group_id": group.id,
                    "volunteer_name": volunteer.full_name,
                    "group_name": group.group_name
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            print("An error occurred: ", str(e))
            return Response(
                {"error": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateGroupView(APIView):
    """
    API endpoint to create a new group.
    Expects group_name, city, and phone (admin's phone).
    The view looks up the AdminUser using the phone.
    """
    def post(self, request):
        group_name = request.data.get("group_name")
        city = request.data.get("city")
        phone = request.data.get("phone")  # Expect admin phone
        
        print(f"Requested for {group_name} and {city} and {phone}")
        
        if not group_name or not city or not phone:
            return Response(
                {"error": "group_name, city, and phone are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Look up the admin using the phone number.
            admin = AdminUser.objects.get(mobile_number=phone)
        except AdminUser.DoesNotExist:
            return Response({"error": "Admin not found with that phone number."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Build payload using admin's primary key.
        group_data = {
            "group_name": group_name,
            "city": city,
            "admin": admin.id,
            "phone": phone,
            "address": admin.address  # Assuming AdminUser has address field
        }
        
        serializer = GroupSerializer(data=group_data, context={'phone': phone})
        if serializer.is_valid():
            group = serializer.save()
            broadcast_progress_update(serializer.data.get("admin"))
            broadcast_new_group(city, serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CreateVolunteerRequestView(APIView):
    """
    API endpoint to create a volunteer request.
    Expects volunteer_id, group_id, group_admin_id, phone, and address.
    """
    def post(self, request):
        volunteer_id = request.data.get("volunteer_id")
        group_id = request.data.get("group_id")
        group_admin_id = request.data.get("group_admin_id")
        phone = request.data.get("phone")
        address = request.data.get("address", "")
        
        if not volunteer_id or not group_id or not group_admin_id or not phone:
            return Response(
                {"error": "volunteer_id, group_id, group_admin_id, and phone are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            volunteer = GeneralUser.objects.get(id=volunteer_id)
            group = AdminGroups.objects.get(id=group_id)
        except (GeneralUser.DoesNotExist, AdminGroups.DoesNotExist):
            return Response({"error": "Invalid volunteer_id or group_id."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create the volunteer request record
        volunteer_request = VolunteerRequests.objects.create(
            volunteer=volunteer,
            group=group
        )
        serializer = VolunteerRequestsSerializer(volunteer_request)
        
        # Broadcast new volunteer request to the admin's WebSocket group.
        data_to_send = serializer.data
        data_to_send.update({
            "volunteer_name": volunteer.full_name,  # Assuming 'name' is a field in GeneralUser
            "phone": phone,
            "address": address
        })
        print("-----------------------------------------------\n\n\n\n")
        print(data_to_send)
        print("-----------------------------------------------\n\n\n\n")
        channel_layer = get_channel_layer()
        admin_ws_group = f"volunteer_requests_admin_{group_admin_id}"
        async_to_sync(channel_layer.group_send)(
            admin_ws_group,
            {
                "type": "new_volunteer_request",
                "data": data_to_send
            }
        )
        
        return Response(data_to_send, status=status.HTTP_201_CREATED)


def broadcast_new_group(city, group_data):
    """
    Broadcasts a new group creation event to all connected users in the same city.
    """
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        city,  # Send to city-specific WebSocket group
        {
            "type": "new_group",
            "data": group_data  # The group details
        }
    )    

class GroupListView(APIView):
    """
    API endpoint that fetches groups where the group's city matches the given query parameter.
    It also returns a boolean `isvolunteer` indicating if the logged-in user's phone number 
    exists in the group's allowed_volunteers.
    """
    def get(self, request):
        city = request.query_params.get('city')
        phone = request.query_params.get('phone')
        print(f"Requested for {city} and {phone}")
        if not city or not phone:
            return Response(
                {"error": "Both 'city' and 'phone' query parameters are required."},
                status=status.HTTP_400_BAD_REQUEST
            )
        groups = AdminGroups.objects.filter(city=city)
        serializer = GroupSerializer(groups, many=True, context={'phone': phone})
        print(serializer.data)
        return Response(serializer.data, status=status.HTTP_200_OK)

def send_sms(phone, message):
    # Use your SMS sending endpoint
    url = "http://172.20.122.192:8000/msg/add_message/"
    payload = json.dumps({"phn_no": phone, "message": message})
    headers = {"Content-Type": "application/json"}
    requests.post(url, data=payload, headers=headers)

import re

@csrf_exempt
def send_otp(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    try:
        data = json.loads(request.body)
        phone = data.get("phone")
        if not phone:
            return HttpResponseBadRequest("Phone number is required")
        
        # Check if the phone number exists in AdminUser or GeneralUser
        admin_qs = AdminUser.objects.filter(mobile_number=phone)
        general_qs = GeneralUser.objects.filter(mobile_number=phone)
        
        # Determine if we should send OTP:
        if admin_qs.exists():
            admin = admin_qs.first()
            if admin.verified:
                # Verified admin: OK to send OTP.
                pass
            else:
                # Admin exists but is not verified; check for a GeneralUser record.
                if not general_qs.exists():
                    return JsonResponse({"status": "failed", "message": "User not found"}, status=400)
        else:
            # No admin record exists; require a GeneralUser record.
            if not general_qs.exists():
                return JsonResponse({"status": "failed", "message": "You are not registered"}, status=400)
        
        # Generate a 4-digit OTP
        otp = str(random.randint(1000, 9999))
        otp_storage[phone] = otp
        print(f"heres the otp {otp}")
        phone = re.sub(r'^\+91', '', phone)  # Remove country code if present
        phone = re.sub(r'\s+', '', phone)
        print(type(phone))
        print(phone)
        phone=int(phone)
        print(type(phone))
        # Send OTP via SMS (make sure send_sms is defined properly)
        send_sms(int(phone), f"Your code is {otp}")
        return JsonResponse({"status": "success", "message": "OTP sent"})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")

@csrf_exempt
def verify_otp(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")
    try:
        data = json.loads(request.body)
        phone = data.get("phone")
        entered_otp = data.get("otp")
        if not phone or not entered_otp:
            return HttpResponseBadRequest("Phone and OTP are required")
        
        stored_otp = otp_storage.get(phone)
        if not stored_otp:
            return JsonResponse({"status": "failed", "message": "OTP expired or invalid"}, status=400)
        
        if str(stored_otp) != str(entered_otp):
            return JsonResponse({"status": "failed", "message": "Invalid OTP"}, status=400)
        
        # OTP is valid; determine which user record matches
        user_data = None
        admin_qs = AdminUser.objects.filter(mobile_number=phone)
        general_qs = GeneralUser.objects.filter(mobile_number=phone)
        
        if admin_qs.exists():
            admin = admin_qs.first()
            if admin.verified:
                # Verified admin: return admin details
                user_data = {
                    "id": admin.id,
                    "username": admin.name,
                    "user_type": "admin",
                    "phone": admin.mobile_number,
                    "email": admin.email,
                    "city": admin.city,
                    "state": admin.state,
                    "isvolunteer": False,
                }
            else:
                # Admin exists but not verified, check for general user record
                if general_qs.exists():
                    general = general_qs.first()
                    user_data = {
                        "id": general.id,
                        "username": general.full_name,
                        "user_type": "general",
                        "phone": general.mobile_number,
                        "email": general.email,
                        "city": general.city,
                        "state": general.state,
                        "isvolunteer": True,
                    }
                else:
                    return JsonResponse({"status": "failed", "message": "User not found"}, status=400)
        else:
            # No admin record found, check for a general user record
            if general_qs.exists():
                general = general_qs.first()
                user_data = {
                    "id": general.id,
                    "username": general.full_name,
                    "user_type": "general",
                    "phone": general.mobile_number,
                    "email": general.email,
                    "city": general.city,
                    "state": general.state,
                    "isvolunteer": general.is_volunteer,
                }
            else:
                return JsonResponse({"status": "failed", "message": "User not found"}, status=400)
        
        # Remove OTP after successful verification
        del otp_storage[phone]
        print(user_data)
        return JsonResponse({"status": "success", "message": "OTP verified", "user": user_data})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")


        
        # Remove OTP after successful verification
        del otp_storage[phone]
        return JsonResponse({"status": "success", "message": "OTP verified", "user": user_data})
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")



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
    
class GeneralUserRegistrationView(APIView):
    """
    API endpoint for registering a general user.
    Expected fields: full_name, email, mobile_number, street_address, city, state.
    is_volunteer is optional (defaults to False).
    """
    def post(self, request):
        print(request.data)
        serializer = GeneralUserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@method_decorator(csrf_exempt, name='dispatch')
class AdminUserRegistrationView(APIView):
    """
    Handles admin user registration, merging uploaded identity documents.
    On success, broadcasts the new admin info via Channels.
    Verbose logging added for each step.
    """
    def post(self, request):
        print("=== Admin Registration Request Received ===")
        print("Request DATA keys:", list(request.data.keys()))
        print("Request FILES keys:", list(request.FILES.keys()))
        
        mobile_number = request.data.get("mobile_number", "unknown")
        print("Mobile number extracted:", mobile_number)
        
        # Retrieve identity documents (all expected documents)
        identity_documents = [
            request.FILES.get("identity_document1"),
            request.FILES.get("identity_document2"),
            request.FILES.get("identity_document3"),
            request.FILES.get("disaster_management_training_certificate"),
            request.FILES.get("authorization_letter"),
        ]
        identity_documents = [doc for doc in identity_documents if doc]
        print("Found identity documents:", [doc.name for doc in identity_documents])
        
        if identity_documents:
            try:
                merger = PdfMerger()
                for doc in identity_documents:
                    print("Appending document:", doc.name)
                    merger.append(doc)
                output_stream = io.BytesIO()
                merger.write(output_stream)
                merger.close()
                output_stream.seek(0)
                merged_file = ContentFile(output_stream.read(), name=f"{mobile_number}_iddocs.pdf")
                print("Merged file created with name:", merged_file.name)
                # If request.data is immutable, make it mutable
                if hasattr(request.data, '_mutable') and not request.data._mutable:
                    request.data._mutable = True
                request.data["merged_documents"] = merged_file
                print("Merged file attached to request.data as 'merged_documents'")
            except Exception as e:
                print("Error during PDF merging:", str(e))
        else:
            print("No identity documents found to merge.")
        
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
                new_name = f"{mobile_number}_{suffix}.{ext}"
                print(f"Renaming file field '{field}': {file_obj.name} --> {new_name}")
                file_obj.name = new_name
        
        # Process additional fields (e.g., job and gender) if present
        if request.data.get("job"):
            print("Job provided:", request.data.get("job"))
        else:
            print("No job provided in request.data.")
        if request.data.get("gender"):
            print("Gender provided:", request.data.get("gender"))
        else:
            print("No gender provided in request.data.")
        
        print("Initializing serializer with request data...")
        serializer = AdminUserSerializer(data=request.data)
        
        if serializer.is_valid():
            print("Serializer validated successfully. Saving admin user...")
            admin_user = serializer.save()
            print("Admin user saved. Serializer data:", serializer.data)
            
            # Broadcast the new admin info via Channels
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "new_admin_users",
                {
                    "type": "new_admin",
                    "admin": serializer.data,
                }
            )
            print("Broadcast complete to 'new_admin_users' channel.")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("Serializer errors encountered:", serializer.errors)
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
            todo = serializer.save()
            # Broadcast the new task only to group members other than the creator.
            creator = request.user  # Assuming authentication sets request.user
            updater_phone = creator.mobile_number if hasattr(creator, 'mobile_number') else None
            # Adjust the filtering below as per your “group” logic.
            receivers = list(AdminUser.objects.filter(city=creator.city).exclude(mobile_number=updater_phone)) \
                        + list(GeneralUser.objects.filter(city=creator.city))
            channel_layer = get_channel_layer()
            for receiver in receivers:
                phone = receiver.mobile_number
                if not phone:
                    continue
                # Sanitize phone number for group naming.
                sanitized_phone = phone.replace("+", "plus")
                receiver_group_name = f"phone_updates_{sanitized_phone}"
                async_to_sync(channel_layer.group_send)(
                    receiver_group_name,
                    {
                        "type": "send_task_update",
                        "data": {
                            "action": "new_task",
                            "todo": serializer.data,  # Send entire task data
                        }
                    }
                )
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
    POST endpoint to create a new SubTask.
    Expects JSON with:
      - todo_title (ID of the parent task)
      - description (text)
      - assigned_volunteer (optional, ID of the volunteer)
    """
    def post(self, request, format=None):
        serializer = SubTaskSerializer(data=request.data)
        if serializer.is_valid():
            subtask = serializer.save()
            # Broadcast the new subtask creation event
            updater = request.user  # Assuming you have authentication in place.
            updater_phone = updater.mobile_number if hasattr(updater, 'mobile_number') else None
            
            # Assume that the parent task (TodoTitle) has a created_by field with a city or group identifier.
            todo_title = subtask.todo_title

            # Determine receivers:
            # For a subtask, broadcast to all group admins and general users,
            # excluding the creator if needed.
            receivers = list(AdminUser.objects.filter(city=todo_title.created_by.city).exclude(mobile_number=updater_phone)) \
                        + list(GeneralUser.objects.filter(city=todo_title.created_by.city))
            
            channel_layer = get_channel_layer()
            for receiver in receivers:
                phone = receiver.mobile_number
                if not phone:
                    continue
                # Sanitize phone for group naming.
                sanitized_phone = phone.replace("+", "plus")
                receiver_group_name = f"phone_updates_{sanitized_phone}"
                async_to_sync(channel_layer.group_send)(
                    receiver_group_name,
                    {
                        "type": "send_task_update",  # This triggers PhoneConsumer.send_task_update on the client
                        "data": {
                            "action": "new_subtask",
                            "subtask": serializer.data,  # Send the new subtask data
                        }
                    }
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SubTaskUpdateView(APIView):
    """
    POST endpoint to update a SubTask's status.
    Expects JSON with: todo_title_id, subtask_id, new_status.
    """
    def post(self, request):
        data = request.data
        todo_title_id = data.get("todo_title_id")
        subtask_id = data.get("subtask_id")
        new_status = data.get("new_status")
        if not (todo_title_id and subtask_id and new_status):
            return Response({"error": "Missing fields."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            subtask = SubTask.objects.get(id=subtask_id, todo_title_id=todo_title_id)
        except SubTask.DoesNotExist:
            return Response({"error": "Subtask not found."}, status=status.HTTP_404_NOT_FOUND)
        
        # Update subtask status.
        if new_status == "completed":
            subtask.completed = True
            subtask.completion_approved = True
            subtask.completed_on = timezone.now()
        else:
            subtask.completed = False
            subtask.completion_approved = False
        subtask.save()

        # Prepare broadcast message.
        updater = request.user  # Assume user is set by authentication.
        updater_phone = updater.mobile_number if hasattr(updater, 'mobile_number') else None
        
        # Retrieve group information from the parent TodoTitle (assumed to have created_by with a city or group field)
        todo_title = subtask.todo_title
        
        # Broadcast receivers:
        # - If an admin updated: broadcast to all other admins and all general users.
        # - If a volunteer/general user updated: broadcast to all admins and all other general users.
        if updater.role == "admin":
            receivers = list(AdminUser.objects.filter(city=todo_title.created_by.city).exclude(mobile_number=updater_phone)) \
                        + list(GeneralUser.objects.filter(city=todo_title.created_by.city))
        else:
            receivers = list(AdminUser.objects.filter(city=todo_title.created_by.city)) \
                        + list(GeneralUser.objects.filter(city=todo_title.created_by.city).exclude(mobile_number=updater_phone))
        
        channel_layer = get_channel_layer()
        for receiver in receivers:
            phone = receiver.mobile_number
            if not phone:
                continue
            sanitized_phone = phone.replace("+", "plus")
            receiver_group_name = f"phone_updates_{sanitized_phone}"
            async_to_sync(channel_layer.group_send)(
                receiver_group_name,
                {
                    "type": "send_task_update",
                    "data": {
                        "action": "update_subtask_status",
                        "todo_title_id": todo_title_id,
                        "subtask_id": subtask_id,
                        "new_status": new_status,
                        "updater": updater.id,
                    }
                }
            )
        serializer = SubTaskSerializer(subtask)
        return Response(serializer.data, status=status.HTTP_200_OK)

model = genai.GenerativeModel('gemini-2.0-flash')
def clean_json_string(data):
    cleaned_data = re.sub(r'[\x00-\x1F\x7F]', '', data).strip()
    try:
        return json.loads(cleaned_data)
    except json.JSONDecodeError:
        return {"error": "Failed to decode JSON. Please check the response format."}

@csrf_exempt
def trend_extractor_view(request):
    print("hii")
    if request.method == 'POST':
        data = json.loads(request.body)
        date = data.get("date", "13/03/2025")
        # trend_data = trend_extractor(date)
        prompt = (
        f"""You are a good trend finder. Find a trend based on the given date include location only in india.
        Return the title in JSON format like this {{"trend":["flood in chennai",""cyclone"]}}.
        The trend should only be disaster-related trends in India.
        ##Instruction : Only in JSON format, with multiple values in a list. Each entry should have context limited to 3 words or fewer.
        ##Query: {date}"""
    )

        response = model.generate_content(
            contents=prompt,
        )

        cleaned_data = re.sub(r'```json|```', '', response.text).strip()
        print(response.text)
        trend_data = clean_json_string(cleaned_data)
        print(trend_data)
        return JsonResponse(trend_data, safe=False)

def image_to_base64(image_path):
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        return "No image found"
def yt_search(yt_search):
    video_list = []
    from googleapiclient.discovery import build

    API_KEY = "AIzaSyCKT_61ACyA0gtQeh0pArUc-NUgBOaTIrc"

    youtube = build("youtube", "v3", developerKey=API_KEY)

    hashtag =yt_search

    search_response = youtube.search().list(
        q=hashtag,
        part="id",
        type="video",
        maxResults=4
    ).execute()

    video_ids = [item["id"]["videoId"] for item in search_response["items"]]

    video_response = youtube.videos().list(
        part="snippet,statistics",
        id=",".join(video_ids)
    ).execute()
    for video in video_response["items"]:
        title = video["snippet"]["title"]
        video_url = f"https://www.youtube.com/watch?v={video['id']}"
       
        video_list.append({"title": title, "url": video_url})

    return video_list


@csrf_exempt
def trend_summarizer_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        trend = data.get("trend", "cyclone alert")
        date = data.get("date", "13/03/2025")
        video_list=yt_search(trend)
        prompt = (
        f"""You are a good summarizer. Summarize the result based on the given date.
        The summary should be related to disaster trends in India. Return the result more than 1000 words.
        ##Query: {trend}, ##Date: {date}
        ##Instruction:
        1. The summary should provide detailed information without analysis or commentary.
        2. Return only in String format.
        3. Add text-based stickers or reactions to improve readability but don't include special symbols like ** or \n like that.
        5. Summarized values should be based on real-time data, no fabricated information.
        6. Avoid personal analysis or unrelated content.
        7. Don't include Okay, here's a detailed summary about directly start with summary and also avoid based on available return only string no need to mention ```string ```.
        """
    )

        response = model.generate_content(
            contents=prompt,
        )
        cleaned_data = response.text
        
        search_term = f"Real time image of a {trend} disaster India"
        output_path = "media"

        # Download the image
        new_path = os.path.join(output_path, f"{trend}.png")

        # Download the image
        downloader.download(search_term, limit=1, output_dir=output_path, adult_filter_off=True, force_replace=False, timeout=60, verbose=True)

        # Locate the downloaded image inside its folder
        search_folder = os.path.join(output_path, search_term)
        image_files = [f for f in os.listdir(search_folder) if f.endswith(('.jpg', '.png', '.jpeg'))] if os.path.exists(search_folder) else []

        # Rename and move image to "media/{trend}.png"
        if image_files:
            old_path = os.path.join(search_folder, image_files[0])

            # **FIX**: Remove existing file before renaming
            if os.path.exists(new_path):
                os.remove(new_path)  # Delete the existing file

            os.rename(old_path, new_path)  # Rename the downloaded file
            image_path = new_path
        else:
            image_path = None

        # Convert image to Base64 if found
        image_base64 = image_to_base64(image_path) if image_path else "No image found"

        data = {"summary": cleaned_data, "image_base64": image_base64,"video_list":video_list}
        # print(data)
        print(data)
        return JsonResponse(data)

def search(request,search):
    genai.configure(api_key="AIzaSyBMugtwcla3HhBCvYbf42BGHcalDyKQ5g0")

    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt =f"""
You are an expert disaster information analyst. I will provide you with the name of a disaster. Your task is to:

1.  **Search the internet for current and historical information** about the disaster I provide.
2.  **Provide a concise summary** of the disaster, including:
    * What type of disaster it is (e.g., earthquake, flood, hurricane).
    * When and where it occurred (or is occurring).
    * The scale and impact of the disaster (e.g., casualties, damage).
3.  **If the disaster type has occurred previously**, research and provide information on:
    * Similar past occurrences, including dates and locations.
    * How past occurrences were addressed and resolved, including any lessons learned or technological advancements that resulted.
4.  **Offer potential suggestions** for:
    * Mitigation efforts to reduce future impact.
    * Response strategies for current or similar future events.
    * Recovery actions.
5.  **Provide sources** for your information, including relevant websites and articles.

Note : Dont give that i asked you a question for that you are answering like Okay, I will analyze the dont include these kinds of words

Disaster Name: {search}
"""

    response = model.generate_content(prompt)

    response_data = {
        "summary": response.text
    }

    return JsonResponse(response_data, safe=False)


def fetch_all_todos(request):
    todos = TodoTitle.objects.prefetch_related('subtasks').all()
    data = [
        {
            "id": todo.id,
            "title": todo.title,
            "created_by": todo.created_by.id,
            "created_on": todo.created_on,
            "subtasks": [
                {
                    "id": subtask.id,
                    "description": subtask.description,
                    "completed": subtask.completed,
                    "completion_approved": subtask.completion_approved,
                    "assigned_volunteer": subtask.assigned_volunteer.id if subtask.assigned_volunteer else None,
                    "created_on": subtask.created_on,
                    "completed_on": subtask.completed_on
                } for subtask in todo.subtasks.all()
            ]
        } for todo in todos
    ]
    return JsonResponse({"todos": data}, safe=False)

# 2. Create a New Todo or Mark a Subtask as Completed
@csrf_exempt
def create_or_update_todo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get("title")
            created_by_id = data.get("created_by")

            if not title or not created_by_id:
                return JsonResponse({"error": "Title and created_by are required"}, status=400)

            todo = TodoTitle.objects.create(title=title, created_by_id=created_by_id)
            return JsonResponse({"message": "Todo created successfully", "id": todo.id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    elif request.method == "PUT":
        try:
            data = json.loads(request.body)
            subtask_id = data.get("subtask_id")
            completed = data.get("completed")

            subtask = get_object_or_404(SubTask, id=subtask_id)
            subtask.completed = completed
            subtask.completed_on = timezone.now() if completed else None
            subtask.save()

            return JsonResponse({"message": "Subtask updated successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

# 3. Delete a Todo or Subtask
@csrf_exempt
def delete_todo_or_subtask(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            todo_id = data.get("todo_id")
            subtask_id = data.get("subtask_id")

            if todo_id:
                todo = get_object_or_404(TodoTitle, id=todo_id)
                todo.delete()
                return JsonResponse({"message": "Todo deleted successfully"})

            elif subtask_id:
                subtask = get_object_or_404(SubTask, id=subtask_id)
                subtask.delete()
                return JsonResponse({"message": "Subtask deleted successfully"})

            return JsonResponse({"error": "Provide either a todo_id or subtask_id"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
       
@csrf_exempt
def create_subtask(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            todo_title_id = data.get("todo_title")  # Parent Todo ID
            description = data.get("description")  # Subtask description
            assigned_volunteer_id = data.get("assigned_volunteer")  # Optional Volunteer
            print("hello")
            if not todo_title_id or not description:
                return JsonResponse({"error": "Todo ID and description are required"}, status=400)

            # Check if the TodoTitle exists
            todo_title = get_object_or_404(TodoTitle, id=todo_title_id)
            print(todo_title)
            # Create the subtask
            subtask = SubTask.objects.create(
                todo_title=todo_title,
                description=description,
                assigned_volunteer_id=assigned_volunteer_id  # Can be None if not provided
            )

            return JsonResponse({
                "message": "Subtask created successfully",
                "subtask_id": subtask.id
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


@csrf_exempt
def hazlebot_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get("query", "Hello there")
        phone_id = data.get("phone_id", "123456789")
        prompt = (
        f"""You are a people helper and consider you as a rescue head you need to give suggestion,adviser
        based on the user query you need to identify the solution or previous occurence idea which helps to solve the issues like that and also includes details about weather and locations
        ##Instruction:
        1.Avoid saying like this in your string operation or other context simply provide the answer
        2.Don't include \n or other symbols like **,## avoid including this symbol instead use emoji and avoiding saying that okay,here,avoid adding more emoji from given simply tell the answer alone based on the query and also real time data in your response
        ##Query:{query}
        """
    )

        response = model.generate_content(
            contents=prompt,
        )
        cleaned_data = response.text

        data = {"Response": cleaned_data}
        print(data)
        return JsonResponse(data)


def fetch_all_todos(request):
    todos = TodoTitle.objects.prefetch_related('subtasks').all()
    data = [
        {
            "id": todo.id,
            "title": todo.title,
            "created_by": todo.created_by.id,
            "admin_group": todo.admin_group.id,
            "created_on": todo.created_on,
            "subtasks": [
                {
                    "id": subtask.id,
                    "description": subtask.description,
                    "completed": subtask.completed,
                    "completion_approved": subtask.completion_approved,
                    "assigned_volunteer": subtask.assigned_volunteer.id if subtask.assigned_volunteer else None,
                    "created_on": subtask.created_on,
                    "completed_on": subtask.completed_on
                } for subtask in todo.subtasks.all()
            ]
        } for todo in todos
    ]
    return JsonResponse({"todos": data}, safe=False)


# 2. Create a New Todo
@csrf_exempt
def create_or_update_todo(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            title = data.get("title")
            created_by_id = data.get("created_by")
            admin_group_id = data.get("admin_group")

            if not title or not created_by_id or not admin_group_id:
                return JsonResponse({"error": "Title, created_by, and admin_group are required"}, status=400)

            created_by = get_object_or_404(AdminUser, id=created_by_id)
            admin_group = get_object_or_404(AdminGroups, id=admin_group_id)

            todo = TodoTitle.objects.create(title=title, created_by=created_by, admin_group=admin_group)
            return JsonResponse({"message": "Todo created successfully", "id": todo.id}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# 3. Update a Subtask (Mark as Completed)
@csrf_exempt
def update_subtask(request):
    if request.method == "PUT":
        try:
            data = json.loads(request.body)
            subtask_id = data.get("subtask_id")
            completed = data.get("completed")
            approved_by_admin = data.get("approved_by_admin", False)  # Only Admin can approve

            subtask = get_object_or_404(SubTask, id=subtask_id)

            if completed:  
                subtask.completed = True
                subtask.completed_on = timezone.now()

            # Check if an Admin is approving the completion
            if approved_by_admin:
                admin_id = data.get("admin_id")
                admin_user = get_object_or_404(AdminUser, id=admin_id)

                # Ensure Admin can approve only if they belong to the same group
                if subtask.todo_title.admin_group.admin.id != admin_user.id:
                    return JsonResponse({"error": "Admin does not have permission to approve this subtask"}, status=403)

                subtask.completion_approved = True

            subtask.save()
            return JsonResponse({"message": "Subtask updated successfully"})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# 4. Delete a Todo or Subtask
@csrf_exempt
def delete_todo_or_subtask(request):
    if request.method == "DELETE":
        try:
            data = json.loads(request.body)
            todo_id = data.get("todo_id")
            subtask_id = data.get("subtask_id")

            if todo_id:
                todo = get_object_or_404(TodoTitle, id=todo_id)
                todo.delete()
                return JsonResponse({"message": "Todo deleted successfully"})

            elif subtask_id:
                subtask = get_object_or_404(SubTask, id=subtask_id)
                subtask.delete()
                return JsonResponse({"message": "Subtask deleted successfully"})

            return JsonResponse({"error": "Provide either a todo_id or subtask_id"}, status=400)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)


# 5. Create a New Subtask
@csrf_exempt
def create_subtask(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            todo_title_id = data.get("todo_title")  # Parent Todo ID
            description = data.get("description")  # Subtask description
            assigned_volunteer_id = data.get("assigned_volunteer")  # Optional Volunteer

            if not todo_title_id or not description:
                return JsonResponse({"error": "Todo ID and description are required"}, status=400)

            todo_title = get_object_or_404(TodoTitle, id=todo_title_id)

            subtask = SubTask.objects.create(
                todo_title=todo_title,
                description=description,
                assigned_volunteer_id=assigned_volunteer_id  # Can be None if not provided
            )

            return JsonResponse({
                "message": "Subtask created successfully",
                "subtask_id": subtask.id
            }, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)





