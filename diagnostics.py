import re


def describe_error(exc, key=""):
    # Avoid sending model outputs/transcripts or credential-bearing SDK bodies to the UI.
    name = type(exc).__name__
    code = getattr(exc, "status_code", None)
    if code == 429:
        return "Groq quota or rate limit reached (429). Wait for quota to reset or check your Groq account. No automatic retry was sent."
    if code in (401, 403):
        return f"Groq access error ({code}). Check the key and model permissions."
    if code == 400:
        return "Groq rejected the request (400). Check that GROQ_MODEL supports strict JSON schemas and low reasoning effort."
    if "Timeout" in name or "Connection" in name:
        return "The Groq connection timed out or failed. Your conversation is preserved; you can retry."
    if name == "ValidationError":
        return "The AI response did not match the required structure. Your work is preserved. Retry manually if you wish."
    if isinstance(exc, (ValueError, RuntimeError)):
        text = str(exc).replace(key, "[REDACTED]") if key else str(exc)
        text = re.sub(r"(?:gsk_|AIza)[\w-]+", "[REDACTED]", text)
        return text[:350]
    return f"{name}: this step could not finish. Your conversation is preserved. Check deployment logs without posting API keys."
