# Phase 7: ClickHouse Implementation + Comprehensive Test Suite

## 🎯 Overview

This document outlines the complete implementation plan for Phase 7, which includes:
1. **ClickHouse Analytics Integration** - Production-ready analytics database
2. **Comprehensive Test Suite** - 60+ tests for all Phase 1-6 features
3. **Error Detection & Fixes** - Validation and bug fixes

---

## 📦 Part 1: ClickHouse Implementation

### 1.1 Analytics Module (`src/analytics/clickhouse_analytics.py`)

**Features:**
- Async ClickHouse client wrapper
- Connection pooling
- Query builder helpers
- Data migration utilities
- ETL pipeline management

**Key Classes:**
```python
class ClickHouseAnalytics:
    """Main analytics interface."""
    - async def insert_trade(trade_data)
    - async def insert_price_snapshot(prices)
    - async def get_trading_history(filters)
    - async def calculate_strategy_performance()
    - async def get_price_trends(item_name, days)

class ClickHouseETL:
    """ETL pipeline for PostgreSQL → ClickHouse sync."""
    - async def sync_trades()
    - async def sync_prices()
    - async def sync_user_events()
```

### 1.2 Docker Configuration

**Update `docker-compose.yml`:**
```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    container_name: dmarket_clickhouse
    ports:
      - "8123:8123"  # HTTP
      - "9000:9000"  # Native TCP
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./scripts/clickhouse_init.sql:/docker-entrypoint-initdb.d/init.sql
    environment:
      CLICKHOUSE_DB: dmarket_analytics
      CLICKHOUSE_USER: ${CLICKHOUSE_USER:-analytics}
      CLICKHOUSE_PASSWORD: ${CLICKHOUSE_PASSWORD}
    networks:
      - bot-network
    healthcheck:
      test: ["CMD", "clickhouse-client", "--query", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  clickhouse_data:
```

### 1.3 Database Schemas (`scripts/clickhouse_init.sql`)

**Tables:**

```sql
-- Trading history table (append-only, optimized for time-series)
CREATE TABLE IF NOT EXISTS trades (
    trade_id String,
    user_id UInt64,
    item_name String,
    game String,
    buy_price Decimal(10, 2),
    sell_price Decimal(10, 2),
    profit Decimal(10, 2),
    profit_percent Decimal(6, 2),
    strategy Enum8('dmarket_only', 'cross_platform', 'hold_waxpeer'),
    platform_buy Enum8('dmarket', 'waxpeer', 'steam'),
    platform_sell Enum8('dmarket', 'waxpeer', 'steam'),
    trade_time DateTime,
    execution_time_ms UInt32,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(trade_time)
ORDER BY (trade_time, user_id, game)
TTL trade_time + INTERVAL 2 YEAR;  -- Auto-delete after 2 years

-- Price snapshots table (high-frequency inserts)
CREATE TABLE IF NOT EXISTS price_snapshots (
    item_name String,
    game String,
    platform Enum8('dmarket', 'waxpeer', 'steam'),
    price Decimal(10, 2),
    liquidity_score UInt8,
    snapshot_time DateTime,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(snapshot_time)
ORDER BY (snapshot_time, game, platform, item_name)
TTL snapshot_time + INTERVAL 6 MONTH;

-- Arbitrage opportunities log
CREATE TABLE IF NOT EXISTS arbitrage_opportunities (
    opportunity_id String,
    item_name String,
    game String,
    buy_platform String,
    sell_platform String,
    buy_price Decimal(10, 2),
    sell_price Decimal(10, 2),
    expected_profit Decimal(10, 2),
    expected_roi Decimal(6, 2),
    liquidity_score UInt8,
    was_executed Boolean,
    found_at DateTime,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(found_at)
ORDER BY (found_at, game, expected_roi DESC);

-- User activity events
CREATE TABLE IF NOT EXISTS user_events (
    event_id String,
    user_id UInt64,
    event_type Enum8('command', 'scan', 'trade', 'notification'),
    event_data String,  -- JSON
    event_time DateTime,
    created_at DateTime DEFAULT now()
) ENGINE = MergeTree()
PARTITION BY toYYYYMM(event_time)
ORDER BY (event_time, user_id, event_type)
TTL event_time + INTERVAL 1 YEAR;

-- Materialized view for fast daily stats
CREATE MATERIALIZED VIEW IF NOT EXISTS daily_stats_mv
ENGINE = SummingMergeTree()
PARTITION BY toYYYYMM(trade_date)
ORDER BY (trade_date, user_id, strategy)
AS SELECT
    toDate(trade_time) as trade_date,
    user_id,
    strategy,
    count() as total_trades,
    sum(profit) as total_profit,
    avg(profit_percent) as avg_roi,
    max(profit) as max_profit
FROM trades
GROUP BY trade_date, user_id, strategy;
```

