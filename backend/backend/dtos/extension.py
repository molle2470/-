"""익스텐션 통신 DTO."""
from typing import List, Optional
from pydantic import BaseModel, Field


class ProductOptionData(BaseModel):
    """상품 옵션 (색상×사이즈)"""
    color: Optional[str] = None
    size: Optional[str] = None
    stock: int = 0


class ExtensionProductData(BaseModel):
    """익스텐션에서 전송하는 수집 상품 데이터"""
    name: str
    original_price: int
    source_url: str
    source_product_id: str
    brand_name: str
    stock_status: str = "in_stock"
    grade_discount_available: bool = True
    point_usable: bool = True
    point_earnable: bool = True
    thumbnail_url: Optional[str] = None
    image_urls: List[str] = Field(default_factory=list)
    options: List[ProductOptionData] = Field(default_factory=list)


class ExtensionProductRequest(BaseModel):
    """POST /api/v1/extension/products 요청"""
    source: str = "musinsa"
    product: ExtensionProductData


class ProductChangeRequest(BaseModel):
    """POST /api/v1/extension/products/{id}/changes 요청"""
    change_type: str  # "price" | "stock" | "both"
    old_price: Optional[int] = None
    new_price: Optional[int] = None
    stock_status: Optional[str] = None


class CommandAckRequest(BaseModel):
    """명령 처리 완료 보고"""
    status: str = "done"  # "done" | "failed"
    message: Optional[str] = None


class HeartbeatRequest(BaseModel):
    """익스텐션 생존 신호"""
    monitoring_count: int = 0
    extension_version: str = "1.0.0"
