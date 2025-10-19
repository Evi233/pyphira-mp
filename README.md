# 使用指南（Python 版 Phira MP Protocol）

下面是把原 Java 协议库完整“等价”迁移到 Python 后的使用文档。保持了**项目结构、类名/文件名/方法名/字段名**一致（Python 风格仅做了最小化调整）。不依赖外部三方库，开箱可用。

---

## 环境要求

* Python 3.9+（建议 3.10 或更高）
* 该仓库（或 `jphira_mp_protocol_python` 目录）在你的 `PYTHONPATH` 中

  * 最简单：把 `jphira_mp_protocol_python` 目录加入你的项目并 `import`
  * 或在运行前：

    ```python
    import sys
    sys.path.append('jphira_mp_protocol_python')
    ```

---

## 目录结构（核心）

```
top/rymc/phira/protocol/
├── PacketRegistry.py               # 包ID映射、编解码入口
├── codec/
│   ├── decoder/FrameDecoder.py     # 帧解码（VarInt长度 + 协议握手）
│   ├── decoder/PacketDecoder.py    # 包解码（转为具体 ServerBoundPacket 实例）
│   ├── encoder/FrameEncoder.py     # 帧编码（写 VarInt 长度前缀）
│   └── encoder/PacketEncoder.py    # 包编码（写包ID + 数据体）
├── data/
│   ├── PacketResult.py             # SUCCESS / FAILED（可编码）
│   ├── RoomInfo.py, UserProfile.py # 数据结构（可编码）
│   ├── state/                      # GameState 及其子类（WaitForReady/SelectChart/Playing）
│   └── message/                    # 服务端广播消息体（ChatMessage 等）
├── exception/                      # 协议异常类型
├── handler/                        # PacketHandler 接口 & 简易实现
├── packet/
│   ├── ClientBoundPacket.py        # 发往客户端的包基类
│   ├── ServerBoundPacket.py        # 发往服务端的包基类
│   ├── clientbound/                # 具体 ClientBound* 包
│   └── serverbound/                # 具体 ServerBound* 包
└── util/
    ├── ByteBuf.py                  # 轻量 ByteBuf（读写原语、切片）
    ├── NettyPacketUtil.py          # VarInt/String 编解码工具
    └── PacketWriter.py             # 统一写入入口（根据类型分发）
```

---

## 快速上手：编码（Server → Client）

### 1）编码一个客户端包为二进制

```python
from top.rymc.phira.protocol.PacketRegistry import PacketRegistry
from top.rymc.phira.protocol.packet.clientbound.ClientBoundPongPacket import ClientBoundPongPacket

# 实例化一个 clientbound 包（示例：PONG）
packet = ClientBoundPongPacket.INSTANCE

# 编码：写入包ID + 数据体，得到 ByteBuf
buf = PacketRegistry.encode(packet)

# 如果要发到网络，通常再做帧封装（写长度前缀）：
from top.rymc.phira.protocol.codec.encoder.FrameEncoder import FrameEncoder

frame = FrameEncoder.encode(buf)   # 帧化
raw_bytes = frame.toBytes()        # bytes，可直接通过 socket 发送
```

### 2）带状态/列表的包示例（JoinRoom 成功）

```python
from top.rymc.phira.protocol.data.state.WaitForReady import WaitForReady
from top.rymc.phira.protocol.data.UserProfile import UserProfile
from top.rymc.phira.protocol.packet.clientbound import ClientBoundJoinRoomPacket
from top.rymc.phira.protocol.PacketRegistry import PacketRegistry

state = WaitForReady()
users = [UserProfile(1, 'Alice'), UserProfile(2, 'Bob')]
monitors = []
live = True

pkt = ClientBoundJoinRoomPacket.Success(state, users, monitors, live)
buf = PacketRegistry.encode(pkt)
raw = buf.toBytes()
```

> 说明
>
> * 多数 *Result* 包都有两个“变体类”：`Failed(reason)` / `Success()`（部分是 `OK()`）。
> * 在 Python 里，这些“变体类”是**独立的类**，并通过 `ClientBoundXxxPacket.Failed/Success/OK` 属性对外暴露，名字和 Java 保持一致。

