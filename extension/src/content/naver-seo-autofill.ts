/**
 * 네이버 스마트스토어 상품 등록 페이지 SEO 자동입력
 *
 * 흐름:
 * 1. 페이지 로드 시 Background SW에 준비 알림
 * 2. Background SW가 SEO_AUTOFILL 메시지 전달
 * 3. DOM 필드에 SEO 데이터 자동입력
 */

interface SeoData {
  optimized_name?: string
  tags?: string[]
  material?: string
  color?: string
  gender?: string
  age_group?: string
  origin?: string
}

/** input/textarea에 값 설정 (React 상태 업데이트 트리거 포함) */
function setInputValue(el: HTMLInputElement | HTMLTextAreaElement, value: string): void {
  const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    el.tagName === "TEXTAREA" ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype,
    "value"
  )?.set
  nativeInputValueSetter?.call(el, value)
  el.dispatchEvent(new Event("input", { bubbles: true }))
  el.dispatchEvent(new Event("change", { bubbles: true }))
}

/** SEO 데이터를 네이버 등록 폼에 자동입력 */
function autofillSeoData(seoData: SeoData): void {
  // 상품명 (id="goodsName" 또는 name="goodsName")
  const nameEl = document.querySelector<HTMLInputElement>(
    'input[id="goodsName"], input[name="goodsName"]'
  )
  if (nameEl && seoData.optimized_name) {
    setInputValue(nameEl, seoData.optimized_name)
  }

  // 태그 (textarea 또는 input)
  const tagEl = document.querySelector<HTMLTextAreaElement | HTMLInputElement>(
    'textarea[id*="tag"], input[id*="tag"], textarea[placeholder*="태그"]'
  )
  if (tagEl && seoData.tags?.length) {
    setInputValue(tagEl, seoData.tags.join(" "))
  }

  console.info("[소싱 어시스턴트] SEO 자동입력 완료:", {
    name: seoData.optimized_name,
    tags: seoData.tags,
  })
}

/** Background SW 메시지 수신 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "SEO_AUTOFILL") {
    autofillSeoData(message.seoData as SeoData)
    sendResponse({ success: true })
  }
})

// 페이지 로드 알림 (Background SW에서 상품 매칭에 활용)
chrome.runtime.sendMessage({ type: "NAVER_REGISTER_PAGE_LOADED" })
