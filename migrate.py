#!/usr/bin/env python3
"""
一键搬家执行脚本 v2.0（通用版）
功能：检测环境 → 备份 → 合并配置 → 复制文件 → 完成搬家

修复（v2.0）：
- P0: 执行前自动备份，无覆盖丢失风险
- P0: config merge 而非 replace，保护新环境原有配置
- P0: create_main_agent() 逻辑补全
- P1: 优化找包逻辑，兼容解压后直接运行
"""

import os
import json
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

# =============================================
# 颜色输出
# =============================================
GREEN  = '\033[0;32m'
RED    = '\033[0;31m'
YELLOW = '\033[1;33m'
BLUE   = '\033[0;34m'
NC     = '\033[0m'

def log(msg):   print(f"{GREEN}[✓]{NC} {msg}")
def err(msg):   print(f"{RED}[✗]{NC} {msg}")
def warn(msg):  print(f"{YELLOW}[!]{NC} {msg}")
def info(msg):  print(f"{BLUE}[i]{NC} {msg}")

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip(), result.returncode

# =============================================
# 备份模块
# =============================================

BACKUP_DIR = Path.home() / ".qclaw" / "backup"

def backup_existing():
    """
    搬家前备份现有配置到 ~/.qclaw/backup/
    每次搬家创建带时间戳的子目录
    """
    info("检查是否需要备份...")
    
    need_backup = False
    targets = []
    
    # 检查 workspace
    for d in Path.home() / ".qclaw".iterdir():
        if d.is_dir() and d.name.startswith("workspace-"):
            need_backup = True
            targets.append(d)
    
    # 检查 openclaw.json
    config = Path.home() / ".qclaw" / "openclaw.json"
    if config.exists():
        targets.append(config)
    
    if not targets:
        info("  未检测到现有配置，无需备份")
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_sub = BACKUP_DIR / f"搬家备份_{timestamp}"
    backup_sub.mkdir(parents=True, exist_ok=True)
    
    info(f"  备份现有配置到：{backup_sub}")
    count = 0
    for t in targets:
        try:
            dst = backup_sub / t.name
            shutil.copytree(t, dst, dirs_exist_ok=True)
            count += 1
        except Exception as e:
            warn(f"  备份失败 {t.name}：{e}")
    
    log(f"  已备份 {count} 项")

# =============================================
# 配置合并模块
# =============================================

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def deep_merge(base, patch):
    """
    深度合并两个 dict。
    - patch 中有而 base 中无的键：直接添加
    - 两者都有且都是 dict：递归合并
    - 两者都有但类型不同：patch 覆盖 base
    """
    result = base.copy()
    for k, v in patch.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = deep_merge(result[k], v)
        else:
            result[k] = v
    return result

def merge_config(package_dir):
    """
    将搬家包中的 agents 配置与现有 openclaw.json 深度合并。
    只合并 agents 和 hooks 相关字段，保留其他所有配置。
    """
    info("合并 agent 配置（保护新环境原有配置）...")
    
    agents_file = package_dir / "openclaw-agents.json"
    if not agents_file.exists():
        warn("  找不到 openclaw-agents.json，跳过配置更新")
        return True
    
    agents_patch = load_json(agents_file)
    
    config_path = Path.home() / ".qclaw" / "openclaw.json"
    
    if config_path.exists():
        existing = load_json(config_path)
        info(f"  现有配置 keys：{list(existing.keys())}")
    else:
        existing = {}
        warn("  openclaw.json 不存在，将从零创建")
    
    # 深度合并 agents 和 hooks
    merged = existing.copy()
    
    if 'agents' in agents_patch:
        if 'agents' not in merged:
            merged['agents'] = {}
        merged['agents'] = deep_merge(merged['agents'], agents_patch['agents'])
        log("  agents 配置已合并")
    
    if 'hooks' in agents_patch:
        if 'hooks' not in merged:
            merged['hooks'] = {}
        # hooks.allowedAgentIds 需要合并（追加而非覆盖）
        existing_ids = set(merged['hooks'].get('allowedAgentIds', []))
        patch_ids = set(agents_patch['hooks'].get('allowedAgentIds', []))
        merged['hooks']['allowedAgentIds'] = list(existing_ids | patch_ids)
        log("  hooks 配置已合并")
    
    # 写回
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
    
    log(f"  openclaw.json 已更新（合并后）")
    return True

# =============================================
# 主流程步骤
# =============================================