### 1.4 ETL Pipeline (`src/analytics/clickhouse_etl.py`)

**Sync Strategy:**
- **Initial**: Full historical data migration
- **Incremental**: Every 5-10 minutes, sync new records
- **Retry Logic**: Exponential backoff on failures

**Implementation:**
```python
class ClickHouseETL:
    async def sync_all(self, since: datetime | None = None):
        """Sync all data from PostgreSQL to ClickHouse."""
        await asyncio.gather(
            self.sync_trades(since),
            self.sync_prices(since),
            self.sync_opportunities(since),
            self.sync_user_events(since),
        )
    
    async def continuous_sync(self, interval_seconds: int = 300):
        """Continuous sync loop every 5 minutes."""
        while True:
            try:
                last_sync = await self.get_last_sync_time()
                await self.sync_all(since=last_sync)
                logger.info("clickhouse_sync_success")
            except Exception as e:
                logger.error("clickhouse_sync_failed", error=str(e))
            await asyncio.sleep(interval_seconds)
```

### 1.5 Query Helpers

**Common Analytics Queries:**

```python
class ClickHouseQueries:
    @staticmethod
    async def get_trading_history(
        client: ClickHouseClient,
        user_id: int,
        days: int = 30
    ) -> list[dict]:
        """Get user trading history with performance metrics."""
        return await client.execute("""
            SELECT
                toStartOfDay(trade_time) as day,
                strategy,
                count() as trades,
                sum(profit) as profit,
                avg(profit_percent) as avg_roi,
                max(profit) as best_trade
            FROM trades
            WHERE user_id = {user_id}
              AND trade_time >= now() - INTERVAL {days} DAY
            GROUP BY day, strategy
            ORDER BY day DESC
        """, {"user_id": user_id, "days": days})
    
    @staticmethod
    async def get_price_trends(
        client: ClickHouseClient,
        item_name: str,
        game: str,
        days: int = 7
    ) -> dict[str, list[dict]]:
        """Get price trends across all platforms."""
        return await client.execute("""
            SELECT
                platform,
                toStartOfHour(snapshot_time) as hour,
                avg(price) as avg_price,
                min(price) as min_price,
                max(price) as max_price,
                avg(liquidity_score) as avg_liquidity
            FROM price_snapshots
            WHERE item_name = {item_name}
              AND game = {game}
              AND snapshot_time >= now() - INTERVAL {days} DAY
            GROUP BY platform, hour
            ORDER BY platform, hour
        """, {"item_name": item_name, "game": game, "days": days})
```

---

## 🧪 Part 2: Comprehensive Test Suite

### 2.1 Unit Tests: n8n Integration

**File:** `tests/unit/api/test_n8n_integration.py`

