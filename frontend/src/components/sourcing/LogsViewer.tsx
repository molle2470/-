"use client"

import type { CollectionLog } from "@/types/sourcing"

interface Props {
  logs: CollectionLog[]
}

/** 수집 로그 뷰어 테이블 */
export function LogsViewer({ logs }: Props) {
  if (logs.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-4 py-10 text-center text-sm text-gray-400">
        수집 로그가 없습니다.
      </div>
    )
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
      <table className="min-w-full divide-y divide-gray-200 text-sm">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
              시간
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
              상품명
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider whitespace-nowrap">
              상태
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">
              메시지
            </th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-100">
          {logs.map((log) => (
            <tr key={log.id} className="hover:bg-gray-50">
              {/* 시간 */}
              <td className="px-4 py-3 whitespace-nowrap text-gray-400 text-xs">
                {new Date(log.created_at).toLocaleString("ko-KR")}
              </td>
              {/* 상품명 */}
              <td className="px-4 py-3 text-gray-700 max-w-xs truncate">
                {log.product_name}
              </td>
              {/* 상태 */}
              <td className="px-4 py-3 whitespace-nowrap">
                <span
                  className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                    log.status === "success"
                      ? "bg-green-100 text-green-700"
                      : "bg-red-100 text-red-700"
                  }`}
                >
                  {log.status === "success" ? "성공" : "실패"}
                </span>
              </td>
              {/* 메시지 */}
              <td className="px-4 py-3 text-gray-500 max-w-sm truncate" title={log.message ?? ""}>
                {log.message ?? "-"}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
