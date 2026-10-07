"""
Full review iteration 9 - exercises all admin menus + kader home-visit flow.

Credentials: admin/admin123, kader11/kader123, MODE_PIN=123456
"""
import os
import time
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
KADER = {"username": "kader11", "password": "kader123"}
MODE_PIN = "123456"


# -------- fixtures --------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE}/auth/login", json=ADMIN, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


@pytest.fixture(scope="module")
def kader_token():
    r = requests.post(f"{BASE}/auth/login", json=KADER, timeout=30)
    assert r.status_code == 200, r.text
    return r.json()["access_token"]


def H(tok):
    return {"Authorization": f"Bearer {tok}", "Content-Type": "application/json"}


# ============ AUTH ============
class TestAuth:
    def test_login_bad(self):
        r = requests.post(f"{BASE}/auth/login", json={"username": "x", "password": "y"})
        assert r.status_code in (400, 401)

    def test_me_admin(self, admin_token):
        r = requests.get(f"{BASE}/auth/me", headers=H(admin_token))
        assert r.status_code == 200
        assert r.json()["role"] == "admin"

    def test_me_kader(self, kader_token):
        r = requests.get(f"{BASE}/auth/me", headers=H(kader_token))
        assert r.status_code == 200
        assert r.json()["role"] == "kader"

    def test_logout(self, admin_token):
        r = requests.post(f"{BASE}/auth/logout", headers=H(admin_token))
        assert r.status_code == 200


# ============ MODE PIN ============
class TestModePin:
    def test_verify_pin_ok(self, admin_token):
        r = requests.post(f"{BASE}/mode/verify-pin", headers=H(admin_token), json={"pin": MODE_PIN})
        assert r.status_code == 200

    def test_verify_pin_bad(self, admin_token):
        r = requests.post(f"{BASE}/mode/verify-pin", headers=H(admin_token), json={"pin": "000000"})
        assert r.status_code == 401

    def test_verify_pin_kader_forbidden(self, kader_token):
        r = requests.post(f"{BASE}/mode/verify-pin", headers=H(kader_token), json={"pin": MODE_PIN})
        assert r.status_code == 403


# ============ MASTER ============
class TestMaster:
    def test_wilayah(self, admin_token):
        r = requests.get(f"{BASE}/master/wilayah", headers=H(admin_token))
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_posyandu(self, admin_token):
        r = requests.get(f"{BASE}/master/posyandu", headers=H(admin_token))
        assert r.status_code == 200

    def test_groups(self, admin_token):
        r = requests.get(f"{BASE}/master/groups", headers=H(admin_token))
        assert r.status_code == 200 and len(r.json()) > 0

    def test_questions_list(self, admin_token):
        r = requests.get(f"{BASE}/master/questions", headers=H(admin_token))
        assert r.status_code == 200 and len(r.json()) > 0

    def test_question_crud(self, admin_token):
        payload = {
            "text": "TEST_pertanyaan review iter9",
            "group": "bayi",
            "section": "ceklis",
            "jenis": "yesno",
            "opsi": ["Ya", "Tidak"],
            "problem_when": ["Ya"],
            "priority": "kuning",
        }
        r = requests.post(f"{BASE}/master/questions", headers=H(admin_token), json=payload)
        assert r.status_code == 200, r.text
        kode = r.json()["kode"]
        # update
        r2 = requests.put(f"{BASE}/master/questions/{kode}", headers=H(admin_token),
                          json={"text": "TEST_pertanyaan updated"})
        assert r2.status_code == 200
        assert r2.json()["text"] == "TEST_pertanyaan updated"
        # delete
        r3 = requests.delete(f"{BASE}/master/questions/{kode}", headers=H(admin_token))
        assert r3.status_code == 200


