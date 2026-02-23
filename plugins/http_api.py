# -*- coding: utf-8 -*-
"""
HTTP API Plugin for pyphira-mp
提供房间查询、管理、OTP鉴权、封禁控制的 HTTP 接口。
"""

import asyncio
import logging
import os
import time
import uuid
import secrets
from typing import Dict, Any
from quart import Quart, request, jsonify

# 引入核心全局状态
import sys
main_module = sys.modules['__main__']
from utils.room import rooms, destroy_room

# 插件信息
PLUGIN_INFO = {
    "name": "http_api",
    "version": "1.0.1",
}

app = Quart(__name__)
logger = logging.getLogger("plugin.http_api")

# 抑制 Quart 默认日志
logging.getLogger('quart.app').setLevel(logging.WARNING)
logging.getLogger('quart.serving').setLevel(logging.WARNING)

# 全局状态引用
room_creation_enabled = True
room_limits_ref = {}  # 用于同步控制台的房间人数限制

# ==================== OTP 与鉴权数据结构 ====================
otp_sessions: Dict[str, Dict[str, Any]] = {}  # ssid -> {otp, expires_at}
temp_tokens: Dict[str, Dict[str, Any]] = {}   # token -> {ip, expires_at}

# ==================== 工具函数 ====================
def get_admin_token():
    return os.environ.get("ADMIN_TOKEN", None)

def clean_expired_tokens():
    """清理过期的 OTP 和 Token"""
    now = time.time()
    for k in list(otp_sessions.keys()):
        if otp_sessions[k]["expires_at"] < now:
            del otp_sessions[k]
    for k in list(temp_tokens.keys()):
        if temp_tokens[k]["expires_at"] < now:
            del temp_tokens[k]

# ==================== 鉴权中间件 ====================
@app.before_request
async def auth_middleware():
    """管理员 API 鉴权拦截"""
    path = request.path
    if not path.startswith("/admin/"):
        return  # 非管理接口放行
    if path in ["/admin/otp/request", "/admin/otp/verify"]:
        return  # OTP 接口放行

    # 获取 Token
    token = request.headers.get("X-Admin-Token") or \
            request.headers.get("Authorization") or \
            request.args.get("token")
    if token and token.startswith("Bearer "):
        token = token[7:]

    perm_token = get_admin_token()

    if perm_token:
        if token != perm_token:
            return jsonify({"ok": False, "error": "unauthorized"}), 401
        return  # 永久 Token 验证通过

    if not token:
        return jsonify({"ok": False, "error": "admin-disabled"}), 403

    # 验证临时 Token
    clean_expired_tokens()
    t_info = temp_tokens.get(token)
    if not t_info or t_info["expires_at"] < time.time() or t_info["ip"] != request.remote_addr:
        return jsonify({"ok": False, "error": "token-expired"}), 401

# ==================== OTP 接口 ====================
@app.route('/admin/otp/request', methods=['POST'])
async def otp_request():
    if get_admin_token():
        return jsonify({"ok": False, "error": "otp-disabled-when-token-configured"}), 403
    
    clean_expired_tokens()
    ssid = str(uuid.uuid4())
    otp = secrets.token_hex(4)
    expires_in = 300000  # 5 minutes in ms
    otp_sessions[ssid] = {"otp": otp, "expires_at": time.time() + 300}
    
    logger.info(f"[OTP Request] SSID: {ssid}, OTP: {otp}, Expires in 5 minutes")
    return jsonify({"ok": True, "ssid": ssid, "expiresIn": expires_in})

@app.route('/admin/otp/verify', methods=['POST'])
async def otp_verify():
    if get_admin_token():
        return jsonify({"ok": False, "error": "otp-disabled-when-token-configured"}), 403
    
    data = await request.get_json() or {}
    ssid = data.get("ssid")
    otp = data.get("otp")
    
    clean_expired_tokens()
    session = otp_sessions.get(ssid)
    if not session or session["otp"] != otp or session["expires_at"] < time.time():
        return jsonify({"ok": False, "error": "invalid-or-expired-otp"}), 401
    
    del otp_sessions[ssid]
    
    token = str(uuid.uuid4())
    expires_in = 14400000  # 4 hours in ms
    temp_tokens[token] = {
        "ip": request.remote_addr,
        "expires_at": time.time() + 14400
    }
    return jsonify({"ok": True, "token": token, "expiresAt": int(time.time()*1000) + expires_in, "expiresIn": expires_in})

