/** 수집 상품 데이터 (백엔드 전송용) */
export interface ProductData {
  name: string
  original_price: number
  source_url: string
  source_product_id: string
  brand_name: string
  stock_status: string
  grade_discount_available: boolean
  point_usable: boolean
  point_earnable: boolean
  thumbnail_url: string | null
  image_urls: string[]
  options: ProductOption[]
}

export interface ProductOption {
  color: string | null
  size: string | null
  stock: number
}

/** 백엔드 명령 */
export interface ExtensionCommand {
  id: number
  command_type: string
  payload: string
}

export type MonitoringGrade = "high" | "normal"

/** 모니터링 대상 */
export interface MonitoringItem {
  product_id: number
  source_url: string
  grade: MonitoringGrade
  last_price: number
  last_stock_status: string
  is_initialized: boolean
}

/** Content Script → Background 메시지 */
export type ContentMessage =
  | { type: "PRODUCT_DATA_CAPTURED"; data: ProductData }
  | { type: "COLLECT_BUTTON_CLICKED"; data: ProductData }
  | { type: "MONITORING_DATA_CAPTURED"; productId: number; data: ProductData }

/** Background → Content Script 메시지 */
export type BackgroundMessage =
  | { type: "PRODUCT_DATA_READY"; data: ProductData }
