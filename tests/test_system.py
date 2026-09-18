import sys, os
sys.path.insert(0, os.path.abspath('server'))
from fastapi.testclient import TestClient
from app.main import app
import time

def test_full_system():
    with TestClient(app) as client:
        print("\n=======================================================")
        print("  RUNNING COMPREHENSIVE MULTI-BIOMETRIC PLATFORM REGRESSION TEST  ")
        print("=======================================================")

        # 1. Health check
        h = client.get('/health')
        assert h.status_code == 200
        assert h.json()['mode'] == 'AIR_GAPPED_ON_PREM'
        assert h.json()['hardware_integration'] in ('MULTI_BIOMETRIC_ACTIVE', 'eSSL_MULTI_BIOMETRIC_ACTIVE')
        print("[PASS] 1. Centralized Server Health Check (Multi-Biometric Active & Air-Gapped)")

        # 2. Master ID Hierarchy Test (Air Force Personnel & Dependents)
        tree = client.get('/api/identity/tree/32')
        assert tree.status_code == 200
        data = tree.json()
        assert data['master']['master_id'] == '32'
        child_ids = [c['child_id'] for c in data['children']]
        assert '32.1' in child_ids
        assert '32.2' in child_ids
        assert '32.D1' in child_ids
        print("[PASS] 2. Master ID Hierarchy (Master 32 -> Spouse 32.1, Child 32.2, Domestic Cook 32.D1)")

        # 3. Vehicle Validation & Gate Alert Matrix with Expiry Countdowns
        # Green (Tata Safari)
        vg = client.post('/api/vehicle/validate', json={'plate_number': 'DL01AB1234'}).json()
        assert vg['status_color'] == 'GREEN'
        assert vg['barrier_actuated'] is True
        assert vg['analytics']['insurance']['months_remaining'] > 6
        print(f"[PASS] 3a. Vehicle GREEN (DL01AB1234): Insurance has {vg['analytics']['insurance']['months_remaining']} months remaining -> Barrier OPEN")

        # Yellow (Royal Enfield - Expiring current month)
        vy = client.post('/api/vehicle/validate', json={'plate_number': 'HR26DQ5555'}).json()
        assert vy['status_color'] == 'YELLOW'
        assert 'Insurance expires' in vy['status_message']
        assert vy['barrier_actuated'] is True
        print(f"[PASS] 3b. Vehicle YELLOW (HR26DQ5555): Insurance expiring this month ({vy['analytics']['insurance']['days_remaining']} days left) -> Barrier OPEN with Warning")

        # Red (Hyundai Creta - Expired Insurance)
        vr = client.post('/api/vehicle/validate', json={'plate_number': 'UP16AX9999'}).json()
        assert vr['status_color'] == 'RED'
        assert vr['barrier_actuated'] is False
        assert vr['analytics']['insurance']['status'] == 'EXPIRED'
        print(f"[PASS] 3c. Vehicle RED (UP16AX9999): Insurance EXPIRED ({abs(vr['analytics']['insurance']['days_remaining'])} days ago) -> Barrier HALTED")

        # Red (Unregistered plate)
        v_unreg = client.post('/api/vehicle/validate', json={'plate_number': 'CH01XX0000'}).json()
        assert v_unreg['status_color'] == 'RED'
        assert 'UNREGISTERED' in v_unreg['status_message']
        print("[PASS] 3d. Vehicle RED (CH01XX0000): Unregistered plate -> Barrier HALTED")

        # 4. All-in-One Multi-Biometric Punch Test (Face, Fingerprint, RFID)
        # Face Punch
        ep_face = client.post('/api/biometric/punch', json={'device_user_pin': '32', 'verify_mode': 15}).json()
        assert ep_face['status_color'] == 'GREEN'
        assert 'FACE' in ep_face['verify_mode']
        print("[PASS] 4a. Face Recognition Punch (Master 32: Wg Cdr Rajesh Sharma) -> Access Granted")

        # Fingerprint Punch
        ep_finger = client.post('/api/biometric/punch', json={'device_user_pin': '32', 'verify_mode': 1}).json()
        assert ep_finger['status_color'] == 'GREEN'
        assert 'FINGERPRINT' in ep_finger['verify_mode']
        print("[PASS] 4b. Optical Fingerprint Punch (Master 32) -> Access Granted")

        # RFID Card Tap (Domestic Staff) - Also test backward compatible /api/essl/punch route
        ep_card = client.post('/api/essl/punch', json={'device_user_pin': '32.D1', 'verify_mode': 4}).json()
        assert ep_card['status_color'] == 'GREEN'
        assert 'RFID_CARD' in ep_card['verify_mode']
        print("[PASS] 4c. RFID Card Tap (Domestic Cook 32.D1: Ramesh Kumar) -> Access Granted")

        # 5. Channel 3: Direct SQL Sync Test
        sample_sql_emp = [
            {'EmployeeCode': f'SQL{int(time.time())%1000}', 'EmployeeName': 'Flight Lt S Kulkarni', 'Designation': 'Officer', 'Department': 'Fighter Wing'}
        ]
        sql_res = client.post('/api/biometric/sync_sql', json={'sync_type': 'EMPLOYEES', 'records': sample_sql_emp}).json()
        assert sql_res['status'] == 'SQL_SYNC_COMPLETED'
        assert sql_res['imported_masters'] == 1
        print("[PASS] 5. Channel 3: Direct SQL Table Synchronization (Biometric Database Sync) -> 1 Master Imported")

        # 6. Workstation Dashboard: Present vs Absent & On-Premise Tracking
        cmd = client.get('/api/command/status').json()
        assert cmd['metrics']['total_employees'] >= 1
        assert cmd['metrics']['employees_present'] >= 1
        assert len(cmd['present_employees']) >= 1
        assert len(cmd['on_premise_people']) >= 1
        print(f"[PASS] 6a. Workstation Attendance Matrix: {cmd['metrics']['employees_present']} Present, {cmd['metrics']['employees_absent']} Absent")
        print(f"[PASS] 6b. Live On-Premise Tracker: {len(cmd['on_premise_people'])} souls currently entered and not exited")

        # 7. Emergency Muster Roll & Evacuation Manifest
        muster = client.get('/api/command/muster_roll').json()
        assert muster['report_type'] == 'EMERGENCY MUSTER ROLL & EVACUATION MANIFEST'
        assert muster['total_headcount'] >= 1
        print(f"[PASS] 7. Emergency Muster Roll Generated ({muster['total_headcount']} souls accounted for)")

        # 8. Offline Aadhaar QR Parsing Test (Zero-Biometric DPDP-23 compliance)
        xml_qr = '<PrintLetterBarcodeData name="Squadron Leader Devendra" dob="1987-08-22" gender="M" uid="123456789012" house="B-4" dist="Ambala" state="Haryana"/>'
        qr_res = client.post('/api/visitor/parse_aadhaar_qr', json={'raw_qr_data': xml_qr}).json()
        assert qr_res['success'] is True
        assert qr_res['masked_aadhaar'] == 'XXXX-XXXX-9012'
        assert qr_res['zero_biometric_guarantee'] is True
        print("[PASS] 8. Offline Aadhaar QR Parser (Zero-Biometric DPDP-23 Masked: XXXX-XXXX-9012)")

        # 9. Overstay Engine Evaluation & Alerts
        overstay_eval = client.post('/api/command/evaluate_overstays').json()
        assert overstay_eval['status'] == 'EVALUATED'
        print("[PASS] 9. Automated Overstay Engine Watchdog -> Successfully monitored active passes")

        # 10. Forensic Audit Ledger Cryptographic Hash Chain Verification
        audit = client.get('/api/audit/verify_integrity').json()
        assert audit['status'] == 'VERIFIED_INTEGRITY'
        assert len(audit['corrupted_records']) == 0
        print(f"[PASS] 10. Forensic Audit Ledger SHA-256 Cryptographic Chain -> VERIFIED_INTEGRITY ({audit['total_records']} immutable records)")

        print("\n=======================================================")
        print("  ALL 10 MULTI-BIOMETRIC SUITE TESTS PASSED!          ")
        print("=======================================================\n")

if __name__ == '__main__':
    test_full_system()
