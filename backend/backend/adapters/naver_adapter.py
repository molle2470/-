"""네이버 스마트스토어 Commerce API 어댑터.

핵심 설계 결정:
- 토큰 캐싱: expires_in 기반으로 만료 30초 전 갱신
- 이미지: 외부 URL 직접 등록 불가 → /v2/product-images/upload 먼저 업로드
- 수정: GET → 병합 → PUT 패턴 (미포함 필드 초기화 방지)
- 비활성화: SUSPENSION (PROHIBITED는 판매자 설정 불가)

참고: https://apicenter.commerce.naver.com/
"""
import base64
import time
from typing import Any

import bcrypt
import httpx

from backend.adapters.base_adapter import BaseMarketAdapter
from backend.adapters.naver_category_map import get_naver_category_info


class NaverAdapter(BaseMarketAdapter):
    """네이버 스마트스토어 Commerce API 어댑터"""

    BASE_URL = "https://api.commerce.naver.com/external"
    AUTH_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"

    def __init__(self, client_id: str, client_secret: str, channel_id: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.channel_id = channel_id
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self._access_token: str | None = None
        self._token_expires_at: float = 0.0

    async def close(self) -> None:
        """httpx 클라이언트 종료 (라우터 finally 블록에서 호출)"""
        await self.http_client.aclose()

    async def _get_access_token(self) -> str:
        """OAuth2 액세스 토큰 발급 (BCrypt 서명, 만료 30초 전 갱신)."""
        # 캐시된 토큰이 유효하면 재사용
        if self._access_token and time.time() < self._token_expires_at - 30:
            return self._access_token

        timestamp = str(int(time.time() * 1000))
        password = f"{self.client_id}_{timestamp}"
        # client_secret을 BCrypt salt로 사용
        hashed = bcrypt.hashpw(password.encode("utf-8"), self.client_secret.encode("utf-8"))
        client_secret_sign = base64.b64encode(hashed).decode("utf-8")

        response = await self.http_client.post(
            self.AUTH_URL,
            data={
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "timestamp": timestamp,
                "client_secret_sign": client_secret_sign,
                "type": "SELF",
            },
        )
        response.raise_for_status()
        data = response.json()
        self._access_token = str(data["access_token"])
        expires_in = int(data.get("expires_in", 3600))
        self._token_expires_at = time.time() + expires_in
        return self._access_token

    def _get_headers(self, access_token: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def upload_image(self, image_url: str) -> str:
        """외부 이미지 URL을 다운로드 후 네이버 호스팅으로 업로드.

        왜 이렇게 하냐면:
        네이버 API는 "무신사 이미지 주소(URL)"를 직접 받아주지 않는다.
        반드시 이미지 파일 자체를 네이버 서버에 먼저 올려야 상품 등록이 된다.
        그래서 ① 무신사에서 이미지를 다운로드 → ② 네이버에 직접 업로드 두 단계를 거친다.
        """
        # ① 무신사 CDN에서 이미지를 바이너리(파일 데이터)로 다운로드한다.
        # - 왜?: 네이버가 URL이 아닌 실제 파일을 요구하기 때문
        image_response = await self.http_client.get(image_url)
        image_response.raise_for_status()
        image_bytes = image_response.content

        # 이미지 종류(JPG, PNG 등)를 응답 헤더에서 읽어온다.
        # - 왜?: 파일 이름에 올바른 확장자를 붙여야 네이버가 이미지를 제대로 인식함
        content_type = image_response.headers.get("content-type", "image/jpeg")
        ext = content_type.split("/")[-1].split(";")[0].strip() or "jpg"
        filename = f"product.{ext}"

        # ② 네이버 이미지 업로드 API로 파일을 직접 전송한다.
        # - 엔드포인트: v1/product-images/upload (v2는 이 기능 없음 → 404 에러 발생)
        # - 전송 방식: multipart/form-data (파일 첨부 방식, JSON이 아님)
        #   왜?: 네이버 API 공식 문서가 파일 바이너리 전송 방식만 지원하도록 명시되어 있음
        access_token = await self._get_access_token()
        files = {"imageFiles": (filename, image_bytes, content_type)}
        response = await self.http_client.post(
            f"{self.BASE_URL}/v1/product-images/upload",
            headers={"Authorization": f"Bearer {access_token}"},
            files=files,
        )
        response.raise_for_status()
        images = response.json().get("images", [])
        if not images or not images[0].get("url"):
            raise ValueError(f"이미지 업로드 응답에 URL 없음: {response.json()}")
        return str(images[0]["url"])

    def _build_product_info_notice(self, notice_type: str) -> dict[str, Any]:
        """카테고리별 상품정보제공고시 생성."""
        common_notice = {
            "returnCostReason": "제조사 및 수입원에 의한 경우 제조사 또는 수입원에서 부담",
            "noRefundReason": "상품의 하자 또는 오배송의 경우 판매자 귀책으로 반품 배송비 무료",
            "qualityAssuranceStandard": "소비자분쟁해결규정에 따름",
            "compensationProcedure": "소비자분쟁해결규정에 따름",
            "troubleShootingContents": "소비자분쟁해결규정에 따름",
        }
        notice_data: dict[str, Any] = {"productInfoProvidedNoticeType": notice_type}
        type_key = notice_type.lower() if notice_type != "ETC" else "etc"
        notice_data[type_key] = {
            **common_notice,
            **({"material": "상세페이지 참조", "color": "상세페이지 참조", "size": "상세페이지 참조",
                "manufacturer": "상세페이지 참조", "importDeclaration": "상세페이지 참조",
                "caution": "상세페이지 참조", "warrantyPolicy": "소비자분쟁해결규정에 따름",
                "afterServiceDirector": "판매자"} if notice_type != "ETC" else {
                # ETC 타입에 네이버가 필수로 요구하는 3가지 항목
                # - 왜?: 네이버 API가 ETC 카테고리에도 modelName/itemName/manufacturer를
                #   반드시 포함하도록 강제함. 없으면 400 에러 발생
                "modelName": "상세페이지 참조",
                "itemName": "상세페이지 참조",
                "manufacturer": "상세페이지 참조",
            })
        }
        return notice_data

    async def _build_product_payload(
        self, product_data: dict[str, Any], naver_image_url: str
    ) -> dict[str, Any]:
        """상품 데이터 → 네이버 커머스 API v2 등록 payload 변환."""
        category_info = get_naver_category_info(
            str(product_data.get("source_category") or "")
        )
        return_fee = int(product_data.get("return_fee") or 5000)
        as_phone = str(product_data.get("as_phone") or "")
        product_info_notice = self._build_product_info_notice(
            category_info.product_info_notice_type
        )

        return {
            "originProduct": {
                "statusType": "SALE",
                "saleType": "NEW",
                "leafCategoryId": category_info.leaf_category_id,
                "name": str(product_data["name"]),
                "detailContent": f"<p>{product_data['name']}</p>",
                "images": {
                    "representativeImage": {"url": naver_image_url},
                },
                # 판매가는 반드시 10원 단위로 맞춰야 한다.
                # - 왜?: 네이버 규정상 10원 단위 미만이면 400 에러 발생
                # - 예) 155,025원 → 155,020원으로 내림
                "salePrice": (int(product_data["selling_price"]) // 10) * 10,
                "stockQuantity": 999,
                "deliveryInfo": {
                    "deliveryType": "DELIVERY",
                    "deliveryAttributeType": "NORMAL",
                    # 택배사 코드 (네이버 자체 코드 사용)
                    # - 왜?: 네이버는 "CJ대한통운" 같은 한글 이름이 아닌 자체 영문 코드를 요구함
                    # - CJGLS = CJ대한통운, POST = 우체국, HANJIN = 한진택배
                    "deliveryCompany": "CJGLS",
                    "deliveryFee": {"deliveryFeeType": "FREE"},
                    "claimDeliveryInfo": {
                        "returnDeliveryFee": return_fee,
                        "exchangeDeliveryFee": return_fee,
                    },
                },
                "detailAttribute": {
                    "afterServiceInfo": {
                        "afterServiceTelephoneNumber": as_phone,
                        "afterServiceGuideContent": "소비자분쟁해결기준에 의거 교환 및 환불",
                    },
                    "originAreaInfo": {
                        "originAreaCode": "0200037",
                        "content": "",
                        # 수입자 정보 (해외구매대행 필수 항목)
                        # - 왜?: 원산지가 해외(0200037=기타국가)면 수입자를 반드시 기재해야 함
                        "importer": "상세페이지 참조",
                    },
                    "productInfoProvidedNotice": product_info_notice,
                    # 미성년자 구매 가능 여부 (네이버 필수 항목)
                    # - 왜?: 없으면 400 에러 발생. 의류/신발은 미성년자도 구매 가능하므로 True
                    "minorPurchasable": True,
                },
            },
            "smartstoreChannelProduct": {
                "naverShoppingRegistration": True,
                "channelProductDisplayStatusType": "ON",
            },
        }

    async def register_product(self, product_data: dict[str, Any]) -> str | None:
        """이미지 업로드 후 상품 등록 → originProductNo 반환."""
        thumbnail_url = str(product_data.get("thumbnail_url") or "")
        naver_image_url = await self.upload_image(thumbnail_url)

        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        payload = await self._build_product_payload(product_data, naver_image_url)

        response = await self.http_client.post(
            f"{self.BASE_URL}/v2/products",
            headers=headers,
            json=payload,
        )

        # 에러 시 네이버가 보내준 상세 메시지를 같이 출력한다.
        # - 왜?: 400/401 같은 에러만 보면 뭐가 문제인지 모름.
        #   네이버는 에러 원인을 JSON으로 함께 보내주므로 그걸 꺼내야 디버깅 가능.
        if not response.is_success:
            raise ValueError(
                f"네이버 상품 등록 실패 ({response.status_code}): {response.text}"
            )

        origin_no = response.json().get("originProductNo")
        return str(origin_no) if origin_no else None

    async def _get_product(self, market_product_id: str) -> dict[str, Any]:
        """기존 상품 전체 데이터 조회 (수정 시 필드 병합용)"""
        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.get(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
        )
        response.raise_for_status()
        return dict(response.json())

    async def update_price(self, market_product_id: str, new_price: int) -> bool:
        """가격 수정 — GET → 병합 → PUT"""
        existing = await self._get_product(market_product_id)
        existing.setdefault("originProduct", {})["salePrice"] = new_price

        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.put(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
            json=existing,
        )
        response.raise_for_status()
        return True

    async def update_stock(self, market_product_id: str, in_stock: bool) -> bool:
        """재고/품절 처리 — GET → 병합 → PUT"""
        existing = await self._get_product(market_product_id)
        # 품절 시 SUSPENSION 사용 (PROHIBITED는 판매자 설정 불가)
        status = "SALE" if in_stock else "SUSPENSION"
        existing.setdefault("originProduct", {})["statusType"] = status

        access_token = await self._get_access_token()
        headers = self._get_headers(access_token)
        response = await self.http_client.put(
            f"{self.BASE_URL}/v2/products/{market_product_id}",
            headers=headers,
            json=existing,
        )
        response.raise_for_status()
        return True

    async def deactivate_product(self, market_product_id: str) -> bool:
        """상품 비활성화 — SUSPENSION 사용 (PROHIBITED는 판매자 설정 불가)"""
        return await self.update_stock(market_product_id, in_stock=False)
