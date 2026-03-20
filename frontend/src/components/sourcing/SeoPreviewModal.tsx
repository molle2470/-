"use client"

import { useState } from "react"
import type { ProductSeo, SeoUpdateForm } from "@/types/sourcing"
import { updateSeoData } from "@/lib/api/seo"

interface Props {
  productId: number
  seo: ProductSeo
  onClose: () => void
  onSaved: () => void
}

/** SEO 상태 뱃지 */
function SeoStatusBadge({ status }: { status: string }) {
  const map: Record<string, { label: string; cls: string }> = {
    generated: { label: "AI 생성", cls: "bg-blue-100 text-blue-700" },
    edited: { label: "수동 수정", cls: "bg-purple-100 text-purple-700" },
    fallback: { label: "규칙 생성", cls: "bg-yellow-100 text-yellow-700" },
    failed: { label: "생성 실패", cls: "bg-red-100 text-red-700" },
  }
  const style = map[status] ?? { label: status, cls: "bg-gray-100 text-gray-500" }
  return (
    <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${style.cls}`}>
      {style.label}
    </span>
  )
}

/** SEO 미리보기/수정 모달 */
export function SeoPreviewModal({ productId, seo, onClose, onSaved }: Props) {
  const [form, setForm] = useState<SeoUpdateForm>({
    optimized_name: seo.optimized_name,
    tags: seo.tags ?? [],
    material: seo.material ?? "",
    color: seo.color ?? "",
    gender: seo.gender ?? "남녀공용",
    age_group: seo.age_group,
    origin: seo.origin,
  })
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const handleSave = async () => {
    setSaving(true)
    setError(null)
    try {
      await updateSeoData(productId, form)
      onSaved()
    } catch (e) {
      setError(e instanceof Error ? e.message : "저장 실패")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-lg rounded-xl bg-white shadow-xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900">SEO 미리보기/수정</h2>
          <SeoStatusBadge status={seo.status} />
        </div>

        <div className="space-y-3">
          {/* 최적화 상품명 */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              최적화 상품명 (100자 이하)
            </label>
            <input
              type="text"
              maxLength={100}
              value={form.optimized_name ?? ""}
              onChange={(e) => setForm({ ...form, optimized_name: e.target.value })}
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
            <span className="text-xs text-gray-400">{form.optimized_name?.length ?? 0}/100자</span>
          </div>

          {/* 태그 */}
          <div>
            <label className="block text-xs font-medium text-gray-500 mb-1">
              검색 태그 (쉼표로 구분, 최대 10개)
            </label>
            <input
              type="text"
              value={(form.tags ?? []).join(", ")}
              onChange={(e) =>
                setForm({
                  ...form,
                  tags: e.target.value.split(",").map((t) => t.trim()).filter(Boolean).slice(0, 10),
                })
              }
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
            />
          </div>

          {/* 소재 / 색상 / 성별 / 원산지 */}
          <div className="grid grid-cols-2 gap-3">
            {(
              [
                { key: "material", label: "소재" },
                { key: "color", label: "색상" },
                { key: "gender", label: "성별" },
                { key: "origin", label: "원산지" },
              ] as const
            ).map(({ key, label }) => (
              <div key={key}>
                <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
                <input
                  type="text"
                  value={(form[key] as string) ?? ""}
                  onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm"
                />
              </div>
            ))}
          </div>
        </div>

        {error && <p className="mt-3 text-sm text-red-500">{error}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            className="rounded-md border border-gray-300 px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
          >
            취소
          </button>
          <button
            onClick={() => void handleSave()}
            disabled={saving}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm text-white hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? "저장 중..." : "저장"}
          </button>
        </div>
      </div>
    </div>
  )
}
