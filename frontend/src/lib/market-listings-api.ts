/** 마켓 등록 관련 클라이언트 사이드 API 클라이언트 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:28080"

/** 마켓 등록 항목 */
export interface MarketListing {
  id: number
  product_id: number
  market_account_id: number
  selling_price: number
  listing_status: "pending" | "registered" | "failed" | "deactivated"
  market_product_id: string | null
  registered_at: string | null
  created_at: string
}

/** 마켓 등록 요청 */
export interface RegisterRequest {
  product_id: number
  market_account_id: number
  market_id: number
  common_template_id: number
  margin_rate?: number
}

/** 클라이언트 사이드 마켓 등록 (POST) */
export async function registerToMarket(req: RegisterRequest): Promise<MarketListing> {
  const res = await fetch(`${API_BASE_URL}/api/v1/market-listings`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error((err as { detail?: string }).detail ?? "마켓 등록 실패")
  }
  return res.json() as Promise<MarketListing>
}

/** 클라이언트 사이드 비활성화 (PATCH) */
export async function deactivateListing(listingId: number): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/v1/market-listings/${listingId}/deactivate`, {
    method: "PATCH",
  })
  if (!res.ok) throw new Error("비활성화 실패")
}
