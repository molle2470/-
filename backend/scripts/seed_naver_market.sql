-- =========================================================
-- 네이버 스마트스토어 마켓 등록 초기 데이터 (Seed SQL)
-- =========================================================
-- 실행 순서: common_templates → markets → market_accounts → market_templates
-- 주의: 이미 데이터가 존재할 경우 ON CONFLICT 절로 중복 삽입을 방지합니다.
-- 주의: common_templates, market_accounts는 unique constraint가 없어
--       ON CONFLICT DO NOTHING이 동작하지 않으므로 아래 가이드를 참고하세요.
--       → 스크립트를 두 번 이상 실행하기 전에 기존 데이터 여부를 먼저 확인하세요.
--       예: SELECT * FROM common_templates; SELECT * FROM market_accounts;
-- =========================================================

-- 1. 사업자 그룹 (BusinessGroup)
--    무재고 구매대행 사업자 1개 그룹 추가
INSERT INTO business_groups (name, created_at)
VALUES ('사업자1', NOW())
ON CONFLICT DO NOTHING;

-- 2. 공통 템플릿 (CommonTemplate)
--    - A/S 전화번호 필수 항목
--    - origin_country 기본값: '기타' (한글 인코딩 주의 — DB 클라이언트에서 UTF-8 확인 후 실행)
INSERT INTO common_templates (
  shipping_origin,
  return_address,
  courier,
  as_phone,
  as_description,
  origin_country,
  kc_cert_info,
  updated_at
)
VALUES (
  '서울시 강남구 테헤란로 123',       -- 출고지
  '서울시 강남구 테헤란로 123',       -- 반품/교환지 (출고지와 동일)
  'CJ대한통운',                        -- 택배사
  '02-1234-5678',                      -- A/S 전화번호 (필수)
  '제품 이상 시 고객센터로 연락 바랍니다. A/S 가능 기간: 구매일로부터 1년',
  '기타',                              -- 원산지 (해외 구매대행)
  NULL,                                -- KC인증 (해당 없음)
  NOW()
);

-- 3. 네이버 스마트스토어 마켓 (Market)
INSERT INTO markets (name, header_image_url, footer_image_url, created_at)
VALUES (
  '네이버 스마트스토어',
  NULL,   -- 헤더 이미지 (선택)
  NULL,   -- 푸터 이미지 (선택)
  NOW()
)
ON CONFLICT (name) DO NOTHING;

-- 4. 마켓 계정 (MarketAccount)
--    - business_group_id, market_id는 위 INSERT 결과 ID를 사용
--    - account_id: 스마트스토어 판매자 ID
INSERT INTO market_accounts (
  business_group_id,
  market_id,
  account_id,
  api_credentials,
  is_active,
  created_at,
  updated_at
)
VALUES (
  (SELECT id FROM business_groups WHERE name = '사업자1' LIMIT 1),
  (SELECT id FROM markets WHERE name = '네이버 스마트스토어' LIMIT 1),
  'my_smartstore_id',                  -- 실제 스마트스토어 판매자 ID로 교체
  NULL,                                -- API 자격증명 (암호화 저장 권장)
  true,
  NOW(),
  NOW()
);

-- 5. 마켓별 템플릿 (MarketTemplate)
--    - 네이버 스마트스토어 수수료율: 약 5.85% (카테고리별 상이 — 실제 값으로 교체)
--    - 마진율: 20% (0.20)
--    - 배송비: 0원 (무료배송)
--    - 반품 배송비: 5,000원
--    - 제주/도서산간 추가 배송비: 5,000원
--    - 상품명 최대 길이: 100자 (스마트스토어 기준)
INSERT INTO market_templates (
  market_id,
  common_template_id,
  commission_rate,
  margin_rate,
  shipping_fee,
  jeju_extra_fee,
  island_extra_fee,
  return_fee,
  product_name_max_length,
  discount_rate,
  market_specific_config,
  product_info_notice_template,
  shipping_origin_override,
  return_address_override,
  updated_at
)
VALUES (
  (SELECT id FROM markets WHERE name = '네이버 스마트스토어' LIMIT 1),
  (SELECT id FROM common_templates ORDER BY id DESC LIMIT 1),
  0.0585,   -- 수수료율 5.85% (카테고리별 다를 수 있음 — 실제 계약 기준으로 교체)
  0.20,     -- 마진율 20%
  0,        -- 배송비 0원 (무료배송)
  5000,     -- 제주 추가 배송비 5,000원
  5000,     -- 도서산간 추가 배송비 5,000원
  5000,     -- 반품 배송비 5,000원
  100,      -- 상품명 최대 100자
  0.0,      -- 할인율 (기본 0%)
  NULL,     -- 마켓별 추가 설정 (JSON)
  NULL,     -- 상품정보제공고시 템플릿 (JSON)
  NULL,     -- 출고지 오버라이드 (NULL이면 공통 템플릿 값 사용)
  NULL,     -- 반품지 오버라이드 (NULL이면 공통 템플릿 값 사용)
  NOW()
);

-- 6. (선택) SEO 규칙 (SeoRule)
--    네이버 스마트스토어 기준 SEO 패턴
INSERT INTO seo_rules (
  market_id,
  tag_pattern,
  title_pattern,
  meta_description_pattern,
  keyword_rules,
  updated_at
)
VALUES (
  (SELECT id FROM markets WHERE name = '네이버 스마트스토어' LIMIT 1),
  '{brand} {product_name} {category}',           -- 태그 패턴
  '{brand} {product_name}',                      -- 제목 패턴
  '{product_name} | {brand} 공식 스토어',        -- 메타 설명 패턴
  '{"max_tags": 10, "min_keyword_length": 2}',  -- 키워드 규칙 (JSON)
  NOW()
)
ON CONFLICT DO NOTHING;

-- =========================================================
-- 확인 쿼리 (실행 후 결과 검증용)
-- =========================================================
-- SELECT * FROM business_groups;
-- SELECT * FROM common_templates;
-- SELECT * FROM markets;
-- SELECT * FROM market_accounts;
-- SELECT * FROM market_templates;
-- SELECT * FROM seo_rules;
