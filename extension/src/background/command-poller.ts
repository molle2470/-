import { COMMAND_POLL_ALARM_NAME } from "../shared/constants"
import { fetchPendingCommands, ackCommand } from "./api-client"
import { registerMonitoring, unregisterMonitoring } from "./monitoring-manager"
import type { MonitoringGrade } from "../shared/types"

/** 명령 폴링 알람 등록 (중복 생성 방지) */
export async function startCommandPolling(): Promise<void> {
  // 이미 알람이 존재하면 재생성하지 않음 (SW 재시작 시 주기 리셋 방지)
  const existing = await chrome.alarms.get(COMMAND_POLL_ALARM_NAME)
  if (existing) return

  // chrome.alarms 최소 주기 1분 (MV3 제약)
  chrome.alarms.create(COMMAND_POLL_ALARM_NAME, {
    periodInMinutes: 1,
  })
}

/** 명령 폴링 처리 */
export async function handleCommandPoll(): Promise<void> {
  const commands = await fetchPendingCommands()

  for (const cmd of commands) {
    try {
      const payload = JSON.parse(cmd.payload) as Record<string, unknown>

      switch (cmd.command_type) {
        case "monitor_register": {
          const productId = Number(payload.product_id)
          const sourceUrl = String(payload.source_url || "")
          const grade: MonitoringGrade =
            payload.grade === "high" ? "high" : "normal"
          if (!productId || !sourceUrl) throw new Error("잘못된 payload")
          await registerMonitoring(productId, sourceUrl, grade)
          break
        }
        case "monitor_unregister": {
          const productId = Number(payload.product_id)
          if (!productId) throw new Error("잘못된 payload")
          await unregisterMonitoring(productId)
          break
        }
        default:
          console.warn(`알 수 없는 명령: ${cmd.command_type}`)
      }

      await ackCommand(cmd.id, "done")
    } catch (error) {
      console.error(`명령 처리 실패: ${cmd.id}`, error)
      await ackCommand(cmd.id, "failed")
    }
  }
}
