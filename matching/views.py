from django.http import JsonResponse


def health(request):
    """Liveness endpoint, used by the container healthcheck."""
    return JsonResponse({"status": "ok"})
