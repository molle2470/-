/**
 * 서버 컴포넌트 전용 API 요청 유틸리티.
 * api.ts는 localStorage 기반 토큰을 사용하므로 서버 컴포넌트에서 사용 불가.
 * 소싱 API는 인증 불필요한 엔드포인트만 대상으로 함.
 */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_ENV === "development"
    ? (process.env.NEXT_PUBLIC_API_URL_DEV ?? "http://localhost:28080")
    : (process.env.NEXT_PUBLIC_API_URL_PROD ?? "http://localhost:28080")

/** 서버 컴포넌트에서 JSON 데이터를 fetch하는 헬퍼 */
export async function serverFetch<T>(path: string): Promise<T | null> {
  try {
    const res = await fetch(`${API_BASE_URL}${path}`, {
      cache: "no-store",
    })
    if (!res.ok) return null
    return (await res.json()) as T
  } catch {
    return null
  }
}

/** 서버 컴포넌트에서 JSON 배열을 fetch하는 헬퍼 (실패 시 빈 배열) */
export async function serverFetchList<T>(path: string): Promise<T[]> {
  const result = await serverFetch<T[]>(path)
  return Array.isArray(result) ? result : []
}
