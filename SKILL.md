# 一键搬家Skill（Team Resurrection）

> **通用的一键搬家技能包** v2.0。支持多Agent团队的完整迁移：打包 → 搬家 → 复活。
>
> **适用场景：** 用户换电脑、重装系统、迁移团队到新环境。
>
> **版本说明：** v2.0 核心改进——自动备份、配置合并（不覆盖）、选项逻辑补全、通用 workspace 检测。

---

## 零、快速开始

### 用户视角的完整流程

```
用户（旧环境）：我要搬家
Agent：好的，开始打包...
       [执行 pack.py]
       检测到 workspace：~/.qclaw/workspace-xxx
       打包完成：~/一键搬家包/Agent搬家包_YYYYMMDD.zip
       请把搬家包复制到新环境

用户（新环境）：[把搬家包丢给agent] 这是一键搬家包，帮我搬家
Agent：好的，开始执行...
       [解压 + 执行 migrate.py]
       
       🔒 Step 0: 备份现有配置 → ~/.qclaw/backup/搬家备份_xxx/
       🔧 Step 0.5: Main Agent 配置
       请选择如何处理 Main Agent：
         1. 指向现有agent（把当前 agent 指向新 workspace）
         2. 新建main agent实例
         3. 覆盖现有main agent（⚠️ 当前的main会被替换）
       用户选择：2
       
       复制身份文件 ✓
       复制团队成员 ✓
       复制skills ✓
       合并agent配置（保护新环境其他配置）✓
       创建cron ✓
       重启Gateway ✓
       ✅ 搬家完成！
       如需回滚：cp -r ~/.qclaw/backup/搬家备份_xxx/* ~/.qclaw/
```

---

## 一、核心概念

### 1.1 团队激活三要素

子代理要正确激活，必须同时满足三个条件：

| 要素 | 参数 | 作用 |
|------|------|------|
| **身份** | `agentId` | 控制读哪个 SOUL.md（人格定义） |
| **隔离** | `cwd` | 控制子代理的 workspace 根目录 |
| **权限** | `allowAgents` | 白名单，允许 spawn 哪些 agentId |

**关键发现：**
- `agentId` 控制人格，不控制 workspace
- `cwd` 才控制 workspace 隔离
- 不设 cwd → 所有子代理读父代理的 workspace

### 1.2 通用化设计

**适配有/无团队：**
- **有团队成员** → 打包 + 复制团队成员
- **没有团队成员** → 跳过团队成员相关步骤

**适配有/无 main agent：**
- **有 main agent** → 提供三个选项（指向/新建/覆盖）
- **没有 main agent** → 提供两个选项（指向/新建）

**自动检测 workspace（v2.0）：**
不再硬编码 `workspace-xxx`，而是自动检测：
1. 读 `openclaw.json` 的 agents.list，找 main agent 的 workspace
2. fallback：遍历 `~/.qclaw/workspace-*` 目录，找包含 SOUL.md + MEMORY.md 的
3. fallback：从当前工作目录向上查找

### 1.3 备份与回滚

**搬家前自动备份：**
- 目标：`~/.qclaw/backup/搬家备份_YYYYMMDD_HHMMSS/`
- 内容：所有 `workspace-*` 目录 + openclaw.json
- 触发条件：检测到已有配置

**回滚方法：**
```bash
cp -r ~/.qclaw/backup/搬家备份_xxx/* ~/.qclaw/
```

### 1.4 配置合并策略（v2.0）

**核心原则：不覆盖新环境的其他配置。**

- agents 配置：deep merge（只合并 agents 字段）
- hooks 配置：union merge（allowedAgentIds 取并集）
- 其他配置（channel、plugins 等）：原样保留

---

## 二、脚本说明

### 2.1 脚本清单

| 脚本 | 功能 | 必需性 | 版本 |
|------|------|--------|------|
| `pack.py` | 打包所有资料 | ✅ 必需 | v2.0 |
| `migrate.py` | 一键搬家执行 | ✅ 必需 | v2.0 |
| `setup_config.py` | ~~仅更新配置~~ | ❌ 已废弃 | — |
| `init.sh` | ~~创建main agent~~ | ❌ 已废弃 | — |

