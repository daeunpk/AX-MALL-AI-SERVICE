# server.py

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import uvicorn
from datetime import datetime, timedelta
import random

from connection_manager import ConnectionManager
from chat_history import ChatHistory

# ------------------------------
# 조작 데이터 생성용 샘플 데이터
# ------------------------------
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


# -----------------------------------------
# ✔ 임시 AI 마케팅 전략 생성기 (나중 AI로 교체)
# -----------------------------------------
def generate_marketing_strategy(payload: dict) -> dict:
    recent = payload["chatMessages"]

    if len(recent) > 0:
        last_utterances = " / ".join([m["text"] for m in recent[-3:]])
    else:
        last_utterances = "(고객 발화 없음)"

    return {
        "summary": "고객은 패션/잡화 카테고리에 관심이 높음으로 판단됩니다.",
        "recommendedCoupons": [
            {"name": "가방 10% 할인 쿠폰", "validUntil": "2025-12-31"},
            {"name": "패션 잡화 5% 적립 혜택", "validUntil": "2025-12-15"},
        ],
        "recommendedProducts": [
            {"category": "가방", "zone": "가방/잡화", "floor": 2},
            {"category": "신발", "zone": "남성 의류", "floor": 3},
        ],
        "nextAction": "직원에게 푸시 알림: 고객에게 가방 프로모션 소개 필요",
        "debugRecentUtterances": last_utterances
    }


# -------------------------
# FastAPI WebSocket 서버
# -------------------------
app = FastAPI()
manager = ConnectionManager()
history = ChatHistory()


@app.websocket("/ws/chat")
async def chat_socket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")

            # 1) 채팅 메시지 처리
            if msg_type == "msg":
                text = data.get("text", "")
                sender = data.get("sender", "customer")  # 기본 sender
                history.add_message(sender, text)

                # 전체 브로드캐스트 (가게 ↔ 고객 실시간 대화)
                await manager.broadcast({
                    "type": "msg",
                    "sender": sender,
                    "text": text
                })

            # 2) 마케팅 전략 요청 처리
            elif msg_type == "strategy_request":
                customer_id = data.get("customerId", "unknown")

                customer_msgs = history.get_customer_messages()
                now = datetime.now()

                payload = {
                    "customerId": customer_id,
                    "chatMessages": customer_msgs,
                    "movementPath": generate_fake_movement(now),
                    "purchasedItems": generate_fake_purchases(now)
                }

                strategy = generate_marketing_strategy(payload)

                await manager.send_to(websocket, {
                    "type": "strategy_result",
                    "customerId": customer_id,
                    "payloadUsed": payload,   # 디버깅용
                    "strategy": strategy
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("클라이언트 연결 해제")


if __name__ == "__main__":
    print("🚀 WebSocket Server on ws://localhost:8000/ws/chat")
    uvicorn.run(app, host="0.0.0.0", port=8000)
