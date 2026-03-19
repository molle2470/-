import { ExtensionStatus } from "@/components/sourcing/ExtensionStatus"
import { serverFetchList } from "@/lib/server-fetch"
import type { CollectionSetting, SourcingProduct, CollectionLog } from "@/types/sourcing"

/** 소싱 메인 대시보드 — 수집 현황 요약 */
export default async function SourcingPage() {
  const [products, settings, logs] = await Promise.all([
    // limit=200 (최대값)으로 전체 수 근사치 조회 — 별도 count 엔드포인트 없음
    serverFetchList<SourcingProduct>("/api/v1/products?limit=200"),
    serverFetchList<CollectionSetting>("/api/v1/collection-settings"),
    serverFetchList<CollectionLog>("/api/v1/collection-logs?limit=5"),
  ])

  const productCount = products.length
  const settingsCount = settings.length
  const recentLogs = logs

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">소싱 메인</h1>

      {/* 익스텐션 안내 */}
      <div className="mb-6">
        <ExtensionStatus />
      </div>

      {/* 요약 카드 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3 mb-6">
        <SummaryCard label="총 수집 상품" value={productCount} unit="개" />
        <SummaryCard label="수집 설정" value={settingsCount} unit="개" />
        <SummaryCard label="최근 로그" value={recentLogs.length} unit="건" />
      </div>

      {/* 최근 수집 로그 */}
      <div className="rounded-lg border border-gray-200 bg-white">
        <div className="px-4 py-3 border-b border-gray-200">
          <h2 className="text-sm font-semibold text-gray-800">최근 수집 로그</h2>
        </div>
        {recentLogs.length === 0 ? (
          <p className="px-4 py-6 text-sm text-gray-400 text-center">
            수집 로그가 없습니다.
          </p>
        ) : (
          <ul className="divide-y divide-gray-100">
            {recentLogs.map((log) => (
              <li key={log.id} className="flex items-center justify-between px-4 py-3">
                <div className="flex items-center gap-3">
                  {/* 상태 배지 */}
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      log.status === "success"
                        ? "bg-green-100 text-green-700"
                        : "bg-red-100 text-red-700"
                    }`}
                  >
                    {log.status === "success" ? "성공" : "실패"}
                  </span>
                  <span className="text-sm text-gray-800">{log.product_name}</span>
                </div>
                <span className="text-xs text-gray-400">
                  {new Date(log.created_at).toLocaleString("ko-KR")}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

/** 요약 카드 서브 컴포넌트 */
function SummaryCard({
  label,
  value,
  unit,
}: {
  label: string
  value: number
  unit: string
}) {
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4">
      <p className="text-xs text-gray-500">{label}</p>
      <p className="mt-1 text-2xl font-bold text-gray-900">
        {value.toLocaleString()}
        <span className="ml-1 text-sm font-normal text-gray-500">{unit}</span>
      </p>
    </div>
  )
}
