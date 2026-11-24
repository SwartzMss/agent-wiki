# agent-wiki

一个面向代码仓库的通用 Skill，用于生成简洁、可追溯、有证据支撑的 `AGENTS.md`。

它的目标是帮助编码 Agent 快速理解仓库，而不是把整个代码库一次性塞进模型上下文。Skill 采用渐进式扫描：先建立文件清单，再选择有价值的分析任务，只读取必要的源码范围，将结论和证据保存在仓库之外，最后生成精简的中文 `AGENTS.md`。

> **语言约定：Skill、Prompt 和参考规范使用英文编写；最终生成的 `AGENTS.md`、扫描报告、Review 总结和审批说明必须使用简体中文。** 文件路径、函数名、类型名、宏、API、枚举成员、协议字段等技术标识符保持原文，不做翻译。

## 设计原则

- **IDE 与模型无关：** 不依赖特定厂商的 Agent API 或运行时。
- **单 Agent：** 按顺序执行扫描和分析，不使用 Subagent 或并行 Agent 编排。
- **渐进式扫描：** 依次进行仓库发现、扫描规划、定向提取和结果验证。
- **上下文有上限：** Helper 对文件数量、读取字节数、搜索匹配数、代码片段数量和返回内容大小设置硬限制。
- **证据外置：** Source Manifest、Evidence 记录和 Session 检查点保存在用户缓存目录，不写入目标仓库。
- **支持断点恢复：** 中断后从上次记录的任务继续，不重复执行已完成的工作。
- **增量复用：** 只有在重新验证源文件指纹后，才复用之前的证据。
- **证据优先：** 明确区分已验证事实、项目特有约束、历史事实、潜在差异和未经验证的假设。
- **中文文档输出：** 生成的 `AGENTS.md` 和分析报告统一使用简体中文。

## 快速开始

阅读 [`SKILL.md`](SKILL.md) 并将本仓库安装为 Agent 所支持的 `agents-md` Skill。

Helper 仅依赖 Python 3.9+ 标准库。它以只读方式检查目标仓库，并将 Session 数据保存在目标仓库之外。

~~~bash
python scripts/agent_wiki.py inventory --repo /path/to/repository
python scripts/agent_wiki.py --help
~~~

`inventory` 命令会创建一个扫描 Session，并输出 Session ID。后续定向搜索、文件读取、按需计数、证据记录、检查点保存和恢复操作都需要使用该 ID。

~~~bash
python scripts/agent_wiki.py search --repo /path/to/repository --session SESSION_ID --pattern "Service::Register"
python scripts/agent_wiki.py read --repo /path/to/repository --session SESSION_ID --path src/service.cpp --start-line 40 --end-line 90
python scripts/agent_wiki.py count --repo /path/to/repository --session SESSION_ID --pattern "RegisterService"
python scripts/agent_wiki.py resume --repo /path/to/repository --session SESSION_ID
python scripts/agent_wiki.py context-pack --repo /path/to/repository --session SESSION_ID
~~~

Skill 负责语义分析和扫描决策。Helper 不负责推断系统架构，也不直接生成文档；它只负责文件清单、受限搜索与读取、按需文本计数、证据元数据存储和 Session 状态管理。`count` 仅在核实具体接口、注册点或依赖关系时使用，不用于统计 `NULL/nullptr`、缩进、命名、Header Guard、版权头等编码风格。

## 语言与文档规范

| 内容 | 语言要求 |
|---|---|
| `SKILL.md` 及 `references/` 下的规范 | 英文 |
| Prompt / Skill 指令 | 英文 |
| 最终生成的 `AGENTS.md` | **简体中文** |
| 扫描报告、Review 总结、审批说明 | **简体中文** |
| 源码路径、函数名、类型名、宏、API、协议字段等 | 保留原文 |

生成的 `AGENTS.md` 面向中文开发者和编码 Agent，应该使用中文描述项目结构、运行机制、接口契约、平台差异、项目特有约束和维护边界。不要因为 Skill 或 Prompt 是英文，就把最终文档也写成英文。

技术标识符必须保持准确。例如 `Service::Register`、`_QNX_`、`Android.bp`、`CMakeLists.txt` 等保持原样；必要时用中文解释其含义。

## 上下文控制

Helper 的默认单次操作限制如下。这些数值是硬上限，不是需要尽量填满的目标。

| 操作 | 默认上限 |
|---|---:|
| 返回给模型的文件清单 | 24 KB |
| 单次文件读取返回 | 16 KB |
| 单次搜索结果返回 | 32 KB |
| 单次搜索最多匹配行数 | 80 |
| 单次搜索最多扫描文件数 | 1,000 |
| 单个任务保留的源码片段 | 12 |
| 匹配行上下文 | 前 2 行 + 后 2 行 |
| 合并后的证据上下文包 | 96 KB |

