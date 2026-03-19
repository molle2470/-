"""네이버 스마트스토어 Commerce API 어댑터.

네이버 커머스 API를 통한 상품 등록/수정/품절 처리.
실제 인증키 없이 스텁 구현으로 제공되며, TODO 주석으로 실제 구현 위치를 표시합니다.

참고: https://apicenter.commerce.naver.com/
"""
import base64
from typing import Dict, Optional

import httpx

from backend.adapters.base_adapter import BaseMarketAdapter


class NaverAdapter(BaseMarketAdapter):
    """네이버 스마트스토어 Commerce API 어댑터

    네이버 커머스 API OAuth2 인증 기반으로 상품을 관리합니다.
    현재는 스텁 구현이며, 실제 API 연동 시 TODO 항목을 구현해야 합니다.
    """

    # 네이버 커머스 API 기본 URL
    BASE_URL = "https://api.commerce.naver.com/external"
    AUTH_URL = "https://api.commerce.naver.com/external/v1/oauth2/token"

    def __init__(self, client_id: str, client_secret: str, channel_id: str) -> None:
        """NaverAdapter 초기화

        Args:
            client_id: 네이버 커머스 API 클라이언트 ID
            client_secret: 네이버 커머스 API 클라이언트 시크릿
            channel_id: 스마트스토어 채널 ID
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.channel_id = channel_id
        # httpx 비동기 클라이언트
        self.http_client = httpx.AsyncClient(timeout=30.0)

    async def _get_access_token(self) -> str:
        """OAuth2 액세스 토큰 취득 (스텁)

        TODO: 네이버 커머스 API OAuth2 토큰 발급 구현
        - POST {AUTH_URL}
        - grant_type=client_credentials
        - client_id, client_secret_sign (HMAC-SHA256 서명) 전달
        - 응답에서 access_token 추출
        """
        raise NotImplementedError(
            "TODO: 네이버 커머스 OAuth2 토큰 발급 구현 필요. "
            "client_id와 client_secret으로 HMAC-SHA256 서명 후 토큰 요청."
        )

    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Authorization 헤더 반환

        Args:
            access_token: OAuth2 액세스 토큰

        Returns:
            API 요청에 필요한 HTTP 헤더 딕셔너리
        """
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    async def register_product(self, product_data: Dict[str, object]) -> Optional[str]:
        """상품 등록 (스텁)

        TODO: 네이버 스마트스토어 상품 등록 API 구현
        - POST /v2/products
        - product_data를 네이버 상품 스펙으로 변환 후 전송
        - 응답에서 originProductNo 추출하여 반환

        Args:
            product_data: 상품 등록 데이터

        Returns:
            마켓 상품 ID (originProductNo)
        """
        raise NotImplementedError(
            "TODO: 네이버 스마트스토어 상품 등록 API 구현 필요. "
            "POST /v2/products 호출 후 originProductNo 반환."
        )

    async def update_price(self, market_product_id: str, new_price: int) -> bool:
        """가격 수정 (스텁)

        TODO: 네이버 스마트스토어 가격 수정 API 구현
        - PUT /v2/products/{originProductNo}
        - salePrice 필드만 업데이트

        Args:
            market_product_id: 네이버 마켓 상품 ID (originProductNo)
            new_price: 새로운 판매가 (원)

        Returns:
            성공 여부
        """
        raise NotImplementedError(
            "TODO: 네이버 스마트스토어 가격 수정 API 구현 필요. "
            f"PUT /v2/products/{market_product_id} 호출."
        )

    async def update_stock(self, market_product_id: str, in_stock: bool) -> bool:
        """재고/품절 처리 (스텁)

        TODO: 네이버 스마트스토어 재고 처리 API 구현
        - PUT /v2/products/{originProductNo}
        - in_stock=False: stockQuantity=0, saleStatusType="SUSPENSION"
        - in_stock=True: saleStatusType="SALE" 로 변경

        Args:
            market_product_id: 네이버 마켓 상품 ID
            in_stock: True=재활성화, False=품절 처리

        Returns:
            성공 여부
        """
        raise NotImplementedError(
            "TODO: 네이버 스마트스토어 재고/품절 처리 API 구현 필요. "
            f"PUT /v2/products/{market_product_id} 호출, saleStatusType 변경."
        )

    async def deactivate_product(self, market_product_id: str) -> bool:
        """상품 비활성화 (스텁)

        TODO: 네이버 스마트스토어 상품 비활성화 API 구현
        - PUT /v2/products/{originProductNo}
        - saleStatusType="PROHIBITED" 또는 판매중지 처리

        Args:
            market_product_id: 네이버 마켓 상품 ID

        Returns:
            성공 여부
        """
        raise NotImplementedError(
            "TODO: 네이버 스마트스토어 상품 비활성화 API 구현 필요. "
            f"PUT /v2/products/{market_product_id} 호출, saleStatusType='PROHIBITED'."
        )