# ==================== 公共接口 ====================
@app.route('/room', methods=['GET'])
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

        res.append({
            "roomid": str(rid),
            "cycle": getattr(room, 'cycle', False),
            "lock": getattr(room, 'locked', False),
            "host": host_info,
            "state": type(room.state).__name__.lower(),
            "chart": {"id": getattr(room, 'chart', None), "name": str(getattr(room, 'chart', 'Unknown'))},
            "players": players
        })
    return jsonify({"rooms": res, "total": len(res)})

# ==================== 管理员接口 (需要鉴权) ====================
@app.route('/admin/rooms', methods=['GET'])
async def admin_get_rooms():
    res = []
    for rid, room in rooms.items():
        users_list = []
        for uid, ruser in room.users.items():
            users_list.append({
                "id": uid,
                "name": getattr(ruser.info, "name", str(uid)),
                "connected": ruser.connection is not None,
                "is_host": uid == room.host,
                "finished": uid in getattr(room, 'finished', {}),
                "ready": uid in getattr(room, 'ready', {})
            })
        
        res.append({
            "roomid": str(rid),
            "max_users": room_limits_ref.get(rid, "无限制"),
            "live": getattr(room, 'live', False),
            "locked": getattr(room, 'locked', False),
            "cycle": getattr(room, 'cycle', False),
            "host": {"id": room.host},
            "state": {"type": type(room.state).__name__.lower()},
            "chart": {"id": getattr(room, 'chart', None)},
            "users": users_list,
            "contest": getattr(room, 'contest_mode', False),
            "whitelist": getattr(room, 'whitelist', [])
        })
    return jsonify({"ok": True, "rooms": res})

@app.route('/admin/rooms/<room_id>/max_users', methods=['POST'])
async def admin_set_max_users(room_id):
    data = await request.get_json() or {}
    max_users = data.get("maxUsers")
    if not isinstance(max_users, int) or not (1 <= max_users <= 64):
        return jsonify({"ok": False, "error": "bad-max-users"}), 400
    try:
        rid = int(room_id) if room_id.isdigit() else room_id
    except ValueError:
        return jsonify({"ok": False, "error": "bad-room-id"}), 400

    if rid not in rooms:
        return jsonify({"ok": False, "error": "room-not-found"}), 404
        
    room_limits_ref[rid] = max_users
    return jsonify({"ok": True, "roomid": str(rid), "max_users": max_users})

@app.route('/admin/rooms/<room_id>/disband', methods=['POST'])
async def admin_disband_room(room_id):
    try:
        rid = int(room_id) if room_id.isdigit() else room_id
    except ValueError:
        return jsonify({"ok": False, "error": "bad-room-id"}), 400

    room = rooms.get(rid)
    if not room:
        return jsonify({"ok": False, "error": "room-not-found"}), 404

    # 通知并踢出所有人
    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket, ClientBoundLeaveRoomPacket
    from rymc.phira.protocol.data.message import LeaveRoomMessage

    for uid, ruser in list(room.users.items()):
        try:
            ruser.connection.send(ClientBoundMessagePacket(LeaveRoomMessage(-1, "房间已被管理员强制解散")))
            ruser.connection.send(ClientBoundLeaveRoomPacket.Success())
        except Exception:
            pass

    destroy_room(rid)
    return jsonify({"ok": True, "roomid": str(rid)})

@app.route('/admin/room-creation/config', methods=['GET', 'POST'])
async def admin_room_creation():
    global room_creation_enabled
    if request.method == 'GET':
        return jsonify({"ok": True, "enabled": room_creation_enabled})
    
    data = await request.get_json() or {}
    if "enabled" not in data:
        return jsonify({"ok": False, "error": "bad-enabled"}), 400
        
    room_creation_enabled = bool(data["enabled"])
    return jsonify({"ok": True, "enabled": room_creation_enabled})