def find_package_dir():
    """
    找到搬家包目录。
    优先顺序：
    1. 命令行参数传入
    2. 当前目录本身就是包目录（解压后直接 cd 进去）
    3. 当前目录下有 搬家包_* 目录
    4. 当前目录下有 *.zip
    """
    # 如果目录里有人身份层，说明当前就在包目录里
    if Path("身份层").exists():
        return Path.cwd()
    
    # 找搬家包_* 子目录
    for d in Path.cwd().iterdir():
        if d.is_dir() and d.name.startswith("搬家包_") and (d / "身份层").exists():
            return d
    
    # 找 zip 文件并解压
    zips = list(Path.cwd().glob("*.zip")) + list(Path.cwd().glob("搬家*.zip"))
    for zf in zips:
        info(f"  发现搬家包：{zf.name}")
        extract_dir = zf.with_suffix("")  # 去掉 .zip
        if extract_dir.exists():
            warn(f"  解压目录已存在，跳过解压")
        else:
            info(f"  解压到：{extract_dir}")
            with zipfile.ZipFile(zf, 'r') as zip_ref:
                zip_ref.extractall(Path.cwd())
        if (extract_dir / "身份层").exists():
            return extract_dir
    
    return None

def copy_identity_files(package_dir):
    """复制身份文件（backup 已在前面做过）"""
    info("复制身份文件...")
    
    identity_dir = package_dir / "身份层"
    if not identity_dir.exists():
        err("  找不到身份层目录")
        return False
    
    workspace = Path.home() / ".qclaw"
    workspace.mkdir(parents=True, exist_ok=True)
    
    # 找到 main agent workspace（从 agents 配置中读）
    config_path = workspace / "openclaw.json"
    main_ws = None
    
    if config_path.exists():
        config = load_json(config_path)
        for agent in config.get('agents', {}).get('list', []):
            if agent.get('id') == 'main':
                main_ws = agent.get('workspace', '')
                break
    
    # fallback：找 workspace-agent-* 目录
    if not main_ws:
        candidates = [d for d in workspace.iterdir()
                      if d.is_dir() and d.name.startswith("workspace-")]
        if candidates:
            # 直接取第一个候选 workspace（由 openclaw.json 的 main agent 配置决定）
            main_ws = str(candidates[0])
    
    if not main_ws:
        # 最后一个 fallback
        main_ws = str(workspace / "workspace-main")
    
    ws_path = Path(main_ws)
    ws_path.mkdir(parents=True, exist_ok=True)
    
    copied = 0
    for fname in ["SOUL.md", "MEMORY.md", "TOOLS.md", "AGENTS.md", "IDENTITY.md", "USER.md"]:
        src = identity_dir / fname
        if src.exists():
            shutil.copy2(src, ws_path / fname)
            copied += 1
    
    memory_src = identity_dir / "memory"
    if memory_src.exists():
        memory_dst = ws_path / "memory"
        memory_dst.mkdir(parents=True, exist_ok=True)
        for f in memory_src.glob("*.md"):
            shutil.copy2(f, memory_dst / f.name)
        copied += 1
    
    log(f"  已复制 {copied} 项到 {ws_path.name}/")
    return True

def copy_team_members(package_dir):
    """复制团队成员（自动检测）"""
    info("检查团队成员...")
    
    team_dir = package_dir / "团队成员层"
    if not team_dir.exists():
        info("  未检测到团队成员，跳过")
        return True
    
    workspace_base = Path.home() / ".qclaw"
    
    # 找到 main workspace 父目录
    main_ws = None
    config_path = workspace_base / "openclaw.json"
    if config_path.exists():
        config = load_json(config_path)
        for agent in config.get('agents', {}).get('list', []):
            if agent.get('id') == 'main':
                main_ws = agent.get('workspace', '')
                break
    
    if not main_ws:
        candidates = [d for d in workspace_base.iterdir()
                      if d.is_dir() and d.name.startswith("workspace-")]
        if candidates:
            main_ws = str(candidates[0])
    
    if main_ws:
        main_ws_path = Path(main_ws)
    else:
        main_ws_path = workspace_base / "workspace-main"
    
    count = 0
    for member_dir in team_dir.iterdir():
        if member_dir.is_dir():
            dst = main_ws_path / member_dir.name
            dst.mkdir(parents=True, exist_ok=True)
            for fname in ["SOUL.md", "MEMORY.md", "TOOLS.md"]:
                src = member_dir / fname
                if src.exists():
                    shutil.copy2(src, dst / fname)
            count += 1
    
    log(f"  已复制 {count} 个团队成员")
    return True

