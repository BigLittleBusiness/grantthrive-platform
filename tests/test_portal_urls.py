from app.models import Council


def test_council_portal_url_uses_the_shared_portal_with_a_tenant_selector(monkeypatch):
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://app.grantthrive.com")
    council = Council(name="Green City", subdomain="green-city", slug="green-city")

    assert council.portal_url() == "https://app.grantthrive.com/portal/login/?tenant=green-city"


def test_council_portal_url_encodes_a_nonstandard_tenant_identifier(monkeypatch):
    monkeypatch.setenv("FRONTEND_BASE_URL", "https://portal.example.test/")
    council = Council(name="Test", subdomain="test tenant", slug="test")

    assert council.portal_url() == "https://portal.example.test/portal/login/?tenant=test%20tenant"
