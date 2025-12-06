#!/usr/bin/env python3
"""
Скрипт для очистки тестовых issues в Sentry перед production.

Usage:
    python scripts/sentry_cleanup.py --all
    python scripts/sentry_cleanup.py --test-only
    python scripts/sentry_cleanup.py --before-date 2025-11-23
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta
from typing import Any

import requests
from dotenv import load_dotenv


class SentryCleanup:
    """Класс для очистки Sentry issues."""

    def __init__(self, auth_token: str, organization: str, project: str):
        """
        Инициализация.

        Args:
            auth_token: Sentry Auth Token
            organization: Название организации в Sentry
            project: Название проекта (slug)
        """
        self.auth_token = auth_token
        self.organization = organization
        self.project = project
        self.base_url = "https://sentry.io/api/0"
        self.headers = {"Authorization": f"Bearer {auth_token}"}

    def get_issues(
        self,
        query: str = "",
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        Получить список issues.

        Args:
            query: Поисковый запрос (например, 'is:unresolved')
            limit: Максимальное количество issues

        Returns:
            Список issues
        """
        url = f"{self.base_url}/projects/{self.organization}/{self.project}/issues/"
        params = {"query": query, "limit": limit, "statsPeriod": "24h"}

        try:
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"❌ Ошибка при получении issues: {e}")
            return []

    def delete_issue(self, issue_id: str) -> bool:
        """
        Удалить issue.

        Args:
            issue_id: ID issue

        Returns:
            True если успешно удалено
        """
        url = f"{self.base_url}/issues/{issue_id}/"

        try:
            response = requests.delete(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"❌ Ошибка при удалении issue {issue_id}: {e}")
            return False

    def resolve_issue(self, issue_id: str) -> bool:
        """
        Пометить issue как resolved.

        Args:
            issue_id: ID issue

        Returns:
            True если успешно помечено
        """
        url = f"{self.base_url}/issues/{issue_id}/"
        data = {"status": "resolved"}

        try:
            response = requests.put(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"❌ Ошибка при resolve issue {issue_id}: {e}")
            return False

    def cleanup_test_issues(self, delete: bool = False, dry_run: bool = True) -> None:
        """
        Очистить тестовые issues.

        Args:
            delete: Удалить или только пометить как resolved
            dry_run: Только показать что будет сделано, не выполнять
        """
        # Получить все issues с "test" в названии
        test_queries = [
            "Test Error",
            "Test Critical",
            "Test Trading",
            "Test Auth",
            "Test Database",
            "Test Rate Limit",
        ]

        total_found = 0
        total_processed = 0

        for test_query in test_queries:
            print(f"\n🔍 Поиск: '{test_query}'...")
            issues = self.get_issues(query=test_query)

            if not issues:
                print("   ℹ️  Ничего не найдено")
                continue

            print(f"   ✅ Найдено: {len(issues)} issues")
            total_found += len(issues)

            for issue in issues:
                issue_id = issue.get("id")
                title = issue.get("title", "Unknown")
                status = issue.get("status", "unknown")

                print(f"\n   📌 Issue: {title}")
                print(f"      ID: {issue_id}")
                print(f"      Status: {status}")

                if dry_run:
                    action = "DELETE" if delete else "RESOLVE"
                    print(f"      [DRY RUN] Будет: {action}")
                    total_processed += 1
                    continue

                if delete:
                    if self.delete_issue(issue_id):
                        print("      ✅ Удалено")
                        total_processed += 1
                    else:
                        print("      ❌ Не удалось удалить")
                elif self.resolve_issue(issue_id):
                    print("      ✅ Помечено как resolved")
                    total_processed += 1
                else:
                    print("      ❌ Не удалось пометить")

        print(f"\n{'=' * 60}")
        print("📊 Итого:")
        print(f"   Найдено: {total_found} issues")
        print(f"   Обработано: {total_processed} issues")
        if dry_run:
            print("\n⚠️  DRY RUN режим - изменения не применены")
            print("   Запустите без --dry-run для применения")

    def cleanup_old_issues(
        self,
        days: int = 7,
        delete: bool = False,
        dry_run: bool = True,
    ) -> None:
        """
        Очистить старые issues.

        Args:
            days: Количество дней (удалить старше этого значения)
            delete: Удалить или только пометить как resolved
            dry_run: Только показать что будет сделано
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        print(f"\n🗓️  Удаление issues старше {cutoff_date.strftime('%Y-%m-%d')}")

        # Получить все resolved issues
        issues = self.get_issues(query="is:resolved", limit=500)

        total_found = 0
        total_processed = 0

        for issue in issues:
            issue_id = issue.get("id")
            title = issue.get("title", "Unknown")
            first_seen = issue.get("firstSeen")

            if not first_seen:
                continue

            # Удалить Z суффикс для совместимости с fromisoformat
            first_seen_clean = first_seen.rstrip("Z")
            issue_date = datetime.fromisoformat(first_seen_clean)

            if issue_date > cutoff_date:
                continue

            total_found += 1
            print(f"\n   📌 Issue: {title}")
            print(f"      ID: {issue_id}")
            print(f"      Дата: {issue_date.strftime('%Y-%m-%d %H:%M')}")

            if dry_run:
                action = "DELETE" if delete else "ARCHIVE"
                print(f"      [DRY RUN] Будет: {action}")
                total_processed += 1
                continue

            if delete:
                if self.delete_issue(issue_id):
                    print("      ✅ Удалено")
                    total_processed += 1
                else:
                    print("      ❌ Не удалось удалить")

        print(f"\n{'=' * 60}")
        print("📊 Итого:")
        print(f"   Найдено старых: {total_found} issues")
        print(f"   Обработано: {total_processed} issues")
        if dry_run:
            print("\n⚠️  DRY RUN режим - изменения не применены")


def main() -> None:
    """Основная функция."""
    parser = argparse.ArgumentParser(description="Очистка тестовых issues в Sentry")
    parser.add_argument(
        "--all",
        action="store_true",
        help="Очистить все тестовые issues",
    )
    parser.add_argument(
        "--test-only",
        action="store_true",
        help="Очистить только issues с 'Test' в названии",
    )
    parser.add_argument(
        "--old",
        type=int,
        metavar="DAYS",
        help="Очистить issues старше указанного количества дней",
    )
    parser.add_argument(
        "--delete",
        action="store_true",
        help="Удалить issues (по умолчанию - только resolve)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=True,
        help="Показать что будет сделано, не применять изменения (по умолчанию)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Выполнить изменения (отключить dry-run)",
    )

    args = parser.parse_args()

    # Загрузить переменные окружения
    load_dotenv()

    # Получить настройки Sentry
    auth_token = os.getenv("SENTRY_AUTH_TOKEN")
    organization = os.getenv("SENTRY_ORGANIZATION")
    project = os.getenv("SENTRY_PROJECT")

    if not all([auth_token, organization, project]):
        print("❌ Ошибка: Не установлены переменные окружения:")
        print("   - SENTRY_AUTH_TOKEN")
        print("   - SENTRY_ORGANIZATION")
        print("   - SENTRY_PROJECT")
        print("\nДобавьте их в .env файл:")
        print("SENTRY_AUTH_TOKEN=your_token_here")
        print("SENTRY_ORGANIZATION=your-org")
        print("SENTRY_PROJECT=your-project-slug")
        print("\nПолучите токен: https://sentry.io/settings/account/api/auth-tokens/")
        sys.exit(1)

    # Создать экземпляр очистки
    cleanup = SentryCleanup(auth_token, organization, project)

    # Определить режим
    dry_run = not args.execute

    if dry_run:
        print("\n⚠️  DRY RUN режим - изменения не будут применены")
        print("   Используйте --execute для применения изменений\n")

    # Выполнить очистку
    if args.all or args.test_only:
        cleanup.cleanup_test_issues(delete=args.delete, dry_run=dry_run)

    if args.old:
        cleanup.cleanup_old_issues(days=args.old, delete=args.delete, dry_run=dry_run)

    if not any([args.all, args.test_only, args.old]):
        parser.print_help()
        print("\nПримеры использования:")
        print("  # Показать что будет удалено (dry run)")
        print("  python scripts/sentry_cleanup.py --test-only")
        print()
        print("  # Пометить тестовые issues как resolved")
        print("  python scripts/sentry_cleanup.py --test-only --execute")
        print()
        print("  # Удалить все тестовые issues")
        print("  python scripts/sentry_cleanup.py --all --delete --execute")
        print()
        print("  # Удалить issues старше 7 дней")
        print("  python scripts/sentry_cleanup.py --old 7 --delete --execute")


if __name__ == "__main__":
    main()