**Tests (10):**
1. `test_arbitrage_webhook_accepts_valid_alert()`
2. `test_arbitrage_webhook_rejects_invalid_alert()`
3. `test_daily_stats_endpoint_returns_correct_format()`
4. `test_create_target_validates_price()`
5. `test_health_check_returns_ok()`
6. `test_prices_dmarket_endpoint_returns_items()`
7. `test_prices_waxpeer_converts_mils_to_usd()`
8. `test_prices_steam_handles_missing_data()`
9. `test_listing_targets_returns_auto_updating_list()`
10. `test_update_target_recalculates_expected_profit()`

### 2.2 Unit Tests: Integrated Arbitrage Scanner

**File:** `tests/unit/dmarket/test_integrated_arbitrage_scanner.py`

**Tests (15):**
1. `test_scanner_initialization_with_all_apis()`
2. `test_scan_multi_platform_returns_opportunities()`
3. `test_liquidity_scoring_calculation()`
4. `test_profit_calculation_with_commissions()`
5. `test_create_waxpeer_listing_target()`
6. `test_update_listing_targets_recalculates_prices()`
7. `test_target_price_formula_with_markup()`
8. `test_get_listing_recommendations_filters_by_roi()`
9. `test_scan_dmarket_only_finds_internal_arbitrage()`
10. `test_scan_all_strategies_returns_both_types()`
11. `test_decide_sell_strategy_chooses_waxpeer_for_high_roi()`
12. `test_decide_sell_strategy_chooses_dmarket_for_quick_profit()`
13. `test_decide_sell_strategy_waits_for_low_roi()`
14. `test_statistics_tracking()`
15. `test_error_handling_on_api_failure()`

### 2.3 Unit Tests: Prompt Engineering

**File:** `tests/unit/ai/test_prompt_engineering_integration.py`

**Tests (12):**
1. `test_prompt_engineer_initialization()`
2. `test_xml_tagged_prompt_structure()`
3. `test_role_based_prompting_trading_advisor()`
4. `test_role_based_prompting_market_analyst()`
5. `test_chain_of_thought_reasoning()`
6. `test_few_shot_examples_formatting()`
7. `test_hallucination_prevention_with_sources()`
8. `test_pre_filled_json_responses()`
9. `test_explain_arbitrage_generates_educational_content()`
10. `test_generate_market_insights_with_analysis()`
11. `test_fallback_method_without_api_key()`
12. `test_user_level_adaptation()`

### 2.4 Unit Tests: ClickHouse Analytics

**File:** `tests/unit/analytics/test_clickhouse_analytics.py`

**Tests (10):**
1. `test_clickhouse_client_connection()`
2. `test_insert_trade_record()`
3. `test_insert_price_snapshot()`
4. `test_get_trading_history_query()`
5. `test_calculate_strategy_performance()`
6. `test_get_price_trends()`
7. `test_etl_sync_trades()`
8. `test_etl_incremental_sync()`
9. `test_query_performance_benchmark()`
10. `test_error_handling_on_connection_failure()`

### 2.5 Integration Tests: Workflows

**File:** `tests/integration/test_n8n_workflows.py`

**Tests (8):**
1. `test_daily_report_workflow_end_to_end()`
2. `test_multi_platform_monitor_workflow()`
3. `test_arbitrage_opportunity_detection_flow()`
4. `test_listing_target_creation_and_update_flow()`
5. `test_dual_strategy_workflow()`
6. `test_ai_explanation_generation_flow()`
7. `test_clickhouse_data_sync_flow()`
8. `test_complete_trade_execution_flow()`

### 2.6 E2E Tests: Complete Flows

**File:** `tests/e2e/test_complete_arbitrage_flows.py`

**Tests (5):**
1. `test_discover_execute_track_arbitrage_opportunity()`
2. `test_hold_in_dmarket_strategy_full_cycle()`
3. `test_dual_strategy_portfolio_management()`
4. `test_ai_assisted_trading_decision()`
5. `test_analytics_dashboard_data_pipeline()`

---

## 🔍 Part 3: Error Detection & Fixes

### 3.1 Test Execution Plan

