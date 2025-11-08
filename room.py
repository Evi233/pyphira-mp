from rymc.phira.protocol.data.state import *
# 全局房间“列表”（实际是 dict）
rooms = {}

# RoomUser 类：用于存储用户的详细信息和其网络连接
class RoomUser:
    """一个简单的容器，用于存储用户信息和其连接。"""
    def __init__(self, user_info, connection):
        self.info = user_info      # 存储 UserProfile/UserInfo 对象
        self.connection = connection # 存储 Connection 对象

class Room:
    def __init__(self, roomId):
        self.id = roomId
        self.host = None
        self.state = SelectChart(None)
        self.live = False
        self.locked = False
        self.cycle = False
        self.users = {} # 这个字典现在会存储 RoomUser 实例
        self.monitors = []
        self.chart = None

# 初始化监控列表
# 【注意】这里有一个潜在的bug：monitors应该是一个列表，但目前每次循环都会覆盖它。
# 应该修改为：
monitors = [] # 先初始化为空列表
try:
    with open("monitors.txt", "r") as f:
        for line in f:
            monitors.append(line.strip()) # 将每个监控者ID添加到列表中
except FileNotFoundError:
    print("monitors.txt not found. No monitors loaded.")


def create_room(roomId, user_info):
    """Create a room with the given ID.
    房间创建返回定义:
    0: 成功
    1: 房间已存在"""
    if roomId in rooms:                 # 已存在
        return {"status": "1"}
    rooms[roomId] = Room(roomId)       # 初始化并放入字典
    # 设置房主
    rooms[roomId].host = user_info.id
    return {"status": "0"}

def destroy_room(roomId):
    """Destroy the room with the given ID.
    房间销毁返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    del rooms[roomId]
    return {"status": "0"}

def add_user(roomId, user_info, connection):
    """Add a user to the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 用户已存在"""
    print("[add_user]called as"+ roomId +",userid:"+str(user_info.id))
    if roomId not in rooms:            # 房间不存在
        print("room 消失了")
        return {"status": "1"}
    if user_info.id in rooms[roomId].users: # 用户已存在
        print("user 存在"+str(user_info.id))
        return {"status": "2"}
    # 【修改】现在存储 RoomUser 实例，而不是直接存储 user_info
    rooms[roomId].users[user_info.id] = RoomUser(user_info, connection)
    return {"status": "0"}

def add_monitor(roomId, monitor_id):
    """Add a monitor to the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 监控已存在
    3: 无监控权限"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    if monitor_id in rooms[roomId].monitors: # 监控已存在
        return {"status": "2"}
    if monitor_id not in monitors: # 无监控权限 (检查全局 monitors 列表)
        return {"status": "3"}
    rooms[roomId].monitors.append(monitor_id)
    # 设置live为True
    if not rooms[roomId].live:
        rooms[roomId].live = True
    return {"status": "0"}

def get_host(roomId):
    """Get the host of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    print(rooms[roomId].host)
    return {"host": rooms[roomId].host}

def get_roomId(user_id):
    """Get the room ID of the user.
    返回定义:
    0: 成功
    1: 用户不存在"""
    for roomId, room in rooms.items():
        if user_id in room.users:
            return {"roomId": roomId}
    return {"status": "1"}
def change_host(roomId, host_id):
    """Change the host of the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 新房主不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    if host_id not in rooms[roomId].users: # 新房主不存在
        return {"status": "2"}
    rooms[roomId].host = host_id
    return {"status": "0"}

def room_lock_state_change(roomId):
    """Lock the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    #如果原来这个房间被锁定
    if rooms[roomId].locked:
        rooms[roomId].locked = False
    else:
        rooms[roomId].locked = True
    return {"status": "0"}

def set_state(roomId, state):
    """Set the state of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[roomId].state = state
    return {"status": "0"}

def set_cycle_mode(roomId, cycle):
    """Set the cycle mode of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[roomId].cycle = cycle
    return {"status": "0"}

def set_chart(roomId, chart):
    """Set the chart of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[roomId].chart = chart
    return {"status": "0"}

def player_leave(roomId, user_id):
    """Remove a user from the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 用户不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    if user_id not in rooms[roomId].users: # 用户不存在
        return {"status": "2"}
    # 【修改】使用 del 从字典中删除用户
    del rooms[roomId].users[user_id]
    return {"status": "0"}

def monitor_leave(roomId, monitor_id):
    """Remove a monitor from the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 监控不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    if monitor_id not in rooms[roomId].monitors: # 监控不存在
        return {"status": "2"}
    rooms[roomId].monitors.remove(monitor_id)
    return {"status": "0"}

# 【修改】is_monitor 函数定义和逻辑
def is_monitor(user_id): # 只接受 user_id 参数
    """检查一个 ID 是否在全局监控者列表中。
    返回定义:
    0: 是监控者
    1: 不是监控者"""
    if user_id in monitors: # 检查 user_id 是否在全局 monitors 列表中
        return {"monitor": "0"} # 是监控者
    else:
        return {"monitor": "1"} # 不是监控者
    
def get_connections(roomId):
    """Get the connection of all users in the room.
    返回定义:
    0: 成功
    1: 房间不存在""" # 这里不需要用户不存在的状态，因为遍历时不存在就不会被添加
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    connections = []
    for user_id in rooms[roomId].users:
        # 【修改】从 RoomUser 实例中获取 connection
        connections.append(rooms[roomId].users[user_id].connection)
    return {"status": "0", "connections": connections}
def get_room_state(roomId):
    """Get the state of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "state": rooms[roomId].state}
def get_all_users(roomId):
    """Get all users in the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "users": rooms[roomId].users}
def get_all_monitors(roomId):
    """Get all monitors in the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "monitors": rooms[roomId].monitors}
def is_live(roomId):
    """Check if the room is live.
    返回定义:
    0: 是直播
    1: 不是直播"""
    if roomId not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "isLive": rooms[roomId].live}

#---群体操作---
#获取一个人所在的所有房间
def get_rooms_of_user(user_id):
    """Get all rooms that a user is in.
    返回定义:
    0: 成功"""
    #TODO:1:用户不存在
    rooms_of_user = []
    for roomId in rooms:
        if user_id in rooms[roomId].users:
            rooms_of_user.append(roomId)
    return {"status": "0", "rooms": rooms_of_user}

def remove_user_from_all_rooms(user_id):
    """Remove a user from all rooms.
    返回定义:
    0: 成功 (用户至少从一个房间被移除)
    1: 用户不存在于任何房间"""
    
    user_was_in_a_room = False # 标志，用于判断用户是否至少从一个房间被移除了
    
    # 遍历所有房间的 ID
    # 使用 list(rooms.keys()) 是为了在遍历时避免字典结构被修改可能导致的问题，虽然这里不会发生
    for roomId in list(rooms.keys()):
        # 调用 player_leave 尝试从当前房间移除用户
        result = player_leave(roomId, user_id)
        
        # 如果 player_leave 返回状态 0 (成功移除)
        if result.get("status") == "0":
            user_was_in_a_room = True # 标记为 True，表示用户至少在一个房间中被发现并移除了
            
    if user_was_in_a_room:
        return {"status": "0"} # 用户至少从一个房间被移除，视为成功
    else:
        # 如果循环结束，user_was_in_a_room 仍然是 False，说明用户不在任何房间
        return {"status": "1"} # 用户不存在于任何房间