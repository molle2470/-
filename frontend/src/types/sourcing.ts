/** 수집 설정 */
export interface CollectionSetting {
  id: number
  name: string
  source_id: number
  brand_name: string
  category_url: string
  max_count: number
  is_active: boolean
  last_collected_at: string | null
  collected_count: number
  created_at: string
  updated_at: string
}

/** 수집 설정 생성 폼 */
export interface CollectionSettingForm {
  name: string
  source_id: number
  brand_name: string
  category_url: string
  max_count: number
}

/** 수집 설정 수정 폼 (is_active 포함, 모든 필드 optional) */
export interface CollectionSettingUpdateForm {
  name?: string
  brand_name?: string
  category_url?: string
  max_count?: number
  is_active?: boolean
}

/** 수집된 상품 (백엔드 products 엔드포인트 응답 구조와 일치) */
export interface SourcingProduct {
  id: number
  name: string
  original_price: number
  brand_id: number | null
  source_url: string
  stock_status: string
  thumbnail_url: string | null
  status: string
  created_at: string
}

/** 상품 상세 (단건 조회 시 추가 필드) */
export interface SourcingProductDetail extends SourcingProduct {
  source_id: number
  source_product_id: string
  image_urls: string[] | null
}

/** 수집 로그 */
export interface CollectionLog {
  id: number
  setting_id: number | null
  product_name: string
  status: "success" | "failed"
  message: string | null
  created_at: string
}

/** 익스텐션 상태 */
export interface ExtensionStatus {
  is_online: boolean
  monitoring_count: number
  last_heartbeat: string | null
}
