from httpx import post, RequestError

# Takes a url and a payload dictionary
def send_webhook(url: str, payload: dict):
    try:
        response = post(url, json=payload, timeout=10)
        if response.is_success:
            return {"success": True, "status_code": response.status_code}
        else:
            return {"success": False, "status_code": response.status_code, "error": response.text}
    # Catches exceptions for timeouts, connection errors, etc.
    except RequestError as e:
        return {"success": False, "status_code": None, "error": str(e)}
