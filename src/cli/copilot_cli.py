"""
DMarket Bot CLI - AI-powered terminal interface.

Предоставляет командную строку для взаимодействия с ботом,
вдохновлённый Claude Code для работы в терминале.

Использование:
    # Спросить о коде
    python -m src.cli.copilot_cli ask "How does arbitrage scanner work?"

    # Выполнить задачу
    python -m src.cli.copilot_cli do "Find arbitrage opportunities for CS:GO above 10%"

    # С контекстом файла
    python -m src.cli.copilot_cli ask "What tests are missing?" -c src/dmarket/api.py

    # Сканировать арбитраж
    python -m src.cli.copilot_cli scan csgo --level standard --min-profit 5

    # Проверить баланс
    python -m src.cli.copilot_cli balance

Created: January 2026
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any

import click
import structlog

from src.copilot_sdk.copilot_agent import CopilotAgent, create_agent


logger = structlog.get_logger(__name__)

# Version from central location
__cli_version__ = "1.0.0"


def async_command(f):
    """Декоратор для async команд в Click."""
    import functools

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@click.group()
@click.version_option(version=__cli_version__, prog_name="DMarket Bot CLI")
@click.option("--verbose", "-v", is_flag=True, help="Включить подробный вывод")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """🤖 DMarket Bot CLI - AI-powered terminal interface.

    Командная строка для работы с DMarket ботом, арбитражем и AI-функциями.
    """
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        structlog.configure(
            wrapper_class=structlog.make_filtering_bound_logger(structlog.DEBUG),
        )


@cli.command()
@click.argument("query")
@click.option("--context", "-c", help="Путь к файлу для контекста")
@click.pass_context
@async_command
async def ask(ctx: click.Context, query: str, context: str | None) -> None:
    """❓ Спросить AI о коде или торговле.

    Примеры:
        ask "How does arbitrage scanner work?"
        ask "What is the rate limit for DMarket API?" -c docs/API.md
    """
    verbose = ctx.obj.get("verbose", False)

    click.echo(click.style("🔍 Анализирую запрос...", fg="cyan"))

    try:
        agent = await create_agent()

        if context:
            # Получить контекст файла
            ctx_data = await agent.get_context(context)
            click.echo(
                click.style(f"📁 Контекст: {context}", fg="blue")
            )
            if verbose:
                click.echo(f"   Instructions: {ctx_data.instructions}")
                click.echo(f"   Skills: {ctx_data.skills}")

        # Генерация ответа через prompt engine
        response = await _generate_answer(agent, query, context)

        click.echo()
        click.echo(click.style("💡 Ответ:", fg="green", bold=True))
        click.echo(response)

    except Exception as e:
        click.echo(click.style(f"❌ Ошибка: {e}", fg="red"), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise SystemExit(1)


@cli.command()
@click.argument("task")
@click.option("--dry-run", is_flag=True, help="Симуляция без реальных действий")
@click.pass_context
@async_command
async def do(ctx: click.Context, task: str, dry_run: bool) -> None:
    """⚡ Выполнить задачу автономно.

    Примеры:
        do "Find arbitrage opportunities for CS:GO above 10%"
        do "Create target for AK-47 Redline at $15" --dry-run
    """
    verbose = ctx.obj.get("verbose", False)

    click.echo(click.style(f"🚀 Выполняю задачу: {task}", fg="cyan"))

    if dry_run:
        click.echo(click.style("   [DRY RUN - симуляция]", fg="yellow"))

    try:
        agent = await create_agent()

        # Анализ задачи и выполнение
        result = await _execute_task(agent, task, dry_run=dry_run)

        click.echo()
        click.echo(click.style("✅ Результат:", fg="green", bold=True))
        click.echo(result)

    except Exception as e:
        click.echo(click.style(f"❌ Ошибка: {e}", fg="red"), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise SystemExit(1)


@cli.command()
@click.argument("game", type=click.Choice(["csgo", "dota2", "rust", "tf2"]))
@click.option("--level", "-l", default="standard", help="Уровень арбитража")
@click.option("--min-profit", "-p", default=5.0, type=float, help="Мин. прибыль в %")
@click.option("--limit", default=10, type=int, help="Количество результатов")
@click.pass_context
@async_command
async def scan(
    ctx: click.Context,
    game: str,
    level: str,
    min_profit: float,
    limit: int,
) -> None:
    """🔎 Сканировать арбитражные возможности.

    Примеры:
        scan csgo --level standard --min-profit 5
        scan dota2 -l advanced -p 10 --limit 20
    """
    verbose = ctx.obj.get("verbose", False)

    click.echo(click.style(f"🔎 Сканирую {game.upper()} (уровень: {level})...", fg="cyan"))

    try:
        from src.dmarket.arbitrage_scanner import ArbitrageScanner
        from src.dmarket.dmarket_api import DMarketAPI
        from src.utils.config import settings

        api = DMarketAPI(
            public_key=settings.dmarket.public_key,
            secret_key=settings.dmarket.secret_key,
        )
        scanner = ArbitrageScanner(api_client=api)

        opportunities = await scanner.scan_level(level=level, game=game)

        # Фильтрация по прибыли
        filtered = [
            opp for opp in opportunities
            if opp.get("profit_percent", 0) >= min_profit
        ][:limit]

        click.echo()
        click.echo(click.style(f"📊 Найдено {len(filtered)} возможностей:", fg="green", bold=True))
        click.echo()

        for i, opp in enumerate(filtered, 1):
            title = opp.get("title", "Unknown")
            profit = opp.get("profit_percent", 0)
            buy_price = opp.get("buy_price", 0) / 100  # cents to dollars
            sell_price = opp.get("sell_price", 0) / 100

            color = "green" if profit >= 10 else "yellow" if profit >= 5 else "white"

            click.echo(
                f"  {i}. {click.style(f'{profit:.1f}%', fg=color, bold=True)} | "
                f"{title[:40]:<40} | "
                f"${buy_price:.2f} → ${sell_price:.2f}"
            )

        if not filtered:
            click.echo(click.style("   Нет подходящих возможностей", fg="yellow"))

    except Exception as e:
        click.echo(click.style(f"❌ Ошибка: {e}", fg="red"), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise SystemExit(1)


@cli.command()
@click.option("--platform", "-p", default="dmarket", type=click.Choice(["dmarket", "waxpeer", "all"]))
@click.pass_context
@async_command
async def balance(ctx: click.Context, platform: str) -> None:
    """💰 Проверить баланс на платформе.

    Примеры:
        balance --platform dmarket
        balance -p waxpeer
        balance -p all
    """
    verbose = ctx.obj.get("verbose", False)

    click.echo(click.style(f"💰 Получаю баланс ({platform})...", fg="cyan"))

    try:
        from src.utils.config import settings

        results = {}

        if platform in ("dmarket", "all"):
            from src.dmarket.dmarket_api import DMarketAPI

            api = DMarketAPI(
                public_key=settings.dmarket.public_key,
                secret_key=settings.dmarket.secret_key,
            )
            balance_data = await api.get_balance()
            results["dmarket"] = balance_data

        if platform in ("waxpeer", "all"):
            from src.waxpeer.waxpeer_api import WaxpeerAPI

            api = WaxpeerAPI(api_key=settings.waxpeer.api_key)
            balance_data = await api.get_balance()
            results["waxpeer"] = {
                "wallet_usd": float(balance_data.wallet),
                "can_trade": balance_data.can_trade,
            }

        click.echo()
        click.echo(click.style("💵 Баланс:", fg="green", bold=True))

        for plat, data in results.items():
            click.echo(f"\n  {plat.upper()}:")
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (int, float)):
                        click.echo(f"    {key}: ${value:.2f}" if "usd" in key.lower() or key == "balance" else f"    {key}: {value}")
                    else:
                        click.echo(f"    {key}: {value}")
            else:
                click.echo(f"    {data}")

    except Exception as e:
        click.echo(click.style(f"❌ Ошибка: {e}", fg="red"), err=True)
        if verbose:
            import traceback

            traceback.print_exc()
        raise SystemExit(1)


@cli.command()
@click.pass_context
@async_command
async def status(ctx: click.Context) -> None:
    """📊 Показать статус Copilot Agent.

    Отображает информацию о загруженных инструкциях, промптах и навыках.
    """
    verbose = ctx.obj.get("verbose", False)

    click.echo(click.style("📊 Статус Copilot Agent:", fg="cyan"))

    try:
        agent = await create_agent()
        status_data = agent.get_status()

        click.echo()
        click.echo(f"  ✅ Инициализирован: {status_data['initialized']}")
        click.echo(f"  📜 Инструкции: {status_data['instructions_count']}")
        click.echo(f"  📝 Промпты: {status_data['prompts_count']}")
        click.echo(f"  🛠️  Навыки: {status_data['skills_count']}")

        if verbose:
            click.echo()
            click.echo("  Конфигурация:")
            for key, value in status_data["config"].items():
                click.echo(f"    {key}: {value}")

    except Exception as e:
        click.echo(click.style(f"❌ Ошибка: {e}", fg="red"), err=True)
        raise SystemExit(1)


# Helper functions

async def _generate_answer(agent: CopilotAgent, query: str, context: str | None) -> str:
    """Генерация ответа на вопрос."""
    # Простая реализация - в будущем можно подключить LLM
    if context:
        ctx = await agent.get_context(context)
        return f"""
