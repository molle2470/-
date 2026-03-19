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

/** 수집 설정 생성/수정 폼 */
export interface CollectionSettingForm {
  name: string
  source_id: number
  brand_name: string
  category_url: string
  max_count: number
}

/** 수집된 상품 */
export interface SourcingProduct {
  id: number
  name: string
  original_price: number
  selling_price: number | null
  brand_name: string
  source_url: string
  stock_status: string
  thumbnail_url: string | null
  grade_discount_available: boolean
  point_usable: boolean
  listing_status: string | null
  created_at: string
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
