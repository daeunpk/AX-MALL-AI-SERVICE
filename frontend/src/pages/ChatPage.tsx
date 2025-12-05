// src/pages/ChatPage.tsx

import { useEffect, useRef, useState } from "react";
import { useParams, useSearchParams, useNavigate } from "react-router-dom";
import styled from "styled-components";
import theme from "../styles/theme";
import type { ChatMessage } from "../types/chat";
import back from "../../public/icons/back-icon.svg";
import dots from "../../public/icons/dots_icon.svg";
import customer from "../../public/img/customer-profile.svg";
import store from "../../public/img/store-profile.svg";
import send from "../../public/icons/send-icon.svg";
import { H3 } from "../styles/Text";

export default function ChatPage() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [searchParams] = useSearchParams();
  const roleParam = searchParams.get("role") as "store" | "customer";
  const [role, setRole] = useState<"store" | "customer">(roleParam || "store");

  const [input, setInput] = useState("");
  const [menuOpen, setMenuOpen] = useState(false);
  const [isEnded, setIsEnded] = useState(false);

  const socketRef = useRef<WebSocket | null>(null);
  const navigate = useNavigate();

  /* ----------------------------------------------
      1) 채팅 종료 여부 localStorage에서 불러오기
  ---------------------------------------------- */
  useEffect(() => {
    const saved = localStorage.getItem("chatEnded");
    if (saved === "true") {
      setIsEnded(true);
    }
  }, []);

  /* ----------------------------------------------
      2) URL role 변경 시 화면 업데이트
  ---------------------------------------------- */
  useEffect(() => {
    if (roleParam === "store" || roleParam === "customer") {
      setRole(roleParam);
    }
  }, [roleParam]);

  /* ----------------------------------------------
      3) WebSocket 연결
  ---------------------------------------------- */
  useEffect(() => {
    const ws = new WebSocket("ws://localhost:8000/ws/chat");
    socketRef.current = ws;

    ws.onopen = () => console.log("WebSocket connected");
    ws.onmessage = (e) => setMessages((prev) => [...prev, JSON.parse(e.data)]);
    ws.onclose = () => console.log("WebSocket disconnected");

    return () => ws.close();
  }, []);

  /* ----------------------------------------------
      4) 초기 채팅 더미 데이터
  ---------------------------------------------- */
  useEffect(() => {
    setMessages([
      { type: "msg", sender: "store", text: "안녕하세요, 고객님.\n고객님께 가장 잘 맞는 제품을 안내해드릴 수 있도록 도와드리겠습니다." },
      // { type: "msg", sender: "store", text: "안녕하세요. 문의 가능합니다.\n어떤 것을 도와드릴까요?" },
      // { type: "msg", sender: "customer", text: "20대 여성에게 어울리는 향수를 찾고 싶은데, 매장에 있는 지 확인하고 싶어요." },
      // { type: "msg", sender: "store", text: "네, 요새 잘나가는 15번 라인 향수가 3개 비치되어 있어요." },
      // { type: "msg", sender: "store", text: "매장으로 방문해 주시면 시향도 도와드릴게요 ^^" },
      // { type: "msg", sender: "customer", text: "네 ~ 감사합니다.\n이따 3시쯤 찾아갈게요!" },
    ]);
  }, []);


  /* ----------------------------------------------
      5) 채팅 보내기
  ---------------------------------------------- */
  const onSend = () => {
    if (!input.trim()) return;

    const newMsg: ChatMessage = {
      type: "msg",
      sender: role,
      text: input,
    };

    setMessages((prev) => [...prev, newMsg]);

    if (socketRef.current && socketRef.current.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(newMsg));
    }

    setInput("");
  };

  /* ----------------------------------------------
      6) 채팅 종료
  ---------------------------------------------- */
  const endChat = () => {
    localStorage.setItem("chatEnded", "true");
    setIsEnded(true);
    setMenuOpen(false);
  };

  return (
    <Wrapper>
      <Header>
        <BackBtn>
            <img src={back} alt="" />
        </BackBtn>
        <H3>{role === "store" ? "최예인님" : "Dior"}</H3>
        <Menu onClick={() => setMenuOpen((prev) => !prev)}>
            <img src={dots} alt="" />
        </Menu>
        {menuOpen && (
        <MenuPopup>
            {role === "customer" && (
            <>
                <MenuItem>신고하기</MenuItem>
                <MenuItem onClick={endChat}>채팅 종료하기</MenuItem>
            </>
            )}
            {role === "store" && (
            <>
                <MenuItem>차단하기</MenuItem>
            </>
            )}
        </MenuPopup>
      )}
      </Header>
      


      <MessageContainer>
        <DateDivider>12월 02일</DateDivider>

        {messages.map((msg, i) => (
          <ChatRow key={i} isMine={msg.sender === role}>
            {/* 프로필 영역 */}
            {! (msg.sender === role) && (
              <ProfileCircle
                src={msg.sender === "customer" ? customer : store}
              />
            )}

            {/* 말풍선 */}
            <Bubble isMine={msg.sender === role}>
              {msg.text.split("\n").map((line, idx) => (
                <div key={idx}>{line}</div>
              ))}
            </Bubble>
          </ChatRow>
        ))}
      </MessageContainer>

      {/* 종료된 채팅인 경우 */}
        {isEnded ? (
        <EndBoxWrapper>
            <EndText>종료된 채팅입니다.</EndText>

            {role === "store" && (
            <ReportButton onClick={() => navigate(`/chat/report`)}>
                채팅 분석 리포트 보기
            </ReportButton>
            )}
        </EndBoxWrapper>
        ) : (
        /* 정상 입력창 */
        <InputBar>
            <Input
            placeholder="메시지를 입력하세요"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            />
            <SendBtn onClick={onSend}><img src={send} alt="" /></SendBtn>
        </InputBar>
        )}

    </Wrapper>
  );
}


