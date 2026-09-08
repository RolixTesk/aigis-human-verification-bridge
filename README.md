# Aigis Human Verification Bridge

一个小型、可移植的人机在环（human-in-the-loop）参考实现：服务端解析上游 `x-rpc-aigis`
challenge，浏览器按 GT3/GT4 打开 GeeTest 组件，服务端严格验证结果结构并生成仅供原上游重试使用的
Aigis 值。

这套流程已在 HoyoPanel 的个人账号手机验证码登录中于 2026-09-08 完成人工验证。本仓库只保留通用桥接
能力和无账号模拟服务，不包含 HoyoPanel 的登录适配器、账号、Cookie、Token、设备身份、数据库或日志。

## 能做什么

- 解析字符串或对象形式的 Aigis `data`，区分 GeeTest GT3/GT4。
- 将 challenge 绑定到用途与业务上下文摘要，限量、短期、一次性地保存在内存中。
- 严格接收 GT3/GT4 浏览器结果，在服务端生成 `session_id;base64(compact-json)`。
- 提供可复制的 React 弹层：动态加载、过期、取消、焦点约束、销毁和单次成功提交。
- 提供无需真实账号的 FastAPI + mock GeeTest 演示，以及真实官方启动脚本的生产构建方式。

它不会自动操作、识别、绕过或重放 CAPTCHA，也不包含第三方打码服务。最终 Aigis 值不得返回浏览器，
只能由宿主后端交给最初返回 challenge 的上游端点。

## 快速启动模拟演示

Windows PowerShell：

```powershell
.\scripts\start_demo.ps1
```

首次运行会在本仓库创建被 Git 忽略的 Python `.venv` 和 `node_modules`，构建 mock 前端并启动
<http://127.0.0.1:8002/>。勾选授权后可分别演示 GT3、GT4；mock 组件会明确标示自己不是官方验证。

也可以手动启动：

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd ..\frontend
npm ci
npm run build:mock

cd ..\backend
.\.venv\Scripts\python.exe -m uvicorn aigis_bridge.demo:app --host 127.0.0.1 --port 8002
```

## 生产组件构建

```powershell
cd frontend
npm ci
npm run build
```

普通 `build` 使用 `frontend/public/vendor/geetest/` 中留存的官方启动脚本；`build:mock` 和开发服务器
使用明确隔离的 `vendor/mock-geetest/`。模拟 challenge 不能用于官方组件，真实集成必须把上游返回的公开
challenge 字段交给 React 组件，并把验证结果提交回自己的后端。

完整接入顺序和代码边界见 [docs/integration.md](docs/integration.md)。
协议研究快照与许可信息见 [REFERENCES.md](REFERENCES.md)。

## 验证

```powershell
.\scripts\verify.ps1
```

该命令运行 Python 测试、TypeScript 检查、官方脚本生产构建和 mock 构建。浏览器回归需要先用
`start_demo.ps1` 启动服务，再在另一窗口运行：

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\browser_check.py
```

## 目录

- `backend/src/aigis_bridge/protocol.py`：Aigis 解析与编码。
- `backend/src/aigis_bridge/store.py`：短期、绑定、一次性 challenge 存储。
- `backend/src/aigis_bridge/models.py`：严格 GT3/GT4 API 类型。
- `backend/src/aigis_bridge/demo.py`：不连接真实上游的模拟服务。
- `frontend/src/HumanVerificationModal.tsx`：可移植 React 弹层。
- `frontend/src/loadSdk.ts`：官方或 mock SDK 生命周期加载。
- `frontend/public/vendor/geetest/`：经哈希记录的官方启动脚本。

## 集成者必须补充的边界

- 在发起上游登录和加载组件前取得用户明确授权。
- 用现有会话认证与 CSRF 防护保护 challenge 创建、提交和取消接口。
- 将 challenge 绑定到实际操作、账号上下文和设备上下文的摘要；不要把手机号等明文作为绑定值。
- 对同一操作限制真人 challenge 轮数；上游继续挑战或返回频率限制时停止，不循环请求。
- 不记录 Aigis header、session、浏览器验证结果、账号或验证码。
- 根据实际部署观测设置 CSP，仅放行必要的 GeeTest 资源域名，不使用通配符。

## 第三方与许可

官方 GeeTest 启动脚本不属于本仓库自有源码，来源、哈希和使用边界见
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。本仓库尚未替自有示例代码选择项目级开源许可证；公开
发布或接受外部贡献前应由仓库所有者明确选择许可证。
