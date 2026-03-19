import { api } from "./api"
import type {
  CollectionSetting,
  CollectionSettingForm,
  CollectionSettingUpdateForm,
  SourcingProduct,
  SourcingProductDetail,
  CollectionLog,
} from "@/types/sourcing"

/** 수집 설정 API */
export const collectionSettingsApi = {
  /** 수집 설정 목록 조회 */
  list: () => api.get<CollectionSetting[]>("/api/v1/collection-settings"),

  /** 수집 설정 단건 조회 */
  get: (id: number) => api.get<CollectionSetting>(`/api/v1/collection-settings/${id}`),

  /** 수집 설정 생성 */
  create: (data: CollectionSettingForm) =>
    api.post<CollectionSetting>("/api/v1/collection-settings", data),

  /** 수집 설정 수정 (is_active 토글 포함) */
  update: (id: number, data: CollectionSettingUpdateForm) =>
    api.put<CollectionSetting>(`/api/v1/collection-settings/${id}`, data),

  /** 수집 설정 삭제 */
  delete: (id: number) =>
    api.delete<void>(`/api/v1/collection-settings/${id}`),
}

/** 상품 API */
export const productsApi = {
  /** 상품 목록 조회 (페이지네이션 + 필터 지원) */
  list: (params?: {
    limit?: number
    skip?: number
    source_id?: number
    brand_id?: number
    status?: string
  }) => {
    const searchParams = new URLSearchParams()
    searchParams.set("limit", String(params?.limit ?? 50))
    searchParams.set("skip", String(params?.skip ?? 0))
    if (params?.source_id != null) searchParams.set("source_id", String(params.source_id))
    if (params?.brand_id != null) searchParams.set("brand_id", String(params.brand_id))
    if (params?.status) searchParams.set("status", params.status)
    return api.get<SourcingProduct[]>(`/api/v1/products?${searchParams.toString()}`)
  },

  /** 상품 상세 조회 */
  get: (id: number) => api.get<SourcingProductDetail>(`/api/v1/products/${id}`),
}

/** 수집 로그 API */
export const logsApi = {
  /** 수집 로그 목록 조회 (페이지네이션 지원) */
  list: (params?: { limit?: number; skip?: number }) => {
    const searchParams = new URLSearchParams()
    searchParams.set("limit", String(params?.limit ?? 50))
    searchParams.set("skip", String(params?.skip ?? 0))
    return api.get<CollectionLog[]>(`/api/v1/collection-logs?${searchParams.toString()}`)
  },
}
