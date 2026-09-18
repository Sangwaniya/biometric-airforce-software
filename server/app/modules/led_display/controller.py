import socket
import json
from typing import Dict, Any, Optional

class GateLEDDisplayController:
    """Controls outdoor large LED matrix screens mounted at station gates.
       Broadcasts real-time color-coded verification alerts (Green, Yellow, Red).
    """

    COLOR_CODES = {
        "GREEN": "\x1b[32m",   # Green color tag
        "YELLOW": "\x1b[33m",  # Yellow/Amber color tag
        "RED": "\x1b[31m",     # Red color tag
        "RESET": "\x1b[0m"
    }

    def __init__(self, display_ip: str = "192.168.1.180", display_port: int = 5005, protocol: str = "UDP"):
        self.display_ip = display_ip
        self.display_port = display_port
        self.protocol = protocol
        self.last_broadcast: Optional[Dict[str, Any]] = None

    def format_frame(self, plate: str, owner: str, status_color: str, message: str) -> Dict[str, Any]:
        """Formats visual lines for matrix LED screen (e.g., 64x32 or 128x64)."""
        color = status_color.upper()
        if color not in self.COLOR_CODES:
            color = "RED"

        line1 = f"{plate.center(16)}"
        line2 = f"{owner[:16].center(16)}"
        line3 = f"[{color}] {message[:14]}"

        return {
            "screen_ip": self.display_ip,
            "color": color,
            "line_1": line1,
            "line_2": line2,
            "line_3": line3,
            "raw_text": f"{line1}\n{line2}\n{line3}"
        }

    def broadcast_alert(self, plate: str, owner: str, status_color: str, message: str) -> Dict[str, Any]:
        """Transmits formatted display packet to LED controller."""
        frame = self.format_frame(plate, owner, status_color, message)
        self.last_broadcast = frame

        packet_payload = json.dumps(frame).encode('utf-8')

        try:
            if self.protocol == "UDP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(1.0)
                sock.sendto(packet_payload, (self.display_ip, self.display_port))
                sock.close()
            elif self.protocol == "TCP":
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1.0)
                sock.connect((self.display_ip, self.display_port))
                sock.sendall(packet_payload)
                sock.close()
            delivery_status = "SENT_TO_HARDWARE"
        except Exception as e:
            # When running on simulation or if physical LED screen is offline
            delivery_status = f"SIMULATED_SUCCESS ({str(e)})"

        frame["delivery_status"] = delivery_status
        return frame