---

## 快速上手：解码（Client → Server）

你从 socket 收到的是**帧**（前缀 VarInt 长度 + 包内容）。流程：

1. 使用 `FrameDecoder` 把字节流切成**完整帧**（并通过首个握手帧验证协议版本——已封装在 `FrameDecoder` 内）。
2. 用 `PacketDecoder` 或更直接的 `PacketRegistry.decode` 把帧内容解析为 `ServerBoundPacket` 实例。
3. 调用 `packet.handle(handler)` 分发给你的业务逻辑。

### 例：解码帧并处理

```python
from top.rymc.phira.protocol.util.ByteBuf import ByteBuf
from top.rymc.phira.protocol.codec.decoder.FrameDecoder import FrameDecoder
from top.rymc.phira.protocol.codec.decoder.PacketDecoder import PacketDecoder
from top.rymc.phira.protocol.handler.SimplePacketHandler import SimplePacketHandler

# 假设 raw_stream 是你从 socket 收到的字节流（可能一次读到多帧/半帧）
raw_stream = b"..."

frame_decoder = FrameDecoder()
for frame_buf in frame_decoder.feed(ByteBuf(raw_stream)):
    # frame_buf 是包体（不含长度前缀）
    packet = PacketDecoder.decode(frame_buf)      # -> ServerBoundPacket 实例
    handler = SimplePacketHandler(channel=None)   # 你也可以实现自定义 PacketHandler
    packet.handle(handler)
```

> 注意
>
> * 如果你自己已处理好版本/长度，也可直接：
>
>   ```python
>   from top.rymc.phira.protocol.PacketRegistry import PacketRegistry
>   packet = PacketRegistry.decode(frame_buf)  # frame_buf 为去掉长度前缀后的 ByteBuf
>   ```
> * 若数据不足，会抛出 `NeedMoreDataException`；VarInt 错误抛 `BadVarintException`；未知包ID抛 `CodecException`。

---

## 广播“消息体”（Message）给客户端

服务端可以把“房间事件”编码成 `ClientBoundMessagePacket`，里面包了一个 `Message` 对象（如 `ChatMessage`、`ReadyMessage` 等），再整体发送给客户端。

```python
from top.rymc.phira.protocol.data.message.ChatMessage import ChatMessage
from top.rymc.phira.protocol.packet.clientbound.ClientBoundMessagePacket import ClientBoundMessagePacket
from top.rymc.phira.protocol.PacketRegistry import PacketRegistry

msg = ChatMessage(user=1, content="Hello Room")
pkt = ClientBoundMessagePacket(msg)
buf = PacketRegistry.encode(pkt)
raw = buf.toBytes()
```

**内置消息（与 Java 对齐）：**

* `ChatMessage(user, content)`
* `CreateRoomMessage(user)`
* `JoinRoomMessage(user, name)`
* `LeaveRoomMessage(user, name)`
* `NewHostMessage(user)`
* `SelectChartMessage(user, chartName, chartId)`
* `GameStartMessage(user)`
* `GameEndMessage()`
* `ReadyMessage(user)`
* `CancelReadyMessage(user)`
* `CancelGameMessage(user)`
* `StartPlayingMessage()`
* `PlayedMessage(user, score, accuracy, fullCombo)`
* `LockRoomMessage(locked: bool)`
* `CycleRoomMessage(cycle: bool)`

---

## 数据结构与状态

* `UserProfile(userId: int, username: str)`
* `RoomInfo(...)`：包含房间 ID、状态 `GameState`、布尔标记（live/locked/cycle/isHost/isReady）、用户列表、监视者列表等
* `PacketResult.SUCCESS / FAILED`：带固定编码的“枚举类”
* `GameState`（3 种）：

  * `WaitForReady()`
  * `SelectChart(chartId: Optional[int] = None)`
  * `Playing()`

这些类都实现了 `encode(buf)`，可以被 `PacketWriter.write` 自动识别写入。

---

## 与 Java 版的差异点（重要）

