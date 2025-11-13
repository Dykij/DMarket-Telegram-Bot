#!/usr/bin/env python3
"""GitHub Actions Monitor and Improvement Suggestions.

Этот скрипт анализирует результаты GitHub Actions workflows
и предоставляет конкретные рекомендации по улучшению проекта.
"""

import asyncio
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table

console = Console()


class GitHubActionsMonitor:
    """Мониторинг GitHub Actions и генерация рекомендаций."""

    def __init__(self, repo_owner: str, repo_name: str, token: str | None = None):
        """
        Инициализация монитора.

        Args:
            repo_owner: Владелец репозитория (например, "Dykij")
            repo_name: Имя репозитория (например, "DMarket-Telegram-Bot")
            token: GitHub Personal Access Token (опционально, для большего rate limit)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.token = token
        self.base_url = "https://api.github.com"

        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DMarket-Bot-Monitor",
        }
        if token:
            self.headers["Authorization"] = f"token {token}"

    async def get_workflow_runs(
        self, status: str | None = None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Получить последние запуски workflows.

        Args:
            status: Фильтр по статусу (success, failure, in_progress)
            limit: Количество запусков

        Returns:
            Список запусков workflows
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs"
        params = {"per_page": limit}
        if status:
            params["status"] = status

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("workflow_runs", [])

    async def get_workflow_jobs(self, run_id: int) -> list[dict[str, Any]]:
        """
        Получить jobs конкретного workflow run.

        Args:
            run_id: ID запуска workflow

        Returns:
            Список jobs
        """
        url = f"{self.base_url}/repos/{self.repo_owner}/{self.repo_name}/actions/runs/{run_id}/jobs"

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            return data.get("jobs", [])

    async def analyze_workflow_health(self) -> dict[str, Any]:
        """
        Анализировать общее состояние workflows.

        Returns:
            Статистика и метрики workflows
        """
        runs = await self.get_workflow_runs(limit=50)

        total_runs = len(runs)
        successful_runs = sum(1 for r in runs if r["conclusion"] == "success")
        failed_runs = sum(1 for r in runs if r["conclusion"] == "failure")
        cancelled_runs = sum(1 for r in runs if r["conclusion"] == "cancelled")

        # Расчет времени выполнения
        durations = []
        for run in runs:
            if run.get("created_at") and run.get("updated_at"):
                created = datetime.fromisoformat(
                    run["created_at"].replace("Z", "+00:00")
                )
                updated = datetime.fromisoformat(
                    run["updated_at"].replace("Z", "+00:00")
                )
                duration = (updated - created).total_seconds()
                durations.append(duration)

        avg_duration = sum(durations) / len(durations) if durations else 0

        # Группировка по workflow
        workflow_stats = {}
        for run in runs:
            workflow_name = run["name"]
            if workflow_name not in workflow_stats:
                workflow_stats[workflow_name] = {
                    "total": 0,
                    "success": 0,
                    "failure": 0,
                    "success_rate": 0.0,
                }
            workflow_stats[workflow_name]["total"] += 1
            if run["conclusion"] == "success":
                workflow_stats[workflow_name]["success"] += 1
            elif run["conclusion"] == "failure":
                workflow_stats[workflow_name]["failure"] += 1

        # Расчет success rate
        for stats in workflow_stats.values():
            if stats["total"] > 0:
                stats["success_rate"] = (stats["success"] / stats["total"]) * 100

        return {
            "total_runs": total_runs,
            "successful_runs": successful_runs,
            "failed_runs": failed_runs,
            "cancelled_runs": cancelled_runs,
            "success_rate": (successful_runs / total_runs * 100)
            if total_runs > 0
            else 0,
            "avg_duration_seconds": avg_duration,
            "avg_duration_minutes": avg_duration / 60,
            "workflow_stats": workflow_stats,
            "recent_runs": runs[:10],
        }

    async def get_failed_jobs_details(self) -> list[dict[str, Any]]:
        """
        Получить детали failed jobs.

        Returns:
            Список проваленных jobs с деталями
        """
        failed_runs = await self.get_workflow_runs(status="failure", limit=5)
        failed_jobs = []

        for run in failed_runs:
            jobs = await self.get_workflow_jobs(run["id"])
            for job in jobs:
                if job["conclusion"] == "failure":
                    failed_jobs.append(
                        {
                            "workflow": run["name"],
                            "run_number": run["run_number"],
                            "job_name": job["name"],
                            "started_at": job["started_at"],
                            "completed_at": job["completed_at"],
                            "html_url": job["html_url"],
                            "steps": [
                                {
                                    "name": step["name"],
                                    "status": step["status"],
                                    "conclusion": step["conclusion"],
                                }
                                for step in job.get("steps", [])
                                if step.get("conclusion") == "failure"
                            ],
                        }
                    )

        return failed_jobs

    def generate_recommendations(self, health_data: dict[str, Any]) -> list[str]:
        """
        Генерировать рекомендации на основе анализа.

        Args:
            health_data: Данные о состоянии workflows

        Returns:
            Список рекомендаций
        """
        recommendations = []

        # Проверка success rate
        if health_data["success_rate"] < 80:
            recommendations.append(
                "🔴 **КРИТИЧНО**: Success rate ниже 80%. "
                "Необходимо срочно исправить failing tests и проверки."
            )
        elif health_data["success_rate"] < 95:
            recommendations.append(
                "🟡 **ВНИМАНИЕ**: Success rate ниже 95%. "
                "Рекомендуется улучшить стабильность тестов."
            )
        else:
            recommendations.append(
                "🟢 **ОТЛИЧНО**: Success rate выше 95%. Продолжайте в том же духе!"
            )

        # Проверка времени выполнения
        if health_data["avg_duration_minutes"] > 15:
            recommendations.append(
                "⏱️ **ПРОИЗВОДИТЕЛЬНОСТЬ**: Среднее время выполнения > 15 минут. "
                "Рекомендации:\n"
                "  - Используйте кэширование зависимостей\n"
                "  - Параллелизуйте тесты (pytest -n auto)\n"
                "  - Разделите длинные workflows на меньшие"
            )
        elif health_data["avg_duration_minutes"] > 10:
            recommendations.append(
                "⏱️ **ОПТИМИЗАЦИЯ**: Среднее время выполнения > 10 минут. "
                "Можно улучшить с помощью кэширования."
            )

        # Анализ по конкретным workflows
        for workflow_name, stats in health_data["workflow_stats"].items():
            if stats["success_rate"] < 70 and stats["total"] > 3:
                recommendations.append(
                    f"🔧 **{workflow_name}**: Success rate {stats['success_rate']:.1f}%. "
                    f"Нестабильный workflow - требует внимания."
                )

        # Проверка количества cancelled runs
        if health_data["cancelled_runs"] > health_data["total_runs"] * 0.2:
            recommendations.append(
                "⚠️ **ОТМЕНЕННЫЕ ЗАПУСКИ**: Много отмененных runs. "
                "Возможно, слишком частые коммиты или проблемы с concurrency."
            )

        # Общие рекомендации
        recommendations.append(
            "\n📚 **ОБЩИЕ РЕКОМЕНДАЦИИ**:\n"
            "  1. Регулярно проверяйте логи failed jobs\n"
            "  2. Используйте branch protection rules\n"
            "  3. Настройте уведомления о failed workflows\n"
            "  4. Поддерживайте актуальность зависимостей\n"
            "  5. Документируйте известные проблемы в Issues"
        )

        return recommendations

    async def generate_improvement_plan(self) -> str:
        """
        Сгенерировать план улучшения на основе анализа.

        Returns:
            Markdown-форматированный план улучшения
        """
        health_data = await self.analyze_workflow_health()
        failed_jobs = await self.get_failed_jobs_details()
        recommendations = self.generate_recommendations(health_data)

        # Формирование отчета
        report = f"""# 📊 GitHub Actions - Отчет и План Улучшения

