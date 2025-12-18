from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ObjectDoesNotExist


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        message = response.data.get("detail", None)

        return Response(
            {
                "success": False,
                "message": message if message else "Validation error",
                "errors": response.data if isinstance(response.data, dict) else {}
            },
            status=response.status_code
        )

    if isinstance(exc, ObjectDoesNotExist):
        return Response(
            {
                "success": False,
                "message": "Resource not found",
                "errors": {}
            },
            status=status.HTTP_404_NOT_FOUND
        )

    return Response(
        {
            "success": False,
            "message": "Internal server error",
            "errors": {}
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
