# -*- coding: utf-8 -*-
"""
HTTP API Plugin for pyphira-mp
提供房间查询、管理、OTP 鉴权、封禁控制的 HTTP 接口。
"""

import asyncio
import logging
import os
import secrets
import sys
import time
import uuid
from typing import Any, Dict

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from utils.room import destroy_room, rooms

main_module = sys.modules["__main__"]

PLUGIN_INFO = {
    "name": "http_api",
    "version": "1.1.0",
}

app = FastAPI()
logger = logging.getLogger("plugin.http_api")

logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)


def get_cors_origins():
    raw = os.environ.get("HTTP_API_CORS_ORIGINS", "https://admin.phira.link")
    origins = [item.strip() for item in raw.split(",") if item.strip()]
    return origins or ["https://admin.phira.link"]


app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

room_creation_enabled = True
room_limits_ref = {}

otp_sessions: Dict[str, Dict[str, Any]] = {}
temp_tokens: Dict[str, Dict[str, Any]] = {}


def get_admin_token():
    return os.environ.get("ADMIN_TOKEN", None)


def clean_expired_tokens():
    now = time.time()
    for key in list(otp_sessions.keys()):
        if otp_sessions[key]["expires_at"] < now:
            del otp_sessions[key]
    for key in list(temp_tokens.keys()):
        if temp_tokens[key]["expires_at"] < now:
            del temp_tokens[key]


def parse_room_id(room_id: str):
    try:
        return int(room_id) if room_id.isdigit() else room_id
    except ValueError:
        return None


async def read_json_body(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}


@app.middleware("http")
async def private_network_middleware(request: Request, call_next):
    response = await call_next(request)
    if request.headers.get("access-control-request-private-network", "").lower() == "true":
        response.headers["Access-Control-Allow-Private-Network"] = "true"
    return response


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if not path.startswith("/admin/"):
        return await call_next(request)
    if path in ["/admin/otp/request", "/admin/otp/verify"]:
        return await call_next(request)

    token = (
        request.headers.get("X-Admin-Token")
        or request.headers.get("Authorization")
        or request.query_params.get("token")
    )
    if token and token.startswith("Bearer "):
        token = token[7:]

    perm_token = get_admin_token()
    if perm_token:
        if token != perm_token:
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
        return await call_next(request)

    if not token:
        return JSONResponse({"ok": False, "error": "admin-disabled"}, status_code=403)

    clean_expired_tokens()
    client_ip = request.client.host if request.client else None
    t_info = temp_tokens.get(token)
    if not t_info or t_info["expires_at"] < time.time() or t_info["ip"] != client_ip:
        return JSONResponse({"ok": False, "error": "token-expired"}, status_code=401)

    return await call_next(request)


@app.post("/admin/otp/request")
async def otp_request():
    if get_admin_token():
        return JSONResponse(
            {"ok": False, "error": "otp-disabled-when-token-configured"},
            status_code=403,
        )

    clean_expired_tokens()
    ssid = str(uuid.uuid4())
    otp = secrets.token_hex(4)
    expires_in = 300000
    otp_sessions[ssid] = {"otp": otp, "expires_at": time.time() + 300}

    logger.info("[OTP Request] SSID: %s, OTP: %s, Expires in 5 minutes", ssid, otp)
    return {"ok": True, "ssid": ssid, "expiresIn": expires_in}


@app.post("/admin/otp/verify")
async def otp_verify(request: Request):
    if get_admin_token():
        return JSONResponse(
            {"ok": False, "error": "otp-disabled-when-token-configured"},
            status_code=403,
        )

    data = await read_json_body(request)
    ssid = data.get("ssid")
    otp = data.get("otp")

    clean_expired_tokens()
    session = otp_sessions.get(ssid)
    if not session or session["otp"] != otp or session["expires_at"] < time.time():
        return JSONResponse({"ok": False, "error": "invalid-or-expired-otp"}, status_code=401)

    del otp_sessions[ssid]
    token = str(uuid.uuid4())
    expires_in = 14400000
    temp_tokens[token] = {
        "ip": request.client.host if request.client else None,
        "expires_at": time.time() + 14400,
    }
    return {
        "ok": True,
        "token": token,
        "expiresAt": int(time.time() * 1000) + expires_in,
        "expiresIn": expires_in,
    }


@app.get("/room")
async def get_public_rooms():
    res = []
    for rid, room in rooms.items():
        host_info = {"id": room.host, "name": str(room.host)}
        players = []
        for uid, ruser in room.users.items():
            name = getattr(ruser.info, "name", str(uid))
            players.append({"id": uid, "name": name})
            if uid == room.host:
                host_info["name"] = name

        res.append(
            {
                "roomid": str(rid),
                "cycle": getattr(room, "cycle", False),
                "lock": getattr(room, "locked", False),
                "host": host_info,
                "state": type(room.state).__name__.lower(),
                "chart": {
                    "id": getattr(room, "chart", None),
                    "name": str(getattr(room, "chart", "Unknown")),
                },
                "players": players,
            }
        )
    return {"rooms": res, "total": len(res)}


