import { api } from "./api"
import type {
  CollectionSetting,
  CollectionSettingForm,
  SourcingProduct,
  CollectionLog,
  ExtensionStatus,
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

  /** 수집 설정 수정 */
  update: (id: number, data: Partial<CollectionSettingForm>) =>
    api.put<CollectionSetting>(`/api/v1/collection-settings/${id}`, data),

  /** 수집 설정 삭제 */
  delete: (id: number) =>
    api.delete<void>(`/api/v1/collection-settings/${id}`),
}

/** 상품 API */
export const productsApi = {
  /** 상품 목록 조회 (페이지네이션 지원) */
  list: (params?: { limit?: number; skip?: number }) =>
    api.get<SourcingProduct[]>(
      `/api/v1/products?limit=${params?.limit ?? 50}&skip=${params?.skip ?? 0}`
    ),

  /** 상품 단건 조회 */
  get: (id: number) => api.get<SourcingProduct>(`/api/v1/products/${id}`),
}

/** 수집 로그 API */
export const logsApi = {
  /** 수집 로그 목록 조회 (페이지네이션 지원) */
  list: (params?: { limit?: number; skip?: number }) =>
    api.get<CollectionLog[]>(
      `/api/v1/collection-logs?limit=${params?.limit ?? 50}&skip=${params?.skip ?? 0}`
    ),
}

/** 익스텐션 상태 API */
export const extensionApi = {
  /** 익스텐션 온라인 상태 조회 */
  getStatus: () => api.get<ExtensionStatus>("/api/v1/extension/status"),
}
