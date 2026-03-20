/**
 * 무신사 fetch 인터셉터 - MAIN world에서 실행 (CSP 우회)
 *
 * manifest.json에서 world: "MAIN", run_at: "document_start"로 실행
 * chrome.runtime 없음 → window.postMessage로 isolated world에 전달
 */

const originalFetch = window.fetch

window.fetch = async function (...args) {
  const response = await originalFetch.apply(this, args)
  const url = typeof args[0] === "string" ? args[0] : (args[0] as Request)?.url || ""

  // 무신사 상품 상세 API 감지
  if (url.includes("/api2/hm/goods/") || url.includes("/api/goods/")) {
    try {
      const clone = response.clone()
      const data = await clone.json()
      window.postMessage(
        {
          type: "MUSINSA_API_RESPONSE",
          url: url,
          data: data,
        },
        window.location.origin,
      )
    } catch {
      /* 파싱 실패 무시 */
    }
  }

  return response
}
