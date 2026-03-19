"""APScheduler 기반 스마트 주기 모니터링 스케줄러.

등록된 상품의 가격/재고를 주기적으로 모니터링하여 변동 감지 시 마켓에 자동 반영.
- 인기 상품(HIGH 등급): 10-15분 ± 2분 랜덤 → 480~1020초
- 일반 상품(NORMAL 등급): 30-60분 ± 5분 랜덤 → 1500~3900초
- 크롤링 실패 시: 자동 재시도 3회 → 품절 처리
"""
import logging
import random
from typing import TYPE_CHECKING, Callable

from apscheduler.jobstores.base import JobLookupError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from backend.domain.product.model import StockStatusEnum
from backend.domain.product.repository import ProductRepository
from backend.services.market_sync import MarketSyncService

if TYPE_CHECKING:
  from backend.domain.crawling.base_crawler import BaseCrawler
  from backend.adapters.base_adapter import BaseMarketAdapter

logger = logging.getLogger(__name__)

# 등급별 주기 설정 (초 단위)
_HIGH_MIN_SECONDS = 10 * 60 - 2 * 60   # 480초
_HIGH_MAX_SECONDS = 15 * 60 + 2 * 60   # 1020초
_NORMAL_MIN_SECONDS = 30 * 60 - 5 * 60  # 1500초
_NORMAL_MAX_SECONDS = 60 * 60 + 5 * 60  # 3900초

# 크롤링 실패 시 최대 재시도 횟수
_MAX_RETRIES = 3

# Phase 2에서 MarketTemplate DB 연동 예정 - 현재는 기본값 사용
_DEFAULT_COMMISSION_RATE = 0.05
_DEFAULT_MARGIN_RATE = 0.20


class MonitoringGradeEnum(str):
  """모니터링 등급 열거형."""

  HIGH = "high"
  NORMAL = "normal"


class MonitoringScheduler:
  """APScheduler 기반 상품 모니터링 스케줄러.

  등록된 상품의 가격/재고를 등급별 주기로 자동 모니터링하며
  변동 감지 시 마켓에 즉시 반영합니다.
  """

  def __init__(
    self,
    session_factory: Callable,
    crawler: "BaseCrawler",
    sync_adapter: "BaseMarketAdapter",
  ) -> None:
    """
    Args:
        session_factory: DB 쓰기 세션 팩토리 (context manager 반환)
        crawler: BaseCrawler 구현체 (check_product 메서드 필요)
        sync_adapter: BaseMarketAdapter 구현체
    """
    self.session_factory = session_factory
    self.crawler = crawler
    self.sync_adapter = sync_adapter
    self.scheduler = AsyncIOScheduler()
    self._running = False

  def start(self) -> None:
    """스케줄러 시작"""
    self.scheduler.start()
    self._running = True
    logger.info("모니터링 스케줄러 시작됨")

  def stop(self) -> None:
    """스케줄러 종료"""
    self.scheduler.shutdown(wait=False)
    self._running = False
    logger.info("모니터링 스케줄러 종료됨")

  async def monitor_product(self, product_id: int, source_url: str) -> None:
    """단일 상품 모니터링 (크롤링 → 변동 감지 → 마켓 반영).

    Args:
        product_id: 모니터링할 상품 ID
        source_url: 소싱처 상품 URL
    """
    # 크롤링 시도 (최대 3회 재시도)
    result = None
    for attempt in range(_MAX_RETRIES):
      result = await self.crawler.check_product(source_url)
      if result is not None:
        break
      logger.warning(
        f"상품 크롤링 실패 (시도 {attempt + 1}/{_MAX_RETRIES}): product_id={product_id}"
      )

    async with self.session_factory() as session:
      repo = ProductRepository(session)
      product = await repo.get_async(product_id)
      if not product:
        logger.warning(f"상품 조회 실패: product_id={product_id}")
        return

      # 크롤링 결과에 따른 재고 상태 결정
      if result is None:
        # 3회 모두 실패 → 품절 처리
        new_status = StockStatusEnum.OUT_OF_STOCK
        logger.warning(
          f"크롤링 {_MAX_RETRIES}회 실패 → 품절 처리: product_id={product_id}"
        )
      else:
        new_status = (
          StockStatusEnum.IN_STOCK
          if result.stock_status == "in_stock"
          else StockStatusEnum.OUT_OF_STOCK
        )

      sync = MarketSyncService(session, self.sync_adapter)

      # 가격 변동 감지 및 마켓 반영
      if result is not None and result.original_price != product.original_price:
        logger.info(
          f"가격 변동 감지: product_id={product_id}, "
          f"{product.original_price}원 → {result.original_price}원"
        )
        # TODO: Phase 2에서 MarketTemplate DB에서 commission_rate, margin_rate 조회 예정
        await sync.sync_price_change(
          product_id=product_id,
          new_price=result.original_price,
          commission_rate=_DEFAULT_COMMISSION_RATE,
          margin_rate=_DEFAULT_MARGIN_RATE,
        )
        # DB 가격 업데이트
        product.original_price = result.original_price
        await session.commit()

      # 재고 변동 감지 및 마켓 반영
      if new_status != product.stock_status:
        logger.info(
          f"재고 변동 감지: product_id={product_id}, "
          f"{product.stock_status} → {new_status}"
        )
        await sync.sync_stock_change(
          product_id=product_id,
          in_stock=(new_status == StockStatusEnum.IN_STOCK),
        )
        # DB 재고 상태 업데이트
        product.stock_status = new_status
        await session.commit()

  def schedule_product(
    self,
    product_id: int,
    source_url: str,
    grade: MonitoringGradeEnum,
  ) -> None:
    """상품 모니터링 스케줄 등록.

    Args:
        product_id: 상품 ID
        source_url: 소싱처 상품 URL
        grade: 모니터링 등급 ("high" | "normal")
    """
    interval_seconds = self._get_interval_seconds(grade)
    job_id = f"product_{product_id}"

    self.scheduler.add_job(
      self.monitor_product,
      trigger=IntervalTrigger(seconds=interval_seconds),
      args=[product_id, source_url],
      id=job_id,
      replace_existing=True,
    )
    logger.info(
      f"상품 모니터링 등록: product_id={product_id}, "
      f"grade={grade}, interval={interval_seconds}초"
    )

  def unschedule_product(self, product_id: int) -> None:
    """상품 모니터링 스케줄 제거.

    Args:
        product_id: 제거할 상품 ID
    """
    job_id = f"product_{product_id}"
    try:
      self.scheduler.remove_job(job_id)
      logger.info(f"상품 모니터링 제거: product_id={product_id}")
    except JobLookupError:
      # 이미 제거된 잡이거나 등록된 적 없는 경우 경고만 출력
      logger.warning(f"제거할 스케줄 없음 (이미 제거되었거나 미등록): product_id={product_id}")

  def _get_interval_seconds(self, grade: MonitoringGradeEnum) -> int:
    """등급별 모니터링 주기 계산 (랜덤 범위 포함).

    Args:
        grade: 모니터링 등급 ("high" | "normal")

    Returns:
        모니터링 주기 (초)
        - HIGH: 480~1020초 (10분±2분 ~ 15분±2분)
        - NORMAL: 1500~3900초 (30분±5분 ~ 60분±5분)
    """
    if grade == "high":
      return random.randint(_HIGH_MIN_SECONDS, _HIGH_MAX_SECONDS)
    else:
      # normal 또는 알 수 없는 등급 → NORMAL 범위 적용
      return random.randint(_NORMAL_MIN_SECONDS, _NORMAL_MAX_SECONDS)
