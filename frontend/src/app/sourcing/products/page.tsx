import { ProductsTable } from "@/components/sourcing/ProductsTable"
import type { SourcingProduct } from "@/types/sourcing"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_ENV === "development"
    ? (process.env.NEXT_PUBLIC_API_URL_DEV ?? "http://localhost:28080")
    : (process.env.NEXT_PUBLIC_API_URL_PROD ?? "http://localhost:28080")

/** 서버에서 수집 상품 목록 조회 */
async function fetchProducts(): Promise<SourcingProduct[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/products?limit=50&skip=0`, {
      cache: "no-store",
    })
    if (!res.ok) return []
    return (await res.json()) as SourcingProduct[]
  } catch {
    return []
  }
}

/** 수집 상품 목록 페이지 */
export default async function ProductsPage() {
  const products = await fetchProducts()

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">수집 상품</h1>
        <span className="text-sm text-gray-400">총 {products.length.toLocaleString()}개</span>
      </div>
      <ProductsTable products={products} />
    </div>
  )
}
