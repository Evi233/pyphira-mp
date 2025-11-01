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
    def __init__(self, room_id):
        self.id = room_id
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


def create_room(room_id):
    """Create a room with the given ID.
    房间创建返回定义:
    0: 成功
    1: 房间已存在"""
    if room_id in rooms:                 # 已存在
        return {"status": "1"}
    rooms[room_id] = Room(room_id)       # 初始化并放入字典
    return {"status": "0"}

def add_user(room_id, user_info, connection):
    """Add a user to the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 用户已存在"""
    print("[add_user]called as"+room_id+",userid:"+str(user_info.id))
    if room_id not in rooms:            # 房间不存在
        print("room 消失了")
        return {"status": "1"}
    if user_info.id in rooms[room_id].users: # 用户已存在
        print("user 存在"+str(user_info.id))
        return {"status": "2"}
    # 【修改】现在存储 RoomUser 实例，而不是直接存储 user_info
    rooms[room_id].users[user_info.id] = RoomUser(user_info, connection)
    return {"status": "0"}

def add_monitor(room_id, monitor_id):
    """Add a monitor to the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 监控已存在
    3: 无监控权限"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    if monitor_id in rooms[room_id].monitors: # 监控已存在
        return {"status": "2"}
    if monitor_id not in monitors: # 无监控权限 (检查全局 monitors 列表)
        return {"status": "3"}
    rooms[room_id].monitors.append(monitor_id)
    # 设置live为True
    if not rooms[room_id].live:
        rooms[room_id].live = True
    return {"status": "0"}

def change_host(room_id, host_id):
    """Change the host of the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 新房主不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    if host_id not in rooms[room_id].users: # 新房主不存在
        return {"status": "2"}
    rooms[room_id].host = host_id
    return {"status": "0"}

def room_lock_state_change(room_id):
    """Lock the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    #如果原来这个房间被锁定
    if rooms[room_id].locked:
        rooms[room_id].locked = False
    else:
        rooms[room_id].locked = True
    return {"status": "0"}

def set_state(room_id, state):
    """Set the state of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[room_id].state = state
    return {"status": "0"}

def set_cycle_mode(room_id, cycle):
    """Set the cycle mode of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[room_id].cycle = cycle
    return {"status": "0"}

def set_chart(room_id, chart):
    """Set the chart of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    rooms[room_id].chart = chart
    return {"status": "0"}

def player_leave(room_id, user_id):
    """Remove a user from the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 用户不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    if user_id not in rooms[room_id].users: # 用户不存在
        return {"status": "2"}
    # 【修改】使用 del 从字典中删除用户
    del rooms[room_id].users[user_id]
    return {"status": "0"}

def monitor_leave(room_id, monitor_id):
    """Remove a monitor from the room.
    返回定义:
    0: 成功
    1: 房间不存在
    2: 监控不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    if monitor_id not in rooms[room_id].monitors: # 监控不存在
        return {"status": "2"}
    rooms[room_id].monitors.remove(monitor_id)
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
    
def get_connections(room_id):
    """Get the connection of all users in the room.
    返回定义:
    0: 成功
    1: 房间不存在""" # 这里不需要用户不存在的状态，因为遍历时不存在就不会被添加
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    connections = []
    for user_id in rooms[room_id].users:
        # 【修改】从 RoomUser 实例中获取 connection
        connections.append(rooms[room_id].users[user_id].connection)
    return {"status": "0", "connections": connections}
def get_room_state(room_id):
    """Get the state of the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "state": rooms[room_id].state}
def get_all_users(room_id):
    """Get all users in the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "users": rooms[room_id].users}
def get_all_monitors(room_id):
    """Get all monitors in the room.
    返回定义:
    0: 成功
    1: 房间不存在"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "monitors": rooms[room_id].monitors}
def is_live(room_id):
    """Check if the room is live.
    返回定义:
    0: 是直播
    1: 不是直播"""
    if room_id not in rooms:            # 房间不存在
        return {"status": "1"}
    return {"status": "0", "isLive": rooms[room_id].live}

#---群体操作---
def remove_user_from_all_rooms(user_id):
    """Remove a user from all rooms.
    返回定义:
    0: 成功 (用户至少从一个房间被移除)
    1: 用户不存在于任何房间"""
    
    user_was_in_a_room = False # 标志，用于判断用户是否至少从一个房间被移除了
    
    # 遍历所有房间的 ID
    # 使用 list(rooms.keys()) 是为了在遍历时避免字典结构被修改可能导致的问题，虽然这里不会发生
    for room_id in list(rooms.keys()):
        # 调用 player_leave 尝试从当前房间移除用户
        result = player_leave(room_id, user_id)
        
        # 如果 player_leave 返回状态 0 (成功移除)
        if result.get("status") == "0":
            user_was_in_a_room = True # 标记为 True，表示用户至少在一个房间中被发现并移除了
            
    if user_was_in_a_room:
        return {"status": "0"} # 用户至少从一个房间被移除，视为成功
    else:
        # 如果循环结束，user_was_in_a_room 仍然是 False，说明用户不在任何房间
        return {"status": "1"} # 用户不存在于任何房间