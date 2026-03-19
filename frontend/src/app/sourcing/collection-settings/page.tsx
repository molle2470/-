import { CollectionSettingsTable } from "@/components/sourcing/CollectionSettingsTable"
import type { CollectionSetting } from "@/types/sourcing"

const API_BASE_URL =
  process.env.NEXT_PUBLIC_ENV === "development"
    ? (process.env.NEXT_PUBLIC_API_URL_DEV ?? "http://localhost:28080")
    : (process.env.NEXT_PUBLIC_API_URL_PROD ?? "http://localhost:28080")

/** 서버에서 수집 설정 목록 조회 */
async function fetchSettings(): Promise<CollectionSetting[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/api/v1/collection-settings`, {
      cache: "no-store",
    })
    if (!res.ok) return []
    return (await res.json()) as CollectionSetting[]
  } catch {
    return []
  }
}

/** 수집 설정 목록 페이지 */
export default async function CollectionSettingsPage() {
  const settings = await fetchSettings()

  return (
    <div>
      <h1 className="text-xl font-semibold text-gray-900 mb-6">수집 설정</h1>
      <CollectionSettingsTable settings={settings} />
    </div>
  )
}
