# 儿童肠套叠超声影像AI辅助诊断平台

大学科研训练项目。面向医院诊疗场景，提供患者管理、超声影像上传、AI 辅助检测、结果展示与报告打印的一站式平台，辅助临床医生诊断儿童肠套叠。

## 技术栈

- **前端**: Vue 3 + Element Plus + Vite + Pinia + Axios
- **后端**: FastAPI + SQLAlchemy + SQLite + JWT
- **算法**: Python 函数接口，平台内置 Mock 实现，团队可替换为真实模型

## 快速开始

### 1. 启动后端
```bash
cd backend
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

首次启动自动创建测试账号：
- 管理员: admin / admin123
- 医生: doctor / doctor123

API 文档: http://127.0.0.1:8000/docs

### 2. 启动前端
```bash
cd frontend
npm install
npm run dev
```

打开 http://localhost:5173

### 3. 运行测试
```bash
# 后端（pytest）
cd backend
pytest tests/ -v

# 前端（单元测试 vitest）
cd frontend
npm test
```

## 功能概览

| 模块 | 说明 |
|------|------|
| 登录认证 | 医生 / 管理员分角色登录，JWT 认证 |
| 患者管理 | 录入、搜索、分页、状态与检测次数汇总、导出 CSV |
| 影像上传 | 拖拽/多选批量上传（JPG/PNG/BMP/DICOM），逐张自动检测并显示进度 |
| 去标识裁剪 | 上传时可选择**自动**（YOLO 模型去除患者信息条/参数栏/刻度条）或**手动框选**裁剪，只保留超声图像区再进模型；`POST /api/images/{id}/crop` |
| AI 检测 | 分类（阳性/阴性/质量不佳）、置信度、严重度、治疗建议、多分类概率 |
| 检测结果 | 影像 + 诊断分析对照展示，含模型名/版本/推理耗时 |
| 检测历史 | 同一患者多次检测时间线、前后对比、按分类/患者筛选、导出 CSV |
| 报告打印 | 生成带医院抬头的检查报告，可导出 PDF |
| 审计日志 | 记录操作人/时间/对象/来源 IP（仅管理员），支持筛选与导出 |
| 系统统计 | 患者统计、检测统计（阳性/阴性占比、平均置信度） |

## 生产环境配置（安全必需）

平台默认使用「开发占位密钥」，仅用于本地跑通。部署到医院内网前请设置以下环境变量：

| 环境变量 | 说明 | 默认（本地开发） |
|---------|------|----------------|
| `JWT_SECRET_KEY` | JWT 签名密钥，**生产必须设置**且用长度≥32 的随机字符串 | 开发占位密钥（会告警） |
| `ALLOWED_ORIGINS` | 允许跨域的前端源，多个用逗号分隔，**不要用 `*`** | `http://localhost:5173,http://127.0.0.1:5173` |
| `LOCAL_TIMEZONE` | 医院所在时区（用于"今日"统计边界） | `Asia/Shanghai` |
| `DATABASE_URL` | 数据库连接串 | `sqlite:///.../app.db` |
| `UPLOAD_DIR` | 影像存储目录 | 项目根目录下的 `uploads/` |

> 可用 `backend/.env.example` 作为模板，复制为 `.env` 并填上实际值（后端启动时会自动加载 `.env`）。

示例（Windows，临时设置）：
```powershell
$env:JWT_SECRET_KEY = "请换成一段至少32位的随机字符串"
$env:ALLOWED_ORIGINS = "http://your-frontend-host:port"
python -m uvicorn main:app --host 0.0.0.0 --port 8000
```

权限说明：普通医生只能编辑/删除**自己录入**的患者与自己上传的影像；管理员可管理全部数据。仅管理员可修改系统设置。

### 审计日志

平台会记录每位医护人员的操作（登录、新增/编辑/删除患者、上传/删除影像、发起检测、修改设置），含时间、操作人、来源 IP、对象和详情。管理员登录后，左侧菜单可进入「审计日志」页查看与搜索、按日期范围筛选、导出 CSV；后端接口为 `GET /api/audit` 与 `GET /api/audit/export`（仅管理员可访问）。

### 检测机制说明

