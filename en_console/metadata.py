"""Server-side validation for provider (Configuration.metadata) settings.

The Configurations page renders each provider's ``config_fields`` (from the
integration MANIFEST) as independent form fields and validates them in the
browser. This module mirrors those exact rules on the backend so the same
guarantees hold when the API is called directly. The metadata itself is still
stored verbatim as raw JSON on ``Configuration.metadata``.
"""
import re

# Kept in lock-step with the regexes used in en_console/templates/en_console/configurations.html
EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
HOST_RE = re.compile(
    r"^(?=.{1,253}$)([a-zA-Z0-9_](?:[a-zA-Z0-9_-]{0,61}[a-zA-Z0-9])?)"
    r"(\.[a-zA-Z0-9_](?:[a-zA-Z0-9_-]{0,61}[a-zA-Z0-9])?)*$"
)
URL_RE = re.compile(r"^https?://[^\s]+\.[^\s]+$")


def _is_empty(value):
    return value is None or (isinstance(value, str) and value.strip() == "")


def _to_int(value):
    """Return an int for whole-number input, else None (bools are rejected)."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return None
    return None


def validate_metadata(config_fields, metadata):
    """Validate/clean ``metadata`` against a provider's ``config_fields``.

    Returns ``(cleaned_metadata, errors)``. ``errors`` is a list of human
    readable strings (empty when valid). ``cleaned_metadata`` keeps every key
    from the input (raw JSON is preserved) but coerces declared ``number`` and
    ``boolean`` fields to their proper JSON types.
    """
    errors = []
    if not isinstance(metadata, dict):
        return metadata, ["Metadata must be a JSON object."]
    # Providers without a manifest schema accept arbitrary JSON as-is.
    if not config_fields:
        return metadata, errors

    cleaned = dict(metadata)
    for field in config_fields:
        name = field.get("name")
        label = field.get("label", name)
        ftype = field.get("type", "text")
        value = metadata.get(name)

        if ftype == "boolean":
            if name in metadata:
                cleaned[name] = bool(value)
            continue

        if _is_empty(value):
            if field.get("required"):
                errors.append(f"{label} is required.")
            continue

        if ftype == "number":
            ivalue = _to_int(value)
            if ivalue is None:
                errors.append(f"{label} must be a whole number.")
                continue
            minimum, maximum = field.get("min"), field.get("max")
            if (minimum is not None and ivalue < minimum) or (
                maximum is not None and ivalue > maximum
            ):
                errors.append(f"{label} must be between {minimum} and {maximum}.")
                continue
            cleaned[name] = ivalue
        elif ftype == "email":
            if not EMAIL_RE.match(str(value)):
                errors.append(f"{label} must be a valid email address.")
        elif ftype == "host":
            if not HOST_RE.match(str(value).strip()):
                errors.append(f"{label} must be a valid hostname.")
        elif ftype == "url":
            if not URL_RE.match(str(value).strip()):
                errors.append(f"{label} must be a valid URL (http:// or https://).")

        # Optional per-field regex format check (applies to any text-like field).
        pattern = field.get("pattern")
        if pattern and ftype not in ("number", "boolean") and not _is_empty(value):
            try:
                if re.match(pattern, str(value).strip()) is None:
                    errors.append(field.get("pattern_message") or f"{label} has an invalid format.")
            except re.error:
                pass

    return cleaned, errors
