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

HOST = '0.0.0.0'  # 监听所有网卡，本地测试可用 '127.0.0.1'
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
        packet = ClientBoundMessagePacket(ChatMessage(-1,"你正在一个早期的 pphira-mp 测试实例上游玩"))
        self.connection.send(packet)
    def on_player_disconnected(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        """
        当玩家断开连接时，这个方法会被调用。
        可以在这里做一些清理工作，比如把玩家从房间里移除。
        """
        addr = writer.get_extra_info('peername')
        print(f"玩家 {addr} 断开连接了。")

        # 检查这个玩家是否已经鉴权（登录），并且有 user_info 信息
        if hasattr(self, 'user_info') and self.user_info:
            print(f"用户 [{self.user_info.id}] {self.user_info.name} 下线。")
            remove_user_from_all_rooms(self.user_info.id)
            #释放资源
            del self.user_info

    def handleCreateRoom(self, packet: ServerBoundCreateRoomPacket) -> None:
        print("Create room with id", packet.roomId)
        creat_room_result = create_room(packet.roomId)
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


def handle_connection(connection: Connection):
    handler = MainHandler(connection)
    connection.set_receiver(lambda packet: packet.handle(handler))
    connection.on_close(handler.on_player_disconnected)

if __name__ == '__main__':
    server = Server(HOST, PORT, handle_connection)
    asyncio.run(server.start())