import type { ProductSeo, SeoUpdateForm } from "@/types/sourcing"

const BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:28080"

/** 상품 SEO 데이터 조회 */
export async function getSeoData(
  productId: number,
  marketType = "naver"
): Promise<ProductSeo | null> {
  const res = await fetch(
    `${BASE_URL}/api/v1/products/${productId}/seo?market_type=${marketType}`,
    { cache: "no-store" }
  )
  if (res.status === 404) return null
  if (!res.ok) throw new Error(`SEO 조회 실패: ${res.status}`)
  return res.json() as Promise<ProductSeo>
}

/** 상품 SEO 데이터 수정 */
export async function updateSeoData(
  productId: number,
  data: SeoUpdateForm,
  marketType = "naver"
): Promise<void> {
  const res = await fetch(
    `${BASE_URL}/api/v1/products/${productId}/seo?market_type=${marketType}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    }
  )
  if (!res.ok) throw new Error(`SEO 수정 실패: ${res.status}`)
}