```bash
# Step 1: Run unit tests
pytest tests/unit/api/test_n8n_integration.py -v
pytest tests/unit/dmarket/test_integrated_arbitrage_scanner.py -v
pytest tests/unit/ai/test_prompt_engineering_integration.py -v
pytest tests/unit/analytics/test_clickhouse_analytics.py -v

# Step 2: Run integration tests
pytest tests/integration/test_n8n_workflows.py -v

# Step 3: Run E2E tests
pytest tests/e2e/test_complete_arbitrage_flows.py -v

# Step 4: Run all new tests
pytest tests/ -m "new_features" -v --cov=src --cov-report=html
```

### 3.2 Common Issues to Check

**Compatibility Issues:**
- [ ] Import conflicts between modules
- [ ] Type hint mismatches (Decimal vs float)
- [ ] Async/await consistency
- [ ] Database connection pooling

**Logic Issues:**
- [ ] Commission calculations accuracy
- [ ] Liquidity scoring edge cases
- [ ] Target price formula validation
- [ ] Strategy decision logic correctness

**Performance Issues:**
- [ ] ClickHouse query optimization
- [ ] ETL sync performance
- [ ] API rate limiting
- [ ] Memory usage in large scans

### 3.3 Expected Fixes

Based on testing, common fixes needed:
1. **Type conversions**: Ensure Decimal used consistently for money
2. **Async patterns**: Fix any sync/async mixing
3. **Error handling**: Add try/catch blocks for API failures
4. **Validation**: Add input validation for all user-facing endpoints

---

## 📊 Success Metrics

### Coverage Goals
- **Unit Test Coverage**: 90%+ for new modules
- **Integration Test Coverage**: 80%+ for workflows
- **E2E Test Coverage**: Critical paths only (5 key flows)

### Performance Benchmarks
- **ClickHouse Queries**: <100ms for simple aggregations
- **ETL Sync**: <10 seconds for 1000 records
- **API Endpoints**: <200ms response time
- **Scanner Performance**: <30 seconds for 50-item scan

### Quality Gates
- ✅ All tests pass
- ✅ No ruff/mypy errors
- ✅ Code coverage meets goals
- ✅ No performance regressions
- ✅ Documentation updated

---

## 🚀 Implementation Status

### Phase 7.1: ClickHouse Core (Weeks 1-2)
- [ ] Analytics module created
- [ ] Docker configuration added
- [ ] Database schemas created
- [ ] ETL pipeline implemented
- [ ] Query helpers added

### Phase 7.2: Test Suite (Weeks 2-3)
- [ ] Unit tests written (47 tests)
- [ ] Integration tests written (8 tests)
- [ ] E2E tests written (5 tests)
- [ ] All tests passing

### Phase 7.3: Validation & Fixes (Week 3)
- [ ] Error detection completed
- [ ] All issues fixed
- [ ] Performance validated
- [ ] Documentation updated

**Total Duration**: 3 weeks (or compressed to 1-2 weeks with focused effort)

---

## 📚 Additional Resources

### Documentation to Update
- [ ] Main README.md - Add ClickHouse section
- [ ] docs/README.md - Link to Phase 7 docs
- [ ] .env.example - Add ClickHouse variables
- [ ] CHANGELOG.md - Document Phase 7 changes

### New Documentation Files
- [x] PHASE_7_IMPLEMENTATION_PLAN.md (this file)
- [ ] CLICKHOUSE_DEPLOYMENT_GUIDE.md
- [ ] TESTING_GUIDE.md
- [ ] TROUBLESHOOTING.md

---

## ✅ Next Steps

1. **Review this plan** with stakeholders
2. **Begin Phase 7.1** - ClickHouse implementation
3. **Parallel development** - Tests can be written alongside implementation
4. **Continuous validation** - Run tests as features complete
5. **Final integration** - Merge all components and validate end-to-end

**Estimated Completion**: 1-3 weeks depending on resources

---

*Last Updated: 2026-01-13*
*Status: Planning Complete - Ready for Implementation*
