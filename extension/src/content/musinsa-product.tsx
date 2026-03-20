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
function parseFromNextData(): ProductData | null {
  try {
    // Content Script는 isolated world라 window.__NEXT_DATA__ 접근 불가
    // HTML에 삽입된 <script id="__NEXT_DATA__"> 태그에서 직접 읽음
    const el = document.getElementById("__NEXT_DATA__")
    if (!el) return null
    const nextData = JSON.parse(el.textContent || "")
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const data = (nextData as any)?.props?.pageProps?.meta?.data
    if (!data || !data.goodsNo) return null

    // 상품명 + 품번(styleNo) 조합 — styleNo가 이미 포함된 경우 중복 방지
    const goodsNm = String(data.goodsNm || "")
    const styleNo = String(data.styleNo || "")
    const productName = styleNo && !goodsNm.includes(styleNo)
      ? `${goodsNm} / ${styleNo}`
      : goodsNm

    const priceObj = data.normalPrice as Record<string, number> | number | undefined
    const price = typeof priceObj === "object" && priceObj !== null
      ? (priceObj.normalPrice ?? priceObj.salePrice ?? 0)
      : Number(priceObj ?? 0)

    const imgBase = "https://image.msscdn.net"

    // 무신사 __NEXT_DATA__ 구조에서 카테고리 추출
    const sourceCategory = String(
      data.categoryInfo?.categoryName
      || data.category?.categoryName
      || data.goodsCategory?.categoryName
      || ""
    ) || null

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

// __NEXT_DATA__ 직접 파싱 시도 (/products/ 페이지)
const nextDataProduct = parseFromNextData()
if (nextDataProduct) {
  capturedProductData = nextDataProduct
  updateButtonState("ready")
}
