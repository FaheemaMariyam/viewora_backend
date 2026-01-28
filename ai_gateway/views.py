import os

import requests
from django.shortcuts import render
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from properties.models import Property

#Provides AI-powered area insights to users
class AreaInsightsGateway(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai_service:8001")

            # Increased timeout to 20s for GenAI latency
            response = requests.post(
                f"{ai_service_url}/ai/area-insights", json=request.data, timeout=20
            )

            # Check if upstream returned an error
            if response.status_code != 200:
                print(f"AI Service Error: {response.text}")
                return Response(
                    {"error": "AI Service returned an error"},
                    status=response.status_code,
                )

            return Response(response.json(), status=response.status_code)

        except requests.exceptions.Timeout:
            print("AI Service Timeout")
            return Response(
                {"error": "AI took too long to respond. Please try again."},
                status=status.HTTP_504_GATEWAY_TIMEOUT,
            )
        except requests.exceptions.RequestException as e:
            print(f"AI Connection Error: {e}")
            return Response(
                {"error": "AI service unavailable"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )


#The AI service calls this endpoint to fetch property data and build/update its RAG index for answering property-related queries
class PropertiesForRAG(APIView):
    """
    Internal API: provides property data to AI service
    """

    permission_classes = []  # internal service only

    def get(self, request):
        properties = Property.objects.filter(status="published")

        data = []
        for p in properties:
            data.append(
                {
                    "id": p.id,
                    "type": p.property_type,
                    "city": p.city,
                    "locality": p.locality,
                    "price_range": f"{p.price_min}-{p.price_max}",
                    "area_size": p.area_size,
                    "amenities": [],  # keep simple for now
                }
            )

        return Response(data)


#When new properties are added or updated, an admin can trigger this to ensure the AI has the latest data
class SyncAIGateway(APIView):
    """
    Gateway to trigger a RAG index refresh in the AI service
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            ai_service_url = os.getenv("AI_SERVICE_URL", "http://ai_service:8001")
            response = requests.post(f"{ai_service_url}/ai/sync", timeout=30)

            if response.status_code != 200:
                return Response(
                    {"error": "Failed to sync AI service"}, status=response.status_code
                )

            return Response(response.json(), status=200)

        except Exception as e:
            return Response(
                {"error": f"Could not reach AI service: {e}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
