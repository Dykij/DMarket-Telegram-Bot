# DMarket API Baseline Responses

This directory contains baseline API responses for automated compatibility checking.

## Purpose

Baseline files are used by the daily API validation workflow (Roadmap Task #9) to detect:
- Breaking changes in API structure
- New/removed fields
- Type changes
- Unexpected API evolution

## Files

- `balance.json` - Baseline for GET /market/api/v1/balance
- `offers.json` - Baseline for GET /market/api/v1/offers
- `buy_offers.json` - Baseline for POST /market/api/v1/buy-offers
- `inventory.json` - Baseline for GET /market/api/v1/inventory

## Workflow

1. **Daily Check** - Tests run every day at 6:00 UTC
2. **Comparison** - Current responses compared with baselines
3. **Detection** - Any differences are flagged
4. **Notification** - GitHub Issue + Telegram alert on changes
5. **Review** - Developer reviews changes and updates baseline if valid

## Updating Baselines

When DMarket updates their API (intentionally):

1. Review the `*_new.json` files in workflow artifacts
2. If changes are expected, copy `*_new.json` → `*.json`
3. Commit updated baselines
4. Re-run validation workflow to confirm

## Manual Testing

Run validation tests locally:

```bash
pytest tests/contracts/test_dmarket_api_validation.py -v
```

## Related Documentation

- [DMarket API Spec](../../../docs/DMARKET_API_FULL_SPEC.md)
- [Contract Testing](../../../docs/CONTRACT_TESTING.md)
- [GitHub Workflow](../../../.github/workflows/daily-api-check.yml)

---

**Note:** Baseline files are committed to git for version control and team visibility.