/* ============ styled-components ============ */

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
  color: ${theme.colors.black};
  position: relative;
`;

const BackBtn = styled.button`
    background-color: transparent;
    padding: 0;
`;
const Menu = styled.button`
    background-color: transparent;
    padding: 0;
`;

const MessageContainer = styled.div`
  flex: 1;
  padding: 0 16px 16px 16px;
  overflow-y: auto;
`;

const DateDivider = styled.div`
  ${theme.typography.body2};
  color: ${theme.colors.gray.gray};
  text-align: center;
  margin-bottom: 20px;
`;

const ChatRow = styled.div<{ isMine: boolean }>`
  display: flex;
  align-items: flex-start;
  margin: 12px 0px;
  justify-content: ${({ isMine }) => (isMine ? "flex-end" : "flex-start")};
  gap: 8px;
`;

const ProfileCircle = styled.img`
  flex-shrink: 0;
`;

const Bubble = styled.div<{ isMine: boolean }>`
  max-width: 70%;
  padding: 12px 16px;
  border-radius: 14px;
  background: ${({ isMine }) =>
    isMine ? theme.colors.green.base : theme.colors.gray.gray6};
  ${theme.typography.body2};
  color: ${({ isMine }) =>
    isMine ? theme.colors.white : theme.colors.black};
  white-space: pre-wrap;
  line-height: 20px;
`;

const InputBar = styled.div`
  display: flex;
  padding: 8px;
  gap: 8px;
  background: ${theme.colors.white};
  box-shadow: ${theme.shadow.card};
`;

const Input = styled.input`
  flex: 1;
  padding: 12px 16px;
  background-color: ${theme.colors.white};
  border-radius: ${theme.radius.m};
  border: 1px solid ${theme.colors.gray.gray5};
  color: ${theme.colors.black};
  ${theme.typography.body2};

  /* 클릭했을 때 테두리 없애기 */
  &:focus {
    outline: none;
    border-color: ${theme.colors.gray.gray5}; /* 유지되도록 */
  }
`;

const SendBtn = styled.button`
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: ${theme.colors.green.dark};
  margin: 0 auto;
  display: flex;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 18px;
  padding: 0px;
  justify-content: center;
  align-items: center;

  & img {
    width: 28px;
    height: 28px;
  }
`;

const MenuPopup = styled.div`
  position: absolute;
  top: 65px;
  right: 16px;
  background: ${theme.colors.white};
  border-radius: ${theme.radius.l};
  box-shadow: ${theme.shadow.popup};
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 100;
  overflow: hidden;
`;

const MenuItem = styled.div`
  ${theme.typography.body1};
  color: ${theme.colors.black};
  cursor: pointer;
  padding: 12px 18px;

  &:hover {
    background: ${theme.colors.gray.gray6};
  }
`;


const EndBoxWrapper = styled.div`
  padding: 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: ${theme.colors.white};
`;

const EndText = styled.div`
  text-align: center;
  ${theme.typography.body1};
  color: ${theme.colors.gray.gray};
  border-top: 1px solid ${theme.colors.gray.gray5};
  border-bottom: 1px solid ${theme.colors.gray.gray5};
  padding: 14px 0px;
`;

const ReportButton = styled.button`
  width: 100%;
  padding: 12px 0;
  background: ${theme.colors.green.base};
  ${theme.typography.heading3};
  color: ${theme.colors.white};
  border-radius: 999px;
  border: none;
  cursor: pointer;

  &:hover {
    opacity: 0.8;
  }
`;

