# 儿童肠套叠超声影像AI辅助诊断平台 — 设计文档

> 版本: v1.0 | 日期: 2026-05-14 | 状态: 设计已确认

---

## 1. 项目概述

### 1.1 项目背景

大学科研项目，搭建一个儿童肠套叠超声影像AI辅助诊断平台。平台负责人负责前后端平台搭建，算法团队负责AI检测模型。双方通过Python函数接口对接，各自独立开发。

### 1.2 目标用户

**临床医生**（儿科、急诊科），用于辅助诊断决策。

### 1.3 核心功能

| 功能 | 描述 |
|------|------|
| 患者管理 | 录入、搜索、编辑患者信息及临床症状 |
| 超声影像上传 | 上传超声图片（jpg/png/bmp/dicom），拖拽+预览 |
| AI检测 | 触发算法模型对影像进行肠套叠分类检测 |
| 结果展示 | 显示分类结果（阳性/阴性/质量不佳）、置信度百分比 |
| 治疗建议 | 基于检测结果，由算法返回治疗建议文本 |
| 检测记录 | 历史检测记录浏览，患者维度检测时间线 |

### 1.4 部署形态

- 开发/测试：笔记本电脑本地运行
- 目标部署：单家医院内网服务器

---

## 2. 技术选型

| 层 | 技术 | 版本 | 选型理由 |
|----|------|------|----------|
| 前端框架 | Vue 3 | 3.4+ | Composition API，国内生态丰富 |
| UI 组件库 | Element Plus | 2.x | 成熟稳定，适合企业/医疗场景 |
| 构建工具 | Vite | 5+ | 快速HMR，Vue官方推荐 |
| 状态管理 | Pinia | 2+ | Vue 3官方状态管理 |
| HTTP客户端 | Axios | 1.x | 拦截器统一处理鉴权/错误 |
| 后端框架 | FastAPI | 0.110+ | 异步、自动Swagger文档、Python原生 |
| ORM | SQLAlchemy | 2.0+ | Python ORM标准 |
| 数据库 | SQLite | - | 零配置，单文件，适合科研MVP |
| 文件存储 | 本地文件系统 | - | `uploads/` 目录，内网环境无需云存储 |
| 后端测试 | pytest | 8+ | Python测试标准 |

---

## 3. 系统架构

```
浏览器 (临床医生)
  |
  | HTTP REST API (JSON)
  |
┌─ FastAPI 后端 ─────────────────────────────────┐
│                                                 │
│  ┌─────────┐ ┌──────────┐ ┌───────┐ ┌────────┐│
│  │ 认证模块 │ │ 患者管理  │ │影像服务│ │检测编排││
│  │JWT Token│ │ CRUD     │ │上传/存│ │调算法  ││
│  └─────────┘ └──────────┘ └───────┘ └────────┘│
│                      │                          │
│        ┌─────────────┼─────────────┐            │
│        ▼             ▼             ▼            │
│  ┌──────────┐ ┌──────────┐ ┌────────────┐      │
│  │ 算法模块  │ │ SQLite  │ │ 文件存储   │      │
│  │team提供   │ │ 数据库   │ │ uploads/   │      │
│  └──────────┘ └──────────┘ └────────────┘      │
└─────────────────────────────────────────────────┘
```

数据流方向: `前端 ↔ HTTP ↔ 后端 ↔ import ↔ 算法模块` | `后端 ↔ SQLAlchemy ↔ SQLite`

---

## 4. 数据库模型

### 4.1 ER关系

```
users 1──N patients
patients 1──N images
images 1──1 detection_results
users 1──N images
```

### 4.2 表结构

**users** — 医生账户
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| username | VARCHAR(50) UNIQUE | 登录用户名 |
| password_hash | VARCHAR(255) | bcrypt哈希 |
| full_name | VARCHAR(100) | 医生姓名 |
| role | VARCHAR(20) | 角色(admin/doctor) |
| created_at | DATETIME | 创建时间 |

**patients** — 患者信息
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| name | VARCHAR(100) | 患者姓名 |
| gender | VARCHAR(10) | 男/女 |
| age | INTEGER | 年龄(月) |
| medical_record_no | VARCHAR(50) | 病历号 |
| clinical_symptoms | TEXT | 临床症状描述 |
| created_by | INTEGER FK→users.id | 录入医生 |
| created_at | DATETIME | 录入时间 |

