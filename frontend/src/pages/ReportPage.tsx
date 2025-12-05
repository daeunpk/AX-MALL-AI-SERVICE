// src/pages/ReportPage.tsx

import { useEffect, useState, useRef } from "react";
import { useParams, useNavigate } from "react-router-dom";
import styled from "styled-components";
import theme from "../styles/theme";
import type { StrategyResult } from "../types/chat";
import { H3 } from "../styles/Text";
import back from "../../public/icons/back-icon.svg";
import dots from "../../public/icons/dots_icon.svg";

export default function ReportPage() {
  const [reportData, setReportData] = useState<any>(null);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    socketRef.current = ws;

    ws.onopen = () => {
      console.log("ReportPage WebSocket connected");
      ws.send(JSON.stringify({ type: "strategy_request" }));
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      if (data.type === "strategy_result") {
        console.log("📩 Received strategy_result:", data);

        setReportData({
          summary: data.summary,
          keyword: data.keyword,
          strategy: data.strategy,
          recommendedProducts: data.recommendedProducts,
          recommendedCoupons: data.recommendedCoupons,
          debug: data.debug
        });
      }
    };

    ws.onclose = () => console.log("ReportPage WebSocket disconnected");

    return () => ws.close();
  }, []);

  // -----------------------------
  // 로딩 화면
  // -----------------------------
  if (!reportData) {
    return (
      <Wrapper>
        <Content>리포트 로딩 중...</Content>
      </Wrapper>
    );
  }

  return (
    <Wrapper>
      <Header>
        <BackBtn>
          <img src={back} alt="" />
        </BackBtn>
        <H3>최예인님의 채팅 분석 리포트</H3>
        <BackBtn2 />
      </Header>

      <Content>

        {/* 핵심 키워드 */}
        <Section>
          <SectionTitle>핵심 키워드</SectionTitle>
          <KeywordWrapper>
            {reportData.keyword?.length ? (
              reportData.keyword.map((k: string, i: number) => (
                <Keyword key={i}>#{k}</Keyword>
              ))
            ) : (
              <Body>키워드 없음</Body>
            )}
          </KeywordWrapper>
        </Section>

        {/* 요약 */}
        <Section>
          <SectionTitle>대화 전체 요약</SectionTitle>
          <Body>{reportData.summary}</Body>
        </Section>

        {/* 마케팅 전략 */}
        <Section>
          <SectionTitle>고객 맞춤 마케팅 전략</SectionTitle>
          {reportData.strategy?.length ? (
            reportData.strategy.map((s: string, i: number) => (
              <Body key={i}>{s}</Body>
            ))
          ) : (
            <Body>전략 없음</Body>
          )}
        </Section>

        {/* 추천 상품 */}
        <Section>
          <SectionTitle>추천 상품</SectionTitle>
          {reportData.recommendedProducts?.length ? (
            reportData.recommendedProducts.map((p: any, i: number) => (
              <Body key={i}>
                {p.name} / {p.price.toLocaleString()}원  
                <br />
                {p.notes}
              </Body>
            ))
          ) : (
            <Body>추천 상품 없음</Body>
          )}
        </Section>

        {/* 추천 쿠폰 */}
        <Section>
          <SectionTitle>추천 쿠폰</SectionTitle>
          {reportData.recommendedCoupons?.length ? (
            reportData.recommendedCoupons.map((c: any, i: number) => (
              <Body key={i}>
                {c.title}  
                <br />
                ({c.valid})
                <br />
                {c.detail}
              </Body>
            ))
          ) : (
            <Body>추천 쿠폰 없음</Body>
          )}
        </Section>

      </Content>
    </Wrapper>
  );
}

/* ========= styled-components ========== */

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 390px;
  background: ${theme.colors.white};
`;

const Header = styled.div`
  height: 70px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: ${theme.colors.black}
`;

const BackBtn = styled.button`
    background-color: transparent;
    padding: 0;
`;
const BackBtn2 = styled.div`
    background-color: transparent;
    padding: 0;
`;

const Content = styled.div`
  padding: 20px 16px;
  overflow-y: auto;
`;

const Section = styled.div`
  margin-bottom: 24px;
`;

const SectionTitle = styled.div`
  ${theme.typography.body1};
  font-weight: 600;
  margin-bottom: 10px;
  color: ${theme.colors.black};
`;

const Body = styled.div`
  ${theme.typography.body2};
  color: #333333;
  background-color: ${theme.colors.gray.gray6};
  padding: 12px 16px;
  border-radius: ${theme.radius.m};
  margin-bottom: 12px;
`;

const KeywordWrapper = styled.div`
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
`;

const Keyword = styled.div`
  padding: 4px 12px;
  background: ${theme.colors.green.base};
  border-radius: 30px;
  ${theme.typography.body2};
  font-weight: 600;
  color: ${theme.colors.white};
`;
