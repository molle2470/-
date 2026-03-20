import {
  COMMAND_POLL_ALARM_NAME,
  HEARTBEAT_ALARM_NAME,
  MONITOR_ALARM_PREFIX,
  TAB_CLEANUP_PREFIX,
} from "../shared/constants"
import { sendHeartbeat, sendCollectedProduct, fetchProductSeo } from "./api-client"
import { startCommandPolling, handleCommandPoll } from "./command-poller"
import {
  handleMonitoringAlarm,
  checkProductChanges,
  getMonitoringCount,
} from "./monitoring-manager"
import type { ContentMessage } from "../shared/types"

// 마지막으로 수집한 상품 ID (네이버 자동입력에 활용)
let lastCollectedProductId: number | null = null

// 알람 이벤트 핸들러
chrome.alarms.onAlarm.addListener(async (alarm) => {
  if (alarm.name === COMMAND_POLL_ALARM_NAME) {
    await handleCommandPoll()
  } else if (alarm.name === HEARTBEAT_ALARM_NAME) {
    const count = await getMonitoringCount()
    await sendHeartbeat(count)
  } else if (alarm.name.startsWith(MONITOR_ALARM_PREFIX)) {
    await handleMonitoringAlarm(alarm.name)
  } else if (alarm.name.startsWith(TAB_CLEANUP_PREFIX)) {
    // 모니터링 탭 정리
    const tabId = parseInt(alarm.name.replace(TAB_CLEANUP_PREFIX, ""), 10)
    if (!isNaN(tabId)) {
      try { await chrome.tabs.remove(tabId) } catch { /* 이미 닫힘 */ }
    }
  }
})

// Content Script 메시지 핸들러
chrome.runtime.onMessage.addListener((message: ContentMessage, sender, sendResponse) => {
  console.log("[SW] 메시지 수신:", message.type)
  if (message.type === "COLLECT_BUTTON_CLICKED") {
    console.log("[SW] 수집 요청 처리 시작", message.data?.name)
    // 개별 수집: 백엔드로 전송
    sendCollectedProduct("musinsa", message.data).then((result) => {
      console.log("[SW] 수집 결과:", result)
      // 수집 성공 시 product_id 저장 (네이버 SEO 자동입력에 활용)
      if (result?.product_id) {
        lastCollectedProductId = result.product_id
      }
      sendResponse({
        success: !!result,
        product_id: result?.product_id,
        warning: result?.warning,
      })
    })
    return true // 비동기 응답
  }

  if (message.type === "MONITORING_DATA_CAPTURED") {
    // 모니터링 데이터 수신: 변동 비교
    checkProductChanges(message.productId, message.data)
    sendResponse({ success: true })
    return true
  }

  if (message.type === "PRODUCT_DATA_CAPTURED") {
    // interceptor에서 데이터 캡처됨 → 같은 탭의 product script에 전달
    if (sender.tab?.id) {
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "PRODUCT_DATA_READY",
        data: message.data,
      }).catch(() => {
        // content script가 아직 준비되지 않은 경우 무시
      })
    }
    sendResponse({ success: true })
  }

  if (message.type === "NAVER_REGISTER_PAGE_LOADED") {
    // 네이버 등록 페이지 로드 → 저장된 product_id로 SEO 데이터 조회 후 자동입력 트리거
    if (lastCollectedProductId !== null) {
      const productId = lastCollectedProductId
      fetchProductSeo(productId).then((seoData) => {
        if (seoData && sender.tab?.id) {
          chrome.tabs.sendMessage(sender.tab.id, {
            type: "SEO_AUTOFILL",
            seoData,
          }).catch(() => {
            // content script가 아직 준비되지 않은 경우 무시
          })
        }
        sendResponse({ success: true })
      })
    } else {
      sendResponse({ success: true })
    }
    return true // 비동기 응답
  }
})

// 익스텐션 설치/업데이트 시 초기화
chrome.runtime.onInstalled.addListener(async () => {
  await startCommandPolling()

  // Heartbeat 알람 (중복 생성 방지)
  const existingHeartbeat = await chrome.alarms.get(HEARTBEAT_ALARM_NAME)
  if (!existingHeartbeat) {
    chrome.alarms.create(HEARTBEAT_ALARM_NAME, { periodInMinutes: 1 })
  }

  console.log("소싱 어시스턴트 익스텐션 초기화 완료")
})

// Service Worker 시작 시 폴링 재시작 (SW 재시작 대응)
startCommandPolling()
