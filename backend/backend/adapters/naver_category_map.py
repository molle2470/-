"""무신사 소싱 카테고리 → 네이버 스마트스토어 leafCategoryId + productInfoProvidedNotice 유형 매핑.

네이버 상품정보제공고시 유형 목록 (주요):
  - "WEAR": 의류 (상의/하의/아우터 등)
  - "SHOES": 신발
  - "BAG": 가방
  - "ACCESSORY": 패션잡화 (모자/벨트/지갑 등)
  - "ETC": 기타

카테고리 ID 검증 필요 URL:
  GET https://api.commerce.naver.com/external/v1/categories/{categoryId}
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class NaverCategoryInfo:
    """네이버 카테고리 매핑 정보"""
    leaf_category_id: str
    product_info_notice_type: str  # productInfoProvidedNoticeType 값


# 무신사 source_category 키워드 → 네이버 매핑 정보
# 키: 무신사 카테고리 문자열에 포함되는 키워드
# 순서 중요: 더 구체적인 키워드를 앞에 배치
MUSINSA_TO_NAVER: dict[str, NaverCategoryInfo] = {
    # 신발
    "스니커즈": NaverCategoryInfo("50000803", "SHOES"),
    "로퍼": NaverCategoryInfo("50000800", "SHOES"),
    "부츠": NaverCategoryInfo("50000797", "SHOES"),
    "샌들": NaverCategoryInfo("50000801", "SHOES"),
    "슬리퍼": NaverCategoryInfo("50000802", "SHOES"),
    "구두": NaverCategoryInfo("50000798", "SHOES"),
    # 가방
    "백팩": NaverCategoryInfo("50000148", "BAG"),
    "숄더백": NaverCategoryInfo("50000150", "BAG"),
    "토트백": NaverCategoryInfo("50000151", "BAG"),
    "크로스백": NaverCategoryInfo("50000149", "BAG"),
    # 상의
    "후드티": NaverCategoryInfo("50000042", "WEAR"),
    "맨투맨": NaverCategoryInfo("50000040", "WEAR"),
    "티셔츠": NaverCategoryInfo("50000039", "WEAR"),
    "셔츠": NaverCategoryInfo("50000038", "WEAR"),
    "니트": NaverCategoryInfo("50000043", "WEAR"),
    # 아우터
    "패딩": NaverCategoryInfo("50000022", "WEAR"),
    "코트": NaverCategoryInfo("50000021", "WEAR"),
    "자켓": NaverCategoryInfo("50000020", "WEAR"),
    "바람막이": NaverCategoryInfo("50000026", "WEAR"),
    # 하의
    "청바지": NaverCategoryInfo("50000050", "WEAR"),
    "슬랙스": NaverCategoryInfo("50000053", "WEAR"),
    "반바지": NaverCategoryInfo("50000055", "WEAR"),
    # 패션잡화
    "모자": NaverCategoryInfo("50000153", "ACCESSORY"),
    "양말": NaverCategoryInfo("50000161", "ACCESSORY"),
    "벨트": NaverCategoryInfo("50000157", "ACCESSORY"),
}

# 매핑 안 될 때 기본값 (패션잡화 > 기타 액세서리 카테고리, ETC 고시 유형)
# 주의: 50000803은 스니커즈 카테고리이므로 기본값으로 사용 불가.
# 50000803 대신 패션잡화 > 기타 카테고리 ID로 교체 필요.
# TODO: 네이버 카테고리 API로 실제 "패션잡화 > 기타" leafCategoryId 확인 후 업데이트
DEFAULT_NAVER_INFO = NaverCategoryInfo("50000166", "ETC")


def get_naver_category_info(source_category: str | None) -> NaverCategoryInfo:
    """무신사 카테고리 문자열에서 네이버 카테고리 정보 반환.

    source_category 내 키워드 부분 매칭으로 찾고, 없으면 기본값(스니커즈/ETC) 반환.
    """
    if not source_category:
        return DEFAULT_NAVER_INFO

    for keyword, info in MUSINSA_TO_NAVER.items():
        if keyword in source_category:
            return info

    return DEFAULT_NAVER_INFO
