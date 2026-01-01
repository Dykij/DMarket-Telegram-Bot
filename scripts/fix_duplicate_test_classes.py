#!/usr/bin/env python3
"""Fix duplicate test class names by renaming them."""

from pathlib import Path


def fix_file(file_path: Path, duplicates: list[tuple[int, str]]) -> None:
    """Fix duplicate class names in a file."""
    with open(file_path, encoding="utf-8") as f:
        lines = f.readlines()

    # Sort by line number in reverse to avoid offset issues
    duplicates_sorted = sorted(duplicates, key=lambda x: x[0], reverse=True)

    for line_num, class_name in duplicates_sorted:
        # Find the class definition line
        for i in range(line_num - 1, min(line_num + 5, len(lines))):
            if f"class {class_name}" in lines[i]:
                # Rename to Extended version
                lines[i] = lines[i].replace(f"class {class_name}:", f"class {class_name}Extended:")
                print(f"  Fixed line {i + 1}: {class_name} -> {class_name}Extended")
                break

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)


def main():
    """Main function."""
    fixes = {
        "tests/dmarket/api/test_inventory.py": [
            (349, "TestGetDepositStatus"),
            (384, "TestWithdrawAssets"),
            (419, "TestSyncInventory"),
        ],
        "tests/dmarket/api/test_market.py": [
            (575, "TestListMarketItems"),
            (616, "TestGetMarketBestOffers"),
            (654, "TestGetAggregatedPrices"),
            (699, "TestGetAggregatedPricesBulk"),
            (731, "TestGetMarketMeta"),
            (754, "TestGetSalesHistoryAggregator"),
        ],
        "tests/dmarket/api/test_wallet.py": [
            (1274, "TestWalletUserProfile"),
        ],
        "tests/utils/test_config_extended.py": [
            (363, "TestSecurityConfig"),
        ],
    }

    base_path = Path(__file__).parent.parent

    for file_path_str, duplicates in fixes.items():
        file_path = base_path / file_path_str
        if file_path.exists():
            print(f"\nFixing {file_path_str}...")
            fix_file(file_path, duplicates)
        else:
            print(f"\nSkipping {file_path_str} (not found)")

    print("\n✅ All duplicate test classes fixed!")


if __name__ == "__main__":
    main()
