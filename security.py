"""
TERRA Security Module
Handles: input validation, rate limiting, password policy,
         SQL injection prevention, XSS sanitisation
"""
import re
import time
import html
import hashlib
import secrets
from datetime import datetime


class Security:
    # Password policy
    MIN_PW_LEN   = 8
    MAX_PW_LEN   = 128
    REQUIRE_NUM  = True
    REQUIRE_SYM  = True

    # Rate limiting
    MAX_ATTEMPTS  = 5
    LOCKOUT_SECS  = 300   # 5 minutes

    # Allowed email pattern
    EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")

    # ── Input sanitisation ────────────────────────────────────────
    def sanitise_text(self, value: str, max_length: int = 500) -> str:
        """Strip HTML/JS, trim whitespace, enforce length."""
        if not value or not isinstance(value, str):
            return ""
        clean = html.escape(value.strip())
        # Remove any null bytes
        clean = clean.replace("\x00", "")
        # Remove common injection patterns
        clean = re.sub(r"[<>{}\[\]\\]", "", clean)
        return clean[:max_length]

    def sanitise_email(self, value: str) -> str:
        """Validate and normalise email address."""
        if not value or not isinstance(value, str):
            return ""
        clean = value.strip().lower()
        if not self.EMAIL_RE.match(clean):
            return ""
        if len(clean) > 254:
            return ""
        return clean

    def sanitise_number(self, value, min_val=0, max_val=1e9, default=0):
        """Clamp numeric input within safe bounds."""
        try:
            v = float(value)
            if v != v:  # NaN check
                return default
            return max(min_val, min(max_val, v))
        except (TypeError, ValueError):
            return default

    # ── Password validation ───────────────────────────────────────
    def validate_password(self, password: str):
        """
        Returns (ok: bool, message: str).
        Policy: min 8 chars, at least 1 digit, at least 1 symbol.
        """
        if not password:
            return False, "Password is required."
        if len(password) < self.MIN_PW_LEN:
            return False, f"Password must be at least {self.MIN_PW_LEN} characters."
        if len(password) > self.MAX_PW_LEN:
            return False, "Password is too long."
        if self.REQUIRE_NUM and not re.search(r"\d", password):
            return False, "Password must contain at least one number."
        if self.REQUIRE_SYM and not re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password):
            return False, "Password must contain at least one symbol (!@#$%^&* etc)."
        return True, "OK"

    # ── Rate limiting ─────────────────────────────────────────────
    def check_rate_limit(self, attempts: int, locked_until: float):
        """Returns (allowed: bool, message: str)."""
        now = time.time()
        if locked_until > now:
            remaining = int(locked_until - now)
            mins, secs = divmod(remaining, 60)
            return False, f"Account temporarily locked. Try again in {mins}m {secs}s."
        if attempts >= self.MAX_ATTEMPTS:
            return False, "Too many attempts. Please wait before trying again."
        return True, "OK"

    # ── CSRF token ────────────────────────────────────────────────
    def generate_csrf_token(self) -> str:
        return secrets.token_hex(32)

    # ── Secure session token ──────────────────────────────────────
    def generate_session_token(self, user_id: int) -> str:
        raw = f"{user_id}:{time.time()}:{secrets.token_hex(16)}"
        return hashlib.sha256(raw.encode()).hexdigest()

    # ── Content Security Policy headers via meta tag ──────────────
    def get_csp_meta(self) -> str:
        return (
            "<meta http-equiv='Content-Security-Policy' "
            "content=\"default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
            "https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' "
            "https://fonts.googleapis.com; "
            "font-src https://fonts.gstatic.com; "
            "img-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';\">"
        )

    # ── PII detection (basic, for logging protection) ─────────────
    def redact_pii(self, text: str) -> str:
        """Redact email addresses and phone numbers from log strings."""
        text = re.sub(self.EMAIL_RE, "[EMAIL REDACTED]", text)
        text = re.sub(r"\b\d{10,13}\b", "[PHONE REDACTED]", text)
        return text