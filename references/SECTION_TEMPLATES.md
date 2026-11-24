# AGENTS.md Section Templates

The templates define possible structures, not mandatory headings. Omit any section that has no useful, repository-specific evidence. Never leave an empty heading.

Write all generated prose and headings in Simplified Chinese. Preserve paths, identifiers, symbols, macros, target names, and protocol fields exactly.

## A. Custom embedded component profile

Use for project-owned APP/CBB/FWK/HAL-style components and repositories with comparable responsibilities.

~~~markdown
# AGENTS.md — <项目名>

> 本文件介绍 <项目名> 的职责、结构、运行关系、接口契约和维护边界。内容以仓库内可验证的事实为依据。

## 1. 项目地图

<用一段话说明组件职责、所在系统层次、主要输入/输出，以及对外提供的产物。>

| 位置 / 产物 | 职责 | 证据 / 关联 |
|---|---|---|
| src/<module>/ | <模块职责> | <关键文件或 target> |
| include/<module>/ | <已确认的对外接口> | <导出/安装证据> |
| test/ / tools/ | <测试或工具职责> | <实际接线情况> |

## 2. 运行时结构

- <进程入口、启动者或框架回调；仅在调用链可追踪时描述顺序。>
- <主要模块之间的调用、事件、IPC 或 RPC 关系。>
- <关键状态、缓存、持久化路径和生命周期。>
- <平台差异及其对应实现路径。>

## 3. 平台与部署

- <平台 → 实际构建 target → 部署产物的对应关系。区分已配置、已构建和已部署。>
- <平台宏及其模块适用范围。>
- <关键编译选项、链接依赖和条件编译事实。>
- <部署清单及目标平台。>
- <依赖 manifest 中声明的依赖和已确认的版本约束。>
- <版本文件及具体不一致；存在可靠差异时标注“需确认”。>

## 4. 跨组件契约

- <公共头文件、导出符号、ABI 和所有权约束。>
- <RPC/IPC/协议定义、字段编号、枚举值、错误码和注册名称。>
- <跨进程共享状态、设备节点、socket、服务端点和持久化路径。>
- <已确认的下游消费者；注明扫描边界。>

## 5. 项目特有约束与风险

- <已确认的启动/退出顺序、回调线程上下文、资源所有权和生命周期约束。>
- <跨组件的协议/错误码/注册键等一致性要求，以及可验证的保护依据。>
- <生成文件的权威输入位置、真实兼容性边界或历史回归风险。>

## 6. 测试与工具

- <测试目录、框架、测试注册方式和实际覆盖的模块/平台。>
- <工具、samples、debug utility 的职责和接线情况。>
- <CI 中实际执行的静态检查、lint 或覆盖率任务。>

## 7. 维护边界

### 修改前先确认

- <有证据支持的 ABI、协议、持久化、启动顺序、平台适配或生成文件边界。>

### 禁止事项

- <仅列出明确安全要求、许可证或已验证的项目约束；没有证据时省略。>
~~~

## B. Lightweight OSS profile

Use when the repository is demonstrably an upstream third-party project or a maintained internal fork.

~~~markdown
# AGENTS.md — <项目名>（OSS）

> 本文件介绍该第三方组件的上游来源、仓库结构、内部集成、本地改动、依赖关系和维护边界。

## 1. 这是什么

- 上游项目：<项目名与 URL；无法确认时明确说明。>
- 上游基线：<版本、tag 或 commit；区分上游版本与内部打包版本。>
- 核心能力：<一句话概括，并以 README 或源码为依据。>
- 许可证：<许可证及 LICENSE / NOTICE / attribution 文件。>
- 本地改动：<已确认的补丁类别、标记方式或内部集成改动。>

## 2. 项目地图

| 位置 | 内容 | 证据 / 说明 |
|---|---|---|
| <source>/ | <上游核心源码职责> | <关键文件> |
| include/ | <已确认的对外头文件> | <导出证据> |
| build/ / Android.bp | <内部构建或分发集成> | <实际接线> |

## 3. 平台与分发

- <上游构建系统和内部集成入口；不写构建命令。>
- <实际产物、安装头文件和导出目录。>
- <已配置、实际构建、实际部署的平台差异。>
- <Android 预编译、下载源、产物名和 license metadata。>
- <关键编译选项、平台配置和链接依赖。>
- <上游版本、内部版本和 changelog 的一致性；具体差异标注“需确认”。>

## 4. 本仓相对上游的改动

- <已确认的本地补丁及其代码位置。>
- <内部平台适配、产物改名、打包或分发改动。>
- <补丁标记和 changelog 的实际使用情况。>
- <升级上游时需要同步检查的版本、配置和补丁位置。>

## 5. 依赖关系与消费者

- <本仓声明的依赖及其版本。>
- <实际链接或运行时加载的依赖；与声明不一致时标注“需确认”。>
- <工作区内已确认的下游消费者及引用位置。>
- <接口、导出符号、默认配置或版本变化的已知影响范围。>

## 6. 维护边界

- <许可证、NOTICE、版权归属、上游来源或安全兼容约束。>
- <修改公共接口、平台配置、打包和子模块时需要确认的具体影响。>
- <只有存在明确依据时才写禁止事项。>
~~~

## C. Other or mixed repositories

Start from the custom-component profile, keep only relevant sections, and add a section only when a repository-specific concept cannot be represented accurately. Do not duplicate detailed documentation owned by nested repositories.

## Shared writing rules

- Use concise declarative Chinese. One bullet should express one fact or constraint.
- Use repository-relative paths.
- Preserve identifiers and symbols exactly.
- Distinguish configured, built, deployed, and runtime-loaded.
- Prefer a path or symbol over a long copied code fragment.
- Use 需确认 only for a concrete, evidence-backed discrepancy.
- Counts are optional and only support a specific interface, registration, or dependency-coverage question; never derive coding-style rules.
- Do not include scan timestamps, raw metric dumps, or irrelevant inventories.
- Never include build/test/lint commands, Git workflow, formatting or coding-style rules (including NULL/nullptr, naming, header guards, and copyright-header coverage), generic coding standards, a standalone open-questions section, build.sh as a build reference, secrets, or speculative architecture.