- 影像上传后默认走**异步检测**（提交任务 → 前端轮询进度 → 完成后跳转结果页），避免真实模型推理阻塞请求。
- 平台同时保留同步检测接口 `POST /api/images/{id}/detect` 与异步接口 `POST /api/detection/tasks/{image_id}` + `GET /api/detection/tasks/{task_id}`。
- 检测结果会记录**模型名/版本/推理耗时**，并支持**多分类概率**展示。
- 支持**重新检测**（覆盖旧结果）：同步接口传 `force=true`，异步接口传 `force=true`。

### 数据库迁移（Alembic）

平台已内置 Alembic 用于管理数据库结构变更。新增表/字段时：
```bash
cd backend
alembic revision --autogenerate -m "描述"
alembic upgrade head
```
> 项目启动仍会通过 `create_all` + 幂等补列保证旧库可用，Alembic 供团队在结构演进时使用。

## 算法对接

算法团队需实现 `backend/algorithm/interface.py` 中定义的 `detect_intussusception` 函数。平台已经帮你处理了影像的接收、存储和结果落库，你只需要：读取 `image_path` → 推理 → 返回 `DetectionResult`。

> 对接提示：`severity`、`treatment_success_rate`、`treatment_advice` 都是可选字段，可以省略不填（平台会按分类给出默认建议），不会因为缺字段报错。只填必填项也能跑通。

```python
from pathlib import Path
from algorithm.interface import DetectionResult

def detect_intussusception(image_path: Path) -> DetectionResult:
    # 1. 加载你的模型
    # 2. 读取/预处理 image_path
    # 3. 推理
    # 4. 返回结果（可只填必填项）
    return DetectionResult(
        classification="肠套叠阳性",   # 必填: 肠套叠阳性 | 肠套叠阴性 | 图像质量不佳
        confidence=0.95,              # 必填: 0.0 ~ 1.0
        severity="中度",              # 可选: 轻度 | 中度 | 重度
        treatment_success_rate=0.86,  # 可选: 0.0 ~ 1.0
        treatment_advice="建议空气灌肠复位",  # 可选
    )
```

将实现文件放入 `backend/algorithm/` 目录即可，平台会自动调用。完整字段说明与对接注意事项见 `docs/算法接入说明.md` 与 `backend/algorithm/interface.py` 顶部注释。

## 项目结构

