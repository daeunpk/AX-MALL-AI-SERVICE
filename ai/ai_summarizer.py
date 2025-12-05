from typing import List, Dict, Any
import os
import json
import time
from dotenv import load_dotenv
load_dotenv()

from google.genai import Client

class AISummarizer:
    def __init__(self,
                 model: str = "gemini-2.5-flash",
                 api_key: str | None = None,
                 vertexai: bool = False,
                 max_retries: int = 2):

        if api_key:
            os.environ.setdefault("GEMINI_API_KEY", api_key)

        self.client = Client(vertexai=vertexai, api_key=os.getenv("GEMINI_API_KEY"))
        self.model = model
        self.max_retries = max_retries

    def _build_prompt(self, conversation: List[Dict[str, str]]) -> str:
        convo_text = []
        for m in conversation:
            role = m.get("role", "user")
            text = m.get("text", "").strip()
            convo_text.append(f"[{role}] {text}")

        convo_blob = "\n".join(convo_text)

        # ❗ 프롬프트는 절대 수정하지 않음 (요청대로)
        prompt = f"""
당신은 ‘백화점 애플리케이션 고객 상담 대화 분석 모델’입니다.
아래에 제공되는 고객과 상담사의 전체 대화를 기반으로, 대화 내용을 다음 3가지 항목으로 요약하십시오.
출력은 반드시 JSON 형식 ONLY로 반환해야 하며, 기타 설명·문장·코드블록(backticks), "정보없음" 등을 포함하면 안 됩니다.
만일 출력할 정보가 없다면 아예 출력을 하지 마세요. "정보 없음" 이거 절대 출력하지 마.

[필수 출력 형식]
{{
  "keywords": {{
    "estimated_age": "고객의 추정 연령대(**대 혹은 **대~**대로만 표현)",
    "interested_products": ["고객이 언급하거나 관심 보인 상품 리스트"],
    "purchase_purpose": "고객의 구매 목적(예: 선물용, 본인 사용, 행사 준비 등)",
    "preferred_categories": ["패션/뷰티/식품/명품/리빙 등 고객이 선호하는 카테고리"],
    "budget": "예산 정보가 명시되면 기입, 없으면 '정보 없음'"
  }},
  "summary": "대화 전체를 2~4문장으로 명확하고 간결하게 요약한 문장",
  "marketing_strategy": [
    "고객의 연령대·관심상품·구매목적·선호 카테고리를 기반으로 현재 고객에게 적용할 수 있는 마케팅 전략 4~6개 제안",
    "전략은 고객의 니즈와 대화 맥락을 직접적으로 반영할 것",
    "상품 추천, 관련 프로모션, 멤버십 혜택, 푸시/DM 메시지 전략 등 구체적 실무 전략 제시",
    "근거가 부족한 경우 추정 가정을 명시하고 그에 따른 전략 제안"
  ]
}}

[대화 내용]
{convo_blob}

주의사항:
- 반드시 유효한 JSON만 출력하십시오.
- 키워드는 단순 단어가 아니라 의미 있는 고객 정보 구조로 구성하십시오.
- 정보가 불명확한 항목은 ‘정보 없음’ 또는 ‘추정’을 명시하십시오.
"""
        return prompt

    def _call_model(self, prompt: str, **kwargs) -> str:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.client.models.generate_content(
                    model=self.model,
                    contents=prompt,
                    **kwargs
                )
                text = getattr(resp, "text", None)
                if text is None:
                    text = str(resp)
                return text

            except Exception:
                if attempt >= self.max_retries:
                    raise
                time.sleep(0.5 * attempt)

        raise RuntimeError("Gemini 호출 실패")

    def summarize_conversation(self, conversation: List[Dict[str, str]]) -> Dict[str, Any]:

        # 1) 프롬프트 생성
        prompt = self._build_prompt(conversation)

        # 2) Gemini 호출
        raw = self._call_model(prompt)

        # 3) JSON 파싱
        try:
            parsed = json.loads(raw)
        except:
            first = raw.find("{")
            last = raw.rfind("}")
            parsed = json.loads(raw[first:last+1])

        # ---- 🎯 server.py에 맞는 변수명으로 변환 ----
        summary = parsed.get("summary", "")

        keywords = parsed.get("keywords", {})
        marketing = parsed.get("marketing_strategy", [])

        # nextAction: AI가 만든 첫 번째 전략 사용
        next_action = marketing[0] if marketing else ""

        # debugRecentUtterances: 키워드 요약 정보 표시
        debug_text = " / ".join([
            str(keywords.get("estimated_age", "")),
            ", ".join(keywords.get("interested_products", [])),
            keywords.get("purchase_purpose", ""),
            ", ".join(keywords.get("preferred_categories", [])),
            keywords.get("budget", "")
        ])

        # server.py 출력 형식으로 최종 반환
        return {
            "summary": summary,
            "keywords": keywords,
            "marketing_strategy": marketing,
            "recommendedCoupons": [],
            "recommendedProducts": [],
            "nextAction": next_action,
            "debugRecentUtterances": debug_text
        }


# usage example
# if __name__ == "__main__":
#     example_conv = [
#         {"role": "user", "text": "30대 여성인데, 선물용으로 화장품 추천해 주세요."},
#         {"role": "agent", "text": "어떤 브랜드나 카테고리를 선호하시나요?"},
#         {"role": "user", "text": "스킨케어 브랜드 쪽으로 관심 있어요. 예산은 15만원 정도요."}
#     ]
#     s = AISummarizer(model="gemini-2.5-flash")
#     result = s.summarize_conversation(example_conv)
#     print(json.dumps(result, ensure_ascii=False, indent=2))

