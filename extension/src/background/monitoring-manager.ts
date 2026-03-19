import type { MonitoringGrade, MonitoringItem, ProductData } from "../shared/types"
import { MONITOR_ALARM_PREFIX, TAB_CLEANUP_PREFIX } from "../shared/constants"
import { sendProductChange } from "./api-client"

const MONITORING_STORAGE_KEY = "monitoringItems"

/** 모니터링 목록 로드 (chrome.storage.local) */
async function loadMonitoringItems(): Promise<MonitoringItem[]> {
  const result = await chrome.storage.local.get(MONITORING_STORAGE_KEY)
  return result[MONITORING_STORAGE_KEY] || []
}

/** 모니터링 목록 저장 */
async function saveMonitoringItems(items: MonitoringItem[]): Promise<void> {
  await chrome.storage.local.set({ [MONITORING_STORAGE_KEY]: items })
}

/** 모니터링 등록 */
export async function registerMonitoring(
  productId: number,
  sourceUrl: string,
  grade: MonitoringGrade,
): Promise<void> {
  const items = await loadMonitoringItems()

  // 중복 방지
  if (items.some((item) => item.product_id === productId)) return

  items.push({
    product_id: productId,
    source_url: sourceUrl,
    grade,
    last_price: 0,
    last_stock_status: "unknown",
    is_initialized: false,
  })
  await saveMonitoringItems(items)

  // 랜덤 주기 알람 등록
  const intervalMinutes = getRandomInterval(grade)
  chrome.alarms.create(`${MONITOR_ALARM_PREFIX}${productId}`, {
    periodInMinutes: intervalMinutes,
  })
}

/** 모니터링 해제 */
export async function unregisterMonitoring(productId: number): Promise<void> {
  const items = await loadMonitoringItems()
  const filtered = items.filter((item) => item.product_id !== productId)
  await saveMonitoringItems(filtered)

  chrome.alarms.clear(`${MONITOR_ALARM_PREFIX}${productId}`)
}

/** 모니터링 알람 처리 (탭 열어서 데이터 수집) */
export async function handleMonitoringAlarm(alarmName: string): Promise<void> {
  const productId = parseInt(alarmName.replace(MONITOR_ALARM_PREFIX, ""), 10)
  if (isNaN(productId)) return

  const items = await loadMonitoringItems()
  const item = items.find((i) => i.product_id === productId)
  if (!item) return

  // 백그라운드 탭으로 무신사 상품 페이지 열기
  const tab = await chrome.tabs.create({
    url: item.source_url,
    active: false,
  })

  // Content Script가 데이터를 캡처하면 메시지로 받음
  // 일회성 알람으로 0.5분 후 탭 닫기 (setTimeout 대신 chrome.alarms 사용)
  if (tab.id) {
    chrome.alarms.create(`${TAB_CLEANUP_PREFIX}${tab.id}`, { delayInMinutes: 0.5 })
  }
}

/** 모니터링 데이터 비교 + 변동 전송 */
export async function checkProductChanges(
  productId: number,
  newData: ProductData,
): Promise<void> {
  const items = await loadMonitoringItems()
  const item = items.find((i) => i.product_id === productId)
  if (!item || !item.is_initialized) {
    // 최초 데이터 → 저장만 (변동 전송 없음)
    if (item) {
      item.last_price = newData.original_price
      item.last_stock_status = newData.stock_status
      item.is_initialized = true
      await saveMonitoringItems(items)
    }
    return
  }

  const priceChanged = newData.original_price !== item.last_price
  const stockChanged = newData.stock_status !== item.last_stock_status

  if (priceChanged || stockChanged) {
    let changeType = "both"
    if (priceChanged && !stockChanged) changeType = "price"
    if (!priceChanged && stockChanged) changeType = "stock"

    await sendProductChange(
      productId,
      changeType,
      priceChanged ? item.last_price : null,
      priceChanged ? newData.original_price : null,
      stockChanged ? newData.stock_status : null,
    )

    // 로컬 상태 업데이트
    item.last_price = newData.original_price
    item.last_stock_status = newData.stock_status
    await saveMonitoringItems(items)
  }
}

/** 등급별 랜덤 주기 (분) — chrome.alarms 최소 1분 */
function getRandomInterval(grade: MonitoringGrade): number {
  if (grade === "high") {
    // 8~17분
    return 8 + Math.random() * 9
  }
  // 25~65분
  return 25 + Math.random() * 40
}

/** 모니터링 중인 상품 수 */
export async function getMonitoringCount(): Promise<number> {
  const items = await loadMonitoringItems()
  return items.length
}
