import { ProductsTable } from "@/components/sourcing/ProductsTable"
import { serverFetchList } from "@/lib/server-fetch"
import type { SourcingProduct } from "@/types/sourcing"

/** 수집 상품 목록 페이지 */
export default async function ProductsPage() {
  const products = await serverFetchList<SourcingProduct>("/api/v1/products?limit=50&skip=0")

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
