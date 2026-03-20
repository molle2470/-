"use client"

import { useState } from "react"
import { registerToMarket } from "@/lib/market-listings-api"

const NAVER_MARKET_ACCOUNT_ID = 1
const NAVER_MARKET_ID = 1
const COMMON_TEMPLATE_ID = 2

interface Props {
  productId: number
}

/** 스마트스토어 마켓 등록 버튼 (마진율 15%/20% 선택) */
export function RegisterButton({ productId }: Props) {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)
  const [marginRate, setMarginRate] = useState<0.15 | 0.20>(0.20)

  async function handleRegister() {
    if (!confirm(`스마트스토어에 등록하시겠습니까? (마진 ${marginRate * 100}%)`)) return
    setLoading(true)
    try {
      await registerToMarket({
        product_id: productId,
        market_account_id: NAVER_MARKET_ACCOUNT_ID,
        market_id: NAVER_MARKET_ID,
        common_template_id: COMMON_TEMPLATE_ID,
        margin_rate: marginRate,
      })
      setDone(true)
    } catch (e) {
      alert(e instanceof Error ? e.message : "등록 실패")
    } finally {
      setLoading(false)
    }
  }

  if (done) {
    return <span className="inline-flex items-center text-xs font-medium text-green-600">등록완료</span>
  }

  return (
    <div className="inline-flex items-center gap-1">
      {/* 마진율 선택 */}
      <select
        value={marginRate}
        onChange={(e) => setMarginRate(Number(e.target.value) as 0.15 | 0.20)}
        disabled={loading}
        className="rounded border border-gray-300 px-1 py-1 text-xs text-gray-700 bg-white disabled:opacity-50"
      >
        <option value={0.20}>20%</option>
        <option value={0.15}>15%</option>
      </select>
      <button
        onClick={() => void handleRegister()}
        disabled={loading}
        className="inline-flex items-center rounded px-2 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
      >
        {loading ? "등록중..." : "마켓 등록"}
      </button>
    </div>
  )
}