@app.get("/admin/rooms")
async def admin_get_rooms():
    res = []
    for rid, room in rooms.items():
        users_list = []
        for uid, ruser in room.users.items():
            users_list.append(
                {
                    "id": uid,
                    "name": getattr(ruser.info, "name", str(uid)),
                    "connected": ruser.connection is not None,
                    "is_host": uid == room.host,
                    "finished": uid in getattr(room, "finished", {}),
                    "ready": uid in getattr(room, "ready", {}),
                }
            )

        res.append(
            {
                "roomid": str(rid),
                "max_users": room_limits_ref.get(rid, "无限制"),
                "live": getattr(room, "live", False),
                "locked": getattr(room, "locked", False),
                "cycle": getattr(room, "cycle", False),
                "host": {"id": room.host},
                "state": {"type": type(room.state).__name__.lower()},
                "chart": {"id": getattr(room, "chart", None)},
                "users": users_list,
                "contest": getattr(room, "contest_mode", False),
                "whitelist": getattr(room, "whitelist", []),
            }
        )
    return {"ok": True, "rooms": res}


@app.post("/admin/rooms/{room_id}/max_users")
async def admin_set_max_users(room_id: str, request: Request):
    data = await read_json_body(request)
    max_users = data.get("maxUsers")
    if not isinstance(max_users, int) or not (1 <= max_users <= 64):
        return JSONResponse({"ok": False, "error": "bad-max-users"}, status_code=400)

    rid = parse_room_id(room_id)
    if rid is None:
        return JSONResponse({"ok": False, "error": "bad-room-id"}, status_code=400)

    if rid not in rooms:
        return JSONResponse({"ok": False, "error": "room-not-found"}, status_code=404)

    room_limits_ref[rid] = max_users
    return {"ok": True, "roomid": str(rid), "max_users": max_users}


@app.post("/admin/rooms/{room_id}/disband")
async def admin_disband_room(room_id: str):
    rid = parse_room_id(room_id)
    if rid is None:
        return JSONResponse({"ok": False, "error": "bad-room-id"}, status_code=400)

    room = rooms.get(rid)
    if not room:
        return JSONResponse({"ok": False, "error": "room-not-found"}, status_code=404)

    from rymc.phira.protocol.data.message import LeaveRoomMessage
    from rymc.phira.protocol.packet.clientbound import (
        ClientBoundLeaveRoomPacket,
        ClientBoundMessagePacket,
    )

    for _, ruser in list(room.users.items()):
        try:
            ruser.connection.send(ClientBoundMessagePacket(LeaveRoomMessage(-1, "房间已被管理员强制解散")))
            ruser.connection.send(ClientBoundLeaveRoomPacket.Success())
        except Exception:
            pass

    destroy_room(rid)
    return {"ok": True, "roomid": str(rid)}


@app.get("/admin/room-creation/config")
async def admin_room_creation_get():
    return {"ok": True, "enabled": room_creation_enabled}


@app.post("/admin/room-creation/config")
async def admin_room_creation_post(request: Request):
    global room_creation_enabled
    data = await read_json_body(request)
    if "enabled" not in data:
        return JSONResponse({"ok": False, "error": "bad-enabled"}, status_code=400)

    room_creation_enabled = bool(data["enabled"])
    return {"ok": True, "enabled": room_creation_enabled}


@app.post("/admin/ban/user")
async def admin_ban_user(request: Request):
    data = await read_json_body(request)
    uid = data.get("userId")
    banned = data.get("banned", True)
    disconnect = data.get("disconnect", True)

    if not uid:
        return JSONResponse({"ok": False, "error": "bad-user-id"}, status_code=400)

    if banned:
        main_module.security_store.add_ban("id", str(uid), None, "API 封禁")
    else:
        main_module.security_store.remove_ban("id", str(uid))

    if disconnect and banned:
        conn = main_module.online_user_list.get(uid) or main_module.online_user_list.get(str(uid))
        if conn:
            try:
                conn.close()
            except Exception:
                pass

    return {"ok": True}


@app.post("/admin/users/{user_id}/disconnect")
async def admin_kick_user(user_id: str):
    uid = parse_room_id(user_id)
    if uid is None:
        return JSONResponse({"ok": False, "error": "bad-user-id"}, status_code=400)

    conn = main_module.online_user_list.get(uid)
    if not conn:
        return JSONResponse({"ok": False, "error": "user-not-connected"}, status_code=404)

    try:
        conn.close()
    except Exception:
        pass
    return {"ok": True}


@app.post("/admin/broadcast")
async def admin_broadcast(request: Request):
    data = await read_json_body(request)
    msg = data.get("message", "")
    if not msg:
        return JSONResponse({"ok": False, "error": "bad-message"}, status_code=400)
    if len(msg) > 200:
        return JSONResponse({"ok": False, "error": "message-too-long"}, status_code=400)

    from rymc.phira.protocol.data.message import ChatMessage
    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket

    packet = ClientBoundMessagePacket(ChatMessage(0, f"[管理员通知] {msg}"))
    rooms_count = len(rooms)

    for _, conn in main_module.online_user_list.items():
        try:
            conn.send(packet)
        except Exception:
            pass

    return {"ok": True, "rooms": rooms_count}


