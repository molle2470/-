"use client"

import { useRouter } from "next/navigation"
import { useState } from "react"
import Link from "next/link"
import type { CollectionSetting } from "@/types/sourcing"
import { collectionSettingsApi } from "@/lib/sourcing-api"

interface Props {
  settings: CollectionSetting[]
}

/** 수집 설정 목록 테이블 */
export function CollectionSettingsTable({ settings }: Props) {
  const router = useRouter()
  /** 토글 중인 설정 ID (중복 클릭 방지) */
  const [togglingId, setTogglingId] = useState<number | null>(null)

  /** 수집 설정 삭제 */
  async function handleDelete(id: number) {
    if (!confirm("이 수집 설정을 삭제하시겠습니까?")) return
    try {
      await collectionSettingsApi.delete(id)
      router.refresh()
    } catch {
      alert("삭제에 실패했습니다.")
    }
  }

  /** is_active 토글 */
  async function handleToggleActive(setting: CollectionSetting) {
    if (togglingId !== null) return
    setTogglingId(setting.id)
    try {
      await collectionSettingsApi.update(setting.id, {
        is_active: !setting.is_active,
      })
      router.refresh()
    } catch {
      alert("상태 변경에 실패했습니다.")
    } finally {
      setTogglingId(null)
    }
  }

  return (
    <div>
      {/* 상단 액션 */}
      <div className="flex justify-end mb-4">
        <Link
          href="/sourcing/collection-settings/new"
          className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 transition-colors"
        >
          + 새 수집 설정 추가
        </Link>
      </div>

      {/* 테이블 */}
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        {settings.length === 0 ? (
          <p className="px-4 py-10 text-center text-sm text-gray-400">
            수집 설정이 없습니다. 새 수집 설정을 추가해주세요.
          </p>
        ) : (
          <table className="min-w-full divide-y divide-gray-200 text-sm">
            <thead className="bg-gray-50">
              <tr>
                <Th>이름</Th>
                <Th>브랜드</Th>
                <Th>카테고리 URL</Th>
                <Th>최대 수집 수</Th>
                <Th>상태</Th>
                <Th>수집 수</Th>
                <Th>마지막 수집</Th>
                <Th>관리</Th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {settings.map((setting) => (
                <tr key={setting.id} className="hover:bg-gray-50">
                  <Td>{setting.name}</Td>
                  <Td>{setting.brand_name}</Td>
                  <Td>
                    <span
                      className="block max-w-xs truncate text-gray-500"
                      title={setting.category_url}
                    >
                      {setting.category_url}
                    </span>
                  </Td>
                  <Td>{setting.max_count.toLocaleString()}</Td>
                  <Td>
                    {/* 활성/비활성 토글 버튼 */}
                    <button
                      onClick={() => handleToggleActive(setting)}
                      disabled={togglingId !== null}
                      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                        setting.is_active
                          ? "bg-green-100 text-green-700 hover:bg-green-200"
                          : "bg-gray-100 text-gray-500 hover:bg-gray-200"
                      }`}
                    >
                      {togglingId === setting.id ? "처리중..." : setting.is_active ? "활성" : "비활성"}
                    </button>
                  </Td>
                  <Td>{setting.collected_count.toLocaleString()}</Td>
                  <Td>
                    {setting.last_collected_at
                      ? new Date(setting.last_collected_at).toLocaleString("ko-KR")
                      : "-"}
                  </Td>
                  <Td>
                    <button
                      onClick={() => handleDelete(setting.id)}
                      className="text-red-500 hover:text-red-700 text-xs font-medium transition-colors"
                    >
                      삭제
                    </button>
                  </Td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  )
}

/** 테이블 헤더 셀 */
function Th({ children }: { children: React.ReactNode }) {
  return (
    <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
      {children}
    </th>
  )
}

/** 테이블 데이터 셀 */
function Td({ children }: { children: React.ReactNode }) {
  return (
    <td className="px-4 py-3 text-gray-700 whitespace-nowrap">{children}</td>
  )
}
