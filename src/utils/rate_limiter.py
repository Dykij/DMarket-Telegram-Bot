"""Модуль для управления лимитами запросов к API."""

import asyncio
import logging
import time


# Настройка логирования
logger = logging.getLogger(__name__)

# Ограничения запросов для различных типов эндпоинтов DMarket API
# Значения в запросах в секунду (rps)
DMARKET_API_RATE_LIMITS = {
    "market": 2,  # Рыночные запросы (2 запроса в секунду)
    "trade": 1,  # Торговые операции (1 запрос в секунду)
    "user": 5,  # Запросы пользовательских данных
    "balance": 10,  # Запросы баланса
    "other": 5,  # Прочие запросы
}

# Базовая задержка для экспоненциального отступа при ошибках 429
BASE_RETRY_DELAY = 1.0  # 1 секунда


class RateLimiter:
    """Класс для контроля скорости запросов к API DMarket.

    Позволяет:
    - Ограничивать скорость запросов к разным эндпоинтам
    - Ожидать до освобождения слота для запроса
    - Обрабатывать ситуации превышения лимита запросов от API
    - Реализовывать экспоненциальную задержку для обработки ошибок 429
    """

    def __init__(self, is_authorized: bool = True) -> None:
        """Инициализирует контроллер лимитов запросов.

        Args:
            is_authorized: Является ли клиент авторизованным
                (влияет на доступные лимиты запросов)

        """
        self.is_authorized = is_authorized

        # Лимиты запросов для разных типов эндпоинтов
        self.rate_limits: dict[str, int] = DMARKET_API_RATE_LIMITS.copy()

        # Пользовательские лимиты запросов
        self.custom_limits: dict[str, float] = {}

        # Временные точки последних запросов для разных типов эндпоинтов
        self.last_request_times: dict[str, float] = {}

        # Временные метки сброса лимитов для каждого эндпоинта
        self.reset_times: dict[str, float] = {}

        # Счетчики оставшихся запросов для каждого эндпоинта
        self.remaining_requests: dict[str, int] = {}

        # Счетчики попыток для экспоненциальной задержки
        self.retry_attempts: dict[str, int] = {}

        logger.info(
            f"Инициализирован контроллер лимитов запросов API (авторизован: {is_authorized})",
        )

    def get_endpoint_type(self, path: str) -> str:
        """Определяет тип эндпоинта по его пути для DMarket API.

        Args:
            path: Путь эндпоинта API

        Returns:
            Тип эндпоинта ("market", "trade", "user", "balance", "other")

        """
        path = path.lower()

        # DMarket маркет эндпоинты
        market_keywords = [
            "/exchange/v1/market/",
            "/market/items",
            "/market/aggregated-prices",
            "/market/best-offers",
            "/market/search",
        ]
        if any(keyword in path for keyword in market_keywords):
            return "market"

        # DMarket торговые эндпоинты
        trade_keywords = [
            "/exchange/v1/market/buy",
            "/exchange/v1/market/create-offer",
            "/exchange/v1/user/offers/edit",
            "/exchange/v1/user/offers/delete",
        ]
        if any(keyword in path for keyword in trade_keywords):
            return "trade"

        # DMarket баланс и аккаунт
        balance_keywords = [
            "/api/v1/account/balance",
            "/account/v1/balance",
        ]
        if any(keyword in path for keyword in balance_keywords):
            return "balance"

        # DMarket пользовательские эндпоинты
        user_keywords = [
            "/exchange/v1/user/inventory",
            "/api/v1/account/details",
            "/exchange/v1/user/offers",
            "/exchange/v1/user/targets",
        ]
        if any(keyword in path for keyword in user_keywords):
            return "user"

        return "other"

    def update_from_headers(self, headers: dict[str, str]) -> None:
        """Обновляет лимиты запросов на основе заголовков ответа DMarket API.

        Args:
            headers: Заголовки HTTP-ответа

        """
        # Заголовки для анализа: X-RateLimit-Remaining, X-RateLimit-Reset, X-RateLimit-Limit
        remaining_header = "X-RateLimit-Remaining"
        reset_header = "X-RateLimit-Reset"
        limit_header = "X-RateLimit-Limit"

        # Получаем тип эндпоинта из заголовков или используем "other" по умолчанию
        endpoint_type = "other"
        if "X-RateLimit-Scope" in headers:
            scope = headers["X-RateLimit-Scope"].lower()
            if "market" in scope:
                endpoint_type = "market"
            elif "trade" in scope:
                endpoint_type = "trade"
            elif "user" in scope:
                endpoint_type = "user"
            elif "balance" in scope:
                endpoint_type = "balance"

        # Obnovlyaem informatsiyu o limitah na osnove zagolovkov
        if remaining_header in headers:
            try:
                remaining = int(headers[remaining_header])
                self.remaining_requests[endpoint_type] = remaining

                # Esli v otvete est zagolovok s limitom, obnovlyaem ego
                if limit_header in headers:
                    try:
                        limit = int(headers[limit_header])
                        # Ustanavlivaem limit tolko esli on otlichaetsya ot tekushchego
                        if limit != self.rate_limits.get(endpoint_type):
                            self.rate_limits[endpoint_type] = limit
                            logger.info(
                                f"Obnovlen limit dlya {endpoint_type}: {limit} zaprosov",
                            )
                    except (ValueError, KeyError):
                        pass

                # Esli ostavsheeesya kolichestvo zaprosov malo, logiruem preduprezhdenie
                if remaining <= 2:
                    logger.warning(
                        f"Pochti ischerpan limit zaprosov dlya {endpoint_type}: "
                        f"ostalos {remaining}",
                    )

                # Esli dostigli limita zaprosov (remaining <= 0),
                # ustanavlivaem vremya sbrosa iz zagolovka Reset
                if remaining <= 0 and reset_header in headers:
                    try:
                        reset_time = float(headers[reset_header])
                        self.reset_times[endpoint_type] = reset_time

                        # Vychislyaem vremya ozhidaniya do sbrosa
                        wait_time = max(0.0, reset_time - time.time())
                        logger.warning(
                            f"Dostignut limit zaprosov dlya {endpoint_type}. "
                            f"Sbros cherez {wait_time:.2f} sek",
                        )
                    except (ValueError, KeyError):
                        pass
            except (ValueError, KeyError):
                pass

    async def wait_if_needed(self, endpoint_type: str = "other") -> None:
        """Ozhidaet, esli neobhodimo, pered vypolneniem zaprosa ukazannogo tipa.

        Args:
            endpoint_type: Tip endpointa

        """
        # Proveryaem, ne nahoditsya li endpoint pod ogranicheniem
        if endpoint_type in self.reset_times:
            reset_time = self.reset_times[endpoint_type]
            current_time = time.time()

            # Esli vremya sbrosa eshche ne nastupilo
            if reset_time > current_time:
                wait_time = reset_time - current_time
                logger.info(
                    f"Ozhidanie sbrosa limita dlya {endpoint_type}: {wait_time:.2f} sek",
                )
                await asyncio.sleep(wait_time)

                # Posle ozhidaniya udalyaem zapis o vremennom ogranichenii
                del self.reset_times[endpoint_type]
                self.remaining_requests[endpoint_type] = self.rate_limits.get(
                    endpoint_type,
                    5,
                )

        # Poluchaem limit zaprosov v sekundu
        rate_limit = self.get_rate_limit(endpoint_type)

        # Esli limit ne ukazan ili raven beskonechnosti, net neobhodimosti zhdat
        if rate_limit <= 0:
            return

        # Minimalnyj interval mezhdu zaprosami v sekundah
        min_interval = 1.0 / rate_limit

        # Vremya poslednego zaprosa etogo tipa
        last_time = self.last_request_times.get(endpoint_type, 0)
        current_time = time.time()

        # Esli s momenta poslednego zaprosa proshlo menshe minimalnogo intervala
        if current_time - last_time < min_interval:
            # Vychislyaem neobhodimoe vremya ozhidaniya
            wait_time = min_interval - (current_time - last_time)

            # Esli vremya ozhidaniya znachitelnoe, logiruem ego
            if wait_time > 0.1:
                logger.debug(
                    f"Soblyudenie limita {endpoint_type}: ozhidanie {wait_time:.3f} sek",
                )

            # Ozhidaem neobhodimoe vremya
            await asyncio.sleep(wait_time)

        # Obnovlyaem vremya poslednego zaprosa
        self.last_request_times[endpoint_type] = time.time()

    async def handle_429(
        self,
        endpoint_type: str,
        retry_after: int | None = None,
    ) -> tuple[float, int]:
        """Obrabatyvaet oshibku 429 (Too Many Requests) s eksponentsialnoy zaderzhkoy.

        Args:
            endpoint_type: Tip endpointa
            retry_after: Rekomenduemoe vremya ozhidaniya iz zagolovka Retry-After

        Returns:
            Tuple[float, int]: (vremya ozhidaniya v sekundah, novoe kolichestvo popytok)

        """
        # Uvelichivaem schetchik popytok dlya dannogo endpointa
        current_attempts = self.retry_attempts.get(endpoint_type, 0) + 1
        self.retry_attempts[endpoint_type] = current_attempts

        # Esli est zagolovok Retry-After, ispolzuem ego znachenie
        if retry_after is not None and retry_after > 0:
            wait_time = retry_after
        else:
            # Inache ispolzuem eksponentialnuyu zaderzhku s nebolshim sluchaynym komponentom
            # Base * 2^(attempts - 1) + random jitter
            base_wait = BASE_RETRY_DELAY * (2 ** (current_attempts - 1))
            jitter = 0.1 * base_wait * (0.5 - (time.time() % 1.0))  # 10% sluchaynoe otklonenie
            wait_time = base_wait + jitter

            # Ogranichivaem maksimalnoe vremya ozhidaniya 30 sekundami
            wait_time = min(wait_time, 30.0)

        # Ustanavlivaem vremya sbrosa limita
        self.reset_times[endpoint_type] = time.time() + wait_time

        logger.warning(
            f"Prevyshen limit zaprosov dlya {endpoint_type} "
            f"(popytka {current_attempts}). "
            f"Ozhidanie {wait_time:.2f} sek pered sleduyushchey popytkoy.",
        )

        # Vypolnyaem ozhidanie
        await asyncio.sleep(wait_time)

        return wait_time, current_attempts

    def reset_retry_attempts(self, endpoint_type: str) -> None:
        """Sbrasываet schetchik popytok dlya endpointa posle uspeshnogo zaprosa.

        Args:
            endpoint_type: Tip endpointa

        """
        if endpoint_type in self.retry_attempts:
            del self.retry_attempts[endpoint_type]

    def get_rate_limit(self, endpoint_type: str = "other") -> float:
        """Vozvrashchaet tekushchiy limit zaprosov v sekundu dlya ukazannogo tipa endpointa.

        Args:
            endpoint_type: Tip endpointa

        Returns:
            Limit zaprosov v sekundu (rps)

        """
        # Proveryaem polzovatelskie limity
        if endpoint_type in self.custom_limits:
            return self.custom_limits[endpoint_type]

        # Proveryaem standartnye limity
        if endpoint_type in self.rate_limits:
            # Dlya neavtorizovannyh polzovateley snizhaem limity
            if not self.is_authorized and endpoint_type in ["market", "trade"]:
                # 50% ot avtorizovannogo limita
                return float(self.rate_limits[endpoint_type]) / 2.0
            return float(self.rate_limits[endpoint_type])

        # Esli tip endpointa neizvesten, ispolzuem limit dlya "other"
        return float(self.rate_limits.get("other", 5))

    def set_custom_limit(self, endpoint_type: str, limit: float) -> None:
        """Ustanavlivaet polzovatelskiy limit dlya ukazannogo tipa endpointa.

        Args:
            endpoint_type: Tip endpointa
            limit: Limit zaprosov v sekundu (rps)

        """
        self.custom_limits[endpoint_type] = limit
        logger.info(
            f"Ustavlen polzovatelskiy limit dlya {endpoint_type}: {limit} rps",
        )

    def get_remaining_requests(self, endpoint_type: str = "other") -> int:
        """Vozvrashchaet kolichestvo ostavshihsya zaprosov v tekushchem okne.

        Args:
            endpoint_type: Tip endpointa

        Returns:
            Kolichestvo ostavshihsya zaprosov

        """
        # Esli endpoint nahoditsya pod ogranicheniem
        if endpoint_type in self.reset_times and time.time() < self.reset_times[endpoint_type]:
            return 0

        # Vozvrashchaem ostavsheeesya kolichestvo zaprosov
        # (ili maksimalnoe znachenie, esli neizvestno)
        return self.remaining_requests.get(
            endpoint_type,
            int(
                self.get_rate_limit(endpoint_type) * 60,
            ),  # Primernaya otsenka na 1 minutu
        )
