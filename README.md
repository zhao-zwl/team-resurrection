# Team Resurrection（团队复活 / 一键搬家）

> 通用的一键搬家 Skill，支持完整迁移 OpenClaw 多 Agent 团队。

## 功能

- **打包**（pack.py）：将当前 Agent 团队的完整配置打包为压缩包
- **迁移**（migrate.py）：在新环境中解压并恢复团队配置
- 支持：SOUL.md、SKILL.md、cron 任务、openclaw agents 配置

## 适用场景

- 换电脑 / 重装系统
- 迁移团队到新设备
- 备份团队配置

## 使用方式

1. **打包**：`python3 pack.py` → 生成搬家包
2. **迁移**：`python3 migrate.py` → 按提示操作

## 文档

- [SKILL.md](./SKILL.md) — 完整使用说明
- [MATERIAL_PACKING.md](./MATERIAL_PACKING.md) — 打包材料清单

## 版本

v2.0 — 自动备份、配置合并（不覆盖）、通用 workspace 检测
