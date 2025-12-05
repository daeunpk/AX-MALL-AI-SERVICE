# backend/server.py
import datetime
import sys, os, random
from datetime import datetime, timedelta

# backend 디렉토리 절대경로
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))    
ROOT_DIR = os.path.dirname(BACKEND_DIR)

sys.path.append(BACKEND_DIR)
sys.path.append(ROOT_DIR)

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from dotenv import load_dotenv
from ai.ai_summarizer import AISummarizer
from ws_connection_manager import ConnectionManager
from chat_history import ChatHistory


# ----------------------------
#  AI 초기화 + DEBUG LOG
# ----------------------------
print("⚙️ Initializing AI Summarizer...")

load_dotenv(os.path.join(ROOT_DIR, "ai", ".env"))

ai = AISummarizer(
    model="gemini-2.5-flash",
    api_key=os.getenv("GEMINI_API_KEY"),
    vertexai=False
)


print("✅ AI Initialized.\n")


# ----------------------------
#  더미 Zone/상품 데이터
# ----------------------------
ZONES = [
    {"zone": "정문", "floor": 1},
    {"zone": "화장품", "floor": 1},
    {"zone": "여성 의류", "floor": 2},
    {"zone": "남성 의류", "floor": 3},
    {"zone": "가방/잡화", "floor": 2},
    {"zone": "푸드코트", "floor": 4},
]

ITEM_TEMPLATES = [
    {"category": "가방", "brand": "브랜드A", "price": (80000, 200000)},
    {"category": "신발", "brand": "브랜드B", "price": (60000, 150000)},
    {"category": "코트", "brand": "브랜드C", "price": (100000, 400000)},
    {"category": "양말", "brand": "브랜드D", "price": (3000, 8000)},
]


def generate_fake_movement(start_time: datetime, steps: int = 4):
    path = []
    current = start_time

    for _ in range(steps):
        zone = random.choice(ZONES)
        path.append({
            "time": current.strftime("%H:%M"),
            "zone": zone["zone"],
            "floor": zone["floor"]
        })
        current += timedelta(minutes=random.randint(3, 10))

    return path


def generate_fake_purchases(start_time: datetime, count: int = 2):
    purchases = []
    current = start_time + timedelta(minutes=15)

    for _ in range(count):
        tpl = random.choice(ITEM_TEMPLATES)
        price = random.randint(*tpl["price"])
        purchases.append({
            "time": current.strftime("%H:%M"),
            "category": tpl["category"],
            "brand": tpl["brand"],
            "price": price
        })
        current += timedelta(minutes=random.randint(5, 15))

    return purchases


# ----------------------------
#  FastAPI + WebSocket
# ----------------------------
app = FastAPI()
manager = ConnectionManager()
history = ChatHistory()


@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    await manager.connect(websocket)
    print("🟢 WebSocket Connected:", websocket.client)

    try:
        while True:
            data = await websocket.receive_json()
            print("\n📩 [RECEIVED]", data)

            msg_type = data.get("type")

            # ------------------------------------------------
            # 1) 실시간 채팅 메시지 전달
            # ------------------------------------------------
            if msg_type == "msg":
                text = data.get("text", "")
                sender = data.get("sender", "customer")

                print(f"💬 Chat message from {sender}: {text}")
                history.add_message(sender, text)

                await manager.broadcast({
                    "type": "msg",
                    "sender": sender,
                    "text": text
                }, exclude=websocket)

            # ------------------------------------------------
            # 2) 마케팅 전략 요청 처리
            # ------------------------------------------------
            elif msg_type in ["strategy_request", "request_report"]:
                print("📊 Strategy request received!")
                customer_id = data.get("customerId", "unknown")

                # 고객 발화만 AI로 전달
                customer_msgs = history.get_customer_messages()
                print("🧾 Chat history for AI:", customer_msgs)

                ai_messages = [
                    {
                        "role": "user" if m["sender"] == "customer" else "agent",
                        "text": m["text"]
                    }
                    for m in customer_msgs
                ]

                print("🧠 Sending to AI:", ai_messages)

                # 🔥 AI 호출
                ai_report = ai.summarize_conversation(ai_messages)
                print("🤖 AI result:", ai_report)

                # -------------------------------
                #  AI가 준 키워드 구조 변환
                # -------------------------------
                # ai_report["keywords"] = {
                #   "estimated_age": "...",
                #   "interested_products": [...],
                #   "purchase_purpose": "...",
                #   "preferred_categories": [...],
                #   "budget": "..."
                # }

                keywords_obj = ai_report.get("keywords", {})
                keyword_list = []

                # 키워드를 프론트에서 원하는 “문자 배열”로 변환
                if isinstance(keywords_obj, dict):
                    if keywords_obj.get("estimated_age"):
                        keyword_list.append(keywords_obj["estimated_age"])
                    if keywords_obj.get("purchase_purpose"):
                        keyword_list.append(keywords_obj["purchase_purpose"])
                    if keywords_obj.get("budget"):
                        keyword_list.append(keywords_obj["budget"])

                    # 리스트 타입은 그대로 확장
                    for arr_name in ["interested_products", "preferred_categories"]:
                        arr = keywords_obj.get(arr_name, [])
                        if isinstance(arr, list):
                            keyword_list.extend(arr)

                print("🔍 Converted keyword list:", keyword_list)

                # ---------------------------
                #  더미 추천상품
                # ---------------------------
                recommended_products = [
                    {
                        "name": "Miss Dior Blooming Bouquet",
                        "price": 165000,
                        "category": "향수",
                        "notes": "산뜻한 플로럴 계열, 20~30대 여성 인기 라인"
                    },
                    {
                        "name": "J’adore Eau de Parfum",
                        "price": 198000,
                        "category": "향수",
                        "notes": "럭셔리 플로럴 부케, 선물용 추천"
                    },
                    {
                        "name": "Dior Addict Lip Glow",
                        "price": 49000,
                        "category": "메이크업",
                        "notes": "향수와 함께 구성 가능한 베스트셀러 리빙 코랄 틴트"
                    }
                ]


                # ---------------------------
                #  더미 쿠폰
                # ---------------------------
                recommended_coupons = [
                    {
                        "title": "Dior Beauty 시향 키트 증정 쿠폰",
                        "valid": "2025-12-31",
                        "detail": "매장 방문 시 Miss Dior · J’adore 시향 키트 제공"
                    },
                    {
                        "title": "향수 구매 고객 한정 기프트 패키지 제공",
                        "valid": "2025-12-31",
                        "detail": "향수 구매 시 디올 익스클루시브 패키지로 포장"
                    }
                ]


                # ---------------------------
                #  최종 전달 JSON
                # ---------------------------
                response = {
                    "type": "strategy_result",
                    "customerId": customer_id,

                    # 프론트에서 그대로 표시하는 필드
                    "summary": ai_report.get("summary", ""),
                    "keyword": keyword_list,   # ← 프론트 요구에 맞춰 배열로 전달
                    "strategy": ai_report.get("marketing_strategy", []),

                    # 추천 데이터
                    "recommendedProducts": recommended_products,
                    "recommendedCoupons": recommended_coupons,

                    # 디버깅용도
                    "debug": ai_report.get("debugRecentUtterances", "")
                }

                print("📤 Sending strategy_result → Front:", response)
                await manager.send_to(websocket, response)


    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("🔴 WebSocket Disconnected:", websocket.client)


if __name__ == "__main__":
    print("🚀 WebSocket Server running at ws://localhost:8000/ws/chat")
    uvicorn.run(app, host="0.0.0.0", port=8000)