@app.route('/admin/ban/user', methods=['POST'])
async def admin_ban_user():
    data = await request.get_json() or {}
    uid = data.get("userId")
    banned = data.get("banned", True)
    disconnect = data.get("disconnect", True)

    if not uid:
        return jsonify({"ok": False, "error": "bad-user-id"}), 400

    if banned:
        main_module.security_store.add_ban("id", str(uid), None, "API 封禁")
    else:
        main_module.security_store.remove_ban("id", str(uid))

    if disconnect and banned:
        conn = main_module.online_user_list.get(uid) or main_module.online_user_list.get(str(uid))
        if conn:
            try: conn.close()
            except Exception: pass

    return jsonify({"ok": True})

@app.route('/admin/users/<user_id>/disconnect', methods=['POST'])
async def admin_kick_user(user_id):
    try:
        uid = int(user_id) if user_id.isdigit() else user_id
    except ValueError:
        return jsonify({"ok": False, "error": "bad-user-id"}), 400

    conn = main_module.online_user_list.get(uid)
    if not conn:
        return jsonify({"ok": False, "error": "user-not-connected"}), 404
        
    try:
        conn.close()
    except Exception:
        pass
    return jsonify({"ok": True})

@app.route('/admin/broadcast', methods=['POST'])
async def admin_broadcast():
    data = await request.get_json() or {}
    msg = data.get("message", "")
    if not msg: return jsonify({"ok": False, "error": "bad-message"}), 400
    if len(msg) > 200: return jsonify({"ok": False, "error": "message-too-long"}), 400

    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket
    from rymc.phira.protocol.data.message import ChatMessage

    packet = ClientBoundMessagePacket(ChatMessage(0, f"[管理员通知] {msg}"))
    rooms_count = len(rooms)
    
    for uid, conn in main_module.online_user_list.items():
        try: conn.send(packet)
        except Exception: pass

    return jsonify({"ok": True, "rooms": rooms_count})

@app.route('/admin/rooms/<room_id>/chat', methods=['POST'])
async def admin_room_chat(room_id):
    data = await request.get_json() or {}
    msg = data.get("message", "")
    if not msg: return jsonify({"ok": False, "error": "bad-message"}), 400
    if len(msg) > 200: return jsonify({"ok": False, "error": "message-too-long"}), 400

    try: rid = int(room_id) if room_id.isdigit() else room_id
    except ValueError: return jsonify({"ok": False, "error": "bad-room-id"}), 400

    room = rooms.get(rid)
    if not room: return jsonify({"ok": False, "error": "room-not-found"}), 404

    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket
    from rymc.phira.protocol.data.message import ChatMessage
    packet = ClientBoundMessagePacket(ChatMessage(0, f"[系统] {msg}"))
    
    for uid, ruser in room.users.items():
        try: ruser.connection.send(packet)
        except Exception: pass
        
    return jsonify({"ok": True})

# ==================== IP 黑名单接口 ====================
@app.route('/admin/ip-blacklist', methods=['GET'])
async def admin_get_blacklist():
    bl = main_module.security_store.list_blacklist_ips()
    res = [{"ip": ip, "expiresIn": int((exp - time.time())*1000) if exp else None} for ip, exp in bl.items()]
    return jsonify({"ok": True, "blacklist": res})

@app.route('/admin/ip-blacklist/remove', methods=['POST'])
async def admin_remove_blacklist():
    data = await request.get_json() or {}
    ip = data.get("ip")
    if ip: main_module.security_store.remove_blacklist_ip(ip)
    return jsonify({"ok": True})

@app.route('/admin/ip-blacklist/clear', methods=['POST'])
async def admin_clear_blacklist():
    main_module.security_store.blacklist_ips.clear()
    main_module.security_store.save()
    return jsonify({"ok": True})

