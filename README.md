<img src="logo.png" alt="pyphira logo" align="right" width="23%">
<div align="center">
  <h1>pyphira-mp</h1>
  <h3>一个基于 Python asyncio 的 <b>Phira</b> 多人游戏服务器</h3>
  <h5><i>正在积极测试中，可能不稳定，如遇任何问题，欢迎提供反馈和建议！</i></h5>
</div>

## 介绍

pyphira-mp 是**完全独立**的 Phira 多人游戏服务器端实现  
独立实现了 [phira-mp](https://github.com/TeamFlos/phira-mp) 的网络协议和游戏逻辑而不基于其源码

允许玩家:
* 创建房间
* 共同游玩谱面
* 管理游戏状态

与原版 phira-mp 的不同且需要注意的差异:
* 断线重连不会自动重新加入房间
* 房主退出房间时会重新指定新的房主
* 没有实现完整的monitor能力

---

## 如何使用

### 环境要求
- Python 3.7+

### 安装与启动

1. **克隆项目**：
```bash
git clone https://github.com/Evi233/pyphira-mp/
cd pyphira-mp
```

2. **安装依赖**：
```bash
pip install -r requirements.txt
```

3. **启动服务器**：
```bash
python main.py
```
服务器默认运行在 `0.0.0.0:12346`

### 配置说明

**服务器地址/端口**：在 `main.py` 中修改 `HOST` 和 `PORT`

**Monitor权限 (未实现)**：在 `monitors.txt` 中每行添加一个用户 ID

**国际化文本**：修改 `i10n/zh-rCN.json`

---

## 插件系统（事件驱动 / 支持热重载）

pyphira-mp 内置了一个轻量的**事件驱动插件系统**：

- 插件目录固定为项目根目录：`./plugins/`
- 插件是普通的 `.py` 文件，直接丢进该目录即可被加载
- 运行中支持**热重载**：新增/修改/删除插件文件，会自动加载/重载/卸载（默认 1 秒轮询一次文件 `mtime`，不依赖额外第三方库）
- 内置的console_admin是指令系统，可以删除来取消指令
更完整的文档请见：[`pyphira-mp-plugin-example`](https://github.com/evi233/pyphira-mp-plugin-example)

### 插件文件结构

在 `plugins/` 下创建一个 `xxx.py`，提供一个 `setup(ctx)` 函数即可：

```py
# plugins/my_plugin.py

PLUGIN_INFO = {
    "name": "my_plugin",
    "version": "0.0.1",
}


def setup(ctx):
    # 注册事件监听
    def on_auth_success(connection=None, user_info=None, **_):
        ctx.logger.info("user authed: %s", getattr(user_info, "id", None))

    ctx.on("auth.success", on_auth_success)

    # 可选：返回 teardown，用于卸载/重载前清理资源
    def teardown():
        ctx.logger.info("plugin teardown")

    return teardown
```

`ctx`（PluginContext）提供：

- `ctx.on(event, callback)`：订阅事件（支持 sync / async 回调）
- `ctx.once(event, callback)`：订阅一次性事件
- `ctx.emit(event, **payload)`：触发事件（一般用于插件间通信）
- `ctx.logger`：带插件名前缀的 logger

> 注意：插件通过 `ctx.on/once` 注册的回调，会自动绑定到该插件；当插件被卸载/重载时，这些回调会被自动移除，避免重复注册/内存泄漏。


### 示例插件

仓库自带示例插件：`auth_test.py`，在用户鉴权成功后向该用户发送：

> `插件测试v0.0.1`

你可以直接修改该文件保存，观察服务端日志出现 `Detected change, reloading`，无需重启服务。

---

## 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feat/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feat/AmazingFeature`)
5. 开启 Pull Request

---

## 致谢

- **[jphira-mp-protocol](https://github.com/lRENyaaa/jphira-mp-protocol)**：Phira 协议实现

---


## 许可证

本项目采用 **GPL v3** 许可证 - 查看 [LICENSE](./LICENSE) 文件了解详情
