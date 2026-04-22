# Team Resurrection

**OpenClaw 多 Agent 团队一键搬家技能包。**

换电脑 / 重装系统后，将整个团队打包带走，一键复活。

---

## 特性

- **零门槛**：一条命令完成打包/迁移
- **安全优先**：自动备份，配置合并不覆盖
- **通用适配**：支持 Main Agent + 任意数量子代理
- **跨平台**：Mac / Windows / Linux 均可用

## 快速开始

### 打包（旧环境）

```
python3 pack.py
```

生成搬家压缩包，复制到新环境。

### 迁移（新环境）

```
python3 migrate.py
```

按提示完成恢复，全程引导式。

## 完整文档

| 文件 | 说明 |
|------|------|
| [SKILL.md](./SKILL.md) | 完整使用说明 |
| [examples/README.md](./examples/) | 使用场景示例 |
| [templates/](./templates/) | 打包/迁移模板 |
| [MATERIAL_PACKING.md](./MATERIAL_PACKING.md) | 打包材料清单 |

## 版本

- v1.0.0（2026-04-22）— 首发
