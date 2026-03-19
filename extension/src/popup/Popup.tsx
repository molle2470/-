import React, { useEffect, useState } from "react"

export function Popup() {
  const [apiKey, setApiKey] = useState("")
  const [serverStatus, setServerStatus] = useState<"checking" | "online" | "offline">("checking")
  const [monitoringCount, setMonitoringCount] = useState(0)

  useEffect(() => {
    // 저장된 API 키 로드
    chrome.storage.local.get(["apiKey"], (result) => {
      if (result.apiKey) setApiKey(result.apiKey)
    })

    // 모니터링 수 로드
    chrome.storage.local.get(["monitoringItems"], (result) => {
      const items = result.monitoringItems || []
      setMonitoringCount(items.length)
    })

    // 서버 상태 확인
    void checkServerStatus()
  }, [])

  async function checkServerStatus() {
    try {
      const result = await chrome.storage.local.get("apiKey")
      const res = await fetch("http://localhost:28080/api/v1/extension/heartbeat", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-Extension-Key": result.apiKey || "",
        },
        body: JSON.stringify({ monitoring_count: 0, extension_version: "1.0.0" }),
      })
      setServerStatus(res.ok ? "online" : "offline")
    } catch {
      setServerStatus("offline")
    }
  }

  function saveApiKey() {
    chrome.storage.local.set({ apiKey })
    void checkServerStatus()
  }

  return (
    <div style={{ width: 320, padding: 16, fontFamily: "sans-serif" }}>
      <h2 style={{ fontSize: 16, marginBottom: 12 }}>소싱 어시스턴트</h2>

      {/* 서버 상태 */}
      <div style={{ marginBottom: 12, display: "flex", alignItems: "center", gap: 8 }}>
        <span style={{
          width: 8, height: 8, borderRadius: "50%",
          background: serverStatus === "online" ? "#10b981"
            : serverStatus === "offline" ? "#ef4444" : "#f59e0b",
        }} />
        <span style={{ fontSize: 13 }}>
          서버: {serverStatus === "online" ? "연결됨" : serverStatus === "offline" ? "연결 끊김" : "확인 중..."}
        </span>
      </div>

      {/* 모니터링 현황 */}
      <div style={{ marginBottom: 16, fontSize: 13, color: "#6b7280" }}>
        모니터링 중: {monitoringCount}개 상품
      </div>

      {/* API 키 설정 */}
      <div>
        <label style={{ fontSize: 12, color: "#6b7280" }}>API 키</label>
        <div style={{ display: "flex", gap: 4, marginTop: 4 }}>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="API 키 입력"
            style={{
              flex: 1, padding: "6px 8px", border: "1px solid #d1d5db",
              borderRadius: 4, fontSize: 13,
            }}
          />
          <button
            onClick={saveApiKey}
            style={{
              padding: "6px 12px", background: "#2563eb", color: "white",
              border: "none", borderRadius: 4, fontSize: 12, cursor: "pointer",
            }}
          >
            저장
          </button>
        </div>
      </div>
    </div>
  )
}
