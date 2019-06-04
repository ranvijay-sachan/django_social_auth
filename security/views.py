import json
import base64
import hashlib
import hmac

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from django.conf import settings
from django.apps import apps


# Create your views here.
def login(request):
    return render(request, 'login.html')


@login_required
def home(request):
    return render(request, 'home.html')


@method_decorator(csrf_exempt, name='dispatch')
class FbDeauthorizeView(View):

    def post(self, request):
        try:
            signed_request = request.POST['signed_request']
            encoded_sig, payload = signed_request.split('.')
        except (ValueError, KeyError):
            return HttpResponse(status=400, content='Invalid request')

        try:
            decoded_payload = base64.urlsafe_b64decode(payload + "==").decode('utf-8')
            decoded_payload = json.loads(decoded_payload)

            if type(decoded_payload) is not dict or 'user_id' not in decoded_payload.keys():
                return HttpResponse(status=400, content='Invalid payload data')

        except (ValueError, json.JSONDecodeError):
            return HttpResponse(status=400, content='Could not decode payload')

        try:
            secret = settings.SOCIAL_AUTH_FACEBOOK_SECRET

            sig = base64.urlsafe_b64decode(encoded_sig + "==")
            expected_sig = hmac.new(bytes(secret, 'utf-8'), bytes(payload, 'utf-8'), hashlib.sha256)
        except:
            return HttpResponse(status=400, content='Could not decode signature')

        if not hmac.compare_digest(expected_sig.digest(), sig):
            return HttpResponse(status=400, content='Invalid request')

        uid = decoded_payload['user_id']
        social_model = apps.get_model('social_django', 'usersocialauth')

        try:
            # now you get facebook user id. you can delete its details from your database like below.
            fb_account = social_model.objects.filter(uid=uid)
            user_obj = User.objects.get(pk=fb_account.user_id)
            user_obj.is_active = False
            user_obj.save()
            fb_account.delete()
        except fb_account.DoesNotExist:
            return HttpResponse(status=200)
        return HttpResponse(status=200)
