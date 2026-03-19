"use client"

/** 크롬 익스텐션 설치 안내 박스 */
export function ExtensionStatus() {
  return (
    <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 shrink-0 text-blue-500">
          <svg
            xmlns="http://www.w3.org/2000/svg"
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <path d="M12 16v-4" />
            <path d="M12 8h.01" />
          </svg>
        </div>
        <div>
          <p className="text-sm font-medium text-blue-800">크롬 익스텐션 안내</p>
          <p className="mt-1 text-sm text-blue-700">
            익스텐션이 설치되어 있으면 무신사 상품 페이지에서{" "}
            <span className="font-semibold">[수집하기]</span> 버튼을 사용할 수
            있습니다.
          </p>
        </div>
      </div>
    </div>
  )
}