**Дата анализа**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Репозиторий**: {self.repo_owner}/{self.repo_name}

---

## 📈 Текущая Статистика

- **Всего запусков**: {health_data["total_runs"]}
- **Успешных**: {health_data["successful_runs"]} ({health_data["success_rate"]:.1f}%)
- **Провалено**: {health_data["failed_runs"]}
- **Отменено**: {health_data["cancelled_runs"]}
- **Среднее время**: {health_data["avg_duration_minutes"]:.1f} минут

---

## 🎯 Статистика по Workflows

"""
        for workflow_name, stats in health_data["workflow_stats"].items():
            emoji = (
                "🟢"
                if stats["success_rate"] >= 95
                else "🟡"
                if stats["success_rate"] >= 80
                else "🔴"
            )
            report += f"### {emoji} {workflow_name}\n"
            report += f"- Запусков: {stats['total']}\n"
            report += f"- Success Rate: {stats['success_rate']:.1f}%\n"
            report += (
                f"- Успешных: {stats['success']}, Провалено: {stats['failure']}\n\n"
            )

        report += "---\n\n"

        # Детали failed jobs
        if failed_jobs:
            report += "## ❌ Недавние Ошибки\n\n"
            for job in failed_jobs[:5]:
                report += f"### {job['workflow']} - Run #{job['run_number']}\n"
                report += f"**Job**: {job['job_name']}\n"
                report += f"**URL**: {job['html_url']}\n"
                if job["steps"]:
                    report += "**Failed Steps**:\n"
                    for step in job["steps"]:
                        report += f"  - {step['name']}\n"
                report += "\n"
            report += "---\n\n"

        # Рекомендации
        report += "## 💡 Рекомендации по Улучшению\n\n"
        for i, rec in enumerate(recommendations, 1):
            report += f"{rec}\n\n"

        # План действий
        report += """---

## 🚀 План Действий