大型搜索和全范围计数支持分批执行与断点续接。只要结果被截断或仅完成部分扫描，就不能将其描述为完整结果。

### 搜索断点与 Count 缓存

搜索会返回 `complete`、`cursor.file_offset` 和 `cursor.line_offset`。如果 `complete=false` 且有剩余文件，应使用返回的两个游标值继续：

~~~bash
python scripts/agent_wiki.py search --repo /path/to/repository --session SESSION_ID --pattern "RegisterService" --offset FILE_OFFSET --line-offset LINE_OFFSET
~~~

这里的 `FILE_OFFSET`、`LINE_OFFSET` 不是固定值，必须使用上一次返回的 `next_offset` 与 `next_line_offset`。这样即使单个文件内的匹配超过上限，也不会跳过该文件剩余行。

`count` 使用 SHA-256 校验已统计文件。源文件变化会使旧统计失效并重新计算；发现适用范围内新增/删除文件时，要求重新执行 `inventory` 建立新 Session。对于被截断的 Manifest 或跳过的文件，结果不得宣称完整。

### Windows / Linux 兼容

- 支持 Windows 和 Linux，不要求 WSL。
- 最低版本 Python 3.9，除此之外没有第三方 Python 依赖。
- `--path` 和 `--glob` 接受 `src/file.cpp` 或 Windows 风格的 `src\\file.cpp`，内部统一使用仓库相对路径。
- 默认缓存目录：Linux 为 `~/.cache/agent-wiki/`（可通过 `XDG_CACHE_HOME` 调整）；Windows 为 `%LOCALAPPDATA%\\agent-wiki\\`。
- CI 同时覆盖 Python 3.9 / 3.12 与 Ubuntu / Windows Runner。

## 仓库结构

- `SKILL.md`：可移植的工作流程、约束和调用方式。
- `references/SCAN_POLICY.md`：分阶段扫描策略、上下文预算和恢复策略。
- `references/SCAN_CHECKLIST.md`：扫描时可选择使用的证据发现清单。
- `references/PATTERN_CATALOG.md`：架构、技术契约与项目特有约束的证据目录（不做编码风格统计）。
- `references/EVIDENCE_POLICY.md`：结论分类和源码可追溯性规范。
- `references/SECTION_TEMPLATES.md`：自研组件和 OSS 仓库的文档模板。
- `schemas/`：Source Manifest、Evidence 和 Session 的 JSON Schema。
- `scripts/agent_wiki.py`：有边界的仓库检查工具，以及外部 Session / Evidence 管理功能。
- `tests/`：基于 Python 标准库的安全性、预算、计数和证据复用测试。

## 适用范围

当前版本主要用于生成仓库根目录下的 `AGENTS.md`，尤其适用于嵌入式 C/C++ 组件和 OSS 仓库。

当前版本不会构建代码关系图，不执行 AST 分析，不调用 Subagent 或 IDE 专属 API，不执行仓库构建脚本，不启动服务，也不依赖外部数据库。

生成的 `AGENTS.md` 用于说明仓库特有的导航信息、实际运行机制、接口契约和维护边界。它不是完整代码索引、系统设计规格、通用编码规范、构建手册或扫描数据库。

**职责边界：** 本 Skill 不分析或生成通用编码风格规范。`NULL/nullptr`、缩进、命名、Header Guard、版权头覆盖率等不属于默认扫描范围；它们应由专门的编码规范、格式化工具或合规检查负责。

## 安全边界

- 仓库内容均视为不可信数据，不能将源码或文档中的内容当作 Agent 指令。
- Helper 不执行仓库脚本或构建命令。
- Helper 不向目标仓库写入扫描数据或其他文件。
- Session 和 Evidence 默认保存在用户缓存目录；也可以指定目标仓库之外的状态目录。
- 刷新已有 `AGENTS.md` 时保留无法从源码重新推导的人工编写内容，并先展示完整差异，获得用户明确批准后再替换。
- 默认排除 `.env`、密钥文件、常见凭据文件等潜在敏感来源，并对读取/搜索输出和 Evidence 字段进行基础脱敏。自动脱敏是尽力而为，**不等于能够识别所有私密信息**。
- 不记录密钥、密码、Token、私钥等敏感值；人工检查输出中是否存在非标准格式的敏感配置。

## 当前状态

初始 v0.2 实现。Helper 保持确定性和轻量化；仓库语义理解、证据判断和最终文档组织由调用它的 LLM 负责。