1. **嵌套 Result 类**
   Java 里很多 `ClientBoundXxxPacket` 有内部类 `Failed/Success/OK`。
   Python 里它们是**独立类**，并通过同名属性暴露：
   `ClientBoundXxxPacket.Failed(...) / .Success(...) / .OK(...)`（调用方式不变）。

2. **ByteBuf**
   使用纯 Python `ByteBuf`，提供 `write/read`、`slice`、`toBytes()` 等常用方法；字符串/VarInt 编解码由 `NettyPacketUtil` 实现。

3. **Netty → 纯 Python**
   没有 ChannelPipeline；`FrameEncoder/FrameDecoder` 提供最小可用的帧编解码；`PacketHandler` 作为回调接口（你实现业务逻辑）。

---

## 典型收发流程（整合示例）

### 服务端发送（伪代码）

```python
# 1) 组包
from top.rymc.phira.protocol.packet.clientbound.ClientBoundReadyPacket import ClientBoundReadyPacket
from top.rymc.phira.protocol.PacketRegistry import PacketRegistry
from top.rymc.phira.protocol.codec.encoder.FrameEncoder import FrameEncoder

pkt = ClientBoundReadyPacket.Success()
body = PacketRegistry.encode(pkt)    # 包ID + 数据体
frame = FrameEncoder.encode(body)    # 长度前缀 + 包体
socket.sendall(frame.toBytes())
```

### 服务端接收（伪代码）

```python
from top.rymc.phira.protocol.codec.decoder.FrameDecoder import FrameDecoder
from top.rymc.phira.protocol.PacketRegistry import PacketRegistry
from top.rymc.phira.protocol.handler.PacketHandler import PacketHandler

class MyHandler(PacketHandler):
    def onPing(self, packet): ...
    def onChat(self, packet): ...
    # 覆盖你关心的方法（同 Java 版）

frame_decoder = FrameDecoder()
handler = MyHandler()

while True:
    chunk = socket.recv(4096)
    if not chunk:
        break
    for frame_buf in frame_decoder.feed(ByteBuf(chunk)):
        packet = PacketRegistry.decode(frame_buf)  # ServerBoundPacket
        packet.handle(handler)                     # 分发回调
```

---

## 常见问题（FAQ）

**Q1：如何把这个库当作依赖来用？**
A：当前是纯源码目录。直接把 `jphira_mp_protocol_python` 放到你的项目里，或把它加入 `PYTHONPATH`。如果你需要 `pip install` 形态，可以把该目录做成本地包（添加 `pyproject.toml`/`setup.cfg` 后 `pip install -e .`）。

**Q2：收包时提示 NeedMoreDataException？**
A：表示还没收到完整帧或包。继续累计字节后再喂给 `FrameDecoder.feed()`；或自己确保凑齐完整帧再调用 `PacketRegistry.decode()`。

**Q3：为什么我看到很多 `PacketWriter.write(buf, x)`？**
A：这是统一的写入入口。它会根据 `x` 的类型（int/str/bool/bytes、自定义可编码对象等）选择正确的写法，保持与 Java 行为一致。

**Q4：包ID表在哪？**
A：在 `PacketRegistry.py` 里面集中维护（与 Java 对应）。添加新包时只需在注册表里补齐映射。

---

## 最小可运行示例（自测）

```python
import sys
sys.path.append('jphira_mp_protocol_python')

from top.rymc.phira.protocol.PacketRegistry import PacketRegistry
from top.rymc.phira.protocol.packet.clientbound.ClientBoundChatPacket import ClientBoundChatPacket

# 编码
pkt = ClientBoundChatPacket.Success()
buf = PacketRegistry.encode(pkt)
print("encoded:", buf.toBytes())

# 简单帧编码
from top.rymc.phira.protocol.codec.encoder.FrameEncoder import FrameEncoder
frame = FrameEncoder.encode(buf)
print("framed:", frame.toBytes())
```

如果你需要我把这份库打成 `pip` 可安装的包、或补上完整的“收发 Socket 示例工程”，我可以直接帮你补齐。