```
intussusception-platform/
│
├── backend/                      ← FastAPI 后端
│   ├── main.py                   ★ 应用入口：启动建表/种子数据、CORS、注册所有路由
│   ├── config.py                 ★ 配置：数据库、上传目录、JWT、时区、CORS 白名单
│   ├── database.py               数据库引擎/会话 + ensure_columns（旧库自动补列）
│   ├── models.py                 ★ 数据库表（ORM 模型）
│   ├── schemas.py                ★ 接口的请求/响应结构（Pydantic）
│   ├── auth.py                   ★ JWT 认证 + 权限控制
│   │
│   ├── routers/                  ← 【接口层】只负责收请求、返回响应、鉴权
│   │   ├── auth.py               登录 / 当前用户
│   │   ├── patients.py           患者 CRUD、统计、导出
│   │   ├── images.py             影像上传/获取/删除、同步检测
│   │   ├── detection_tasks.py    异步检测任务（提交 + 轮询）
│   │   ├── results.py            检测结果、统计、导出
│   │   ├── settings.py           系统设置（仅管理员可改）
│   │   └── audit.py              审计日志、导出
│   │
│   ├── services/                 ← 【业务层】真正的业务逻辑
│   │   ├── detection.py          检测编排（调算法 → 校验 → 落库）
│   │   ├── detection_tasks.py    异步任务管理（后台线程 + 状态）
│   │   └── audit.py              审计埋点
│   │
│   ├── algorithm/                ← 【算法层】交给算法团队的部分
│   │   ├── interface.py          ★ 算法接口定义（输入/输出契约）+ Mock 实现
│   │   └── team_model.py         算法团队的实现模板
│   │
│   ├── alembic/                  ← 数据库迁移（改表结构不丢数据）
│   │   ├── env.py
│   │   └── versions/3334f406abf7_initial_schema.py
│   │
│   ├── tests/                    ← 后端自动化测试（pytest）
│   │   ├── conftest.py           测试夹具（测试库、账号、登录头）
│   │   ├── test_auth.py / test_patients.py / test_images.py
│   │   └── test_results.py / test_settings.py / test_audit.py
│   │
│   ├── requirements.txt          Python 依赖
│   └── .env.example              环境变量模板
│
├── frontend/                     ← Vue 3 前端
│   ├── src/
│   │   ├── views/                ← 页面（一个页面对应一个路由）
│   │   │   ├── LoginView.vue             登录
│   │   │   ├── PatientListView.vue       患者管理
│   │   │   ├── PatientDetailView.vue     患者详情（影像列表 + 检测历史时间线）
│   │   │   ├── ImageUploadView.vue       影像上传（批量）
│   │   │   ├── DetectionResultView.vue   AI 检测结果
│   │   │   ├── HistoryView.vue           检测记录（筛选/导出）
│   │   │   └── AuditLogView.vue          审计日志（管理员）
│   │   │
│   │   ├── components/           ← 复用组件
│   │   │   ├── AppLayout.vue             整体框架（导航/菜单/水印）
│   │   │   ├── UploadZone.vue            上传区（多选/拖拽/预览）
│   │   │   ├── ImageViewer.vue           影像查看（DICOM 提示）
│   │   │   ├── ResultCard.vue            结果卡片（置信度/概率条）
│   │   │   └── ReportPrint.vue           打印报告 + PDF 导出
│   │   │
│   │   ├── api/                  ← 接口封装（统一走 axios 实例）
│   │   │   ├── index.js                  axios 实例 + 拦截器（token/错误处理）
│   │   │   └── auth/patients/images/results/settings/audit.js
│   │   │
│   │   ├── router/index.js       路由配置 + 登录/管理员守卫
│   │   ├── stores/               Pinia 状态（auth 登录态、settings 设置）
│   │   ├── utils/                工具（time.js 时间处理、theme.js 主题）
│   │   ├── styles/theme.css      双主题设计变量（现代 / 中世纪手稿）
│   │   ├── main.js               前端入口
│   │   └── App.vue               根组件
│   │
│   ├── public/                   静态资源（医院 logo 等）
│   ├── index.html
│   ├── vite.config.js            构建 / 开发服务器 / 代理配置
│   └── package.json
│
├── docs/                         ← 文档
│   ├── 算法接入说明.md            ★ 给算法团队的对接文档
│   ├── 平台介绍与使用说明.html    平台介绍页（图片内嵌单文件版：platform-intro.html）
│   ├── screenshots/              介绍页用的界面截图
│   └── superpowers/              最初的设计文档与实施计划
│
├── uploads/                      ← 【运行时生成】上传的超声影像
├── README.md
└── .gitignore
```

### 架构分层（后端）

```
routers/   接口层  ── 只做"收请求、返回响应、鉴权"，不写业务逻辑
    ↓
services/  业务层  ── 真正的业务编排（检测流程、任务调度、审计埋点）
    ↓
algorithm/ 算法层  ── 只负责"看图 → 给结果"，可被算法团队整体替换
```

职责分离、层与层解耦：算法层可独立开发与替换，接口层不含业务逻辑，便于分工与维护。

### 一次检测的数据流

```
UploadZone.vue（选图上传）
   → api/images.js
   → routers/images.py（收文件、格式校验）
   → services/detection.py（编排、计时）
   → algorithm/interface.py  ← ★ 算法团队在这里给出结果
   → models.py 落库
   → routers/results.py 返回
   → ResultCard.vue / ReportPrint.vue 展示
```

### 「想改什么，去哪个文件」

| 我要改… | 去这里 |
|--------|--------|
| 加一个接口 | `backend/routers/xxx.py` + 在 `main.py` 注册 |
| 加一张表 / 字段 | `backend/models.py`（+ `main.py` 的 `ensure_columns` 或 Alembic 迁移） |
| 接口的出入参 | `backend/schemas.py` |
| 权限规则 | `backend/auth.py`（`can_manage` / `get_current_admin`） |
| 换成真实 AI 模型 | `backend/algorithm/interface.py`（或 `team_model.py`） |
| 改页面 | `frontend/src/views/xxxView.vue` |
| 改接口调用 | `frontend/src/api/xxx.js` |
| 改配色 / 主题 | `frontend/src/styles/theme.css` |

### 源码目录 vs 运行时生成

- **源码（需提交/打包）**：`backend/`、`frontend/src/`、`docs/`
- **运行时生成（需备份，不进 git）**：`backend/app.db`（数据库）、`uploads/`（影像）、`*.log` / `*.err`（运行日志）
