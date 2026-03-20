import { MarketListingTable } from "@/components/sourcing/MarketListingTable"
import { serverFetchList } from "@/lib/server-fetch"
import type { MarketListing } from "@/lib/market-listings-api"

/** 마켓 등록 관리 페이지 */
export default async function MarketListingsPage() {
  const listings = await serverFetchList<MarketListing>("/api/v1/market-listings")

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">마켓 등록 관리</h1>
        <span className="text-sm text-gray-400">총 {listings.length.toLocaleString()}개</span>
      </div>
      <MarketListingTable listings={listings} />
    </div>
  )
}
