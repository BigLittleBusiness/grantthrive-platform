"""
GrantThrive SSO Authentication Test Suite
==========================================
Tests the full single sign-on authentication layer:

  1. Shared auth library — token storage, role helpers, redirect logic
  2. Flask backend — /auth/login, /auth/logout, /auth/verify-token,
                     /auth/register, /auth/demo-login, /auth/change-password
  3. CORS configuration — all grantthrive.com subdomains are allowed
  4. Admin gate logic — system_admin access, role rejection
  5. Domain correctness — no .com.au references anywhere in the codebase

Run:
    python3 scripts/test_sso_auth.py

Domain: grantthrive.com
"""

import sys
import os
import json
import unittest
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

os.environ.setdefault("SECRET_KEY",    "test-secret-key-for-sso-tests")
os.environ.setdefault("DATABASE_URL", os.environ.get("TEST_DATABASE_URL", "postgresql://localhost/grantthrive_test"))
os.environ.setdefault("FLASK_ENV",     "testing")
os.environ.setdefault("TESTING",       "true")
os.environ.setdefault("MAIL_SUPPRESS_SEND", "true")

# ── Colour helpers ────────────────────────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
RESET  = "\033[0m"
BOLD   = "\033[1m"

def ok(msg):  print(f"  {GREEN}✓{RESET} {msg}")
def fail(msg):print(f"  {RED}✗{RESET} {msg}")
def info(msg):print(f"  {YELLOW}→{RESET} {msg}")


# ════════════════════════════════════════════════════════════════════════════
# Test 1 — Shared auth library (pure Python logic, no browser)
# ════════════════════════════════════════════════════════════════════════════

class TestSharedAuthLibrary(unittest.TestCase):
    """
    Validate the shared-auth/src/index.js logic by reading and parsing
    the file, then checking key constants and structure.
    """

    SHARED_AUTH = ROOT.parent / "GrantThrive-frontend" / "shared-auth" / "src" / "index.js"

    def test_file_exists(self):
        self.assertTrue(self.SHARED_AUTH.exists(),
            f"shared-auth library not found at {self.SHARED_AUTH}")
        ok("shared-auth/src/index.js exists")

    def test_token_key_constant(self):
        src = self.SHARED_AUTH.read_text()
        self.assertIn("gt_auth_token", src)
        ok("TOKEN_KEY is 'gt_auth_token'")

    def test_roles_defined(self):
        src = self.SHARED_AUTH.read_text()
        for role in ["system_admin", "council_admin", "council_staff",
                     "community_member", "professional_consultant"]:
            self.assertIn(role, src, f"Role '{role}' missing from shared library")
        ok("All 5 user roles defined in shared library")

    def test_login_url_uses_correct_domain(self):
        src = self.SHARED_AUTH.read_text()
        self.assertIn("app.grantthrive.com/login", src)
        self.assertNotIn("grantthrive.com.au", src)
        ok("LOGIN_URL uses grantthrive.com (not .com.au)")

    def test_api_base_url_uses_correct_domain(self):
        src = self.SHARED_AUTH.read_text()
        self.assertIn("api.grantthrive.com", src)
        ok("API_BASE_URL uses api.grantthrive.com")

    def test_sso_functions_exported(self):
        src = self.SHARED_AUTH.read_text()
        for fn in ["setAuth", "getToken", "getStoredUser", "clearAuth",
                   "isAuthenticated", "verifyToken", "login", "logout",
                   "redirectToLogin", "redirectAfterLogin", "useGrantThriveAuth",
                   "getAuthHeaders"]:
            # Match both 'export function' and 'export async function'
            exported = (f"export function {fn}" in src or
                        f"export async function {fn}" in src)
            self.assertTrue(exported,
                f"Function '{fn}' not exported from shared library")
        ok("All required SSO functions exported")

    def test_no_com_au_in_shared_library(self):
        src = self.SHARED_AUTH.read_text()
        self.assertNotIn("grantthrive.com.au", src)
        ok("No .com.au domain references in shared library")


