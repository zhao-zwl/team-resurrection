# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-04-22

### Added
- 完整一键搬家技能包 v1.0.0
- `SKILL.md` — 完整使用说明与交互流程
- `pack.py` — 自动检测并打包团队配置
- `migrate.py` — 用户选择式迁移恢复
- `cron_tasks.json` — 定时任务配置模板
- `openclaw-agents.json` — Agent 配置模板
- `MATERIAL_PACKING.md` — 打包材料清单文档

### 核心功能
- 自动检测 workspace 结构
- 自动备份现有配置
- 配置合并（不覆盖已有配置）
- 支持 Main Agent + 子代理完整迁移
