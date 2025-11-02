from connection import Connection
from phiraapi import PhiraFetcher
from rymc.phira.protocol.data import UserProfile
from rymc.phira.protocol.data.message import *
from rymc.phira.protocol.handler import SimplePacketHandler
from rymc.phira.protocol.packet.clientbound import *
from rymc.phira.protocol.packet.serverbound import *
from room import *
from server import Server
from i10n import get_i10n_text
import asyncio
import random

HOST = '0.0.0.0'
PORT = 12346
FETCHER = PhiraFetcher()

class MainHandler(SimplePacketHandler):
    def handleAuthenticate(self, packet: ServerBoundAuthenticatePacket) -> None:
        print("Authenticate with token", packet.token)
        user_info = FETCHER.get_user_info(packet.token)
        self.user_info = user_info

        packet = ClientBoundAuthenticatePacket.Success(UserProfile(user_info.id, user_info.name), False)
        self.connection.send(packet)

        packet = ClientBoundMessagePacket(ChatMessage(-1, f"你好 [{user_info.id}] {user_info.name}"))
        self.connection.send(packet)
        packet = ClientBoundMessagePacket(ChatMessage(-1,"你正在一个早期的 pphira-mp 测试实例上游玩，功能不完整"))
        self.connection.send(packet)
        packet = ClientBoundMessagePacket(ChatMessage(-1,"Phira协议 by lRENyaaa"))
        self.connection.send(packet)
        packet = ClientBoundMessagePacket(ChatMessage(-1,"逻辑 by Evi233"))
        self.connection.send(packet)
    def on_player_disconnected(self) -> None:
        """
        当玩家断开连接时，这个方法会被调用。
        可以在这里做一些清理工作，比如把玩家从房间里移除。
        """
        # 检查这个玩家是否已经鉴权（登录），并且有 user_info 信息
        if hasattr(self, 'user_info') and self.user_info:
            print(f"用户 [{self.user_info.id}] {self.user_info.name} 下线。")
            # 获取这个用户所在的所有房间
            rooms_of_user = get_rooms_of_user(self.user_info.id)
            if rooms_of_user["status"] == "0":
                for roomId in rooms_of_user["rooms"]:
                    # 从房间里移除玩家
                    player_leave(roomId, self.user_info.id)
                    # 提醒这些房间里的所有其他玩家
                    packet = ClientBoundMessagePacket(
                        LeaveRoomMessage(self.user_info.id, self.user_info.name))
                    # 广播给房间里的其他人
                    for _, room_user in rooms[roomId].users.items():
                        if room_user.connection != self.connection:
                            room_user.connection.send(packet)

            # 释放资源
            del self.user_info

    def handleCreateRoom(self, packet: ServerBoundCreateRoomPacket) -> None:
        print("Create room with id", packet.roomId)
        creat_room_result = create_room(packet.roomId, self.user_info)
        if creat_room_result == {"status": "0"}:
            #错误处理
            if self.user_info == None:
                #未鉴权
                #断开连接
                self.connection.close()
                return
            # 【修改】确保传递了 self.connection 参数
            add_user(packet.roomId, self.user_info, self.connection) 
            packet = ClientBoundCreateRoomPacket.Success()
            self.connection.send(packet)
        elif creat_room_result == {"status": "1"}:
            #房间已存在
            packet = ClientBoundCreateRoomPacket.Failed(get_i10n_text("zh-rCN", "room_already_exist"))
            self.connection.send(packet)

    def handleJoinRoom(self, packet: ServerBoundJoinRoomPacket) -> None:
        print("Join room with id", packet.roomId)
        #检查是否是监控者
        # 【修改】is_monitor 只接受一个 user_id 参数
        monitor_result = is_monitor(self.user_info.id)
        if monitor_result == {"monitor": "0"}: # {"monitor": "0"} 表示是监控者
            # todo：monitor加入处理
            # 这里可以调用 add_monitor 函数来将监控者加入房间
            # add_monitor(packet.roomId, self.user_info.id)
            # 然后发送 ClientBoundJoinRoomPacket.Success()
            pass
        elif monitor_result == {"monitor": "1"}: # {"monitor": "1"} 表示不是监控者
            #错误处理
            if self.user_info == None:
                #未鉴权
                #断开连接
                self.connection.close()
                return
            # 【修改】确保传递了 self.connection 参数
            join_room_result = add_user(packet.roomId, self.user_info, self.connection)
            if join_room_result == {"status": "0"}:
                #获取一堆信息
                #烦人
                #获取房间状态
                room_state = get_room_state(packet.roomId)["state"]
                #获取所有用户
                users = get_all_users(packet.roomId)["users"]
                user_profiles = [UserProfile(user.info.id, user.info.name) for user  in users.values()]
                #获取所有监控者
                monitors = get_all_monitors(packet.roomId)["monitors"]
                #检查是否是直播
                islive = is_live(packet.roomId)["isLive"]
                #通知其他用户
                connections = get_connections(packet.roomId)["connections"]
                for connection in connections:
                    #如果当前要发送的消息是要发给自己
                    if connection == self.connection:
                        #跳过发送
                        continue
                    #否则发送给其他用户
                    #TODO：这里的false（指下文）是monitor状态
                    #暂时没实现，也不清楚什么意思
                    #所以todo
                    packet = ClientBoundOnJoinRoomPacket(UserProfile(self.user_info.id, self.user_info.name), False)
                    connection.send(packet)
                #通知自己
                #4 required positional arguments: 'gameState', 'users', 'monitors', and 'isLive'
                packet = ClientBoundJoinRoomPacket.Success(gameState=room_state, users=user_profiles, monitors=monitors, isLive=islive)
                self.connection.send(packet)
            elif join_room_result == {"status": "1"}:
                #房间不存在
                packet = ClientBoundJoinRoomPacket.Failed(get_i10n_text("zh-rCN", "room_not_exist"))
                self.connection.send(packet)
            elif join_room_result == {"status": "2"}:
                #用户已存在
                packet = ClientBoundJoinRoomPacket.Failed(get_i10n_text("zh-rCN", "user_already_exist"))
                self.connection.send(packet)
    #ServerBoundLeaveRoomPacket


    def handleLeaveRoom(self, packet: ServerBoundLeaveRoomPacket) -> None:
        room_id_query_result = get_roomId(self.user_info.id) # 获取用户所在的房间信息
        roomId = room_id_query_result["roomId"] # 从结果字典中提取实际的房间ID字符串
        print("Leave room with id", roomId)

        # --------- 鉴权 ---------
        if self.user_info is None:
            self.connection.close()
            return
        # 检查用户是否真的在房间里
        if room_id_query_result.get("status") == "1":
            print(f"用户 [{self.user_info.id}] {self.user_info.name} 尝试离开房间但未在任何房间中找到。")
            self.connection.send(ClientBoundLeaveRoomPacket.Failed(get_i10n_text("zh-rCN", "not_in_room")))
            return
        # --------- 真正离开房间 ---------
        
        print(f"User [{self.user_info.id}] {self.user_info.name} attempts to leave room {roomId}.")
        leave_room_result = player_leave(roomId, self.user_info.id)
        if leave_room_result.get("status") != "0":
            # 失败反馈
            error_message = ""
            if leave_room_result == {"status": "1"}:
                error_message = get_i10n_text("zh-rCN", "room_not_exist")
            elif leave_room_result == {"status": "2"}:
                error_message = get_i10n_text("zh-rCN", "user_not_exist")
            else: # 备用错误消息
                error_message = f"[Error leaving room: {leave_room_result}]"
            self.connection.send(ClientBoundLeaveRoomPacket.Failed(error_message))
            return

        # --------- 给客户端发成功包 ---------
        self.connection.send(ClientBoundLeaveRoomPacket.Success())

        # --------- 只给这个房间广播离开消息 ---------
        room = rooms.get(roomId)          # 房间可能已被销毁
        if room is None:
            return

        leave_msg = ClientBoundMessagePacket(
            LeaveRoomMessage(self.user_info.id, self.user_info.name)
        )

        # 广播给房间里的“其他”人
        for other in room.users.values():
            if other.connection is not self.connection:
                other.connection.send(leave_msg)
        
        #获取该房间的所有用户
        users = get_all_users(roomId)["users"]
        #如果是房主
        if get_host(roomId)["host"] == self.user_info.id:
            #如果房间就剩一个人了
            if len(users) <= 1:
                #销毁房间
                destory_room(roomId)
            else:
                #如果是房主，随机一个不是monitor的人做新房主
                #随机一个不是monitor的人
                new_host = random.choice([user for user in users.values() if user.info.id != get_host(roomId)["host"]])
                #设置新房主
                change_host(roomId, new_host.info.id)
                #给新房主发送ClientBoundHostChangePacket
                new_host.connection.send(ClientBoundChangeHostPacket(True))
                #TODO:把这玩意往前移，在移除这个用户之前处理完
            







    def handleSelectChart(self, packet: ServerBoundSelectChartPacket) -> None:
        print("Select chart with id", packet.id)
        #获取用户所在房间
        roomId = get_roomId(self.user_info.id)
        if roomId == None:
            #用户不在房间
            packet = ClientBoundSelectChartPacket.Failed(get_i10n_text("zh-rCN", "not_in_room"))
            self.connection.send(packet)
            return
        roomId = roomId["roomId"]
        if self.user_info == None:
            #未鉴权
            #断开连接
            self.connection.close()
            return
            #判断是不是房主
        if get_host(roomId)["host"] != self.user_info.id:
            #不是房主
            packet = ClientBoundSelectChartPacket.Failed(get_i10n_text("zh-rCN", "not_host"))
            self.connection.send(packet)
            return
        #是房主
        #设置chart
        set_chart(packet.roomId, packet.id)
        #通知其他用户
        connections = get_connections(packet.roomId)["connections"]
        for connection in connections:
            #如果当前要发送的消息是要发给自己
            if connection == self.connection:
                #跳过发送
                continue
            #否则发送给其他用户
            packet = ClientBoundSelectChartPacket.Success(packet.id)
            connection.send(packet)
        #通知自己
        packet = ClientBoundSelectChartPacket.Success(packet.id)
        self.connection.send(packet)

def handle_connection(connection: Connection):
    handler = MainHandler(connection)

    #WARNING:傻逼嵌套def
    def on_disconnect():
        handler.on_player_disconnected()

    connection.set_receiver(lambda packet: packet.handle(handler))
    connection.on_close(on_disconnect)

if __name__ == '__main__':
    server = Server(HOST, PORT, handle_connection)
    asyncio.run(server.start())