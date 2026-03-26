# 🚀 My AI Workspace

一個基於 Vue 3 (Vite) 與 FastAPI 構建的現代化 AI 對話工作區。支援多模型切換、多模態輸入（圖片/PDF）、自動標題生成以及 Token 消耗追蹤。

--------------------------------------------------

📂 專案結構

```
my-ai-workspace/
├── backend/             
│   ├── main.py          
│   ├── database.py      
│   ├── .env             
│   └── requirements.txt 
├── frontend/            
│   ├── src/
│   │   ├── App.vue      
│   │   └── components/  
│   └── package.json     
└── README.md            
```
--------------------------------------------------

🛠️ 環境建置與運行步驟

1. 後端 (Backend - FastAPI)
```
cd backend
python -m venv venv
source venv/Scripts/activate
# Windows:
.\venv\Scripts\Activate

pip install -r requirements.txt
```
在backend資料夾內建立 .env ，內容放入你的key：
```
GEMINI_API_KEY=你的_GEMINI_KEY
OPENAI_API_KEY=你的_OPENAI_KEY
GROQ_API_KEY=你的_GROQ_KEY
```
啟動：
```
uvicorn main:app --reload
```
--------------------------------------------------

2. 前端 (Frontend - Vue 3)
```
cd frontend
npm install
npm run dev
```
http://localhost:5173

--------------------------------------------------

✨ 核心功能

1. 自動標題生成
2. 多模態支援（圖片/PDF）
3. Token 統計
4. 對話管理（新增 / 刪除 / 編輯）

