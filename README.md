# EU AI Act Standards Monitor

自动监控 [ai-act-standards.com](https://ai-act-standards.com/) 上的协调标准状态，
每6小时检查一次，发现变化时发送邮件通知。

## 监控内容

- 各阶段标准数量（Stage 10 / 20 / 40 / 50 / 60）
- 已在 OJEU 引用的标准数量
- 总标准数量
- Changelog 表格新增条目
- 页面新出现或消失的标准编号

## 快速开始

### 第一步：Fork 或创建此仓库

将此仓库推送到你的 GitHub 账号。

### 第二步：配置 Gmail 应用专用密码

> ⚠️ **不要用你的 Gmail 登录密码**，需要生成"应用专用密码"

1. 前往 [Google 账号安全设置](https://myaccount.google.com/security)
2. 启用两步验证（若未启用）
3. 搜索"应用专用密码" → 创建一个，名称填 `github-actions`
4. 复制生成的16位密码（格式：`xxxx xxxx xxxx xxxx`）

### 第三步：在 GitHub 仓库中设置 Secrets

进入仓库 → **Settings → Secrets and variables → Actions → New repository secret**，
添加以下三个 Secret：

| Secret 名称 | 说明 | 示例 |
|---|---|---|
| `MAIL_USERNAME` | 你的 Gmail 地址 | `yourname@gmail.com` |
| `MAIL_PASSWORD` | 应用专用密码（16位，去掉空格） | `abcdabcdabcdabcd` |
| `NOTIFY_EMAIL` | 接收通知的邮件地址 | `yourname@gmail.com` |

> 收件地址和发件地址可以相同。

### 第四步：手动触发测试

1. 进入仓库 → **Actions** 选项卡
2. 找到 `Monitor EU AI Act Standards`
3. 点击 **Run workflow** → 勾选 `force_notify = true` → 运行
4. 检查你的邮箱

---

## 文件结构

```
.
├── .github/
│   └── workflows/
│       └── monitor.yml          # GitHub Actions 工作流
├── scripts/
│   └── check_standards.py      # 核心抓取与比对脚本
├── snapshots/
│   └── standards_snapshot.json # 自动生成的快照（首次运行后）
├── requirements.txt
└── README.md
```

## 运行逻辑

```
每6小时触发
    │
    ├─ 抓取 ai-act-standards.com
    ├─ 解析：各阶段数量 + Changelog + 标准编号
    ├─ 与 snapshots/standards_snapshot.json 对比
    │
    ├─ 有变化 → 生成邮件正文 → 发送邮件 → 更新快照
    └─ 无变化 → 更新快照（静默）
```

## 注意事项

- **首次运行**：仅建立基线快照，不发送邮件
- **快照存储**：每次运行后 bot 会自动 commit 更新的快照到仓库
- **调试**：每次运行的 `check_result.json` 会保存为 Actions Artifact，
  可在 Actions 页面下载查看

## 故障排查

| 问题 | 解决方案 |
|---|---|
| 邮件发送失败 | 确认 Secret 名称拼写正确；确认用的是应用专用密码而非登录密码 |
| 首次运行没有邮件 | 正常，首次仅建立快照。用 `force_notify=true` 手动测试 |
| Actions 报权限错误 | 检查 Settings → Actions → Workflow permissions 是否开启读写 |
| 网站结构变化导致解析失败 | 查看 Actions 日志，可能需要更新 `check_standards.py` 中的解析逻辑 |
