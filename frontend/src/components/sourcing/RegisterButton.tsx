"use client"

import { useState } from "react"
import { registerToMarket } from "@/lib/market-listings-api"

/**
 * Phase 1: DB에 직접 삽입한 초기 데이터 ID 사용.
 * Task 7에서 실제 마켓 계정/템플릿 ID로 업데이트 예정.
 */
const NAVER_MARKET_ACCOUNT_ID = 1
const NAVER_MARKET_ID = 1
const COMMON_TEMPLATE_ID = 2

interface Props {
  productId: number
}

/** 스마트스토어 마켓 등록 버튼 */
export function RegisterButton({ productId }: Props) {
  const [loading, setLoading] = useState(false)
  const [done, setDone] = useState(false)

  async function handleRegister() {
    if (!confirm("스마트스토어에 등록하시겠습니까?")) return
    setLoading(true)
    try {
      await registerToMarket({
        product_id: productId,
        market_account_id: NAVER_MARKET_ACCOUNT_ID,
        market_id: NAVER_MARKET_ID,
        common_template_id: COMMON_TEMPLATE_ID,
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
    <button
      onClick={() => void handleRegister()}
      disabled={loading}
      className="inline-flex items-center rounded px-2 py-1 text-xs font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-50"
    >
      {loading ? "등록중..." : "마켓 등록"}
    </button>
  )
}