# ============ DASHBOARD / RECAP / INSIGHT ============
class TestDashboard:
    def test_kpi(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/kpi", headers=H(admin_token))
        assert r.status_code == 200

    def test_charts(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/charts", headers=H(admin_token))
        assert r.status_code == 200

    def test_jawaban(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/jawaban", headers=H(admin_token))
        assert r.status_code == 200

    def test_insights(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/insights", headers=H(admin_token))
        assert r.status_code == 200

    def test_rekap_kader(self, admin_token):
        r = requests.get(f"{BASE}/dashboard/rekap-kader", headers=H(admin_token))
        assert r.status_code == 200

    def test_rekap(self, admin_token):
        r = requests.get(f"{BASE}/rekap", headers=H(admin_token))
        assert r.status_code == 200


# ============ KASUS / TINDAK LANJUT ============
class TestKasusTindakLanjut:
    def test_list_kasus(self, admin_token):
        r = requests.get(f"{BASE}/kasus", headers=H(admin_token))
        assert r.status_code == 200

    def test_tindak_lanjut_sumber(self, admin_token):
        r = requests.get(f"{BASE}/admin/tindak-lanjut/sumber", headers=H(admin_token))
        assert r.status_code == 200

    def test_tindak_lanjut_list(self, admin_token):
        r = requests.get(f"{BASE}/admin/tindak-lanjut", headers=H(admin_token))
        assert r.status_code == 200


# ============ KADER MGMT ============
class TestKaderMgmt:
    def test_list_kader(self, admin_token):
        r = requests.get(f"{BASE}/admin/kader", headers=H(admin_token))
        assert r.status_code == 200 and len(r.json()) > 0


# ============ IMPORT TEMPLATES ============
class TestImportTemplates:
    def test_tpl_keluarga(self, admin_token):
        r = requests.get(f"{BASE}/admin/import/template/keluarga", headers=H(admin_token))
        assert r.status_code == 200

    def test_tpl_kader(self, admin_token):
        r = requests.get(f"{BASE}/admin/import/template/kader", headers=H(admin_token))
        assert r.status_code == 200

    def test_tpl_pertanyaan(self, admin_token):
        r = requests.get(f"{BASE}/admin/import/template/pertanyaan", headers=H(admin_token))
        assert r.status_code == 200


# ============ LAPORAN & EXPORT ============
class TestLaporan:
    def test_laporan_settings(self, admin_token):
        r = requests.get(f"{BASE}/admin/laporan-settings", headers=H(admin_token))
        assert r.status_code == 200

    @pytest.mark.parametrize("jenis", ["kasus", "kunjungan", "keluarga", "tindak_lanjut", "masalah_sasaran", "masalah_kolektif"])
    def test_preview(self, admin_token, jenis):
        r = requests.get(f"{BASE}/laporan/preview/{jenis}", headers=H(admin_token))
        assert r.status_code == 200, f"{jenis}: {r.status_code} {r.text[:200]}"

    @pytest.mark.parametrize("jenis", ["kasus", "kunjungan", "keluarga", "tindak_lanjut"])
    @pytest.mark.parametrize("fmt", ["csv", "xlsx", "pdf"])
    def test_export(self, admin_token, jenis, fmt):
        r = requests.get(f"{BASE}/export/{jenis}?format={fmt}", headers=H(admin_token))
        assert r.status_code == 200, f"{jenis}/{fmt}: {r.status_code} {r.text[:200]}"


# ============ AUDIT / NOTIF / AKREDITASI ============
class TestMisc:
    def test_audit(self, admin_token):
        r = requests.get(f"{BASE}/audit", headers=H(admin_token))
        assert r.status_code == 200

    def test_notif(self, admin_token):
        r = requests.get(f"{BASE}/notifikasi", headers=H(admin_token))
        assert r.status_code == 200

    def test_akreditasi(self, admin_token):
        r = requests.get(f"{BASE}/akreditasi", headers=H(admin_token))
        assert r.status_code == 200


# ============ KADER FLOW ============
class TestKaderFlow:
    created_keluarga_id = None
    created_anggota_id = None
    created_kunjungan_id = None

    def test_beranda(self, kader_token):
        r = requests.get(f"{BASE}/kader/beranda", headers=H(kader_token))
        assert r.status_code == 200

    def test_laporan_status(self, kader_token):
        r = requests.get(f"{BASE}/kader/laporan-status", headers=H(kader_token))
        assert r.status_code == 200

    def test_list_my_keluarga(self, kader_token):
        r = requests.get(f"{BASE}/keluarga", headers=H(kader_token))
        assert r.status_code == 200
        data = r.json()
        assert "items" in data

    def test_create_keluarga_and_anggota_and_visit(self, kader_token, admin_token):
        # get kader's wilayah
        me = requests.get(f"{BASE}/auth/me", headers=H(kader_token)).json()
        kelurahan = (me.get("wilayah") or ["Selat Tengah"])[0]
        payload = {
            "nama_kk": "TEST_KK_iter9",
            "nik_kk": "1234567890123456",
            "alamat": "Jl Test 1",
            "rt": "01", "rw": "02",
            "kelurahan": kelurahan,
            "posyandu": "",
            "no_hp": "081234567890",
            "jumlah_anggota": 1,
        }
        r = requests.post(f"{BASE}/keluarga", headers=H(kader_token), json=payload)
        assert r.status_code == 200, r.text
        kid = r.json()["id"]
        TestKaderFlow.created_keluarga_id = kid

        # add anggota (bayi for simple rule evaluation)
        anggota = {
            "keluarga_id": kid, "nama": "TEST_Anak",
            "nik": "1234567890123457",
            "tanggal_lahir": "2024-01-01", "jk": "L",
            "hubungan": "Anak", "status": "hidup",
        }
        r2 = requests.post(f"{BASE}/anggota", headers=H(kader_token), json=anggota)
        assert r2.status_code == 200, r2.text
        aid = r2.json()["id"]
        TestKaderFlow.created_anggota_id = aid

        # verify GET keluarga returns anggota
        r3 = requests.get(f"{BASE}/keluarga/{kid}", headers=H(kader_token))
        assert r3.status_code == 200
        assert any(a["id"] == aid for a in r3.json().get("anggota", []))

        # Create kunjungan with no answers (hijau prioritas)
        visit = {
            "keluarga_id": kid, "anggota_ids": [aid],
            "answers": {aid: {}}, "edukasi": {}, "tanggal": None,
            "catatan": "TEST visit", "gps": None,
            "status": "selesai", "reminder_confirmed": True,
        }
        r4 = requests.post(f"{BASE}/kunjungan", headers=H(kader_token), json=visit)
        assert r4.status_code == 200, r4.text
        vid = r4.json()["id"]
        TestKaderFlow.created_kunjungan_id = vid

        # Admin can see the visit
        r5 = requests.get(f"{BASE}/kunjungan/{vid}", headers=H(admin_token))
        assert r5.status_code == 200

        # Kader list of visits includes this one
        r6 = requests.get(f"{BASE}/kunjungan?mine=true", headers=H(kader_token))
        assert r6.status_code == 200
        assert any(v["id"] == vid for v in r6.json())

    def test_cleanup(self, kader_token, admin_token):
        kid = TestKaderFlow.created_keluarga_id
        if kid:
            r = requests.delete(f"{BASE}/keluarga/{kid}", headers=H(kader_token))
            assert r.status_code == 200
