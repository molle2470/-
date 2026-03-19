import { LogsViewer } from "@/components/sourcing/LogsViewer"
import { serverFetchList } from "@/lib/server-fetch"
import type { CollectionLog } from "@/types/sourcing"

/** 수집 로그 목록 페이지 */
export default async function LogsPage() {
  const logs = await serverFetchList<CollectionLog>("/api/v1/collection-logs?limit=50&skip=0")

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold text-gray-900">수집 로그</h1>
        <span className="text-sm text-gray-400">총 {logs.length.toLocaleString()}건</span>
      </div>
      <LogsViewer logs={logs} />
    </div>
  )
}