> ⚠️ v2.0 将 setup_config.py 和 init.sh 的功能全部并入 migrate.py，无需单独执行。

### 2.2 pack.py（打包脚本）

**功能：** 自动检测当前 workspace，收集所有资料，生成搬家包

**执行方式：**
```bash
cd skills/team-resurrection
python3 pack.py
```

**自动检测内容：**
1. 从 `openclaw.json` 找到当前 active workspace
2. 检测是否有团队成员（有 → 打包，无 → 跳过）
3. 收集 skills、Cron 配置、Agent 配置片段
4. 动态生成 README.md（根据实际内容）

**输出：** `~/一键搬家包/{Agent名称}搬家包_YYYYMMDD_HHMMSS.zip`

**v2.0 改进：**
- ✅ 不再硬编码 workspace 路径
- ✅ 自动推断 agent 名称（从 SOUL.md/IDENTITY.md）
- ✅ README.md 根据实际内容动态生成

### 2.3 migrate.py（一键执行脚本）

**功能：** 完整的一键搬家流程（v2.0）

**执行方式：**
```bash
# 方式A（推荐）：解压后直接运行
unzip 搬家包.zip
cd 搬家包
python3 migrate.py

# 方式B：zip 在当前目录
python3 migrate.py

# 方式C：传入路径
python3 migrate.py /path/to/搬家包.zip
```

**执行步骤（v2.0）：**

| Step | 内容 | 说明 |
|------|------|------|
| 0 | 备份现有配置 | 自动检测已有机配置，备份到 `~/.qclaw/backup/` |
| 0.5 | Main Agent 配置 | **交互选择**（三个选项均有完整执行逻辑） |
| 1 | 复制身份文件 | SOUL.md / MEMORY.md / TOOLS.md 等 |
| 2 | 复制团队成员 | 自动检测，有则复制，无则跳过 |
| 3 | 复制 skills | 整个 skills 目录覆盖 |
| 4 | 合并 agent 配置 | deep merge，保护新环境其他配置 |
| 5 | 创建 cron 任务 | 跳过已存在的 |
| 6 | 重启 Gateway | 等待 5 秒让 channel 注册 |

**Main Agent 选项（v2.0 逻辑补全）：**

```
选项 1：指向现有 agent
  → 自动找到当前 workspace → 写入 openclaw.json agents.list

选项 2：新建 main agent 实例
  → 创建目录（~/.qclaw/workspace-new-main/）
  → 创建 agentDir + models.json
  → 写入 openclaw.json agents.list

选项 3：覆盖现有 main agent（需二次确认）
  → 删除旧 main workspace → 执行正常复制流程
```

**v2.0 核心改进：**
- ✅ 搬家前自动备份，可随时回滚
- ✅ config deep merge 而非 replace，保护新环境已有配置
- ✅ 三个 main agent 选项均有**完整执行逻辑**（v1.0 选项1/2 只打印警告）
- ✅ 兼容多种运行方式（解压后直接运行 / zip 在当前 / 传入路径）

### 2.4 ~~setup_config.py~~（已废弃）

⚠️ **v2.0 已废弃**：配置更新、cron 创建、Gateway 重启功能已全部并入 `migrate.py`。
保留此文件仅用于旧版搬家包兼容。

### 2.5 ~~init.sh~~（已废弃）

⚠️ **v2.0 已废弃**：创建 main agent 实例功能已并入 `migrate.py` 交互流程。
保留此文件仅用于旧版搬家包兼容。

---

## 三、搬家包结构

### 3.1 标准结构

```
搬家包/
├── README.md                    ← 动态生成（含团队成员列表）
├── migrate.py                   ← v2.0 一键执行脚本
│
├── 身份层/                      ← Main Agent
│   ├── SOUL.md                  ← 人格定义
│   ├── MEMORY.md                ← 长期记忆
│   ├── TOOLS.md                 ← 工具配置
│   ├── AGENTS.md                ← 团队成员表
│   ├── IDENTITY.md              ← 身份标识
│   ├── USER.md                  ← 用户信息
│   └── memory/                  ← 历史记录（如有）
│
├── 团队成员层/                  ← 子代理（自动检测，有则包含）
│   ├── 成员A/
│   │   └── SOUL.md
│   ├── 成员B/
│   └── ...
│
├── skills/                      ← Skills（自动检测，有则包含）
│
├── openclaw-agents.json         ← Agent 配置片段
├── cron_tasks.json              ← Cron 任务清单（如有）
└── 工作目录说明.md             ← git工作目录提示（打包时检测）
```

