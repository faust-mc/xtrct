import requests
from django.conf import settings

AZURE_VISION_ENDPOINT = getattr(settings, "AZURE_VISION_ENDPOINT", None)
AZURE_VISION_KEY = getattr(settings, "AZURE_VISION_KEY", None)

def analyze_image(image_file):
    """
    Call Azure Computer Vision OCR API with an uploaded image file (synchronous).
    """

    if not AZURE_VISION_ENDPOINT or not AZURE_VISION_KEY:
        return {"error": "Azure Vision endpoint or key not configured."}

    url = f"{AZURE_VISION_ENDPOINT}/computervision/imageanalysis:analyze"
    params = {
        "features": "caption,read",
        "model-version": "latest",
        "language": "en",
        "api-version": "2024-02-01"
    }

    headers = {
        "Ocp-Apim-Subscription-Key": AZURE_VISION_KEY,
        "Content-Type": "application/octet-stream",
    }

    # Read raw bytes
    image_data = image_file.read()

    response = requests.post(url, headers=headers, params=params, data=image_data)

    if response.status_code != 200:
        return {"error": response.text}

    # ✅ For synchronous API → result is in body, not headers
    return response.json()
