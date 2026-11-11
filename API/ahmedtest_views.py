import time
import threading
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

# In-memory thread-safe room registry for real-time pairing & haptics
# Room structure:
# rooms[code] = {
#     "created_at": timestamp,
#     "last_active": timestamp,
#     "devices": {
#         device_id: {"name": "...", "role": "Device 1"|"Device 2", "last_seen": timestamp}
#     },
#     "events": [
#         {"id": int, "sender_id": str, "style": str, "pattern": list, "timestamp": float}
#     ],
#     "seq": int
# }

_rooms_lock = threading.Lock()
_rooms = {}

def _cleanup_old_rooms():
    """Removes rooms inactive for over 2 hours and trims old events."""
    now = time.time()
    dead_keys = []
    for code, room in _rooms.items():
        if now - room.get("last_active", 0) > 7200:
            dead_keys.append(code)
        else:
            # Keep only events from the last 60 seconds
            room["events"] = [e for e in room["events"] if now - e["timestamp"] < 60]
    for k in dead_keys:
        del _rooms[k]

class AhmedTestView(View):
    """
    Renders the mobile-first AhmedTest vibration pairing interface.
    URL: /ahmedtest/
    """
    def get(self, request):
        return render(request, "API/ahmedtest.html")


@method_decorator(csrf_exempt, name='dispatch')
class VibeJoinView(View):
    """
    Joins or creates a pairing room with a given code (e.g. 123).
    POST /api/ahmedtest/join/
    Body: {"code": "123", "device_id": "...", "device_name": "iPhone 15"}
    """
    def post(self, request):
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        code = str(data.get("code", "")).strip().upper()
        device_id = str(data.get("device_id", "")).strip()
        device_name = str(data.get("device_name", "")).strip() or "Device"

        if not code or not device_id:
            return JsonResponse({"success": False, "error": "Room code and device_id are required."}, status=400)

        now = time.time()
        with _rooms_lock:
            _cleanup_old_rooms()

            if code not in _rooms:
                _rooms[code] = {
                    "created_at": now,
                    "last_active": now,
                    "devices": {},
                    "events": [],
                    "seq": 0
                }

            room = _rooms[code]
            room["last_active"] = now

            # Clean stale devices (inactive for > 45 seconds)
            active_devices = {
                k: v for k, v in room["devices"].items()
                if (now - v["last_seen"] < 45) or (k == device_id)
            }
            room["devices"] = active_devices

            # Assign role
            if device_id in room["devices"]:
                role = room["devices"][device_id]["role"]
            else:
                existing_roles = [d["role"] for d in room["devices"].values()]
                role = "Device 2" if "Device 1" in existing_roles else "Device 1"

            room["devices"][device_id] = {
                "name": device_name,
                "role": role,
                "last_seen": now
            }

            connected = len(room["devices"]) >= 2
            partner_name = ""
            for did, dinfo in room["devices"].items():
                if did != device_id:
                    partner_name = dinfo.get("name") or dinfo.get("role")

            return JsonResponse({
                "success": True,
                "code": code,
                "role": role,
                "connected": connected,
                "devices_count": len(room["devices"]),
                "partner_name": partner_name,
                "latest_seq": room["seq"]
            })


@method_decorator(csrf_exempt, name='dispatch')
class VibeSendView(View):
    """
    Sends a vibration command / pattern to the other paired device.
    POST /api/ahmedtest/send/
    Body: {"code": "123", "device_id": "...", "style": "heartbeat", "pattern": [200, 100, 200]}
    """
    def post(self, request):
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        code = str(data.get("code", "")).strip().upper()
        device_id = str(data.get("device_id", "")).strip()
        style = str(data.get("style", "tap")).strip()
        pattern = data.get("pattern", [100])
        continuous = bool(data.get("continuous", False))

        if not code or not device_id:
            return JsonResponse({"success": False, "error": "Room code and device_id are required."}, status=400)

        now = time.time()
        with _rooms_lock:
            if code not in _rooms:
                return JsonResponse({"success": False, "error": "Room does not exist or has expired."}, status=404)

            room = _rooms[code]
            room["last_active"] = now

            if device_id in room["devices"]:
                room["devices"][device_id]["last_seen"] = now

            room["seq"] += 1
            event = {
                "id": room["seq"],
                "sender_id": device_id,
                "sender_role": room["devices"].get(device_id, {}).get("role", "Partner"),
                "style": style,
                "pattern": pattern,
                "continuous": continuous,
                "timestamp": now
            }
            room["events"].append(event)

            # Keep at most latest 50 events in buffer
            if len(room["events"]) > 50:
                room["events"] = room["events"][-50:]

            return JsonResponse({
                "success": True,
                "seq": room["seq"],
                "style": style
            })


class VibeSyncView(View):
    """
    Polls for new vibration events from the partner device and heartbeats presence.
    GET /api/ahmedtest/sync/?code=123&device_id=...&last_seq=0
    """
    def get(self, request):
        code = str(request.GET.get("code", "")).strip().upper()
        device_id = str(request.GET.get("device_id", "")).strip()
        try:
            last_seq = int(request.GET.get("last_seq", 0))
        except (ValueError, TypeError):
            last_seq = 0

        if not code or not device_id:
            return JsonResponse({"success": False, "error": "Room code and device_id are required."}, status=400)

        now = time.time()
        with _rooms_lock:
            if code not in _rooms:
                return JsonResponse({
                    "success": False,
                    "connected": False,
                    "error": "Room not found or expired"
                }, status=404)

            room = _rooms[code]
            room["last_active"] = now

            if device_id in room["devices"]:
                room["devices"][device_id]["last_seen"] = now
            else:
                # Re-register if needed
                room["devices"][device_id] = {
                    "name": "Device",
                    "role": "Device 2" if len(room["devices"]) >= 1 else "Device 1",
                    "last_seen": now
                }

            # Check partner status: any other device seen in last 12 seconds
            active_partners = [
                dinfo for did, dinfo in room["devices"].items()
                if did != device_id and (now - dinfo.get("last_seen", 0) < 12)
            ]
            connected = len(active_partners) > 0
            partner_name = active_partners[0].get("name") if active_partners else ""
            partner_role = active_partners[0].get("role") if active_partners else ""

            # Filter events: only events from OTHER devices that occurred after last_seq
            new_events = [
                e for e in room["events"]
                if e["id"] > last_seq and e["sender_id"] != device_id
            ]

            return JsonResponse({
                "success": True,
                "connected": connected,
                "partner_name": partner_name,
                "partner_role": partner_role,
                "devices_count": 1 + len(active_partners),
                "latest_seq": room["seq"],
                "events": new_events
            })


@method_decorator(csrf_exempt, name='dispatch')
class VibeLeaveView(View):
    """
    Leaves the room.
    POST /api/ahmedtest/leave/
    Body: {"code": "123", "device_id": "..."}
    """
    def post(self, request):
        import json
        try:
            data = json.loads(request.body.decode('utf-8'))
        except Exception:
            return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

        code = str(data.get("code", "")).strip().upper()
        device_id = str(data.get("device_id", "")).strip()

        with _rooms_lock:
            if code in _rooms and device_id in _rooms[code]["devices"]:
                del _rooms[code]["devices"][device_id]
                if not _rooms[code]["devices"]:
                    del _rooms[code]

        return JsonResponse({"success": True})