### 3.2 通用化

| 场景 | pack.py 行为 | migrate.py 行为 |
|------|-------------|----------------|
| 有团队 | 打包团队成员 | 复制团队成员 |
| 无团队 | 跳过 | 跳过并提示 |
| 有 cron | 打包 | 创建（跳过已存在） |
| 无 cron | 跳过 | 跳过并提示 |

---

## 四、配置文件说明

### 4.1 openclaw.json 核心配置

```json
{
  "agents": {
    "list": [
      { "id": "main", "name": "Main Agent" },
      {
        "id": "member-a",
        "name": "成员A",
        "workspace": "/Users/xxx/.qclaw/workspace-xxx/member-a",
        "agentDir": "/Users/xxx/.qclaw/agents/member-a/agent"
      }
    ],
    "defaults": {
      "model": { "primary": "qclaw/modelroute" },
      "maxConcurrent": 10,
      "subagents": {
        "allowAgents": ["*"]
      }
    }
  },
  "hooks": {
    "allowedAgentIds": ["member-a", "member-b", ...]
  }
}
```

### 4.2 关键配置项

| 配置项 | 说明 |
|--------|------|
| `agents.list[].id` | Agent 标识，新版用英文名（如 `member-a`） |
| `agents.list[].name` | 显示名，可以是中文（如 `成员A`） |
| `agents.list[].workspace` | Agent workspace 绝对路径 |
| `agents.list[].agentDir` | Agent 独立目录，含 `models.json` |
| `agents.defaults.subagents.allowAgents` | Spawn 白名单，`["*"]` 允许所有 |
| `hooks.allowedAgentIds` | hooks 触发时的白名单 |

### 4.3 models.json（每个 agent 独立）

```json
{
  "providers": {
    "qclaw": {
      "baseUrl": "http://127.0.0.1:19000/proxy/llm",
      "apiKey": "__QCLAW_AUTH_GATEWAY_MANAGED__",
      "api": "openai-completions",
      "models": [
        { "id": "modelroute", "name": "modelroute", "input": ["text", "image"] }
      ]
    }
  }
}
```

---

## 五、目录结构

```
~/.qclaw/
├── openclaw.json                    # 主配置
├── backup/                          # v2.0 备份目录
│   └── 搬家备份_YYYYMMDD_HHMMSS/
│
├── workspace-xxx/                   # Main Agent workspace（自动检测）
│   ├── SOUL.md                      # 人格定义
│   ├── MEMORY.md                    # 长期记忆
│   ├── TOOLS.md                     # 工具说明
│   ├── AGENTS.md                    # 团队配置
│   ├── skills/                      # 专属技能
│   └── memory/                      # 历史记录
│       └── 2026-04-22.md
│
├── agents/                          # Agent 独立目录
│   ├── main/
│   │   └── agent/
│   │       └── models.json          # 模型配置
│   ├── 成员A/
│   └── ...
```

---

## 六、常见问题排查

### 问题1：`agentId is not allowed`

**错误：** `agentId is not allowed for sessions_spawn (allowed: none)`

**原因：** openclaw.json 缺少 `allowAgents` 白名单

**解决：** migrate.py 执行时自动合并，配置 patch 会补上：
```json
{ "agents": { "defaults": { "subagents": { "allowAgents": ["*"] } } } }
```

### 问题2：子代理读错 SOUL.md

**现象：** spawn 成员A，但读的是 main 的 SOUL.md

**原因：** 没传 `cwd` 参数

**解决：** 确保 spawn 时传 `cwd` 参数：
```javascript
sessions_spawn({
  agentId: "member-a",
  cwd: "/Users/xxx/.qclaw/workspace-xxx/成员A", // 必须传
  mode: "run",
  task: "..."
})
```

### 问题3：Gateway 重启后 spawn 报错

