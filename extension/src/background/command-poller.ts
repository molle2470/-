import { COMMAND_POLL_ALARM_NAME } from "../shared/constants"
import { fetchPendingCommands, ackCommand } from "./api-client"
import { registerMonitoring, unregisterMonitoring } from "./monitoring-manager"

/** 명령 폴링 알람 등록 */
export function startCommandPolling(): void {
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
      const payload = JSON.parse(cmd.payload)

      switch (cmd.command_type) {
        case "monitor_register":
          await registerMonitoring(
            payload.product_id,
            payload.source_url,
            payload.grade || "normal",
          )
          break
        case "monitor_unregister":
          await unregisterMonitoring(payload.product_id)
          break
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
