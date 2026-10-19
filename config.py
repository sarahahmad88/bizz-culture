"""Small, explicit app settings. No secrets belong in source control."""
import os

os.environ.setdefault("CREWAI_TELEMETRY_DISABLED", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
LEVELS = {"Beginner": 3, "Intermediate": 8, "Advanced": 15}
MODEL = "openai/gpt-oss-120b"
MAX_RESPONSE_CHARS = 2000
RUBRIC_VERSION = "practice-1.0"
CAVEAT = ("These are provisional practice scores using Hofstede-informed scenario criteria, "
          "not validated assessments of a person or a country. Cultural dimensions describe "
          "broad tendencies; individuals and situations vary.")
