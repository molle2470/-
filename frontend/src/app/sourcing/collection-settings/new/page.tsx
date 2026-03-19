"use client"

import { useState, type FormEvent } from "react"
import { useRouter } from "next/navigation"
import { collectionSettingsApi } from "@/lib/sourcing-api"
import type { CollectionSettingForm } from "@/types/sourcing"

/** 폼 유효성 검증 오류 */
interface FormErrors {
  name?: string
  source_id?: string
  brand_name?: string
  category_url?: string
  max_count?: string
}

/** 수집 설정 생성 폼 페이지 */
export default function NewCollectionSettingPage() {
  const router = useRouter()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [errors, setErrors] = useState<FormErrors>({})
  const [apiError, setApiError] = useState<string | null>(null)

  /** 폼 유효성 검증 */
  function validate(form: FormData): FormErrors {
    const errs: FormErrors = {}

    const name = (form.get("name") as string).trim()
    if (!name) errs.name = "이름을 입력해주세요."

    const sourceId = form.get("source_id") as string
    if (!sourceId || isNaN(Number(sourceId)) || Number(sourceId) <= 0) {
      errs.source_id = "올바른 소싱처 ID를 입력해주세요."
    }

    const brandName = (form.get("brand_name") as string).trim()
    if (!brandName) errs.brand_name = "브랜드명을 입력해주세요."

    const categoryUrl = (form.get("category_url") as string).trim()
    if (!categoryUrl) errs.category_url = "카테고리 URL을 입력해주세요."

    const maxCount = form.get("max_count") as string
    if (!maxCount || isNaN(Number(maxCount)) || Number(maxCount) <= 0) {
      errs.max_count = "올바른 최대 수집 수를 입력해주세요."
    }

    return errs
  }

  /** 폼 제출 핸들러 */
  async function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setApiError(null)

    const form = new FormData(e.currentTarget)
    const errs = validate(form)

    if (Object.keys(errs).length > 0) {
      setErrors(errs)
      return
    }

    setErrors({})
    setIsSubmitting(true)

    const payload: CollectionSettingForm = {
      name: (form.get("name") as string).trim(),
      source_id: Number(form.get("source_id")),
      brand_name: (form.get("brand_name") as string).trim(),
      category_url: (form.get("category_url") as string).trim(),
      max_count: Number(form.get("max_count")),
    }

    try {
      await collectionSettingsApi.create(payload)
      router.push("/sourcing/collection-settings")
    } catch {
      setApiError("수집 설정 생성에 실패했습니다. 다시 시도해주세요.")
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="max-w-lg">
      <h1 className="text-xl font-semibold text-gray-900 mb-6">새 수집 설정 추가</h1>

      {apiError && (
        <div className="mb-4 rounded-md bg-red-50 border border-red-200 px-4 py-3 text-sm text-red-700">
          {apiError}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4 bg-white rounded-lg border border-gray-200 p-5">
        {/* 이름 */}
        <FormField
          label="이름"
          name="name"
          placeholder="예: 무신사 아디다스"
          error={errors.name}
        />

        {/* 소싱처 ID */}
        <FormField
          label="소싱처 ID"
          name="source_id"
          type="number"
          placeholder="예: 1"
          error={errors.source_id}
        />

        {/* 브랜드명 */}
        <FormField
          label="브랜드명"
          name="brand_name"
          placeholder="예: 아디다스"
          error={errors.brand_name}
        />

        {/* 카테고리 URL */}
        <FormField
          label="카테고리 URL"
          name="category_url"
          placeholder="예: https://www.musinsa.com/brands/adidas"
          error={errors.category_url}
        />

        {/* 최대 수집 수 */}
        <FormField
          label="최대 수집 수"
          name="max_count"
          type="number"
          defaultValue="500"
          placeholder="예: 500"
          error={errors.max_count}
        />

        {/* 버튼 */}
        <div className="flex gap-3 pt-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="flex-1 rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isSubmitting ? "저장 중..." : "저장"}
          </button>
          <button
            type="button"
            onClick={() => router.back()}
            className="flex-1 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
          >
            취소
          </button>
        </div>
      </form>
    </div>
  )
}

/** 폼 필드 서브 컴포넌트 */
function FormField({
  label,
  name,
  type = "text",
  placeholder,
  defaultValue,
  error,
}: {
  label: string
  name: string
  type?: string
  placeholder?: string
  defaultValue?: string
  error?: string
}) {
  return (
    <div>
      <label
        htmlFor={name}
        className="block text-sm font-medium text-gray-700 mb-1"
      >
        {label}
      </label>
      <input
        id={name}
        name={name}
        type={type}
        placeholder={placeholder}
        defaultValue={defaultValue}
        className={`block w-full rounded-md border px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          error ? "border-red-400 focus:ring-red-400" : "border-gray-300"
        }`}
      />
      {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
    </div>
  )
}
