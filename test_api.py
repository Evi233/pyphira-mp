import os
import time
import requests

# 配置
BASE_URL = "http://127.0.0.1:12347"
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN", "") # 如果你设置了永久Token，可以在这里填入，或者通过环境变量传入

def print_header(title):
    print(f"\n{'='*20} {title} {'='*20}")

def print_result(name, res, expected_status=[200]):
    is_success = res.status_code in expected_status
    status_color = "\033[92m" if is_success else "\033[91m"
    reset_color = "\033[0m"
    
    print(f"[{status_color}{res.status_code}{reset_color}] {name}")
    if not is_success:
        print(f"    -> 响应: {res.text}")
    else:
        try:
            print(f"    -> 返回: {res.json()}")
        except:
            print(f"    -> 返回: {res.text}")
    return is_success

def test_otp_flow():
    """测试 OTP 临时鉴权流程"""
    print_header("测试 OTP 鉴权流程")
    
    # 1. 请求 OTP
    res = requests.post(f"{BASE_URL}/admin/otp/request")
    if res.status_code == 403 and "otp-disabled" in res.text:
        print("[-] 服务器已配置永久 ADMIN_TOKEN，跳过 OTP 流程。")
        return ADMIN_TOKEN
        
    print_result("请求 OTP", res, [200])
    data = res.json()
    if not data.get("ok"):
        return None
        
    ssid = data["ssid"]
    print(f"\n[*] 请查看 pyphira-mp 的服务端控制台日志，找到类似 [OTP Request] 的输出。")
    otp_code = input(f"[*] 请输入分配给 SSID ({ssid}) 的 8 位 OTP 验证码: ").strip()
    
    # 2. 验证 OTP
    res = requests.post(f"{BASE_URL}/admin/otp/verify", json={
        "ssid": ssid,
        "otp": otp_code
    })
    print_result("验证 OTP 获取 Token", res, [200])
    
    verify_data = res.json()
    if verify_data.get("ok"):
        temp_token = verify_data["token"]
        print(f"[+] 成功获取临时 Token: {temp_token}")
        return temp_token
    return None

def run_tests(token):
    headers = {"X-Admin-Token": token} if token else {}
    
    print_header("1. 测试公共接口")
    res = requests.get(f"{BASE_URL}/room")
    print_result("获取公开房间列表", res, [200])

    print_header("2. 测试基础管理接口")
    res = requests.get(f"{BASE_URL}/admin/rooms", headers=headers)
    print_result("获取完整房间详情", res, [200])
    
    res = requests.get(f"{BASE_URL}/admin/room-creation/config", headers=headers)
    print_result("查询房间创建开关", res, [200])
    
    res = requests.post(f"{BASE_URL}/admin/room-creation/config", headers=headers, json={"enabled": False})
    print_result("关闭房间创建", res, [200])
    
    res = requests.post(f"{BASE_URL}/admin/room-creation/config", headers=headers, json={"enabled": True})
    print_result("恢复房间创建", res, [200])

    print_header("3. 测试全服系统接口")
    res = requests.post(f"{BASE_URL}/admin/broadcast", headers=headers, json={"message": "这是一条来自 API 自动化测试的广播！"})
    print_result("发送全服广播", res, [200])

    print_header("4. 测试黑名单接口")
    res = requests.get(f"{BASE_URL}/admin/ip-blacklist", headers=headers)
    print_result("查看 IP 黑名单", res, [200])
    
    res = requests.post(f"{BASE_URL}/admin/ip-blacklist/clear", headers=headers)
    print_result("清空 IP 黑名单", res, [200])

    print_header("5. 测试针对性管理接口 (预期返回 404, 因为使用虚构 ID)")
    
    dummy_room = "test_room_999"
    dummy_user = 999999
    
    res = requests.post(f"{BASE_URL}/admin/rooms/{dummy_room}/max_users", headers=headers, json={"maxUsers": 8})
    print_result("修改不存在房间的人数限制", res, [404])
    
    res = requests.post(f"{BASE_URL}/admin/rooms/{dummy_room}/chat", headers=headers, json={"message": "Hello!"})
    print_result("向不存在的房间发送消息", res, [404])
    
    res = requests.post(f"{BASE_URL}/admin/rooms/{dummy_room}/disband", headers=headers)
    print_result("解散不存在的房间", res, [404])
    
    res = requests.post(f"{BASE_URL}/admin/users/{dummy_user}/disconnect", headers=headers)
    print_result("踢出不在线的玩家", res, [404])

    # 封禁用户由于是直接落盘的，所以即使玩家不存在也会返回 200 (封禁记录会写入 json)
    res = requests.post(f"{BASE_URL}/admin/ban/user", headers=headers, json={
        "userId": dummy_user,
        "banned": True,
        "disconnect": False
    })
    print_result("封禁虚构玩家并写入记录", res, [200])
    
    # 记得解封清理测试数据
    res = requests.post(f"{BASE_URL}/admin/ban/user", headers=headers, json={
        "userId": dummy_user,
        "banned": False,
        "disconnect": False
    })
    print_result("解封虚构玩家", res, [200])
    
    print_header("6. 测试比赛模式接口 (预期 404)")
    res = requests.post(f"{BASE_URL}/admin/contest/rooms/{dummy_room}/config", headers=headers, json={"enabled": True})
    print_result("开启不存在房间的比赛模式", res, [404])
    
    res = requests.post(f"{BASE_URL}/admin/contest/rooms/{dummy_room}/start", headers=headers, json={"force": True})
    print_result("强制开始不存在的比赛", res, [404])

if __name__ == "__main__":
    print(f"开始测试 pyphira-mp HTTP API ({BASE_URL})")
    try:
        requests.get(BASE_URL)
    except requests.exceptions.ConnectionError:
        print("\n[!] 无法连接到服务器，请确认 pyphira-mp 已启动且 http_api 插件加载成功。")
        exit(1)
        
    token = ADMIN_TOKEN
    if not token:
        token = test_otp_flow()
        
    if not token:
        print("\n[!] 未能获取到管理员 Token，无法继续测试被保护的接口。")
    else:
        run_tests(token)
        
    print("\n测试执行完毕！")