**images** — 超声影像
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| patient_id | INTEGER FK→patients.id | 所属患者 |
| filename | VARCHAR(255) | 原始文件名 |
| filepath | VARCHAR(500) | 存储路径 |
| file_size | INTEGER | 文件大小(bytes) |
| uploaded_by | INTEGER FK→users.id | 上传医生 |
| uploaded_at | DATETIME | 上传时间 |

**detection_results** — 检测结果
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER PK | 自增主键 |
| image_id | INTEGER FK→images.id UNIQUE | 关联影像(一对一) |
| classification | VARCHAR(50) | 分类结果 |
| confidence | FLOAT | 置信度(0.0~1.0) |
| treatment_advice | TEXT | 治疗建议 |
| detected_by | INTEGER FK→users.id | 执行检测的医生 |
| created_at | DATETIME | 检测时间 |

---

## 5. 算法接口协议

### 5.1 接口定义 (v1.0.0)

```python
from dataclasses import dataclass
from pathlib import Path

@dataclass
class DetectionResult:
    """算法团队必须按此结构返回"""
    classification: str      # "肠套叠阳性" | "肠套叠阴性" | "图像质量不佳"
    confidence: float        # 0.0 ~ 1.0
    treatment_advice: str    # 治疗建议文本

def detect_intussusception(image_path: Path) -> DetectionResult:
    """算法团队实现此函数。输入超声图片路径，返回检测结果。"""
    ...
```

### 5.2 对接方式

- 平台方先实现一个 Mock 版本（返回固定数据），确保前后端流程跑通
- 算法团队按同一接口协议实现真实模型
- 对接时只需替换 `algorithm/` 目录下的模块，无需改其他代码

### 5.3 分类枚举

| 分类 | 含义 | 前端展示 |
|------|------|----------|
| `肠套叠阳性` | 检测到肠套叠特征 | 红色标签 + 治疗建议 |
| `肠套叠阴性` | 未检测到肠套叠特征 | 绿色标签 |
| `图像质量不佳` | 图片模糊/不满足检测条件 | 黄色警告，建议重拍 |

---

## 6. API 接口设计

### 6.1 认证

所有业务接口需在 Header 中携带 `Authorization: Bearer <token>`。

### 6.2 端点列表

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录，返回 JWT token |
| GET | `/api/users/me` | 当前登录用户信息 |
| GET | `/api/patients` | 患者列表(?search=&page=&size=) |
| POST | `/api/patients` | 新增患者 |
| GET | `/api/patients/{id}` | 患者详情+关联影像列表 |
| PUT | `/api/patients/{id}` | 更新患者信息 |
| DELETE | `/api/patients/{id}` | 删除患者 |
| POST | `/api/images/upload` | 上传超声影像(multipart, 需patient_id) |
| GET | `/api/images/{id}` | 获取影像文件(图片二进制) |
| GET | `/api/images/{id}/info` | 影像元信息 |
| DELETE | `/api/images/{id}` | 删除影像 |
| POST | `/api/images/{id}/detect` | **核心**：触发AI检测 |
| GET | `/api/results/{id}` | 检测结果详情 |
| GET | `/api/results` | 检测历史(?patient_id=) |

### 6.3 统一错误响应格式

```json
{
  "code": 401,
  "message": "登录已过期，请重新登录",
  "detail": "JWT token expired at 2024-05-01T15:30:00"
}
```

---

## 7. 项目目录结构

```
intussusception-platform/
├── backend/
│   ├── main.py              # FastAPI 入口 + CORS + 路由注册
│   ├── config.py            # 配置常量(DB路径、上传目录、JWT密钥)
│   ├── database.py          # SQLAlchemy engine + SessionLocal
│   ├── models.py            # ORM 模型定义
│   ├── schemas.py           # Pydantic 请求/响应模型
│   ├── auth.py              # JWT token 生成与验证
│   ├── routers/
│   │   ├── auth.py          # /api/auth/*
│   │   ├── patients.py      # /api/patients/*
│   │   ├── images.py         # /api/images/*
│   │   └── results.py       # /api/results/*
│   ├── services/
│   │   └── detection.py     # 检测业务逻辑(调用算法模块)
│   └── algorithm/
│       ├── __init__.py
│       ├── interface.py     # DetectionResult定义 + Mock实现
│       └── team_model.py    # 算法团队的真实模型(待对接)
├── frontend/
│   ├── src/
│   │   ├── views/           # 页面组件: Login, PatientList, PatientDetail, UploadImage, DetectionResult, HistoryRecords
│   │   ├── components/      # 通用组件: ImageViewer, ResultCard, UploadZone
│   │   ├── api/             # axios实例 + 各模块API封装
│   │   ├── router/          # Vue Router路由配置
│   │   ├── stores/          # Pinia stores: auth, patient
│   │   ├── App.vue
│   │   └── main.js
│   ├── index.html
│   ├── vite.config.js
│   └── package.json
├── uploads/                 # 超声影像存储目录
├── requirements.txt         # Python依赖
└── README.md
```

