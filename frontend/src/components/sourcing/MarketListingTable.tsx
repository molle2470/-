"use client"

import { useState } from "react"
import { deactivateListing, type MarketListing } from "@/lib/market-listings-api"

/** 등록 상태 한국어 라벨 */
const STATUS_LABEL: Record<string, string> = {
  pending: "대기",
  registered: "등록됨",
  failed: "실패",
  deactivated: "비활성",
}

/** 등록 상태별 색상 클래스 */
const STATUS_COLOR: Record<string, string> = {
  pending: "bg-yellow-100 text-yellow-800",
  registered: "bg-green-100 text-green-800",
  failed: "bg-red-100 text-red-800",
  deactivated: "bg-gray-100 text-gray-500",
}

interface Props {
  listings: MarketListing[]
  onUpdate?: () => void
}

/** 마켓 등록 현황 테이블 */
export function MarketListingTable({ listings, onUpdate }: Props) {
  const [loadingId, setLoadingId] = useState<number | null>(null)

  async function handleDeactivate(listingId: number) {
    if (!confirm("정말 비활성화하시겠습니까?")) return
    setLoadingId(listingId)
    try {
      await deactivateListing(listingId)
      onUpdate?.()
    } catch (e) {
      alert(e instanceof Error ? e.message : "오류 발생")
    } finally {
      setLoadingId(null)
    }
  }

  if (listings.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-4 py-10 text-center text-sm text-gray-400">
        등록된 상품이 없습니다.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              상품 ID
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              판매가
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              마켓 상품번호
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              상태
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              등록일
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              액션
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {listings.map((listing) => (
            <tr key={listing.id} className="hover:bg-gray-50">
              {/* 상품 ID */}
              <td className="px-4 py-3 text-gray-700">#{listing.product_id}</td>
              {/* 판매가 */}
              <td className="px-4 py-3 whitespace-nowrap font-medium text-gray-900">
                {listing.selling_price.toLocaleString()}원
              </td>
              {/* 마켓 상품번호 */}
              <td className="px-4 py-3 text-gray-500 font-mono text-xs whitespace-nowrap">
                {listing.market_product_id ?? "-"}
              </td>
              {/* 상태 배지 */}
              <td className="px-4 py-3 whitespace-nowrap">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLOR[listing.listing_status] ?? "bg-gray-100 text-gray-500"}`}
                >
                  {STATUS_LABEL[listing.listing_status] ?? listing.listing_status}
                </span>
              </td>
              {/* 등록일 */}
              <td className="px-4 py-3 whitespace-nowrap text-gray-400 text-xs">
                {listing.registered_at
                  ? new Date(listing.registered_at).toLocaleDateString("ko-KR")
                  : "-"}
              </td>
              {/* 액션 */}
              <td className="px-4 py-3 whitespace-nowrap">
                {listing.listing_status === "registered" && (
                  <button
                    onClick={() => void handleDeactivate(listing.id)}
                    disabled={loadingId === listing.id}
                    className="inline-flex items-center rounded px-2 py-1 text-xs font-medium text-red-600 hover:text-red-800 disabled:opacity-50"
                  >
                    {loadingId === listing.id ? "처리중..." : "비활성화"}
                  </button>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
