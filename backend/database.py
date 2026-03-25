# 後端路徑：database.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime

# 指定 SQLite 資料庫檔案名稱 (會自動建立在專案根目錄)
SQLALCHEMY_DATABASE_URL = "sqlite:///./chat_history.db"

# 建立資料庫引擎 (check_same_thread=False 是 SQLite 在 FastAPI 中必須的設定)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 建立 Session 類別，用來與資料庫進行對話
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 建立 Base 類別，我們的資料表都會繼承它
Base = declarative_base()

# ==========================================
# 資料表定義 (Models)
# ==========================================

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, index=True) # 我們後續會用 UUID 作為 ID
    title = Column(String, default="新對話")
    created_at = Column(DateTime, default=datetime.utcnow)

    # 建立關聯：一個對話可以有多條訊息
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String, ForeignKey("conversations.id"))
    role = Column(String) # 'user', 'assistant', 'system'
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    prompt_tokens = Column(Integer, default=0)       # 提問消耗的 Token
    completion_tokens = Column(Integer, default=0)   # 回答消耗的 Token
    total_tokens = Column(Integer, default=0)        # 總共消耗的 Token
    cost = Column(Float, default=0.0)                # 預估成本 (美金 USD)

    # 建立關聯：這條訊息屬於哪個對話
    conversation = relationship("Conversation", back_populates="messages")

class PromptTemplate(Base):
    __tablename__ = "prompt_templates"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)      # 模板標題 (例如: "繁體中文工程師")
    content = Column(Text)                  # 模板內容 (用 Text 比較好，因為提示詞可能會很長)
    created_at = Column(DateTime, default=datetime.utcnow) # 順便加上建立時間，保持一致性

# ==========================================
# 初始化資料庫函數
# ==========================================
def init_db():
    # 建立所有定義好的資料表
    Base.metadata.create_all(bind=engine)

# 取得資料庫連線的 Dependency (供 FastAPI API 使用)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()