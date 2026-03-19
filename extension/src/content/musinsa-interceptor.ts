/**
 * 무신사 페이지에 스크립트를 주입하여 fetch/XHR을 오버라이드.
 * 무신사 내부 API 응답을 가로채서 상품 데이터를 파싱합니다.
 *
 * 흐름: 주입 스크립트 → window.postMessage → Content Script → Background SW
 *
 * manifest.json에서 run_at: "document_start"로 실행 (API 호출 전 주입)
 */

import type { ProductData } from "../shared/types"

// 페이지 origin (postMessage 대상 명시적 지정용)
const pageOrigin = window.location.origin

// 페이지 컨텍스트에 주입할 스크립트 (isolated world → main world 우회)
const injectedScript = `
(function() {
  const originalFetch = window.fetch;

  window.fetch = async function(...args) {
    const response = await originalFetch.apply(this, args);
    const url = typeof args[0] === "string" ? args[0] : args[0]?.url || "";

    // 무신사 상품 상세 API 감지
    if (url.includes("/api2/hm/goods/") || url.includes("/api/goods/")) {
      try {
        const clone = response.clone();
        const data = await clone.json();
        window.postMessage({
          type: "MUSINSA_API_RESPONSE",
          url: url,
          data: data,
        }, "${pageOrigin}");
      } catch(e) { /* 파싱 실패 무시 */ }
    }

    return response;
  };
})();
`

// 페이지 컨텍스트에 스크립트 주입 (MV3 content script는 isolated world이므로 script 태그 주입 필요)
const script = document.createElement("script")
script.textContent = injectedScript
document.documentElement.appendChild(script)
script.remove()

// 주입된 스크립트에서 보내는 메시지 수신
window.addEventListener("message", (event) => {
  if (event.source !== window) return
  if (event.origin !== pageOrigin) return
  if (event.data?.type !== "MUSINSA_API_RESPONSE") return

  const { data } = event.data

  // 무신사 API 응답에서 ProductData 파싱
  const productData = parseMusinsaProduct(data)
  if (productData) {
    // Background SW로 전달 (Background가 다시 product script에 PRODUCT_DATA_READY 전달)
    chrome.runtime.sendMessage({
      type: "PRODUCT_DATA_CAPTURED",
      data: productData,
    }).catch(() => {
      // Background SW 비활성 시 무시
    })
  }
})

/** 무신사 API 응답 → ProductData 파싱 */
function parseMusinsaProduct(apiData: Record<string, unknown>): ProductData | null {
  try {
    // 무신사 API 응답 구조에 맞게 파싱 (실제 API 분석 후 조정 필요)
    const data = apiData.data as Record<string, unknown> | undefined
    if (!data) return null

    const goodsNo = data.goodsNo || data.goodsNumber
    if (!goodsNo) return null

    const benefitInfo = (data.benefitInfo || {}) as Record<string, unknown>
    const brand = (data.brand || {}) as Record<string, unknown>

    return {
      name: String(data.goodsName || data.goodsNm || ""),
      original_price: Number(data.normalPrice || data.goodsPrice || 0),
      source_url: `https://www.musinsa.com/app/goods/${goodsNo}`,
      source_product_id: String(goodsNo),
      brand_name: String(data.brandName || brand.name || ""),
      stock_status: data.isSoldOut ? "out_of_stock" : "in_stock",
      grade_discount_available: benefitInfo.gradeDiscountAvailable !== false,
      point_usable: benefitInfo.pointUsable !== false,
      point_earnable: benefitInfo.pointEarnable !== false,
      thumbnail_url: String(data.thumbnailImageUrl || data.goodsImage || "") || null,
      image_urls: Array.isArray(data.imageUrls)
        ? data.imageUrls.filter((item): item is string => typeof item === "string")
        : [],
      options: [], // Phase 2에서 옵션 파싱 추가
    }
  } catch {
    return null
  }
}
