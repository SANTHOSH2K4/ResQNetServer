from django.http import JsonResponse, HttpResponseBadRequest
from messaging.models import Message
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt


def test_server(request):
    return JsonResponse({"server_access": True})

@csrf_exempt
def add_message(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST allowed")

    try:
        data = json.loads(request.body)
        phn_no = data.get("phn_no")
        msg = data.get("message")
        payload = f'send_sms({json.dumps(phn_no)}, {json.dumps(msg)})'
        if not phn_no or not msg:
            return HttpResponseBadRequest("Both 'phn_no' and 'message' are required")

        # Create a new message record (ID auto-increments)
        message_obj = Message.objects.create(request=payload)

        # Broadcast the new message to the "messages" group via the channel layer
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "messages",
            {
                "type": "new_message",
                "message": payload,
                "id": message_obj.id,
            }
        )

        return JsonResponse({"status": "success", "id": message_obj.id, "request": payload})
    
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON format")
    
@csrf_exempt  # Exempts from CSRF verification, needed for API endpoints
def receive_sms(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            sender = data.get('sender')
            message = data.get('message')
            timestamp = data.get('timestamp')

            # Log or process the received SMS
            print(f"Received SMS from {sender}: {message} at {timestamp}")

            return JsonResponse({'status': 'success', 'message': 'SMS received successfully'}, status=200)

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method'}, status=405)