### Приоритет 1 (Срочно)
- [ ] Исправить все failing tests
- [ ] Проверить и обновить устаревшие зависимости
- [ ] Настроить уведомления о failed workflows

### Приоритет 2 (Важно)
- [ ] Оптимизировать время выполнения workflows
- [ ] Добавить кэширование для ускорения
- [ ] Улучшить покрытие тестами

### Приоритет 3 (Желательно)
- [ ] Настроить автоматический мониторинг
- [ ] Создать dashboard с метриками
- [ ] Документировать CI/CD процесс

---

## 📝 Как Использовать Этот Отчет

1. **Изучите статистику** - определите проблемные области
2. **Проверьте failed jobs** - найдите причины ошибок
3. **Следуйте рекомендациям** - внедряйте улучшения постепенно
4. **Запускайте монитор регулярно** - отслеживайте прогресс

---

**Следующий запуск**: Рекомендуется через 24 часа для отслеживания изменений.
"""

        return report

    def display_summary(self, health_data: dict[str, Any]) -> None:
        """
        Отобразить краткую сводку в консоли.

        Args:
            health_data: Данные о состоянии workflows
        """
        # Заголовок
        console.print("\n")
        console.print(
            Panel.fit(
                "[bold cyan]GitHub Actions - Мониторинг и Анализ[/bold cyan]",
                border_style="cyan",
            )
        )

        # Основная статистика
        table = Table(title="📊 Общая Статистика", show_header=True)
        table.add_column("Метрика", style="cyan")
        table.add_column("Значение", style="green")

        table.add_row("Всего запусков", str(health_data["total_runs"]))
        table.add_row(
            "Успешных",
            f"{health_data['successful_runs']} ({health_data['success_rate']:.1f}%)",
        )
        table.add_row("Провалено", str(health_data["failed_runs"]))
        table.add_row("Отменено", str(health_data["cancelled_runs"]))
        table.add_row("Среднее время", f"{health_data['avg_duration_minutes']:.1f} мин")

        console.print(table)

        # Статистика по workflows
        workflow_table = Table(title="\n🎯 Статистика по Workflows", show_header=True)
        workflow_table.add_column("Workflow", style="cyan")
        workflow_table.add_column("Запусков", justify="center")
        workflow_table.add_column("Success Rate", justify="center")
        workflow_table.add_column("Статус", justify="center")

        for workflow_name, stats in health_data["workflow_stats"].items():
            success_rate = stats["success_rate"]
            if success_rate >= 95:
                status = "🟢 Отлично"
                style = "green"
            elif success_rate >= 80:
                status = "🟡 Хорошо"
                style = "yellow"
            else:
                status = "🔴 Требует внимания"
                style = "red"

            workflow_table.add_row(
                workflow_name,
                str(stats["total"]),
                f"[{style}]{success_rate:.1f}%[/{style}]",
                status,
            )

        console.print(workflow_table)


async def main():
    """Основная функция для запуска мониторинга."""
    # Настройки репозитория
    REPO_OWNER = "Dykij"
    REPO_NAME = "DMarket-Telegram-Bot"

    # GitHub Token (опционально, для большего rate limit)
    # Получить можно здесь: https://github.com/settings/tokens
    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

    console.print("\n[bold cyan]🚀 Запуск GitHub Actions Monitor...[/bold cyan]\n")

    # Создание монитора
    monitor = GitHubActionsMonitor(REPO_OWNER, REPO_NAME, GITHUB_TOKEN)

    try:
        # Анализ workflow health
        console.print("[yellow]📊 Анализирую workflows...[/yellow]")
        health_data = await monitor.analyze_workflow_health()

        # Отображение сводки в консоли
        monitor.display_summary(health_data)

        # Генерация полного отчета
        console.print("\n[yellow]📝 Генерирую детальный отчет...[/yellow]")
        report = await monitor.generate_improvement_plan()

        # Сохранение отчета
        report_dir = Path("build") / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_file = (
            report_dir
            / f"github_actions_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        report_file.write_text(report, encoding="utf-8")

        console.print(f"\n[green]✅ Отчет сохранен: {report_file}[/green]")

        # Отображение рекомендаций
        console.print("\n")
        recommendations = monitor.generate_recommendations(health_data)
        for rec in recommendations[:3]:  # Показываем топ-3
            console.print(Panel(Markdown(rec), border_style="yellow"))

        console.print(f"\n[cyan]📖 Полный отчет доступен в: {report_file}[/cyan]\n")

    except httpx.HTTPStatusError as e:
        console.print(f"\n[red]❌ Ошибка HTTP: {e}[/red]")
        if e.response.status_code == 404:
            console.print("[yellow]Проверьте правильность имени репозитория[/yellow]")
        elif e.response.status_code == 403:
            console.print(
                "[yellow]Rate limit превышен. Используйте GITHUB_TOKEN для увеличения лимита[/yellow]"
            )
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]❌ Ошибка: {e}[/red]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