На основе контекста файла {context}:
- Применяемые инструкции: {', '.join(ctx.instructions) or 'нет'}
- Доступные навыки: {', '.join(ctx.skills) or 'нет'}

Ваш вопрос: {query}

Для полного ответа требуется LLM интеграция (OpenAI/Claude API).
Пока используйте: python -m src.mcp_server.dmarket_mcp для MCP интеграции.
"""
    return f"""
Ваш вопрос: {query}

Статус агента: {agent.get_status()}

Для полного ответа требуется LLM интеграция (OpenAI/Claude API).
Используйте MCP сервер для интеграции с AI:
  python -m src.mcp_server.dmarket_mcp
"""


async def _execute_task(agent: CopilotAgent, task: str, dry_run: bool = False) -> str:
    """Выполнение задачи."""
    # Простая реализация - в будущем autonomous agent
    if dry_run:
        return f"""
[DRY RUN] Задача: {task}

Шаги для выполнения:
1. Анализ задачи через Copilot Agent
2. Поиск релевантных skills
3. Выполнение pipeline
4. Проверка результатов

Для реального выполнения уберите флаг --dry-run.
"""

    return f"""
Задача: {task}

Автономное выполнение требует настройки AutonomousAgent.
См. src/copilot_sdk/autonomous_agent.py для полной реализации.

Текущие возможности:
- scan: сканирование арбитража
- balance: проверка баланса
- ask: вопросы к AI
"""


if __name__ == "__main__":
    cli()