---

## 8. 前端页面路由与状态

### 8.1 路由设计

| 路径 | 页面 | 说明 |
|------|------|------|
| `/login` | 登录页 | JWT认证，token存localStorage |
| `/patients` | 患者列表 | 搜索、分页、新增患者入口 |
| `/patients/:id` | 患者详情 | 基本信息+该患者影像列表+新增检测入口 |
| `/patients/:id/upload` | 影像上传 | 拖拽/选择超声图片上传 |
| `/results/:id` | 检测结果 | 分类标签+置信度+治疗建议 |
| `/history` | 检测记录 | 按时间倒序展示检测历史 |

### 8.2 前端状态覆盖

| 状态 | 触发条件 | UI表现 |
|------|----------|--------|
| 加载中 | API请求进行中 | 骨架屏 / Spin |
| 空数据 | 列表为空 | 引导文案 + 操作入口 |
| 请求错误 | 网络异常/服务器错误 | 错误提示 + 重试按钮 |
| 检测中 | 算法推理中 | 进度动画 |
| 质量不佳 | 算法返回图片不可用 | 黄色警告 + 重传引导 |
| 表单验证 | 必填项为空/格式错 | 字段下方红色提示 |

---

## 9. 异常处理

### 9.1 后端异常映射

| 场景 | HTTP Status | 处理 |
|------|-------------|------|
| 未登录/Token过期 | 401 | 前端拦截，跳转登录页 |
| 权限不足 | 403 | 提示无权限 |
| 资源不存在 | 404 | 提示"未找到该患者/影像" |
| 文件类型不符合 | 400 | 仅允许 jpg/png/bmp/dicom |
| 文件超过20MB | 413 | 提示文件过大 |
| 算法调用失败 | 500 | 记录日志+返回"检测服务异常" |
| 数据库异常 | 500 | 记录日志+通用错误信息 |
| 算法返回"图片质量不佳" | 200 | 正常返回，前端友好提示 |

### 9.2 前端错误拦截

- Axios 响应拦截器统一处理 401（跳转登录）、500（Toast提示）
- 请求拦截器自动附加 JWT token

---

## 10. 测试策略

### 10.1 后端测试（pytest）

- API端点测试：每个接口至少覆盖正常+异常场景
- 使用 pytest fixture 创建临时SQLite数据库
- 使用 monkeypatch 替换 `detect_intussusception` 为 Mock 函数
- 测试文件与路由模块一一对应

### 10.2 前端测试（手工走查为主）

- 科研MVP阶段以手工走查为主
- 使用 FastAPI Swagger UI (`/docs`) 进行API联调
- 关键路径验证：登录→新增患者→上传影像→触发检测→查看结果

---

## 11. 开发计划概要

| 阶段 | 内容 | 预计耗时 |
|------|------|----------|
| 1. 项目初始化 | 前后端项目脚手架、依赖安装、开发环境配置 | 0.5天 |
| 2. 后端基础 | 数据库模型、认证、患者CRUD API + 测试 | 2天 |
| 3. 后端影像 | 上传/存储/获取API + 算法Mock + 检测API + 测试 | 2天 |
| 4. 前端基础 | 项目搭建、路由、登录页、患者列表页 | 1.5天 |
| 5. 前端核心 | 患者详情、影像上传、检测结果页、历史记录页 | 2.5天 |
| 6. 前后端联调 | 接口联调、错误处理、状态覆盖 | 1.5天 |
| 7. 文档验收 | README、演示数据准备、完整流程走通 | 0.5天 |
| **合计** | | **约10.5天** |
