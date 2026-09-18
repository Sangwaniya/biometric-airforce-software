"""Indian Air Force Station Security Management Platform
Main Production Server Launcher
"""
import sys
import os
import uvicorn

sys.path.insert(0, os.path.abspath('server'))

if __name__ == "__main__":
    print("=" * 68)
    print("   INDIAN AIR FORCE STATION SECURITY MANAGEMENT PLATFORM")
    print("   Station: AFS-SEC-01 | Mode: 100% On-Premises Air-Gapped")
    print("   Multi-Biometric (Face+Finger+RFID) & ANPR Gateway Active")
    print("=" * 68)
    print("Workstation Web Console: http://127.0.0.1:8000")
    print("Biometric SOAP Service:  http://127.0.0.1:8000/iclock/WebAPIService.asmx")
    print("Terminal ADMS Push:      http://127.0.0.1:8000/iclock/cdata")
    print("Interactive API Docs:    http://127.0.0.1:8000/docs")
    print("=" * 68)
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False, log_level="info")
