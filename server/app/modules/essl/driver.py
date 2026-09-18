import socket
import struct
import time
import os
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from app.db.models import BiometricCredential, GateTransaction, MasterIdentity, ChildIdentity
from app.core.config import settings, PHOTO_DIR

# eSSL / Standalone SDK Standard Protocol Constants (TCP/UDP port 4370)
CMD_CONNECT = 1000
CMD_EXIT = 1001
CMD_ENABLEDEVICE = 1002
CMD_DISABLEDEVICE = 1003
CMD_GET_LOG_DATA = 1005
CMD_ACK_OK = 2000
CMD_ACK_ERROR = 2001
CMD_ACK_DATA = 2002

class eSSLMultiBiometricDriver:
    """Direct TCP/IP driver for eSSL Multi-Biometric Terminals
       (All-in-One: Face Recognition, Fingerprint & RFID Card Reader).
       Compatible with eSSL uFace, SilkBio, MB160, and AiFace series.
    """
    def __init__(self, ip: str = "192.168.1.201", port: int = 4370, machine_id: int = 1):
        self.ip = ip
        self.port = port
        self.machine_id = machine_id
        self.session_id = 0
        self.reply_id = 0
        self.sock: Optional[socket.socket] = None
        self.connected = False

    def connect(self, timeout: float = 3.0) -> bool:
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(timeout)
            self.sock.connect((self.ip, self.port))
            
            # Send standard eSSL / ZK connect command packet
            pkt = self._create_packet(CMD_CONNECT, 0)
            self.sock.sendall(pkt)
            resp = self.sock.recv(1024)
            if len(resp) >= 8:
                cmd, chksum, session, reply = struct.unpack('<4H', resp[0:8])
                if cmd == CMD_ACK_OK:
                    self.session_id = session
                    self.reply_id = reply
                    self.connected = True
                    return True
            self.connected = False
            return False
        except Exception:
            self.connected = False
            return False

    def disconnect(self):
        if self.sock:
            try:
                pkt = self._create_packet(CMD_EXIT, 0)
                self.sock.sendall(pkt)
                self.sock.close()
            except Exception:
                pass
        self.connected = False

    def _create_packet(self, command: int, checksum: int, data: bytes = b'') -> bytes:
        self.reply_id = (self.reply_id + 1) & 0xFFFF
        top = struct.pack('<4H', command, checksum, self.session_id, self.reply_id)
        raw = top + data
        calc_chk = self._calc_checksum(raw)
        top = struct.pack('<4H', command, calc_chk, self.session_id, self.reply_id)
        return top + data

    def _calc_checksum(self, p: bytes) -> int:
        l = len(p)
        chk = 0
        while l > 1:
            val = struct.unpack('<H', p[0:2])[0]
            chk += val
            p = p[2:]
            l -= 2
        if l:
            chk += p[0]
        chk = (chk >> 16) + (chk & 0xFFFF)
        chk += (chk >> 16)
        return (~chk) & 0xFFFF

    def register_punch(
        self,
        db: Session,
        device_user_pin: str,
        verify_mode: int = 15, # 15 = Face, 1 = Fingerprint, 4 = RFID Card, 0 = Password
        in_out_mode: int = 0,  # 0 = Check-in / Entry, 1 = Check-out / Exit
        gate_id: str = "GATE-01-MAIN"
    ) -> Dict[str, Any]:
        """Processes an incoming verification punch from an eSSL All-in-One hardware device."""
        matched_entity = None
        entity_type = "UNKNOWN"
        entity_name = "Unknown Personnel"
        status_color = "RED"
        status_msg = f"Unregistered eSSL PIN {device_user_pin}"
        barrier_open = False

        # Mode label
        verify_labels = {15: "FACE", 1: "FINGERPRINT", 4: "RFID_CARD", 0: "PIN_CODE"}
        mode_label = verify_labels.get(verify_mode, "BIOMETRIC")

        # 1. Match Master Personnel
        master = db.query(MasterIdentity).filter(
            (MasterIdentity.master_id == device_user_pin) |
            (MasterIdentity.service_number == device_user_pin)
        ).first()

        # 2. Match Child / Dependent / Staff
        child = None
        if not master:
            child = db.query(ChildIdentity).filter(
                (ChildIdentity.child_id == device_user_pin) |
                (ChildIdentity.rfid_card_number == device_user_pin)
            ).first()

        if master:
            entity_type = "MASTER"
            matched_entity = master
            entity_name = f"{master.rank} {master.full_name}"
            if master.status == "ACTIVE":
                status_color = "GREEN"
                status_msg = f"ACCESS GRANTED [{mode_label}] - {entity_name} ({master.unit})"
                barrier_open = True
            else:
                status_color = "RED"
                status_msg = f"ACCESS DENIED - Personnel Status: {master.status}"
                barrier_open = False

        elif child:
            entity_type = "CHILD"
            matched_entity = child
            parent_master = child.master
            entity_name = f"{child.full_name} ({child.relationship_type} of {parent_master.rank} {parent_master.full_name})"
            if child.status == "ACTIVE" and parent_master.status == "ACTIVE":
                status_color = "GREEN"
                status_msg = f"ACCESS GRANTED [{mode_label}] - {entity_name}"
                barrier_open = True
            else:
                status_color = "RED"
                status_msg = f"ACCESS DENIED - Status: {child.status} (Host: {parent_master.status})"
                barrier_open = False

        # Record gate transaction
        gate_type = "ENTRY" if in_out_mode == 0 else "EXIT"
        tx = GateTransaction(
            timestamp=datetime.utcnow(),
            gate_id=gate_id,
            gate_type=gate_type,
            channel=f"ESSL_{mode_label}",
            identifier=device_user_pin,
            matched_entity_type=entity_type,
            matched_entity_id=matched_entity.id if matched_entity else None,
            matched_entity_name=entity_name,
            status_color=status_color,
            status_message=status_msg,
            barrier_actuated=barrier_open,
            sentry_override=False,
            sentry_id="ESSL-UFACE-01"
        )
        db.add(tx)
        db.commit()
        db.refresh(tx)

        return {
            "transaction_id": tx.id,
            "timestamp": tx.timestamp.isoformat(),
            "device_user_pin": device_user_pin,
            "verify_mode": mode_label,
            "gate_id": gate_id,
            "gate_type": gate_type,
            "status_color": status_color,
            "status_message": status_msg,
            "matched_name": entity_name,
            "barrier_actuated": barrier_open
        }