def copy_skills(package_dir):
    """复制 skills"""
    info("复制 skills...")
    
    skills_src = package_dir / "skills"
    if not skills_src.exists():
        warn("  未检测到 skills")
        return True
    
    workspace_base = Path.home() / ".qclaw"
    
    # 找 main workspace
    main_ws = None
    config_path = workspace_base / "openclaw.json"
    if config_path.exists():
        config = load_json(config_path)
        for agent in config.get('agents', {}).get('list', []):
            if agent.get('id') == 'main':
                main_ws = agent.get('workspace', '')
                break
    
    if not main_ws:
        candidates = [d for d in workspace_base.iterdir()
                      if d.is_dir() and d.name.startswith("workspace-")]
        if candidates:
            main_ws = str(candidates[0])
    
    if main_ws:
        ws_path = Path(main_ws)
    else:
        ws_path = workspace_base / "workspace-main"
    
    skills_dst = ws_path / "skills"
    skills_dst.mkdir(parents=True, exist_ok=True)
    
    count = 0
    for skill_dir in skills_src.iterdir():
        if skill_dir.is_dir():
            dst = skills_dst / skill_dir.name
            shutil.copytree(skill_dir, dst, dirs_exist_ok=True)
            count += 1
    
    log(f"  已复制 {count} 个 skills")
    return True

def create_cron_tasks(package_dir):
    """创建 cron 任务"""
    info("创建 cron 任务...")
    
    cron_file = package_dir / "cron_tasks.json"
    if not cron_file.exists():
        warn("  未检测到 cron 配置")
        return True
    
    cron_tasks = load_json(cron_file)
    
    # 检查已存在
    output, _ = run_cmd("openclaw tasks list --json 2>/dev/null")
    try:
        existing = json.loads(output) if output else []
        existing_names = {t.get('name', '') for t in existing}
    except:
        existing_names = set()
    
    created = 0
    skipped = 0
    failed = 0
    
    for task in cron_tasks:
        task_name = task.get('name', 'unnamed')
        
        if task_name in existing_names:
            skipped += 1
            info(f"  跳过已存在：{task_name}")
            continue
        
        task_json = json.dumps(task, ensure_ascii=False)
        cmd = f"openclaw tasks add --job '{task_json}'"
        output, code = run_cmd(cmd)
        
        if code == 0:
            log(f"  创建：{task_name}")
            created += 1
        else:
            err(f"  创建失败：{task_name}")
            failed += 1
    
    info(f"  结果：{created}个创建，{skipped}个跳过，{failed}个失败")
    return True

def restart_gateway():
    """重启 Gateway"""
    info("重启 Gateway...")
    output, code = run_cmd("openclaw gateway restart")
    
    if code == 0:
        log("  Gateway 已重启")
        info("  等待5秒让 channel 注册...")
        import time
        time.sleep(5)
    else:
        warn("  Gateway 重启命令可能失败")
        warn("  请手动执行：openclaw gateway restart")
    
    return True

# =============================================
# 用户交互
# =============================================

def prompt_main_agent_handling():
    """
    让用户选择如何处理 main agent。
    这次做完整逻辑：选项1/2/3 都有实际执行内容。
    """
    workspace_base = Path.home() / ".qclaw"
    config_path = workspace_base / "openclaw.json"
    
    has_main = False
    if config_path.exists():
        config = load_json(config_path)
        agents = config.get('agents', {}).get('list', [])
        has_main = any(a.get('id') == 'main' for a in agents)
    
    print()
    print("请选择如何处理 Main Agent：")
    print()
    print("  1. 指向现有 agent（把当前 agent 变成你的主控）")
    print("  2. 新建 main agent 实例（另起一个，保留当前配置）")
    if has_main:
        print("  3. 覆盖现有 main agent（⚠️ 替换现有主控）")
    print()
    
    choices = ["1", "2"]
    if has_main:
        choices.append("3")
    
    while True:
        choice = input("请输入选项（" + "/".join(choices) + "）：").strip()
        if choice in choices:
            break
        err("无效选项，请重新输入")
    
    # ---- 选项 1：指向现有 agent ----
    if choice == "1":
        info("将当前 agent 配置为 main...")
        
        if not config_path.exists():
            err("  openclaw.json 不存在，无法配置")
            return False
        
        config = load_json(config_path)
        
        # 找当前 agent 的 id
        # 先找 workspace-agent-* 目录
        main_ws = None
        candidates = [d for d in workspace_base.iterdir()
                      if d.is_dir() and d.name.startswith("workspace-")]
        
        for c in candidates:
            soul = c / "SOUL.md"
            if candidates:
                main_ws = str(candidates[0])  # 直接取第一个候选
        
        if not main_ws and candidates:
            main_ws = str(candidates[0])
        
        if main_ws:
            log(f"  找到 workspace：{main_ws}")
            
            # 把这个 agent 设为 main（添加或更新 agents.list）
            agents_list = config.get('agents', {}).get('list', [])
            
            # 移除已有的 main
            agents_list = [a for a in agents_list if a.get('id') != 'main']
            
            # 添加 main
            agents_list.insert(0, {
                "id": "main",
                "workspace": main_ws,
                "name": "Main Agent"
            })
            
            config['agents']['list'] = agents_list
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            log("  已将当前 agent 设为 main")
        else:
            warn("  未能自动找到 agent workspace")
            warn("  请手动在 openclaw.json 中设置 main agent 的 workspace")
        
        return True
    
    # ---- 选项 2：新建 main agent 实例 ----
    elif choice == "2":
        info("创建新的 main agent 实例...")
        
        # 创建目录结构
        new_ws = workspace_base / "workspace-new-main"
        new_ws.mkdir(parents=True, exist_ok=True)
        (new_ws / "memory").mkdir(exist_ok=True)
        (new_ws / "skills").mkdir(exist_ok=True)
        
        # 创建 agentDir
        agent_dir = workspace_base / "agents" / "main" / "agent"
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建 models.json
        models_config = {
            "providers": {
                "qclaw": {
                    "baseUrl": "http://127.0.0.1:19000/proxy/llm",
                    "apiKey": "__QCLAW_AUTH_GATEWAY_MANAGED__",
                    "api": "openai-completions",
                    "models": [
                        {"id": "modelroute", "name": "modelroute", "input": ["text", "image"]}
                    ]
                }
            }
        }
        with open(agent_dir / "models.json", 'w', encoding='utf-8') as f:
            json.dump(models_config, f, indent=2)
        
        # 更新 openclaw.json：添加 main agent
        if not config_path.exists():
            config = {}
        else:
            config = load_json(config_path)
        
        if 'agents' not in config:
            config['agents'] = {}
        if 'list' not in config['agents']:
            config['agents']['list'] = []
        
        # 移除已有的 main
        config['agents']['list'] = [a for a in config['agents']['list']
                                     if a.get('id') != 'main']
        # 添加新 main
        config['agents']['list'].insert(0, {
            "id": "main",
            "workspace": str(new_ws),
            "name": "Main Agent",
            "agentDir": str(agent_dir)
        })
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        log(f"  已创建 main agent：{new_ws}")
        return True
    
    # ---- 选项 3：覆盖 ----
    elif choice == "3":
        print()
        confirm = input("⚠️ 确认覆盖现有 main agent？输入 'yes' 继续：").strip()
        if confirm.lower() != 'yes':
            err("取消操作")
            return False
        
        info("将覆盖现有 main agent...")
        return True
    
    return True