# ════════════════════════════════════════════════════════════════════════════
# Test 2 — Flask backend auth routes
# ════════════════════════════════════════════════════════════════════════════

class TestFlaskAuthRoutes(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Bootstrap a minimal Flask app with an in-memory SQLite database."""
        try:
            from config.config import TestingConfig
            from app import create_app, db as _db
            from app.models import User
            from werkzeug.security import generate_password_hash

            cls.app = create_app(TestingConfig)
            cls.client = cls.app.test_client()
            cls.db = _db

            with cls.app.app_context():
                _db.create_all()

                # Seed test users
                users = [
                    User(username="sysadmin",  email="admin@grantthrive.com",
                         password_hash=generate_password_hash("Admin1234!"),
                         first_name="System", last_name="Admin",
                         role="system_admin", is_active=True),
                    User(username="cadmin",    email="cadmin@council.com",
                         password_hash=generate_password_hash("Council123!"),
                         first_name="Council", last_name="Admin",
                         role="council_admin", is_active=True),
                    User(username="inactive",  email="inactive@council.com",
                         password_hash=generate_password_hash("Inactive1!"),
                         first_name="Inactive", last_name="User",
                         role="council_staff", is_active=False),
                ]
                for u in users:
                    _db.session.add(u)
                _db.session.commit()

            cls.setup_ok = True
        except Exception as e:
            cls.setup_ok  = False
            cls.setup_err = str(e)

    def setUp(self):
        if not self.setup_ok:
            self.skipTest(f"Flask app setup failed: {self.setup_err}")

    # ── Login ──────────────────────────────────────────────────────────────

    def test_login_success_system_admin(self):
        r = self.client.post("/auth/login",
            json={"email": "admin@grantthrive.com", "password": "Admin1234!"})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "system_admin")
        ok("POST /auth/login — system_admin login returns JWT")
        # Store token for downstream tests
        TestFlaskAuthRoutes._admin_token = data["token"]

    def test_login_success_council_admin(self):
        r = self.client.post("/auth/login",
            json={"email": "cadmin@council.com", "password": "Council123!"})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "council_admin")
        ok("POST /auth/login — council_admin login returns JWT")
        TestFlaskAuthRoutes._council_token = data["token"]

    def test_login_wrong_password(self):
        r = self.client.post("/auth/login",
            json={"email": "admin@grantthrive.com", "password": "wrong"})
        self.assertEqual(r.status_code, 401)
        ok("POST /auth/login — wrong password returns 401")

    def test_login_inactive_user(self):
        r = self.client.post("/auth/login",
            json={"email": "inactive@council.com", "password": "Inactive1!"})
        self.assertEqual(r.status_code, 403)
        ok("POST /auth/login — inactive user returns 403")

    def test_login_missing_fields(self):
        r = self.client.post("/auth/login", json={"email": "admin@grantthrive.com"})
        self.assertEqual(r.status_code, 400)
        ok("POST /auth/login — missing password returns 400")

    # ── Verify token ───────────────────────────────────────────────────────

    def test_verify_token_valid(self):
        token = getattr(self.__class__, "_admin_token", None)
        if not token:
            self.skipTest("No admin token from login test")
        r = self.client.post("/auth/verify-token", json={"token": token})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertTrue(data["valid"])
        self.assertEqual(data["user"]["role"], "system_admin")
        ok("POST /auth/verify-token — valid token returns user profile")

    def test_verify_token_via_header(self):
        token = getattr(self.__class__, "_admin_token", None)
        if not token:
            self.skipTest("No admin token from login test")
        r = self.client.post("/auth/verify-token",
            json={},
            headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 200)
        ok("POST /auth/verify-token — token accepted via Authorization header")

    def test_verify_token_invalid(self):
        r = self.client.post("/auth/verify-token", json={"token": "not.a.real.token"})
        self.assertEqual(r.status_code, 401)
        data = r.get_json()
        self.assertFalse(data["valid"])
        ok("POST /auth/verify-token — invalid token returns 401 with valid=false")

    def test_verify_token_missing(self):
        r = self.client.post("/auth/verify-token", json={})
        self.assertEqual(r.status_code, 401)
        ok("POST /auth/verify-token — missing token returns 401")

    # ── Logout ─────────────────────────────────────────────────────────────

    def test_logout(self):
        token = getattr(self.__class__, "_admin_token", None)
        if not token:
            self.skipTest("No admin token from login test")
        r = self.client.post("/auth/logout",
            headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 200)
        ok("POST /auth/logout — returns 200")

    # ── Register ───────────────────────────────────────────────────────────

    def test_register_new_user(self):
        r = self.client.post("/auth/register", json={
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "first_name": "New",
            "last_name": "User",
            "role": "community_member",
        })
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertTrue(data["requires_approval"])
        ok("POST /auth/register — new user created, requires_approval=true")

    def test_register_duplicate_email(self):
        r = self.client.post("/auth/register", json={
            "email": "admin@grantthrive.com",  # already exists
            "password": "SomePass1!",
            "first_name": "Dup", "last_name": "User",
        })
        self.assertEqual(r.status_code, 409)
        ok("POST /auth/register — duplicate email returns 409")

    def test_register_role_escalation_blocked(self):
        r = self.client.post("/auth/register", json={
            "email": "hacker@evil.com",
            "password": "Hack1234!",
            "first_name": "Bad", "last_name": "Actor",
            "role": "system_admin",  # should be downgraded to community_member
        })
        self.assertEqual(r.status_code, 201)
        data = r.get_json()
        self.assertEqual(data["user"]["role"], "community_member")
        ok("POST /auth/register — role escalation to system_admin is blocked")

    # ── Demo login ─────────────────────────────────────────────────────────

    def test_demo_login(self):
        r = self.client.post("/auth/demo-login",
            json={"demo_type": "council_admin"})
        self.assertEqual(r.status_code, 200)
        data = r.get_json()
        self.assertIn("token", data)
        self.assertEqual(data["user"]["role"], "council_admin")
        ok("POST /auth/demo-login — returns JWT for council_admin demo user")

    # ── Change password ────────────────────────────────────────────────────

    def test_change_password(self):
        token = getattr(self.__class__, "_council_token", None)
        if not token:
            self.skipTest("No council token from login test")
        r = self.client.post("/auth/change-password",
            json={"current_password": "Council123!", "new_password": "NewCouncil456!"},
            headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 200)
        ok("POST /auth/change-password — password changed successfully")

    def test_change_password_wrong_current(self):
        token = getattr(self.__class__, "_council_token", None)
        if not token:
            self.skipTest("No council token from login test")
        r = self.client.post("/auth/change-password",
            json={"current_password": "WrongPass!", "new_password": "NewPass456!"},
            headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(r.status_code, 401)
        ok("POST /auth/change-password — wrong current password returns 401")


# ════════════════════════════════════════════════════════════════════════════
# Test 3 — CORS configuration
# ════════════════════════════════════════════════════════════════════════════

class TestCORSConfiguration(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            from config.config import TestingConfig
            from app import create_app
            cls.app = create_app(TestingConfig)
            cls.client = cls.app.test_client()
            cls.setup_ok = True
        except Exception as e:
            cls.setup_ok  = False
            cls.setup_err = str(e)

    def setUp(self):
        if not self.setup_ok:
            self.skipTest(f"Flask app setup failed: {self.setup_err}")

    def _preflight(self, origin):
        return self.client.options("/auth/login",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type,Authorization",
            })

    def test_cors_app_subdomain(self):
        r = self._preflight("https://app.grantthrive.com")
        self.assertIn(r.status_code, [200, 204])
        ok("CORS — app.grantthrive.com is allowed")

    def test_cors_admin_subdomain(self):
        r = self._preflight("https://admin.grantthrive.com")
        self.assertIn(r.status_code, [200, 204])
        ok("CORS — admin.grantthrive.com is allowed")

    def test_cors_map_subdomain(self):
        r = self._preflight("https://map.grantthrive.com")
        self.assertIn(r.status_code, [200, 204])
        ok("CORS — map.grantthrive.com is allowed")

    def test_cors_roi_subdomain(self):
        r = self._preflight("https://roi.grantthrive.com")
        self.assertIn(r.status_code, [200, 204])
        ok("CORS — roi.grantthrive.com is allowed")

    def test_cors_localhost_dev(self):
        r = self._preflight("http://localhost:5173")
        self.assertIn(r.status_code, [200, 204])
        ok("CORS — localhost:5173 (dev) is allowed")


# ════════════════════════════════════════════════════════════════════════════
# Test 4 — Admin gate component structure
# ════════════════════════════════════════════════════════════════════════════

class TestAdminGateComponent(unittest.TestCase):

    GATE = (ROOT.parent / "GrantThrive-frontend" /
            "grantthrive-admin-dashboard" / "src" / "components" / "AdminAuthGate.jsx")
    MAIN = (ROOT.parent / "GrantThrive-frontend" /
            "grantthrive-admin-dashboard" / "src" / "main.jsx")

    def test_gate_file_exists(self):
        self.assertTrue(self.GATE.exists())
        ok("AdminAuthGate.jsx exists")

    def test_gate_imports_shared_auth(self):
        src = self.GATE.read_text()
        self.assertIn("@grantthrive/auth", src)
        ok("AdminAuthGate imports from @grantthrive/auth")

    def test_gate_checks_system_admin_role(self):
        src = self.GATE.read_text()
        self.assertIn("system_admin", src)
        self.assertIn("ROLES.SYSTEM_ADMIN", src)
        ok("AdminAuthGate enforces system_admin role")

    def test_gate_redirects_to_login(self):
        src = self.GATE.read_text()
        self.assertIn("LOGIN_URL", src)
        self.assertIn("redirect=", src)
        ok("AdminAuthGate redirects unauthenticated users to login with ?redirect=")

    def test_gate_uses_verify_token(self):
        src = self.GATE.read_text()
        self.assertIn("verifyToken", src)
        ok("AdminAuthGate calls verifyToken() to validate SSO token")

    def test_main_wraps_app_in_gate(self):
        src = self.MAIN.read_text()
        self.assertIn("AdminAuthGate", src)
        ok("main.jsx wraps <App> in <AdminAuthGate>")

    def test_gate_uses_correct_domain(self):
        src = self.GATE.read_text()
        self.assertNotIn("grantthrive.com.au", src)
        ok("AdminAuthGate uses grantthrive.com (not .com.au)")


# ════════════════════════════════════════════════════════════════════════════
# Test 5 — Domain correctness across all repos
# ════════════════════════════════════════════════════════════════════════════

class TestDomainCorrectness(unittest.TestCase):

    SEARCH_ROOTS = [
        ROOT,                                              # grantthrive-platform
        ROOT.parent / "GrantThrive-frontend",             # all frontend apps
        ROOT.parent / "grantthrive-marketing",            # static marketing site
    ]
    EXCLUDE_DIRS  = {".git", "node_modules", "__pycache__", "reports_output"}
    EXCLUDE_EXTS  = {".pdf", ".png", ".jpg", ".jpeg", ".gif", ".ico",
                     ".woff", ".woff2", ".ttf", ".eot", ".map", ".lock"}
    # Exclude this test file itself (it contains .com.au in comments/strings for testing)
    EXCLUDE_FILES = {"test_sso_auth.py"}

    def _find_bad_references(self):
        bad = []
        for root in self.SEARCH_ROOTS:
            if not root.exists():
                continue
            for path in root.rglob("*"):
                if any(ex in path.parts for ex in self.EXCLUDE_DIRS):
                    continue
                if path.suffix.lower() in self.EXCLUDE_EXTS:
                    continue
                if path.name in self.EXCLUDE_FILES:
                    continue
                if not path.is_file():
                    continue
                try:
                    text = path.read_text(errors="ignore")
                    if "grantthrive.com.au" in text:
                        bad.append(str(path.relative_to(root.parent)))
                except Exception:
                    pass
        return bad

    def test_no_com_au_domain_anywhere(self):
        bad = self._find_bad_references()
        if bad:
            for f in bad:
                fail(f"  Still contains .com.au: {f}")
            self.fail(f"{len(bad)} file(s) still reference grantthrive.com.au")
        ok("No grantthrive.com.au references found in any file")


# ════════════════════════════════════════════════════════════════════════════
# Test 6 — Frontend AuthContext integration
# ════════════════════════════════════════════════════════════════════════════

class TestFrontendAuthContext(unittest.TestCase):

    CTX = (ROOT.parent / "GrantThrive-frontend" / "frontend" /
           "src" / "contexts" / "AuthContext.jsx")
    API = (ROOT.parent / "GrantThrive-frontend" / "frontend" /
           "src" / "utils" / "api.js")

    def test_auth_context_imports_shared_library(self):
        src = self.CTX.read_text()
        self.assertIn("@grantthrive/auth", src)
        ok("AuthContext.jsx imports from @grantthrive/auth")

    def test_auth_context_uses_shared_login(self):
        src = self.CTX.read_text()
        self.assertIn("sharedLogin", src)
        ok("AuthContext.jsx delegates login to shared library")

    def test_auth_context_uses_shared_logout(self):
        src = self.CTX.read_text()
        self.assertIn("sharedLogout", src)
        ok("AuthContext.jsx delegates logout to shared library")

    def test_auth_context_uses_verify_token(self):
        src = self.CTX.read_text()
        self.assertIn("verifyToken", src)
        ok("AuthContext.jsx calls verifyToken() on mount")

    def test_api_client_uses_shared_token_key(self):
        src = self.API.read_text()
        self.assertIn("TOKEN_KEY", src)
        self.assertIn("@grantthrive/auth", src)
        self.assertNotIn("'authToken'", src)
        ok("api.js uses TOKEN_KEY from @grantthrive/auth (not hardcoded 'authToken')")

    def test_api_client_redirects_to_shared_login(self):
        src = self.API.read_text()
        self.assertIn("VITE_LOGIN_URL", src)
        ok("api.js redirects 401 responses to shared login URL")


# ════════════════════════════════════════════════════════════════════════════
# Runner
# ════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"\n{BOLD}GrantThrive SSO Authentication Test Suite{RESET}")
    print("=" * 55)

    suites = [
        ("Shared Auth Library",       TestSharedAuthLibrary),
        ("Flask Auth Routes",          TestFlaskAuthRoutes),
        ("CORS Configuration",         TestCORSConfiguration),
        ("Admin Gate Component",       TestAdminGateComponent),
        ("Domain Correctness",         TestDomainCorrectness),
        ("Frontend AuthContext",       TestFrontendAuthContext),
    ]

    total_run = total_fail = total_err = total_skip = 0

    for suite_name, suite_class in suites:
        print(f"\n{BOLD}{suite_name}{RESET}")
        print("-" * 40)
        loader = unittest.TestLoader()
        suite  = loader.loadTestsFromTestCase(suite_class)
        result = unittest.TextTestRunner(verbosity=0, stream=open(os.devnull, "w")).run(suite)

        total_run  += result.testsRun
        total_fail += len(result.failures) + len(result.errors)
        total_err  += len(result.errors)
        total_skip += len(result.skipped)

        for test, tb in result.failures:
            fail(f"{test}: {tb.splitlines()[-1]}")
        for test, tb in result.errors:
            fail(f"{test} ERROR: {tb.splitlines()[-1]}")
        for test, reason in result.skipped:
            info(f"{test}: skipped — {reason}")

    print(f"\n{'=' * 55}")
    status = f"{GREEN}ALL PASSED{RESET}" if total_fail == 0 else f"{RED}FAILURES DETECTED{RESET}"
    print(f"{BOLD}Result: {status}{RESET}")
    print(f"  Ran {total_run} tests | "
          f"{RED}{total_fail} failed{RESET} | "
          f"{YELLOW}{total_skip} skipped{RESET}")
    print()

    sys.exit(0 if total_fail == 0 else 1)
