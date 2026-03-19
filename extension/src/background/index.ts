import { COMMAND_POLL_ALARM_NAME, HEARTBEAT_ALARM_NAME } from "../shared/constants"
import { sendHeartbeat, sendCollectedProduct } from "./api-client"
import { startCommandPolling, handleCommandPoll } from "./command-poller"
import {
  handleMonitoringAlarm,
  checkProductChanges,
  getMonitoringCount,
} from "./monitoring-manager"
import type { ContentMessage } from "../shared/types"

const MONITOR_ALARM_PREFIX = "monitor_"
const TAB_CLEANUP_PREFIX = "tab_cleanup_"

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
  if (message.type === "COLLECT_BUTTON_CLICKED") {
    // 개별 수집: 백엔드로 전송
    sendCollectedProduct("musinsa", message.data).then((result) => {
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
      })
    }
    sendResponse({ success: true })
  }
})

// 익스텐션 설치/업데이트 시 초기화
chrome.runtime.onInstalled.addListener(() => {
  startCommandPolling()

  // Heartbeat 알람 (1분마다)
  chrome.alarms.create(HEARTBEAT_ALARM_NAME, { periodInMinutes: 1 })

  console.log("소싱 어시스턴트 익스텐션 초기화 완료")
})

// Service Worker 시작 시 폴링 재시작 (SW 재시작 대응)
startCommandPolling()
