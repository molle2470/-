import { API_BASE_URL } from "../shared/constants"
import type { ExtensionCommand, ProductData } from "../shared/types"

/** chrome.storage.local에서 API 키 읽기 */
async function getApiKey(): Promise<string> {
  const result = await chrome.storage.local.get("apiKey")
  return result.apiKey || ""
}

/** 공통 헤더 */
async function getHeaders(): Promise<HeadersInit> {
  const apiKey = await getApiKey()
  return {
    "Content-Type": "application/json",
    "X-Extension-Key": apiKey,
  }
}

/** 대기 중인 명령 조회 */
export async function fetchPendingCommands(): Promise<ExtensionCommand[]> {
  try {
    const headers = await getHeaders()
    const res = await fetch(`${API_BASE_URL}/extension/commands`, { headers })
    if (!res.ok) return []
    return res.json()
  } catch {
    return []
  }
}

/** 명령 처리 완료 보고 */
export async function ackCommand(
  commandId: number,
  status: "done" | "failed" = "done",
): Promise<void> {
  try {
    const headers = await getHeaders()
    await fetch(`${API_BASE_URL}/extension/commands/${commandId}/ack`, {
      method: "POST",
      headers,
      body: JSON.stringify({ status }),
    })
  } catch {
    // 네트워크 오류 시 무시 (재시도 없음)
  }
}

/** 수집 상품 전송 */
export async function sendCollectedProduct(
  source: string,
  product: ProductData,
): Promise<{ product_id: number; warning?: string } | null> {
  try {
    const headers = await getHeaders()
    const res = await fetch(`${API_BASE_URL}/extension/products`, {
      method: "POST",
      headers,
      body: JSON.stringify({ source, product }),
    })
    if (!res.ok) return null
    return res.json()
  } catch {
    return null
  }
}

/** 모니터링 변동 전송 */
export async function sendProductChange(
  productId: number,
  changeType: string,
  oldPrice: number | null,
  newPrice: number | null,
  stockStatus: string | null,
): Promise<void> {
  try {
    const headers = await getHeaders()
    await fetch(`${API_BASE_URL}/extension/products/${productId}/changes`, {
      method: "POST",
      headers,
      body: JSON.stringify({
        change_type: changeType,
        old_price: oldPrice,
        new_price: newPrice,
        stock_status: stockStatus,
      }),
    })
  } catch {
    // 네트워크 오류 시 무시
  }
}

/** Heartbeat 전송 */
export async function sendHeartbeat(monitoringCount: number): Promise<void> {
  const headers = await getHeaders()
  await fetch(`${API_BASE_URL}/extension/heartbeat`, {
    method: "POST",
    headers,
    body: JSON.stringify({
      monitoring_count: monitoringCount,
      extension_version: "1.0.0",
    }),
  }).catch(() => {
    // 서버 다운 시 무시
  })
}

/** product_id로 SEO 데이터 조회 */
export async function fetchProductSeo(productId: number): Promise<Record<string, unknown> | null> {
  try {
    const headers = await getHeaders()
    const res = await fetch(`${API_BASE_URL}/products/${productId}/seo`, {
      headers,
    })
    if (!res.ok) return null
    return res.json() as Promise<Record<string, unknown>>
  } catch {
    return null
  }
}
