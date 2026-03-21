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

// 캡처된 상품 데이터
let capturedProductData: ProductData | null = null

// __NEXT_DATA__에서 상품 데이터 직접 파싱 (무신사 /products/ 페이지)
function parseFromNextData(): ProductData | null | "not_logged_in" {
  try {
    const el = document.getElementById("__NEXT_DATA__")
    if (!el) return null
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const nextData = JSON.parse(el.textContent || "") as any
    const pageProps = nextData?.props?.pageProps

    // 로그인 여부 확인 — 비로그인 시 수집 차단 (정상가로 수집되는 문제 방지)
    if (!pageProps?.shared?.loggedIn) return "not_logged_in"

    const data = pageProps?.meta?.data
    if (!data || !data.goodsNo) return null

    // 상품명 + 품번(styleNo) 조합 — styleNo가 이미 포함된 경우 중복 방지
    const goodsNm = String(data.goodsNm || "")
    const styleNo = String(data.styleNo || "")
    const productName = styleNo && !goodsNm.includes(styleNo)
      ? `${goodsNm} / ${styleNo}`
      : goodsNm

    // 실구매가 = salePrice × (1 - memberDiscountRate / 100) — 등급 할인 항상 적용 가능
    const goodsPriceObj = data.goodsPrice as Record<string, number> | undefined
    const salePrice = typeof goodsPriceObj === "object" && goodsPriceObj !== null
      ? (goodsPriceObj.salePrice ?? goodsPriceObj.normalPrice ?? 0)
      : Number(data.normalPrice ?? 0)
    const memberDiscountRate = typeof goodsPriceObj === "object" && goodsPriceObj !== null
      ? Number(goodsPriceObj.memberDiscountRate ?? 0)
      : 0
    const price = Math.round(salePrice * (1 - memberDiscountRate / 100))

    const imgBase = "https://image.msscdn.net"

    // 무신사 카테고리 추출
    // - 왜 baseCategoryFullPath?: 실제 API 응답 확인 결과 이 필드가
    //   "Shoes > 스니커즈 > 패션스니커즈화" 형태로 전체 경로를 문자열로 줌.
    //   백엔드 키워드 매핑("스니커즈" in source_category)과 바로 호환됨.
    const sourceCategory = String(data.baseCategoryFullPath || "") || null

    return {
      name: productName,
      original_price: price,
      source_url: `https://www.musinsa.com/products/${data.goodsNo}`,
      source_product_id: String(data.goodsNo),
      brand_name: String(data.brandInfo?.brandName || data.brand || ""),
      stock_status: data.isSoldOut ? "out_of_stock" : "in_stock",
      grade_discount_available: true,
      point_usable: true,
      point_earnable: true,
      thumbnail_url: data.thumbnailImageUrl ? `${imgBase}${data.thumbnailImageUrl}` : null,
      image_urls: Array.isArray(data.goodsImages)
        ? data.goodsImages.map((img: { imageUrl: string }) => `${imgBase}${img.imageUrl}`)
        : [],
      options: [],
      source_category: sourceCategory,
    }
  } catch {
    return null
  }
}

// Background SW에서 PRODUCT_DATA_READY 수신 (구형 /app/goods/ 페이지 fallback)
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
      button.textContent = "무신사 로그인 필요"
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

// __NEXT_DATA__ 직접 파싱 시도 (/products/ 페이지)
const nextDataProduct = parseFromNextData()
if (nextDataProduct === "not_logged_in") {
  // 비로그인 → 버튼 비활성화 유지 (기본 "무신사 로그인 필요" 상태)
} else if (nextDataProduct) {
  capturedProductData = nextDataProduct
  updateButtonState("ready")
}
