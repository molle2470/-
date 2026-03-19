/**
 * 무신사 상품 상세 페이지에 [수집하기] 버튼을 삽입합니다.
 *
 * manifest.json에서 run_at: "document_idle"로 실행 (DOM 준비 후)
 *
 * 데이터 흐름:
 * 1. interceptor가 API 응답 캡처 → Background SW로 전송
 * 2. Background SW가 chrome.tabs.sendMessage()로 이 스크립트에 PRODUCT_DATA_READY 전달
 * 3. 사용자가 [수집하기] 클릭 → COLLECT_BUTTON_CLICKED → Background SW → 백엔드
 */

import type { ProductData, BackgroundMessage } from "../shared/types"

// 캡처된 상품 데이터 (Background SW에서 수신)
let capturedProductData: ProductData | null = null

// Background SW에서 PRODUCT_DATA_READY 수신 (tabs.sendMessage로 전달됨)
chrome.runtime.onMessage.addListener((message: BackgroundMessage, _sender, sendResponse) => {
  if (message.type === "PRODUCT_DATA_READY") {
    capturedProductData = message.data
    updateButtonState("ready")
    sendResponse({ success: true })
  }
})

/** 버튼 상태별 UI 업데이트 */
type ButtonState = "loading" | "ready" | "collecting" | "done" | "error"

function updateButtonState(state: ButtonState): void {
  const button = document.getElementById("sourcing-collect-btn") as HTMLButtonElement | null
  if (!button) return

  switch (state) {
    case "loading":
      button.textContent = "데이터 로딩중..."
      button.disabled = true
      button.style.background = "#6b7280"
      break
    case "ready":
      button.textContent = "수집하기"
      button.disabled = false
      button.style.background = "#2563eb"
      break
    case "collecting":
      button.textContent = "수집 중..."
      button.disabled = true
      button.style.background = "#f59e0b"
      break
    case "done":
      button.textContent = "수집 완료"
      button.disabled = true
      button.style.background = "#10b981"
      break
    case "error":
      button.textContent = "수집 실패"
      button.disabled = false
      button.style.background = "#ef4444"
      break
  }
}

/** [수집하기] 버튼 클릭 핸들러 */
async function handleCollectClick(): Promise<void> {
  if (!capturedProductData) return

  updateButtonState("collecting")

  try {
    const response = await chrome.runtime.sendMessage({
      type: "COLLECT_BUTTON_CLICKED",
      data: capturedProductData,
    })

    if (response?.success) {
      updateButtonState("done")
      // 브랜드 지재권 경고 표시
      if (response.warning) {
        console.warn(`[소싱 어시스턴트] ${response.warning}`)
      }
    } else {
      updateButtonState("error")
    }
  } catch {
    updateButtonState("error")
  }
}

/** 수집 버튼 생성 및 페이지에 삽입 */
function createCollectButton(): HTMLButtonElement {
  const button = document.createElement("button")
  button.id = "sourcing-collect-btn"
  button.textContent = "데이터 로딩중..."
  button.disabled = true
  button.style.cssText = `
    position: fixed;
    bottom: 20px;
    right: 20px;
    z-index: 99999;
    padding: 12px 24px;
    background: #6b7280;
    color: white;
    border: none;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 600;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transition: all 0.2s;
  `

  button.addEventListener("click", () => {
    void handleCollectClick()
  })

  document.body.appendChild(button)
  return button
}

// 페이지 로드 시 버튼 삽입 (document_idle이므로 DOM 준비됨)
createCollectButton()
