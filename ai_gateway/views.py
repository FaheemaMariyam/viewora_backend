# Create your views here.
import os
import requests
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView


class AreaInsightsGateway(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai_service:8001")
            response = requests.post(
                f"{ai_service_url}/ai/area-insights", json=request.data, timeout=5
            )
            return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "AI service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
