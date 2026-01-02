from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(response.data, list):
            message = response.data[0]
        else:
            message = response.data.get("detail", "Error")

        response.data = {"error": message}

    return response
