import Link from "next/link"

/** 소싱 섹션 사이드바 네비게이션 항목 */
const navItems = [
  { href: "/", label: "대시보드" },
  { href: "/sourcing", label: "소싱 메인" },
  { href: "/sourcing/collection-settings", label: "수집 설정" },
  { href: "/sourcing/products", label: "수집 상품" },
  { href: "/sourcing/monitoring", label: "모니터링" },
  { href: "/sourcing/market-listings", label: "마켓 등록" },
  { href: "/sourcing/logs", label: "수집 로그" },
]

export default function SourcingLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="flex min-h-screen bg-gray-50">
      {/* 사이드바 */}
      <aside className="w-56 shrink-0 border-r border-gray-200 bg-white">
        <div className="px-4 py-5 border-b border-gray-200">
          <h2 className="text-base font-bold text-gray-900">소싱 관리</h2>
        </div>
        <nav className="py-3">
          <ul className="space-y-0.5">
            {navItems.map((item) => (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 transition-colors"
                >
                  {item.label}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* 메인 콘텐츠 */}
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
