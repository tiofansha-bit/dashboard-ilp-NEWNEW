"""Iteration 10 - verify dashboard KPI cakupan fix (<=100%, intersection with registered)."""
import os
import pytest
import requests


def _read_env(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(key + "="):
                    return line.split("=", 1)[1].strip()
    except Exception:
        return None
    return None


_BE = os.environ.get("REACT_APP_BACKEND_URL") or _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL")
assert _BE, "REACT_APP_BACKEND_URL not set"
BASE = _BE.rstrip("/") + "/api"
ADMIN = {"username": "admin", "password": "admin123"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200
    return r.json()["access_token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}"}


def _check_kpi_invariants(data):
    """dikunjungi <= terdaftar; cakupan <= 100; cakupan == round(dikunjungi/terdaftar*100,1)"""
    t = data["keluarga_terdaftar"]
    d = data["keluarga_dikunjungi"]
    c = data["cakupan"]
    assert isinstance(t, int) and isinstance(d, int)
    assert d <= t, f"dikunjungi ({d}) must be <= terdaftar ({t})"
    assert c <= 100.0, f"cakupan {c}% must be <= 100%"
    if t > 0:
        expected = min(round(d / t * 100, 1), 100.0)
        assert abs(c - expected) < 0.05, f"cakupan {c} != expected {expected}"
    else:
        assert c == 0
    return t, d, c


class TestCakupanFix:
    def test_kpi_no_filter(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/kpi", headers=H(admin_token))
        assert r.status_code == 200
        data = r.json()
        t, d, c = _check_kpi_invariants(data)
        print(f"[no filter] terdaftar={t} dikunjungi={d} cakupan={c}%")
        # Expected per problem statement: 127 terdaftar, 122 dikunjungi, 96.1%
        assert t == 127, f"expected 127 terdaftar, got {t}"
        assert d == 122, f"expected 122 dikunjungi, got {d}"
        assert c == 96.1, f"expected 96.1%, got {c}"

    @pytest.mark.parametrize("kel", ["Selat Hulu", "Selat Tengah", "Selat Dalam", "Selat Utara"])
    def test_kpi_by_kelurahan(self, admin_token, kel):
        r = requests.get(f"{BASE}/dashboard/kpi", headers=H(admin_token), params={"kelurahan": kel})
        assert r.status_code == 200
        data = r.json()
        t, d, c = _check_kpi_invariants(data)
        print(f"[{kel}] terdaftar={t} dikunjungi={d} cakupan={c}%")

    def test_kpi_date_range(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/kpi", headers=H(admin_token),
                         params={"start": "2025-01-01", "end": "2026-12-31"})
        assert r.status_code == 200
        _check_kpi_invariants(r.json())

    def test_kpi_narrow_date_range(self, admin_token):
        # very narrow range -> dikunjungi should drop but still <= terdaftar
        r = requests.get(f"{BASE}/dashboard/kpi", headers=H(admin_token),
                         params={"start": "2026-01-01", "end": "2026-01-02"})
        assert r.status_code == 200
        _check_kpi_invariants(r.json())


class TestOtherDashboardRegression:
    def test_charts(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/charts", headers=H(admin_token))
        assert r.status_code == 200

    def test_insights(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/insights", headers=H(admin_token))
        assert r.status_code == 200

    def test_jawaban(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/jawaban", headers=H(admin_token))
        assert r.status_code == 200

    def test_charts_with_kel(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/charts", headers=H(admin_token),
                         params={"kelurahan": "Selat Tengah"})
        assert r.status_code == 200