**错误：** `invalid agent params: unknown channel: xxx`

**原因：** Gateway 重启时 channel 注册需要几秒完成

**解决：** 重启后等 5-10 秒再 spawn

### 问题4：子代理空跑/截断

**现象：** 子代理返回"我来写审核报告"然后停住，没有实际输出

**原因：** 任务描述不够具体，或 timeout 太短

**解决：**
1. 任务 prompt 简化，只说"做什么"不说"怎么做"
2. 增加示例输出格式
3. 预写脚本让子代理执行而非自己写

### 问题5：搬家后配置丢失

**现象：** 新环境的 channel、plugins 等配置被覆盖

**原因：** v1.0 用 config replace 而非 merge

**解决：** v2.0 已修复，使用 deep merge。如需回滚：
```bash
cp -r ~/.qclaw/backup/搬家备份_xxx/* ~/.qclaw/
openclaw gateway restart
```

---

## 七、验证清单

搬家完成后，逐一检查：

### 基础检查

- [ ] `openclaw gateway status` 显示 running
- [ ] `ls ~/.qclaw/workspace-*/SOUL.md` 找到主 Agent SOUL.md
- [ ] `ls ~/.qclaw/workspace-*/SOUL.md` 显示主 Agent SOUL.md

### 配置检查

- [ ] openclaw.json 包含所有 agent 配置
- [ ] `agents.defaults.subagents.allowAgents: ["*"]` 已设置
- [ ] `hooks.allowedAgentIds` 包含所有成员
- [ ] 每个 workspace 包含 SOUL.md
- [ ] 每个 agentDir 包含 models.json

### 功能检查

- [ ] Gateway 已重启并等待 5-10 秒
- [ ] 测试 spawn 至少 2 个 agent，确认人格正确
- [ ] Cron 任务已创建（如需要）
- [ ] Skills 已安装

### 完整验证命令

```bash
# 检查 Gateway
openclaw gateway status

# 检查 SOUL.md
ls ~/.qclaw/workspace-*/SOUL.md

# 检查团队成员
ls ~/.qclaw/workspace-*/

# 测试子代理（在 agent 对话中）
"测试激活团队成员"

# 检查 cron
openclaw tasks list

# 回滚（如需要）
ls ~/.qclaw/backup/
cp -r ~/.qclaw/backup/搬家备份_xxx/* ~/.qclaw/
openclaw gateway restart
```

---

## 八、维护建议

1. **定期打包**：每次重大变更后重新 `pack.py`
2. **备份保留**：至少保留最近 3 次搬家备份
3. **版本记录**：搬家包文件名含时间戳，保留记录
4. **测试验证**：搬家后立即执行验证清单
5. **日志记录**：所有配置变更记录到 `memory/YYYY-MM-DD.md`

---

## 九、相关文档

- OpenClaw 官方文档：https://docs.openclaw.ai/
- Sessions 文档：https://docs.openclaw.ai/automation/sessions
- Cron 文档：https://docs.openclaw.ai/automation/cron
- Agent 配置：https://docs.openclaw.ai/config/agents
- **材料打包记录：** `MATERIAL_PACKING.md`

---

## 附录：版本变更记录

### v2.0（2026-04-22）

**P0 修复：**
- ✅ pack.py 不再硬编码 workspace-xxx，改为自动检测 active workspace
- ✅ migrate.py 执行前自动备份，现有配置不再丢失
- ✅ config 改为 deep merge，保护新环境其他配置（channel、plugins 等）
- ✅ create_main_agent() 三个选项逻辑补全（v1.0 选项1/2 只打印警告）

**P1 修复：**
- ✅ 删除了 init.sh/setup_config.py 的"可选执行"误导文档
- ✅ migrate.py 找包逻辑优化，兼容多种运行方式

**P1 优化：**
- ✅ backup_existing() 自动检测需备份的目标
- ✅ cron 创建区分已存在/失败，不混淆
- ✅ find_package_dir() 支持解压后直接 cd 运行

### v1.0（2026-04-21）

- 初始版本：pack.py + migrate.py + setup_config.py + init.sh
- 支持有/无团队的通用化检测
- 三个 main agent 选项（但选项1/2 执行逻辑残缺）