@app.post("/admin/rooms/{room_id}/chat")
async def admin_room_chat(room_id: str, request: Request):
    data = await read_json_body(request)
    msg = data.get("message", "")
    if not msg:
        return JSONResponse({"ok": False, "error": "bad-message"}, status_code=400)
    if len(msg) > 200:
        return JSONResponse({"ok": False, "error": "message-too-long"}, status_code=400)

    rid = parse_room_id(room_id)
    if rid is None:
        return JSONResponse({"ok": False, "error": "bad-room-id"}, status_code=400)

    room = rooms.get(rid)
    if not room:
        return JSONResponse({"ok": False, "error": "room-not-found"}, status_code=404)

    from rymc.phira.protocol.data.message import ChatMessage
    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket

    packet = ClientBoundMessagePacket(ChatMessage(0, f"[系统] {msg}"))

    for _, ruser in room.users.items():
        try:
            ruser.connection.send(packet)
        except Exception:
            pass

    return {"ok": True}


@app.get("/admin/ip-blacklist")
async def admin_get_blacklist():
    bl = main_module.security_store.list_blacklist_ips()
    res = [
        {"ip": ip, "expiresIn": int((exp - time.time()) * 1000) if exp else None}
        for ip, exp in bl.items()
    ]
    return {"ok": True, "blacklist": res}


@app.post("/admin/ip-blacklist/remove")
async def admin_remove_blacklist(request: Request):
    data = await read_json_body(request)
    ip = data.get("ip")
    if ip:
        main_module.security_store.remove_blacklist_ip(ip)
    return {"ok": True}


@app.post("/admin/ip-blacklist/clear")
async def admin_clear_blacklist():
    main_module.security_store.blacklist_ips.clear()
    main_module.security_store.save()
    return {"ok": True}


@app.post("/admin/contest/rooms/{room_id}/config")
async def admin_contest_config(room_id: str, request: Request):
    data = await read_json_body(request)
    rid = parse_room_id(room_id)
    if rid is None:
        return JSONResponse({"ok": False, "error": "bad-room-id"}, status_code=400)

    room = rooms.get(rid)
    if not room:
        return JSONResponse({"ok": False, "error": "room-not-found"}, status_code=404)

    enabled = data.get("enabled", False)
    room.contest_mode = enabled
    if enabled:
        whitelist = data.get("whitelist")
        if not whitelist:
            whitelist = list(room.users.keys())
        room.whitelist = whitelist
    else:
        room.whitelist = []

    return {"ok": True}


@app.post("/admin/contest/rooms/{room_id}/start")
async def admin_contest_start(room_id: str, request: Request):
    data = await read_json_body(request)
    rid = parse_room_id(room_id)
    if rid is None:
        return JSONResponse({"ok": False, "error": "bad-room-id"}, status_code=400)

    room = rooms.get(rid)
    if not room:
        return JSONResponse({"ok": False, "error": "room-not-found"}, status_code=404)

    if not getattr(room, "contest_mode", False):
        return JSONResponse({"ok": False, "error": "not-a-contest-room"}, status_code=400)

    force = data.get("force", False)
    if not force and len(room.ready) < len(room.users):
        return JSONResponse({"ok": False, "error": "not-all-ready"}, status_code=400)

    from rymc.phira.protocol.data.message import StartPlayingMessage
    from rymc.phira.protocol.data.state import Playing
    from rymc.phira.protocol.packet.clientbound import (
        ClientBoundChangeStatePacket,
        ClientBoundMessagePacket,
    )

    room.ready.clear()
    room.state = Playing()
    for _, ru in room.users.items():
        try:
            ru.connection.send(ClientBoundMessagePacket(StartPlayingMessage()))
            ru.connection.send(ClientBoundChangeStatePacket(Playing()))
        except Exception:
            pass

    return {"ok": True}


def on_room_create(roomId, user_info, **kwargs):
    if not room_creation_enabled:
        return {"status": "1"}
    return None


def setup(ctx):
    def on_commands_init(registry=None, ctx=None, **_):
        global room_limits_ref
        if ctx and hasattr(ctx, "server_state"):
            room_limits_ref = ctx.server_state.room_limits

    ctx.on("commands.init", on_commands_init)
    ctx.on("room.before_create", on_room_create)

    port = int(os.environ.get("HTTP_PORT", 12347))
    logger.info("正在启动 HTTP API 服务 (端口 %s)...", port)

    loop = asyncio.get_event_loop()
    config = uvicorn.Config(
        app=app,
        host="0.0.0.0",
        port=port,
        log_level="warning",
        access_log=False,
        loop="asyncio",
    )
    server = uvicorn.Server(config)
    web_task = loop.create_task(server.serve())

    def teardown():
        logger.info("正在关闭 HTTP API 服务...")
        server.should_exit = True
        if not web_task.done():
            web_task.cancel()

    return teardown
