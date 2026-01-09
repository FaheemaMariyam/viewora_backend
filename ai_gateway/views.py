from django.shortcuts import render

# Create your views here.
import requests
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

class AreaInsightsGateway(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            response = requests.post(
                "http://ai_service:8001/ai/area-insights",
                json=request.data,
                timeout=5
            )
            return Response(response.json(), status=response.status_code)

        except requests.exceptions.RequestException as e:
            return Response(
                {"error": "AI service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
