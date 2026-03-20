"use client"

import Image from "next/image"
import { useState, useCallback } from "react"
import type { SourcingProduct, ProductSeo } from "@/types/sourcing"
import { getSeoData } from "@/lib/api/seo"
import { SeoPreviewModal } from "./SeoPreviewModal"

interface Props {
  products: SourcingProduct[]
}

/** 재고 상태 한국어 라벨 */
function StockStatusBadge({ status }: { status: string }) {
  const isInStock = status === "in_stock"
  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
        isInStock
          ? "bg-green-100 text-green-700"
          : "bg-red-100 text-red-700"
      }`}
    >
      {isInStock ? "재고 있음" : "품절"}
    </span>
  )
}

/** 등록 상태 한국어 라벨 */
function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    collected: { label: "수집됨", cls: "bg-blue-100 text-blue-700" },
    listed: { label: "등록됨", cls: "bg-purple-100 text-purple-700" },
    rejected: { label: "거절됨", cls: "bg-gray-100 text-gray-500" },
  }
  const style = map[status] ?? { label: status, cls: "bg-gray-100 text-gray-500" }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style.cls}`}>
      {style.label}
    </span>
  )
}

/** 수집 상품 목록 테이블 */
export function ProductsTable({ products }: Props) {
  const [seoModal, setSeoModal] = useState<{ productId: number; seo: ProductSeo } | null>(null)

  const openSeoModal = useCallback(async (productId: number) => {
    try {
      const seo = await getSeoData(productId)
      if (seo) setSeoModal({ productId, seo })
    } catch {
      console.error(`SEO 데이터 조회 실패 (productId=${productId})`)
    }
  }, [])

  if (products.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-4 py-10 text-center text-sm text-gray-400">
        수집된 상품이 없습니다.
      </div>
    )
  }

  return (
    <>
      {seoModal && (
        <SeoPreviewModal
          productId={seoModal.productId}
          seo={seoModal.seo}
          onClose={() => setSeoModal(null)}
          onSaved={() => setSeoModal(null)}
        />
      )}
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              썸네일
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              상품명
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              원가
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              재고 상태
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              등록 상태
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              수집일
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              SEO
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {products.map((product) => (
            <tr key={product.id} className="hover:bg-gray-50">
              {/* 썸네일 */}
              <td className="px-4 py-3">
                {product.thumbnail_url ? (
                  <div className="relative h-12 w-12 overflow-hidden rounded-md bg-gray-100">
                    <Image
                      src={product.thumbnail_url}
                      alt={product.name}
                      fill
                      className="object-cover"
                      sizes="48px"
                      unoptimized
                    />
                  </div>
                ) : (
                  <div className="h-12 w-12 rounded-md bg-gray-100 flex items-center justify-center text-gray-300 text-xs">
                    없음
                  </div>
                )}
              </td>
              {/* 상품명 */}
              <td className="px-4 py-3">
                <a
                  href={product.source_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="max-w-xs block truncate font-medium text-gray-900 hover:text-blue-600"
                  title={product.name}
                >
                  {product.name}
                </a>
              </td>
              {/* 원가 */}
              <td className="px-4 py-3 whitespace-nowrap text-gray-700">
                {product.original_price.toLocaleString()}원
              </td>
              {/* 재고 상태 */}
              <td className="px-4 py-3 whitespace-nowrap">
                <StockStatusBadge status={product.stock_status} />
              </td>
              {/* 등록 상태 */}
              <td className="px-4 py-3 whitespace-nowrap">
                <StatusBadge status={product.status} />
              </td>
              {/* 수집일 */}
              <td className="px-4 py-3 whitespace-nowrap text-gray-400">
                {new Date(product.created_at).toLocaleDateString("ko-KR")}
              </td>
              {/* SEO */}
              <td className="px-4 py-3 whitespace-nowrap">
                <button
                  onClick={() => void openSeoModal(product.id)}
                  className="inline-flex items-center rounded px-2 py-1 text-xs font-medium bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                >
                  SEO 보기
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
    </>
  )
}
