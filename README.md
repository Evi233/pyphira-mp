# pyphira-mp

一个基于 Python asyncio 的 **Phira** 多人游戏服务器

---

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

> **注意**：当前pyphira-mp仍在测试阶段，可能不稳定。欢迎提供反馈和建议！
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