# ==================== 比赛模式接口 ====================
@app.route('/admin/contest/rooms/<room_id>/config', methods=['POST'])
async def admin_contest_config(room_id):
    data = await request.get_json() or {}
    try: rid = int(room_id) if room_id.isdigit() else room_id
    except ValueError: return jsonify({"ok": False, "error": "bad-room-id"}), 400
    
    room = rooms.get(rid)
    if not room: return jsonify({"ok": False, "error": "room-not-found"}), 404
    
    enabled = data.get("enabled", False)
    room.contest_mode = enabled
    if enabled:
        whitelist = data.get("whitelist")
        if not whitelist:
            whitelist = list(room.users.keys())
        room.whitelist = whitelist
    else:
        room.whitelist = []
        
    return jsonify({"ok": True})

@app.route('/admin/contest/rooms/<room_id>/start', methods=['POST'])
async def admin_contest_start(room_id):
    data = await request.get_json() or {}
    try: rid = int(room_id) if room_id.isdigit() else room_id
    except ValueError: return jsonify({"ok": False, "error": "bad-room-id"}), 400
    
    room = rooms.get(rid)
    if not room: return jsonify({"ok": False, "error": "room-not-found"}), 404
    
    if not getattr(room, 'contest_mode', False):
        return jsonify({"ok": False, "error": "not-a-contest-room"}), 400
        
    force = data.get("force", False)
    if not force:
        if len(room.ready) < len(room.users):
            return jsonify({"ok": False, "error": "not-all-ready"}), 400

    from rymc.phira.protocol.data.state import Playing
    from rymc.phira.protocol.packet.clientbound import ClientBoundChangeStatePacket, ClientBoundMessagePacket
    from rymc.phira.protocol.data.message import StartPlayingMessage
    
    room.ready.clear()
    room.state = Playing()
    for uid, ru in room.users.items():
        try:
            ru.connection.send(ClientBoundMessagePacket(StartPlayingMessage()))
            ru.connection.send(ClientBoundChangeStatePacket(Playing()))
        except Exception: pass
        
    return jsonify({"ok": True})


# ==================== 钩子事件拦截 (房间创建) ====================
def on_room_create(roomId, user_info, **kwargs):
    """如果关闭了房间创建，拦截此事件"""
    if not room_creation_enabled:
        return {"status": "1"} 
    return None

# ==================== 插件生命周期 ====================
def setup(ctx):
    # 1. 同步控制台的房间人数限制
    def on_commands_init(registry=None, context=None, **_):
        global room_limits_ref
        if context and hasattr(context, "server_state"):
            room_limits_ref = context.server_state.room_limits
            
    ctx.on("commands.init", on_commands_init)
    
    # 2. 拦截房间创建
    ctx.on("room.before_create", on_room_create)
    
    # 3. 【修复 Ctrl+C 卡死的核心代码】
    # 强制接管 SIGINT (Ctrl+C) 信号，主动触发 pyphira-mp 的安全停机事件
    import signal
    def handle_sigint(signum, frame):
        logger.warning("接收到 Ctrl+C (SIGINT)，正在通知主程序及所有插件安全停机...")
        ctx.shutdown_event.set()
        
    try:
        # 仅在主线程中生效，如果抛出 ValueError 则忽略
        signal.signal(signal.SIGINT, handle_sigint)
    except ValueError:
        pass

    # 4. 启动 Web 服务
    port = int(os.environ.get("HTTP_PORT", 12347))
    logger.info(f"正在启动 HTTP API 服务 (端口 {port})...")
    
    loop = asyncio.get_event_loop()
    
    # 5. 定义 Quart 的联动关闭触发器
    async def quart_shutdown_trigger():
        # 死等主程序的关机信号，一旦收到，Quart 也会自行优雅切断所有连接
        await ctx.shutdown_event.wait()
        
    web_task = loop.create_task(app.run_task(
        host='0.0.0.0', 
        port=port, 
        shutdown_trigger=quart_shutdown_trigger
    ))
    
    def teardown():
        logger.info("正在卸载 HTTP API 服务...")
        if not web_task.done():
            web_task.cancel()
            
    return teardown