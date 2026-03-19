import { CollectionSettingsTable } from "@/components/sourcing/CollectionSettingsTable"
import { serverFetchList } from "@/lib/server-fetch"
import type { CollectionSetting } from "@/types/sourcing"

/** 수집 설정 목록 페이지 */
export default async function CollectionSettingsPage() {
  const settings = await serverFetchList<CollectionSetting>("/api/v1/collection-settings")

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">수집 설정</h1>
      <CollectionSettingsTable settings={settings} />
    </div>
  )
}
