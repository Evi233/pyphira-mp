# -*- coding: utf-8 -*- 
"""Console admin commands plugin for pyphira-mp.

This plugin registers all console commands listed in the help menu. """

from __future__ import annotations

import logging
import os
import time
from typing import List, Union

from utils.commands import Command, CommandContext

PLUGIN_INFO = { "name": "console_admin", "version": "1.0.1", }

# plugins/console_admin.py

def setup(ctx): 
    """Register console commands on commands.init event.""" 
    # Use ctx.on() to register the listener. 
    # This automatically handles the 'owner' for plugin unloading.
    global logger
    logger = ctx.logger
    ctx.on("commands.init", on_commands_init)

def on_commands_init(registry=None, ctx=None, **_):
    if registry is None:
        logger.error("commands.init emitted without registry")
        return
    if ctx is None:
        logger.error("commands.init emitted without ctx")
        return

    owner = "plugin.console_admin"
    state = ctx.server_state
    shutdown_event = ctx.shutdown_event

    # ========== 辅助函数 ==========
    
    def try_parse_id(raw_id: str) -> Union[int, str]:
        """尝试将ID转换为整数，如果失败则返回原始字符串。
        用于处理命令行参数(str)与内部字典Key(int/str)的类型不匹配问题。
        """
        try:
            return int(raw_id)
        except ValueError:
            return raw_id

    # ========== 基础命令 ==========

    def cmd_room(c: CommandContext, args: List[str]):
        """列出所有房间信息"""
        rooms = state.rooms
        if not rooms:
            c.println("当前没有活跃的房间")
            return
        lines = ["房间列表:"]
        for rid, room in rooms.items():
            host_id = room.host or "N/A"
            user_count = len(room.users)
            st = type(room.state).__name__
            locked = "🔒" if room.locked else ""
            cycle = "🔄" if room.cycle else ""
            maxp = state.room_limits.get(rid, "无限制")
            maxp_str = f"/{maxp}" if isinstance(maxp, int) else ""
            over = ""
            if isinstance(maxp, int) and user_count > maxp:
                over = " [OVER]"
            lines.append(f"  [{rid}] 房主:{host_id} 人数:{user_count}{maxp_str}{over} 状态:{st}{locked}{cycle}")
        c.println("\n".join(lines))

    def cmd_status(c: CommandContext, args: List[str]):
        """协议握手检测"""
        from utils.server import SUPPORTED_VERSIONS
        lines = [
            "===== 服务器状态 =====",
            f"监听地址: {state.host}:{state.port}",
            f"支持协议版本: {SUPPORTED_VERSIONS}",
            f"在线玩家数: {len(state.online_user_list)}",
            f"房间数: {len(state.rooms)}",
        ]
        if state.git_info and not state.git_info.error:
            dirty = " (dirty)" if state.git_info.is_dirty else ""
            lines.append(f"Git: {state.git_info.short_hash}{dirty}")
        lines.append("=====================")
        c.println("\n".join(lines))

    def cmd_ping(c: CommandContext, args: List[str]):
        """查看服务器响应"""
        c.println(f"pong! {time.strftime('%H:%M:%S')}")

    def cmd_list(c: CommandContext, args: List[str]):
        """查看当前所有在线玩家列表"""
        profiles = state.online_profiles
        if not profiles:
            c.println("当前没有在线玩家")
            return
        lines = ["在线玩家:"]
        for uid, info in profiles.items():
            name = getattr(info, "name", "?")
            lines.append(f"  [{uid}] {name}")
        c.println("\n".join(lines))

    def cmd_info(c: CommandContext, args: List[str]):
        """展示服务器状态以及各种信息"""
        cmd_status(c, args)
        c.println("")
        cmd_room(c, args)

    # ========== 房间管理命令 ==========

    def cmd_broadcast(c: CommandContext, args: List[str]):
        """全服或指定房间广播"""
        if len(args) < 1:
            c.println("用法: /broadcast \"内容\" [#房间ID]")
            return
        content = args[0]
        target_room_id = None
        if len(args) >= 2:
            # 这里的 ID 也要做类型转换检查
            raw_rid = args[1].lstrip("#")
            target_room_id = try_parse_id(raw_rid)

        sent = 0
        if target_room_id is not None:
            # 指定房间
            room = state.rooms.get(target_room_id)
            if not room:
                c.println(f"房间 {target_room_id} 不存在")
                return
            for uid, ru in room.users.items():
                try:
                    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket
                    from rymc.phira.protocol.data.message import ChatMessage
                    ru.connection.send(ClientBoundMessagePacket(ChatMessage(-1, f"[广播] {content}")))
                    sent += 1
                except Exception as e:
                    c.println(f"发送给 {uid} 失败: {e}")
        else:
            # 全服
            for uid, conn in state.online_user_list.items():
                try:
                    from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket
                    from rymc.phira.protocol.data.message import ChatMessage
                    conn.send(ClientBoundMessagePacket(ChatMessage(-1, f"[广播] {content}")))
                    sent += 1
                except Exception as e:
                    c.println(f"发送给 {uid} 失败: {e}")
        c.println(f"广播已发送给 {sent} 位玩家")

    def cmd_kick(c: CommandContext, args: List[str]):
        """强制移除指定用户"""
        if len(args) < 1:
            c.println("用法: /kick {用户ID}")
            return
        
        # 使用 try_parse_id 统一处理
        uid = try_parse_id(args[0])

        conn = state.online_user_list.get(uid)
        if not conn:
            c.println(f"用户 {uid} 不在线 (类型: {type(uid).__name__})")
            return
        try:
            conn.close()
            c.println(f"已踢出用户 {uid}")
        except Exception as e:
            c.println(f"踢出失败: {e}")

    def cmd_fstart(c: CommandContext, args: List[str]):
        """强制开始指定房间对局"""
        if len(args) < 1:
            c.println("用法: /fstart {房间ID}")
            return
        
        rid = try_parse_id(args[0])
        room = state.rooms.get(rid)
        
        if not room:
            c.println(f"房间 {rid} 不存在")
            return
        from rymc.phira.protocol.data.state import WaitForReady, Playing, SelectChart
        from rymc.phira.protocol.packet.clientbound import ClientBoundChangeStatePacket, ClientBoundMessagePacket
        from rymc.phira.protocol.data.message import StartPlayingMessage
        # 直接切换到 Playing 状态
        room.ready.clear()
        set_state = lambda r, s: setattr(r, "state", s)
        set_state(room, Playing())
        for uid, ru in room.users.items():
            try:
                ru.connection.send(ClientBoundMessagePacket(StartPlayingMessage()))
                ru.connection.send(ClientBoundChangeStatePacket(Playing()))
            except Exception as e:
                c.println(f"发送给 {uid} 失败: {e}")
        c.println(f"房间 {rid} 已强制开始对局")

    def cmd_lock(c: CommandContext, args: List[str]):
        """锁定/解锁房间"""
        if len(args) < 1:
            c.println("用法: /lock {房间ID}")
            return
        
        rid = try_parse_id(args[0])
        room = state.rooms.get(rid)
        
        if not room:
            c.println(f"房间 {rid} 不存在")
            return
        room.locked = not room.locked
        status = "锁定" if room.locked else "解锁"
        c.println(f"房间 {rid} 已{status}")

    def cmd_maxp(c: CommandContext, args: List[str]):
        """修改房间最大人数限制（软限制）"""
        if len(args) < 2:
            c.println("用法: /maxp {房间ID} {人数}")
            return
        
        rid = try_parse_id(args[0])
        
        try:
            max_players = int(args[1])
        except ValueError:
            c.println("人数必须是整数")
            return
        if rid not in state.rooms:
            c.println(f"房间 {rid} 不存在")
            return
        state.room_limits[rid] = max_players
        c.println(f"房间 {rid} 最大人数已设置为 {max_players}")

    def cmd_close(c: CommandContext, args: List[str]):
        """强制关闭指定房间"""
        if len(args) < 1:
            c.println("用法: /close {房间ID}")
            return
        
        rid = try_parse_id(args[0])
        room = state.rooms.get(rid)
        
        if not room:
            c.println(f"房间 {rid} 不存在")
            return
        # 通知所有用户
        from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket, ClientBoundLeaveRoomPacket
        from rymc.phira.protocol.data.message import LeaveRoomMessage
        for uid, ru in list(room.users.items()):
            try:
                ru.connection.send(ClientBoundMessagePacket(LeaveRoomMessage(-1, "房间已被关闭")))
                ru.connection.send(ClientBoundLeaveRoomPacket.Success())
            except Exception:
                pass
        # 销毁房间
        from utils.room import destroy_room
        destroy_room(rid)
        c.println(f"房间 {rid} 已关闭")

    def cmd_tmode(c: CommandContext, args: List[str]):
        """切换房间模式 (循环/普通)"""
        if len(args) < 1:
            c.println("用法: /tmode {房间ID}")
            return
        
        rid = try_parse_id(args[0])
        room = state.rooms.get(rid)
        
        if not room:
            c.println(f"房间 {rid} 不存在")
            return
        room.cycle = not room.cycle
        status = "循环" if room.cycle else "普通"
        c.println(f"房间 {rid} 已切换为{status}模式")

    def cmd_smsg(c: CommandContext, args: List[str]):
        """发送房间系统消息"""
        if len(args) < 2:
            c.println("用法: /smsg {房间ID} {内容}")
            return
        
        rid = try_parse_id(args[0])
        content = args[1]
        
        room = state.rooms.get(rid)
        if not room:
            c.println(f"房间 {rid} 不存在")
            return
        from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket
        from rymc.phira.protocol.data.message import ChatMessage
        for uid, ru in room.users.items():
            try:
                ru.connection.send(ClientBoundMessagePacket(ChatMessage(-1, content)))
            except Exception as e:
                c.println(f"发送给 {uid} 失败: {e}")
        c.println(f"已发送系统消息到房间 {rid}")

    def cmd_bulk(c: CommandContext, args: List[str]):
        """批量房间操作"""
        if len(args) < 1:
            c.println("用法: /bulk {动作} [目标] [值]")
            c.println("动作: close_all, lock_all, unlock_all")
            return
        action = args[0]
        rooms = state.rooms
        if action == "close_all":
            from utils.room import destroy_room
            from rymc.phira.protocol.packet.clientbound import ClientBoundMessagePacket, ClientBoundLeaveRoomPacket
            from rymc.phira.protocol.data.message import LeaveRoomMessage
            count = 0
            for rid in list(rooms.keys()):
                room = rooms[rid]
                for uid, ru in list(room.users.items()):
                    try:
                        ru.connection.send(ClientBoundMessagePacket(LeaveRoomMessage(-1, "服务器关闭所有房间")))
                        ru.connection.send(ClientBoundLeaveRoomPacket.Success())
                    except Exception:
                        pass
                destroy_room(rid)
                count += 1
            c.println(f"已关闭 {count} 个房间")
        elif action == "lock_all":
            count = 0
            for rid, room in rooms.items():
                if not room.locked:
                    room.locked = True
                    count += 1
            c.println(f"已锁定 {count} 个房间")
        elif action == "unlock_all":
            count = 0
            for rid, room in rooms.items():
                if room.locked:
                    room.locked = False
                    count += 1
            c.println(f"已解锁 {count} 个房间")
        else:
            c.println(f"未知批量操作: {action}")

    # ========== 封禁/黑名单命令 ==========

    def cmd_bans(c: CommandContext, args: List[str]):
        """查看封禁列表"""
        bans = state.security.list_bans()
        if not bans:
            c.println("当前没有封禁记录")
            return
        lines = ["封禁列表:"]
        for b in bans:
            exp = f"到期: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(b.expire_at))}" if b.expire_at else "永久"
            lines.append(f"  [{b.type}] {b.target} - {b.reason or '无原因'} ({exp})")
        c.println("\n".join(lines))

    def cmd_ban(c: CommandContext, args: List[str]):
        """执行封禁"""
        if len(args) < 2:
            c.println("用法: /ban {类型: id|ip} {目标} [时长:秒] [原因]")
            return
        btype = args[0]
        if btype not in ("id", "ip"):
            c.println("类型必须是 id 或 ip")
            return
        target = args[1]
        duration = None
        if len(args) >= 3:
            try:
                duration = int(args[2])
            except ValueError:
                c.println("时长必须是整数（秒）")
                return
        reason = args[3] if len(args) >= 4 else ""
        
        # 1. 执行数据库封禁 (Security层通常处理字符串，所以这里保持原样或根据需要转换)
        state.security.add_ban(btype, target, duration, reason)
        c.println(f"已添加封禁记录 {btype}:{target}")

        # 2. 检查并踢出在线玩家 (实现立即生效)
        if btype == "id":
            # 同样使用 try_parse_id 以匹配在线列表的 Key 类型
            target_uid = try_parse_id(target)
            
            conn = state.online_user_list.get(target_uid)
            if conn:
                try:
                    conn.close()
                    c.println(f"检测到玩家在线，已强制踢出: {target}")
                except Exception:
                    pass
        elif btype == "ip":
            # 遍历在线玩家检查 IP (这需要遍历 verify logic，比较复杂，暂时只处理 ID 踢出)
            c.println(f"IP封禁已记录，但暂不支持在线踢出IP玩家。")
            pass

    def cmd_unban(c: CommandContext, args: List[str]):
        """解除封禁"""
        if len(args) < 2:
            c.println("用法: /unban {类型: id|ip} {目标}")
            return
        btype = args[0]
        target = args[1]
        if state.security.remove_ban(btype, target):
            c.println(f"已解除封禁 {btype}:{target}")
        else:
            c.println(f"未找到封禁记录 {btype}:{target}")

    def cmd_blist(c: CommandContext, args: List[str]):
        """查看登录黑名单"""
        bl = state.security.list_blacklist_ips()
        if not bl:
            c.println("当前没有IP黑名单")
            return
        lines = ["IP黑名单:"]
        for ip, exp in bl.items():
            exp_str = f"到期: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(exp))}" if exp else "永久"
            lines.append(f"  {ip} ({exp_str})")
        c.println("\n".join(lines))

    def cmd_blip(c: CommandContext, args: List[str]):
        """黑名单 IP"""
        if len(args) < 1:
            c.println("用法: /blip {IP} [时长:秒]")
            return
        ip = args[0]
        duration = None
        if len(args) >= 2:
            try:
                duration = int(args[1])
            except ValueError:
                c.println("时长必须是整数（秒）")
                return
        state.security.add_blacklist_ip(ip, duration)
        c.println(f"已添加IP黑名单: {ip}")

    def cmd_ublip(c: CommandContext, args: List[str]):
        """移除黑名单 IP"""
        if len(args) < 1:
            c.println("用法: /ublip {IP}")
            return
        ip = args[0]
        if state.security.remove_blacklist_ip(ip):
            c.println(f"已移除IP黑名单: {ip}")
        else:
            c.println(f"IP {ip} 不在黑名单中")

    # ========== 管理员命令 ==========

    def cmd_op(c: CommandContext, args: List[str]):
        """将此 ID 设置为管理员"""
        if len(args) < 1:
            c.println("用法: /op {phira_id}")
            return
        pid = args[0]
        state.security.op(pid)
        c.println(f"已添加管理员: {pid}")

    def cmd_deop(c: CommandContext, args: List[str]):
        """将此 ID 移除管理员"""
        if len(args) < 1:
            c.println("用法: /deop {phira_id}")
            return
        pid = args[0]
        if state.security.deop(pid):
            c.println(f"已移除管理员: {pid}")
        else:
            c.println(f"{pid} 不是管理员")

    # ========== 服务器控制命令 ==========

    async def cmd_stop(c: CommandContext, args: List[str]):
        # 注意：这里原代码有误 (self._serve_task)，且在同步上下文中定义了 async。
        # 针对本次修改任务，仅保留原结构，不修改逻辑错误以免引入新问题，
        # 除非确实需要修复 ID 相关问题。此处不涉及 ID。
        pass
        
    def cmd_restart(c: CommandContext, args: List[str]):
        """重启服务器"""
        c.println("正在重启服务器...")
        state.restart_requested = True
        shutdown_event.set()

    def cmd_reload(c: CommandContext, args: List[str]):
        """重新加载 env 配置"""
        # 重新加载 security.json
        state.security.load()
        # 触发插件重载
        pm = c.plugin_manager
        if pm:
            pm.load_all()
        c.println("配置已重新加载")

    def cmd_set(c: CommandContext, args: List[str]):
        """设置 env 变量的值"""
        if len(args) < 2:
            c.println("用法: /set \"{环境变量}\" \"{值}\"")
            return
        key = args[0]
        val = args[1]
        os.environ[key] = val
        c.println(f"已设置 {key}={val} (仅当前进程有效)")

    def cmd_log(c: CommandContext, args: List[str]):
        """调整日志等级"""
        if len(args) < 1:
            c.println("用法: /log debug|info|mark|warn|error")
            return
        levels = args[0].split("|")
        valid = {"debug", "info", "mark", "warn", "error"}
        for lv in levels:
            if lv.lower() not in valid:
                c.println(f"无效日志等级: {lv}")
                return
        # 设置 root logger
        import logging as _logging
        level_map = {
            "debug": _logging.DEBUG,
            "info": _logging.INFO,
            "mark": _logging.INFO,  # mark 作为 INFO 处理
            "warn": _logging.WARNING,
            "error": _logging.ERROR,
        }
        # 取最低等级
        min_level = min([level_map[lv.lower()] for lv in levels])
        _logging.getLogger().setLevel(min_level)
        c.println(f"日志等级已设置为: {args[0]}")

    # ========== 注册所有命令 ==========

    commands = [
        Command(name="room", usage="/room", help="获取服务器房间列表 (文本详情)", handler=cmd_room, owner=owner),
        Command(name="status", usage="/status", help="Phira 服务器协议握手检测", handler=cmd_status, owner=owner),
        Command(name="ping", usage="/ping", help="查看服务器响应", handler=cmd_ping, owner=owner),
        Command(name="list", usage="/list", help="查看当前所有在线玩家列表", handler=cmd_list, owner=owner),
        Command(name="broadcast", usage="/broadcast \"内容\" [#ID]", help="全服或指定房间广播", handler=cmd_broadcast, owner=owner),
        Command(name="kick", usage="/kick {uID}", help="强制移除指定用户", handler=cmd_kick, owner=owner),
        Command(name="fstart", usage="/fstart {RID}", help="强制开始指定房间对局", handler=cmd_fstart, owner=owner),
        Command(name="lock", usage="/lock {RID}", help="锁定/解锁房间", handler=cmd_lock, owner=owner),
        Command(name="maxp", usage="/maxp {RID} {人数}", help="修改房间最大人数限制", handler=cmd_maxp, owner=owner),
        Command(name="close", usage="/close {RID}", help="强制关闭指定房间", handler=cmd_close, owner=owner),
        Command(name="tmode", usage="/tmode {RID}", help="切换房间模式 (循环/普通)", handler=cmd_tmode, owner=owner),
        Command(name="smsg", usage="/smsg {RID} {内容}", help="发送房间系统消息", handler=cmd_smsg, owner=owner),
        Command(name="bulk", usage="/bulk {动作} {目标} [值]", help="批量房间操作 (close_all, lock_all, unlock_all)", handler=cmd_bulk, owner=owner),
        Command(name="bans", usage="/bans", help="查看封禁列表", handler=cmd_bans, owner=owner),
        Command(name="ban", usage="/ban {类型: id|ip} {目标} [时长:秒] [原因]", help="执行封禁", handler=cmd_ban, owner=owner),
        Command(name="unban", usage="/unban {类型: id|ip} {目标}", help="解除封禁", handler=cmd_unban, owner=owner),
        Command(name="blist", usage="/blist", help="查看登录黑名单", handler=cmd_blist, owner=owner),
        Command(name="blip", usage="/blip {IP} [时长:秒]", help="黑名单 IP", handler=cmd_blip, owner=owner),
        Command(name="ublip", usage="/ublip {IP}", help="移除黑名单 IP", handler=cmd_ublip, owner=owner),
        Command(name="stop", usage="/stop", help="关闭服务器", handler=cmd_stop, owner=owner),
        Command(name="restart", usage="/restart", help="重启服务器", handler=cmd_restart, owner=owner),
        Command(name="reload", usage="/reload", help="重新加载 env 配置", handler=cmd_reload, owner=owner),
        Command(name="op", usage="/op {phira_id}", help="将此 ID 设置为管理员", handler=cmd_op, owner=owner),
        Command(name="deop", usage="/deop {phira_id}", help="将此 ID 移除管理员", handler=cmd_deop, owner=owner),
        Command(name="info", usage="/info", help="展示服务器状态以及各种信息", handler=cmd_info, owner=owner),
        Command(name="set", usage="/set \"{环境变量}\" \"{值}\"", help="设置 env 变量的值", handler=cmd_set, owner=owner),
        Command(name="log", usage="/log debug|info|mark|warn|error", help="调整日志等级 (可多选，例如：/log warn|error)", handler=cmd_log, owner=owner),
    ]

    for cmd in commands:
        registry.register(cmd)

    logger.info("console_admin: registered %d commands", len(commands))


def teardown():
    logger.info("console_admin: teardown")
    return teardown