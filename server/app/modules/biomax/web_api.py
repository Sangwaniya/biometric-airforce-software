from fastapi import APIRouter, Request, Response, Depends
from sqlalchemy.orm import Session
import xml.etree.ElementTree as ET
from datetime import datetime
from app.db.database import get_db
from app.db.models import MasterIdentity, GateTransaction
from app.modules.biomax.driver import BiomaxIndigoFaceDriver

router = APIRouter(tags=["Biomax Hardware Integration"])

@router.post("/iclock/WebAPIService.asmx")
async def handle_soap_service(request: Request, db: Session = Depends(get_db)):
    """Implements eTimeTrackLite / Biomax SOAP 1.1 Web API Service."""
    body = await request.body()
    body_str = body.decode("utf-8", errors="ignore")
    
    soap_action = request.headers.get("SOAPAction", "").strip('"')
    method_name = soap_action.split("/")[-1] if "/" in soap_action else "Unknown"

    driver = BiomaxIndigoFaceDriver()

    if "AddEmployee" in method_name or "AddEmployee" in body_str:
        # Parse XML
        emp_code = "UNKNOWN"
        emp_name = "UNKNOWN"
        try:
            root = ET.fromstring(body_str)
            for elem in root.iter():
                if "EmployeeCode" in elem.tag:
                    emp_code = elem.text.strip() if elem.text else ""
                elif "EmployeeName" in elem.tag:
                    emp_name = elem.text.strip() if elem.text else ""
        except Exception:
            pass

        response_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <AddEmployeeResponse xmlns="http://tempuri.org/">
      <AddEmployeeResult>Success</AddEmployeeResult>
      <CommandId>CMD_{int(datetime.utcnow().timestamp())}</CommandId>
    </AddEmployeeResponse>
  </soap:Body>
</soap:Envelope>"""
        return Response(content=response_xml, media_type="text/xml")

    elif "BlockUnblockUser" in method_name or "BlockUnblockUser" in body_str:
        response_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <BlockUnblockUserResponse xmlns="http://tempuri.org/">
      <BlockUnblockUserResult>Success</BlockUnblockUserResult>
      <CommandId>CMD_BLOCK_{int(datetime.utcnow().timestamp())}</CommandId>
    </BlockUnblockUserResponse>
  </soap:Body>
</soap:Envelope>"""
        return Response(content=response_xml, media_type="text/xml")

    elif "GetTransactionsLog" in method_name or "GetTransactionsLog" in body_str:
        # Return transaction log
        logs = db.query(GateTransaction).filter(GateTransaction.channel == "BIOMETRIC_FACE").order_by(GateTransaction.timestamp.desc()).limit(50).all()
        log_lines = []
        for l in logs:
            log_lines.append(f"{l.identifier}\t{l.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\t{l.gate_type}\t{l.status_color}")
        
        data_content = "\\n".join(log_lines)
        response_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <GetTransactionsLogResponse xmlns="http://tempuri.org/">
      <GetTransactionsLogResult>Success</GetTransactionsLogResult>
      <strDataList>{data_content}</strDataList>
    </GetTransactionsLogResponse>
  </soap:Body>
</soap:Envelope>"""
        return Response(content=response_xml, media_type="text/xml")

    # Default fallback ACK
    return Response(content="<soap:Envelope><soap:Body><Response>OK</Response></soap:Body></soap:Envelope>", media_type="text/xml")

@router.get("/iclock/cdata")
async def iclock_cdata_handshake(SN: str = ""):
    """Biomax Push / ADMS device handshake response."""
    return Response(content="OK", media_type="text/plain")

@router.post("/iclock/cdata")
async def iclock_cdata_push(request: Request, SN: str = "", table: str = "ATTLOG", db: Session = Depends(get_db)):
    """Receives live punches pushed automatically by Biomax Indigo Face 8."""
    body = await request.body()
    body_text = body.decode("utf-8", errors="ignore")
    driver = BiomaxIndigoFaceDriver()
    
    # Format per line: PIN \t Date Time \t Status \t VerifyType
    lines = body_text.strip().split("\n")
    processed_count = 0
    for line in lines:
        parts = line.strip().split("\t")
        if len(parts) >= 2:
            pin = parts[0].strip()
            # Register punch in DB
            driver.register_punch(db=db, device_user_pin=pin, gate_id=f"BIOMAX-{SN or 'GATE-01'}")
            processed_count += 1
            
    return Response(content=f"OK: {processed_count}", media_type="text/plain")
