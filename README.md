# 儿童肠套叠超声影像AI辅助诊断平台

大学科研项目。平台提供超声影像上传和AI检测功能，辅助临床医生诊断儿童肠套叠。

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
cd backend
pytest tests/ -v
```

## 算法对接

算法团队需实现 `backend/algorithm/interface.py` 中定义的接口：

```python
from pathlib import Path
from algorithm.interface import DetectionResult

def detect_intussusception(image_path: Path) -> DetectionResult:
    return DetectionResult(
        classification="肠套叠阳性",
        confidence=0.95,
        treatment_advice="建议空气灌肠复位"
    )
```

将实现文件放入 `backend/algorithm/` 目录，修改 `backend/services/detection.py` 的 import 即可。

## 项目结构
```
├── backend/          # FastAPI 后端
│   ├── routers/      # API 路由
│   ├── services/     # 业务逻辑
│   ├── algorithm/    # 算法接口+Mock
│   └── tests/        # pytest 测试
├── frontend/         # Vue 3 前端
│   └── src/
│       ├── views/    # 页面组件
│       ├── components/ # 通用组件
│       ├── api/      # API 调用封装
│       ├── router/   # 路由配置
│       └── stores/   # Pinia 状态
└── uploads/          # 影像存储
```
