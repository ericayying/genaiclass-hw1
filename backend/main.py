# 檔案路徑：backend/main.py

import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from litellm import completion, acompletion
from database import init_db, get_db, SessionLocal, Conversation, Message, PromptTemplate
import uuid
from sqlalchemy.orm import Session
from typing import List, Optional
import json

# 提示詞模板的新增請求格式
class PromptCreate(BaseModel):
    title: str
    content: str

# 提示詞模板的回傳格式
class PromptResponse(BaseModel):
    id: int
    title: str
    content: str

    class Config:
        from_attributes = True  # SQLAlchemy v2 寫法 (若是 v1 則是 orm_mode = True)

# 1. 載入 .env 檔案中的環境變數
load_dotenv()

# 2. 初始化 FastAPI 應用程式
app = FastAPI()

# === 啟動時自動建立 SQLite 資料表 ===
init_db()

# 3. 設定 CORS (跨來源資源共用)
# 這非常重要！因為你的前端 (Vite) 和後端 (FastAPI) 會跑在不同的 Port，
# 沒有設定 CORS 的話，瀏覽器會阻擋前端去跟後端要資料。
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開發階段先允許所有來源
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 對話管理 API
# ==========================================

# 1. 建立新對話 (按下 "New Chat" 時呼叫)
@app.post("/api/conversations")
def create_conversation(db: Session = Depends(get_db)):
    # 產生一組獨一無二的 UUID
    new_id = str(uuid.uuid4())
    # 建立一筆對話紀錄 (預設標題先叫 "新對話")
    db_conv = Conversation(id=new_id, title="新對話")
    db.add(db_conv)
    db.commit()
    return {"id": new_id, "title": "新對話"}

# 2. 取得左側的「歷史對話列表」
@app.get("/api/conversations")
def get_conversations(db: Session = Depends(get_db)):
    # 從資料庫撈出所有對話，並依時間由新到舊排序
    convs = db.query(Conversation).order_by(Conversation.created_at.desc()).all()
    return [{"id": c.id, "title": c.title} for c in convs]

# 3. 點擊左側選單時，取得該對話的「完整聊天紀錄」
@app.get("/api/conversations/{conv_id}")
def get_conversation_history(conv_id: str, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="找不到此對話")
    
    # 撈出這則對話底下的所有訊息，依照時間由舊到新排序 (才能還原對話順序)
    messages = db.query(Message).filter(Message.conversation_id == conv_id).order_by(Message.created_at.asc()).all()
    
    return {
        "id": conv.id,
        "title": conv.title,
        "messages": [{"role": m.role, "content": m.content} for m in messages]
    }

# 4. 定義前端傳過來的資料格式
class ChatRequest(BaseModel):
    model: str              # 例如："gpt-3.5-turbo", "gemini/gemini-pro", "groq/llama3-8b-8192"
    messages: list          # 對話紀錄陣列
    temperature: float = 0.7 # 預設溫度設定
    conversation_id: str

# ==========================================
# 提示詞模板庫 (Prompt Library) API
# ==========================================

# 1. 取得所有模板
@app.get("/api/prompts", response_model=list[PromptResponse])
def get_prompts(db: Session = Depends(get_db)):
    return db.query(PromptTemplate).all()

# 2. 新增模板
@app.post("/api/prompts", response_model=PromptResponse)
def create_prompt(prompt: PromptCreate, db: Session = Depends(get_db)):
    db_prompt = PromptTemplate(title=prompt.title, content=prompt.content)
    db.add(db_prompt)
    db.commit()
    db.refresh(db_prompt)
    return db_prompt

# 3. 刪除模板
@app.delete("/api/prompts/{prompt_id}")
def delete_prompt(prompt_id: int, db: Session = Depends(get_db)):
    db_prompt = db.query(PromptTemplate).filter(PromptTemplate.id == prompt_id).first()
    if db_prompt:
        db.delete(db_prompt)
        db.commit()
        return {"message": "模板已刪除"}
    return {"error": "找不到該模板"}

# ==========================================
# 核心聊天 API (升級版：具備記憶寫入功能)
# ==========================================
@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    
    # 1. 取得使用者最新輸入的那句話，並存入資料庫
    user_msg_content = request.messages[-1]["content"]
    # 【新增防呆處理】：如果 content 是陣列 (包含圖片)，就轉成 JSON 字串存入資料庫
    if isinstance(user_msg_content, list):
        db_content = json.dumps(user_msg_content, ensure_ascii=False)
    else:
        db_content = user_msg_content

    db_user_msg = Message(
        conversation_id=request.conversation_id,
        role="user",
        content=db_content  # 使用處理過後的 db_content
    )
    db.add(db_user_msg)
    db.commit()

    # 2. 定義非同步的產生器 (Async Generator)
    async def generate():
        ai_full_response = ""
        
        try:
            # 呼叫 litellm 產生串流 (記得這裡要用 acompletion 才能非同步)
            # 注意：這裡的 acompletion 需要 import
            # from litellm import acompletion
            response = await acompletion(
                model=request.model,
                messages=request.messages,
                stream=True,
                temperature=request.temperature
            )

            # 非同步迴圈讀取串流片段
            async for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    ai_full_response += content
                    yield content
                    
        except Exception as e:
            print(f"Error during LLM generation: {e}")
            yield "\n[伺服器錯誤：無法產生回應]"
            
        finally:
            # 3. 串流結束後，把 AI 完整的回覆存進資料庫
            # 因為這是在 async generator 裡面，最好開一個獨立的 Session
            with SessionLocal() as session:
                db_ai_msg = Message(
                    conversation_id=request.conversation_id,
                    role="assistant",
                    content=ai_full_response
                )
                session.add(db_ai_msg)
                session.commit()

    # 回傳 StreamingResponse，傳入我們寫好的 async generator
    return StreamingResponse(generate(), media_type="text/event-stream")