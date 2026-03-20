/**
 * 무신사 메시지 릴레이 - ISOLATED world에서 실행
 *
 * musinsa-fetch-interceptor.ts(MAIN world)가 보낸 postMessage를 수신해서
 * 상품 데이터를 파싱하고 Background SW로 전달합니다.
 */

import type { ProductData } from "../shared/types"

const pageOrigin = window.location.origin

window.addEventListener("message", (event) => {
  if (event.source !== window) return
  if (event.origin !== pageOrigin) return
  if (event.data?.type !== "MUSINSA_API_RESPONSE") return

  const { data } = event.data

  const productData = parseMusinsaProduct(data)
  if (productData) {
    chrome.runtime
      .sendMessage({
        type: "PRODUCT_DATA_CAPTURED",
        data: productData,
      })
      .catch(() => {
        // Background SW 비활성 시 무시
      })
  }
})

/** 무신사 API 응답 → ProductData 파싱 */
function parseMusinsaProduct(apiData: Record<string, unknown>): ProductData | null {
  try {
    const data = apiData.data as Record<string, unknown> | undefined
    if (!data) return null

    const goodsNo = data.goodsNo || data.goodsNumber
    if (!goodsNo) return null

    const benefitInfo = (data.benefitInfo || {}) as Record<string, unknown>
    const brand = (data.brand || {}) as Record<string, unknown>

    // 실제 API 응답 구조 확인용 임시 로그
    console.log("[MUSINSA] data keys:", Object.keys(data))
    console.log("[MUSINSA] price fields:", {
      normalPrice: data.normalPrice,
      goodsPrice: data.goodsPrice,
      salePrice: data.salePrice,
      price: data.price,
      finalSalePrice: data.finalSalePrice,
      goodsSalePrice: data.goodsSalePrice,
    })

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
      options: [],
    }
  } catch {
    return null
  }
}
