"""
TERRA Authentication Module
Password hashing: bcrypt with cost factor 12
Session: Streamlit session_state (stateless per request)
"""
import hashlib
import os

try:
    import bcrypt
    BCRYPT_AVAILABLE = True
except ImportError:
    BCRYPT_AVAILABLE = False


class Auth:
    COST = 12  # bcrypt work factor

    def __init__(self, db):
        self.db = db

    # ── Password hashing ──────────────────────────────────────────
    def _hash_password(self, password: str) -> str:
        if BCRYPT_AVAILABLE:
            salt = bcrypt.gensalt(rounds=self.COST)
            return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
        else:
            # Fallback: PBKDF2-HMAC-SHA256 (if bcrypt not installed)
            salt = os.urandom(32)
            key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
            return "pbkdf2:" + salt.hex() + ":" + key.hex()

    def _check_password(self, password: str, hashed: str) -> bool:
        if BCRYPT_AVAILABLE and not hashed.startswith("pbkdf2:"):
            try:
                return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
            except Exception:
                return False
        elif hashed.startswith("pbkdf2:"):
            try:
                _, salt_hex, key_hex = hashed.split(":")
                salt = bytes.fromhex(salt_hex)
                key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310000)
                return key.hex() == key_hex
            except Exception:
                return False
        return False

    # ── Register ──────────────────────────────────────────────────
    def register(self, name, email, password, org, plan,
                 agreed_terms, agreed_privacy, marketing=False):
        existing = self.db.get_user_by_email(email)
        if existing:
            return False, "An account with this email already exists."
        try:
            pw_hash = self._hash_password(password)
            self.db.create_user(
                name=name, email=email, password_hash=pw_hash,
                org=org, plan=plan,
                agreed_terms=agreed_terms, agreed_privacy=agreed_privacy,
                marketing=marketing
            )
            self.db.log_event(None, f"REGISTER:{email[:3]}***")
            return True, "Account created."
        except Exception as e:
            return False, f"Registration failed. Please try again."

    # ── Login ─────────────────────────────────────────────────────
    def login(self, email, password):
        user = self.db.get_user_by_email(email)
        if not user:
            return None
        if not self._check_password(password, user.get("password_hash", "")):
            self.db.log_event(user['id'], "LOGIN_FAIL")
            return None
        # Remove hash from session object — never expose it
        user.pop("password_hash", None)
        self.db.update_user(user['id'], last_login=__import__('datetime').datetime.utcnow().isoformat())
        self.db.log_event(user['id'], "LOGIN_OK")
        return user

    # ── Verify current password (for change-password flow) ────────
    def verify_password(self, user_id, password):
        with self.db._conn() as conn:
            row = conn.execute(
                "SELECT password_hash FROM users WHERE id=?", (user_id,)
            ).fetchone()
            if not row:
                return False
            return self._check_password(password, row['password_hash'])

    # ── Change password ───────────────────────────────────────────
    def change_password(self, user_id, new_password):
        new_hash = self._hash_password(new_password)
        self.db.update_password_hash(user_id, new_hash)
        self.db.log_event(user_id, "PASSWORD_CHANGED")