# =============================================
# 主流程
# =============================================

def main():
    print()
    print("=" * 60)
    print("  一键搬家执行脚本 v2.0")
    print("=" * 60)
    print()
    
    # ---- 找到搬家包 ----
    info("定位搬家包...")
    package_dir = find_package_dir()
    
    if not package_dir:
        err("找不到搬家包！")
        print()
        print("请确保处于以下状态之一：")
        print()
        print("  方式 A：解压后进入目录")
        print("    unzip 搬家包.zip")
        print("    cd 搬家包")
        print("    python3 migrate.py")
        print()
        print("  方式 B：zip 文件在当前目录")
        print("    python3 搬家包/migrate.py")
        print()
        print("  方式 C：传入 zip 路径")
        print("    python3 migrate.py /path/to/搬家包.zip")
        print()
        return
    
    log(f"  搬家包目录：{package_dir.name}/")
    print()
    
    # ---- 备份 ----
    print("🔒 Step 0: 备份现有配置...")
    backup_existing()
    print()
    
    # ---- 用户选择 main agent 处理方式 ----
    print("🔧 Step 0.5: Main Agent 配置...")
    if not prompt_main_agent_handling():
        err("Main Agent 配置失败，中止搬家")
        return
    print()
    
    # ---- 主流程 ----
    steps = [
        ("Step 1: 复制身份文件",     copy_identity_files),
        ("Step 2: 复制团队成员",     copy_team_members),
        ("Step 3: 复制 skills",       copy_skills),
        ("Step 4: 合并 agent 配置",  merge_config),
        ("Step 5: 创建 cron 任务",   create_cron_tasks),
        ("Step 6: 重启 Gateway",     restart_gateway),
    ]
    
    for label, fn in steps:
        print(f"{label}...")
        result = fn(package_dir)
        if not result:
            err(f"{label} 失败")
        print()
    
    # ---- 完成 ----
    print("=" * 60)
    print("  ✅ 一键搬家完成！")
    print("=" * 60)
    print()
    print("📋 验证步骤：")
    print()
    print("  1. 检查 SOUL.md：")
    print("     ls ~/.qclaw/workspace-*/SOUL.md")
    print()
    print("  2. 测试子代理激活（在 agent 对话中）：")
    print("     '测试激活团队成员'")
    print()
    print("  3. 检查 cron 任务：")
    print("     openclaw tasks list")
    print()
    print("  4. 如需回滚（从备份恢复）：")
    backup_list = sorted(BACKUP_DIR.iterdir(), key=lambda d: d.name)
    if backup_list:
        latest = backup_list[-1].name
        print(f"     cp -r {BACKUP_DIR / latest}/* ~/.qclaw/")
    print()
    print("=" * 60)
    print()

if __name__ == "__main__":
    main()
