# 开发规范

## 代码风格

### Python 代码规范
- 遵循 [PEP 8](https://peps.python.org/pep-0008/) 编码规范
- 使用 4 个空格缩进，不使用制表符
- 行长度不超过 120 个字符
- 函数和类之间使用两个空行分隔
- 导入语句按标准库、第三方库、本地模块分组，每组之间用空行分隔

### 命名规范
- **类名**: 使用 PascalCase（如 `RoomUser`, `ClientBoundPacket`）
- **函数名**: 使用 snake_case（如 `create_room`, `get_user_info`）
- **变量名**: 使用 snake_case（如 `user_info`, `room_id`）
- **常量**: 使用 UPPER_SNAKE_CASE（如 `HOST`, `PORT`）
- **私有成员**: 使用单下划线前缀（如 `_client_bound_packet_map`）

### 注释规范
- 使用中文注释，保持与项目一致
- 函数和类必须有文档字符串（docstring）
- 复杂逻辑需要行内注释说明
- TODO 注释使用 `TODO:` 前缀，并说明需要完成的内容

## 项目结构规范

### 目录组织
```
pphira-mp/
├── main.py                 # 主程序入口
├── server.py              # 服务器核心逻辑
├── connection.py          # 连接管理
├── room.py                # 房间管理
├── phiraapi.py            # Phira API 接口
├── i10n.py                # 国际化支持
├── asyncioutil.py         # 异步工具函数
├── monitors.txt           # 监控者列表
├── i10n/                  # 国际化文件
│   └── zh-rCN.json        # 中文翻译
├── rymc/                  # Phira 协议实现
│   └── phira/
│       ├── protocol/      # 协议层
│       │   ├── packet/    # 数据包定义
│       │   ├── data/      # 数据结构
│       │   ├── handler/   # 处理器
│       │   ├── codec/     # 编解码器
│       │   ├── exception/ # 异常定义
│       │   └── util/      # 工具类
│       └── __init__.py
└── DEVELOPMENT.md         # 开发规范（本文件）
```

### 模块职责
- **`main.py`**: 主程序入口，包含 `MainHandler` 类处理所有业务逻辑
- **`server.py`**: TCP 服务器实现，处理客户端连接
- **`connection.py`**: 管理单个客户端连接，负责数据收发
- **`room.py`**: 房间状态管理，包括用户、房主、状态等
- **`phiraapi.py`**: 与 Phira 官方 API 交互，获取用户信息
- **`i10n.py`**: 国际化支持，加载多语言文本
- **`asyncioutil.py`**: 异步 IO 工具函数，处理 VarInt 编码等

## 协议实现规范

### 数据包结构
1. **继承体系**: 所有数据包继承自 `ClientBoundPacket` 或 `ServerBoundPacket`
2. **命名规则**: 
   - 客户端到服务器: `ServerBoundXXXPacket`
   - 服务器到客户端: `ClientBoundXXXPacket`
3. **状态码**: 使用字符串状态码（如 `"0"` 表示成功，`"1"` 表示失败）

### 错误处理
- 使用返回值字典表示操作结果，包含 `status` 字段
- 状态 `"0"` 表示成功，其他值表示不同类型的错误
- 错误消息通过国际化系统获取，支持多语言

### 状态管理
- 房间状态使用状态机模式实现
- 状态类继承自基类，如 `SelectChart`, `WaitForReady`, `Playing`
- 状态转换通过 `set_state()` 函数统一管理

## 开发流程

### 添加新功能
1. **分析需求**: 理解需要实现的功能和涉及的协议
2. **设计协议**: 如果需要新数据包，在 `rymc/phira/protocol/` 下创建
3. **实现处理器**: 在 `MainHandler` 中添加处理方法
4. **更新房间逻辑**: 在 `room.py` 中添加相应的管理函数
5. **添加国际化**: 在 `i10n/zh-rCN.json` 中添加错误消息
6. **测试**: 确保功能正常工作，处理边界情况

### 添加新数据包
1. 在 `rymc/phira/protocol/packet/serverbound/` 或 `clientbound/` 创建新类
2. 继承相应的基类（`ServerBoundPacket` 或 `ClientBoundPacket`）
3. 在 `PacketRegistry.py` 中注册数据包 ID
4. 在 `MainHandler` 中添加处理方法

### 代码审查要点
- 是否处理了所有错误情况
- 是否有适当的日志输出
- 是否遵循命名规范
- 是否添加了必要的注释
- 是否更新了国际化文本
- 是否考虑了并发安全性

## 调试和日志

### 日志规范
- 使用 `print()` 输出关键信息（当前项目使用的方式）
- 连接/断开连接必须记录
- 错误情况必须记录
- 重要状态变更需要记录

### 调试技巧
- 使用 `data.hex()` 打印二进制数据便于调试
- 在异常处理中打印详细的错误信息
- 使用 TODO 标记需要完善的地方

## 性能考虑

### 异步编程
- 所有 IO 操作必须使用 `async/await`
- 使用 `asyncio.create_task()` 处理并发任务
- 避免阻塞操作，必要时使用线程池

### 内存管理
- 及时清理不再使用的连接和房间
- 使用 `del` 删除字典中的过期数据
- 注意循环引用，避免内存泄漏

## 安全规范

### 输入验证
- 验证所有来自客户端的数据
- 检查用户权限（房主、监控者等）
- 防止非法的状态转换

### 鉴权机制
- 使用 Phira 官方 API 验证用户 token
- 监控者列表从 `monitors.txt` 文件加载
- 敏感操作需要验证用户身份

## 测试建议

### 单元测试
- 为核心函数编写单元测试
- 测试边界条件和错误处理
- 模拟网络异常和并发场景

### 集成测试
- 测试完整的游戏流程
- 验证多客户端交互
- 测试房间状态转换

## 部署和维护

### 环境要求
- Python 3.7+
- 安装依赖：`pydantic`, `requests`, `tenacity`

### 配置文件
- `monitors.txt`: 监控者用户 ID 列表，每行一个
- `i10n/zh-rCN.json`: 中文错误消息配置

### 监控和运维
- 监控服务器日志
- 定期检查内存使用情况
- 备份重要数据（如监控者列表）