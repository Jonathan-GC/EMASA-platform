import re
import requests
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver

# List


CHIRPSTACK_BASE_URL = "http://chirpstack-rest-api:8090/api"

CHIRPSTACK_API_URL = CHIRPSTACK_BASE_URL + "/users"
CHIRPSTACK_TENANT_URL = CHIRPSTACK_BASE_URL + "/tenants"
CHIRPSTACK_GATEWAYS_URL = CHIRPSTACK_BASE_URL + "/gateways"
CHIRPSTACK_DEVICE_PROFILE_URL = CHIRPSTACK_BASE_URL + "/device-profiles"
CHIRPSTACK_DEVICE_URL = CHIRPSTACK_BASE_URL + "/devices"
CHIRPSTACK_DEVICE_PROFILE_TEMPLATE_URL = CHIRPSTACK_BASE_URL + "/device-profiles-template"
CHIRPSTACK_APPLICATION_URL = CHIRPSTACK_BASE_URL + "/applications"

HEADERS = {
    "Authorization": f"Bearer {settings.CHIRPSTACK_JWT_TOKEN}",
    "Content-Type": "application/json"
}

