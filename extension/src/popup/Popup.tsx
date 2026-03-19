import React, { useEffect, useState } from "react"

export function Popup() {
  const [apiKey, setApiKey] = useState("")
  const [serverStatus, setServerStatus] = useState<"checking" | "online" | "offline">("checking")
  const [monitoringCount, setMonitoringCount] = useState(0)

  useEffect(() => {
    // apiKey + monitoringItems 한 번에 로드
    chrome.storage.local.get(["apiKey", "monitoringItems"], (result) => {
      const savedKey: string = result.apiKey || ""
      if (savedKey) setApiKey(savedKey)
      setMonitoringCount((result.monitoringItems || []).length)
      // 로드한 키로 바로 서버 상태 확인
      void checkServerStatus(savedKey)
    })
  }, [])

  // apiKey 파라미터를 받아 storage 재조회 없이 사용
  async function checkServerStatus(key: string) {
    try {
      const res = await fetch("http://localhost:28080/api/v1/extension/heartbeat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Extension-Key": key,
        },
        body: JSON.stringify({ monitoring_count: 0, extension_version: "1.0.0" }),
      })
      setServerStatus(res.ok ? "online" : "offline")
    } catch {
      setServerStatus("offline")
    }
  }

  async function saveApiKey() {
    // 저장 완료 후 상태 확인 (경쟁 조건 방지)
    await chrome.storage.local.set({ apiKey })
    void checkServerStatus(apiKey)
  }

  const statusColor =
    serverStatus === "online" ? "#10b981"
    : serverStatus === "offline" ? "#ef4444"
    : "#f59e0b"

  const statusText =
    serverStatus === "online" ? "연결됨"
    : serverStatus === "offline" ? "연결 끊김"
    : "확인 중..."

  return (
    <div className="w-80 p-4 font-sans">
      <h2 className="text-base font-semibold mb-3">소싱 어시스턴트</h2>

      {/* 서버 상태 */}
      <div className="flex items-center gap-2 mb-3">
        <span
          className="w-2 h-2 rounded-full"
          style={{ background: statusColor }}
        />
        <span className="text-sm">서버: {statusText}</span>
      </div>

      {/* 모니터링 현황 */}
      <div className="mb-4 text-sm text-gray-500">
        모니터링 중: {monitoringCount}개 상품
      </div>

      {/* API 키 설정 */}
      <div>
        <label className="text-xs text-gray-500">API 키</label>
        <div className="flex gap-1 mt-1">
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API 키 입력"
            className="flex-1 px-2 py-1.5 border border-gray-300 rounded text-sm"
          />
          <button
            onClick={() => void saveApiKey()}
            className="px-3 py-1.5 bg-blue-600 text-white rounded text-xs cursor-pointer hover:bg-blue-700"
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
