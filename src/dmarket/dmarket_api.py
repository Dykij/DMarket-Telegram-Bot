"""DMarket API client module for interacting with DMarket API.

This module provides an asynchronous client for DMarket API, including:
- Signature generation for authenticated requests
- Rate limiting and retry logic
- Methods for market operations (get items, buy, sell, inventory, balance)
- Error handling and logging
- Caching of frequently used requests
- Support for all documented DMarket API endpoints

Example usage:

    # Импортируем класс DMarketAPI
    from src.dmarket.dmarket_api import DMarketAPI

    # Создаем экземпляр API клиента
    api = DMarketAPI(public_key, secret_key)

    # Используем методы API
    items = await api.get_market_items(game="csgo")
    balance = await api.get_balance()  # Рекомендуемый метод получения баланса

Documentation: https://docs.dmarket.com/v1/swagger.html
"""

import asyncio
import hashlib
import hmac
import json
import logging
import time
import traceback
from typing import Any

import httpx
import nacl.encoding
import nacl.signing
from circuitbreaker import CircuitBreakerError

from src.utils.api_circuit_breaker import call_with_circuit_breaker
from src.utils.rate_limiter import RateLimiter


logger = logging.getLogger(__name__)

# TTL для кэша в секундах
CACHE_TTL = {
    "short": 30,  # 30 секунд для часто меняющихся данных
    "medium": 300,  # 5 минут для умеренно стабильных данных
    "long": 1800,  # 30 минут для стабильных данных
}

# Кэш для хранения результатов запросов
api_cache = {}


class DMarketAPI:
    """Асинхронный клиент для работы с DMarket API.

    Основные возможности:
    - Генерация подписей для приватных запросов
    - Асинхронные методы для работы с маркетом, инвентарём, балансом
    - Встроенный rate limiting и автоматические повторы при ошибках
    - Логирование и обработка ошибок
    - Кэширование часто используемых запросов
    - Поддержка всех документированных эндпоинтов DMarket API

    Пример:
        api = DMarketAPI(public_key, secret_key)
        items = await api.get_market_items(game="csgo")
    """

    # БАЗОВЫЕ ЭНДПОИНТЫ (согласно документации)
    BASE_URL = "https://api.dmarket.com"

    # Баланс и аккаунт
    ENDPOINT_BALANCE = "/account/v1/balance"  # Основной эндпоинт баланса
    ENDPOINT_BALANCE_LEGACY = "/api/v1/account/balance"  # Альтернативный эндпоинт
    ENDPOINT_ACCOUNT_DETAILS = "/api/v1/account/details"  # Детали аккаунта
    ENDPOINT_ACCOUNT_OFFERS = "/api/v1/account/offers"  # Активные торговые предложения

    # Маркет
    ENDPOINT_MARKET_ITEMS = "/exchange/v1/market/items"  # Поиск предметов на маркете
    ENDPOINT_MARKET_PRICE_AGGREGATED = (
        "/exchange/v1/market/aggregated-prices"  # Агрегированные цены
    )
    ENDPOINT_MARKET_META = "/exchange/v1/market/meta"  # Метаданные маркета

    # Пользователь
    ENDPOINT_USER_INVENTORY = "/exchange/v1/user/inventory"  # Инвентарь пользователя
    ENDPOINT_USER_OFFERS = "/exchange/v1/user/offers"  # Предложения пользователя
    ENDPOINT_USER_TARGETS = "/exchange/v1/target-lists"  # Целевые предложения пользователя

    # Операции
    ENDPOINT_PURCHASE = "/exchange/v1/market/items/buy"  # Покупка предмета
    ENDPOINT_SELL = "/exchange/v1/user/inventory/sell"  # Выставить на продажу
    ENDPOINT_OFFER_EDIT = "/exchange/v1/user/offers/edit"  # Редактирование предложения
    ENDPOINT_OFFER_DELETE = "/exchange/v1/user/offers/delete"  # Удаление предложения

    # Статистика и аналитика
    ENDPOINT_SALES_HISTORY = "/account/v1/sales-history"  # История продаж
    ENDPOINT_ITEM_PRICE_HISTORY = "/exchange/v1/market/price-history"  # История цен предмета
    ENDPOINT_LAST_SALES = "/trade-aggregator/v1/last-sales"  # История последних продаж (API v1.1.0)

    # Новые эндпоинты 2024/2025 (API v1.1.0)
    ENDPOINT_MARKET_BEST_OFFERS = "/exchange/v1/market/best-offers"  # Лучшие предложения на маркете
    ENDPOINT_MARKET_SEARCH = "/exchange/v1/market/search"  # Расширенный поиск
    ENDPOINT_AGGREGATED_PRICES_POST = (
        "/marketplace-api/v1/aggregated-prices"  # Агрегированные цены (POST, v1.1.0)
    )
    ENDPOINT_TARGETS_BY_TITLE = (
        "/marketplace-api/v1/targets-by-title"  # Таргеты по названию (v1.1.0)
    )
    ENDPOINT_DEPOSIT_ASSETS = "/marketplace-api/v1/deposit-assets"  # Депозит активов (v1.1.0)
    ENDPOINT_DEPOSIT_STATUS = "/marketplace-api/v1/deposit-status"  # Статус депозита (v1.1.0)
    ENDPOINT_WITHDRAW_ASSETS = "/exchange/v1/withdraw-assets"  # Вывод активов (v1.1.0)
    ENDPOINT_INVENTORY_SYNC = (
        "/marketplace-api/v1/user-inventory/sync"  # Синхронизация инвентаря (v1.1.0)
    )

    # Известные коды ошибок DMarket API и рекомендации по их обработке
    ERROR_CODES = {
        400: "Неверный запрос или параметры",
        401: "Неверная аутентификация",
        403: "Доступ запрещен",
        404: "Ресурс не найден",
        429: "Слишком много запросов (rate limit)",
        500: "Внутренняя ошибка сервера",
        502: "Bad Gateway",
        503: "Сервис недоступен",
        504: "Gateway Timeout",
    }

    def __init__(
        self,
        public_key: str,
        secret_key: str,
        api_url: str = "https://api.dmarket.com",
        max_retries: int = 3,
        connection_timeout: float = 30.0,
        pool_limits: httpx.Limits = None,
        retry_codes: list[int] | None = None,
        enable_cache: bool = True,
    ) -> None:
        """Initialize DMarket API client.

        Args:
            public_key: DMarket API public key
            secret_key: DMarket API secret key
            api_url: API URL (default is https://api.dmarket.com)
            max_retries: Maximum number of retries for failed requests
            connection_timeout: Connection timeout in seconds
            pool_limits: Connection pool limits
            retry_codes: HTTP status codes to retry on
            enable_cache: Enable caching of frequent requests

        """
        self.public_key = public_key
        self._public_key = public_key  # Store for test access
        self._secret_key = (
            secret_key if isinstance(secret_key, str) else secret_key.decode("utf-8")
        )  # Store original string for test access
        # Convert secret_key to bytes if it's a string
        if isinstance(secret_key, str):
            self.secret_key = secret_key.encode("utf-8")
        elif isinstance(secret_key, bytes):
            self.secret_key = secret_key
        else:
            self.secret_key = b""
        self.api_url = api_url
        self.max_retries = max_retries
        self.connection_timeout = connection_timeout
        self.enable_cache = enable_cache

        # Default retry codes: server errors and too many requests
        self.retry_codes = retry_codes or [429, 500, 502, 503, 504]

        # Connection pool settings
        self.pool_limits = pool_limits or httpx.Limits(
            max_connections=100,
            max_keepalive_connections=20,
        )

        # HTTP client
        self._client = None

        # Initialize RateLimiter with authorization check
        self.rate_limiter = RateLimiter(
            is_authorized=bool(public_key and secret_key),
        )
        logger.info(
            f"Initialized DMarketAPI client "
            f"(authorized: {'yes' if public_key and secret_key else 'no'}, cache: {'enabled' if enable_cache else 'disabled'})",
        )

    async def __aenter__(self) -> "DMarketAPI":
        """Context manager to use the client with async with."""
        await self._get_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Close client when exiting context manager."""
        await self._close_client()

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=self.connection_timeout,
                limits=self.pool_limits,
            )
        return self._client

    async def _close_client(self) -> None:
        """Close HTTP client if it exists."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    def _generate_signature(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> dict[str, str]:
        """Генерирует подпись для приватных запросов DMarket API согласно документации.

        DMarket API использует Ed25519 для подписи запросов.
        Формат: timestamp + method + path + body

        Args:
            method: HTTP-метод ("GET", "POST" и т.д.)
            path: Путь запроса (например, "/account/v1/balance")
            body: Тело запроса (строка JSON)

        Returns:
            dict: Заголовки с подписью и ключом API

        """
        if not self.public_key or not self.secret_key:
            return {"Content-Type": "application/json"}

        try:
            # Generate timestamp
            timestamp = str(int(time.time()))

            # Build string to sign: method + path + timestamp (+ body if present)
            # NOTE: DMarket API format is METHOD + PATH + TIMESTAMP (without spaces)
            string_to_sign = f"{method.upper()}{path}{timestamp}"
            if body:
                string_to_sign += body

            logger.debug(f"String to sign: {string_to_sign}")

            # Convert secret key from string to bytes
            # DMarket API keys can be in different formats
            if isinstance(self.secret_key, str):
                secret_key_str = self._secret_key
            else:
                secret_key_str = self.secret_key.decode("utf-8")

            # Try different formats for secret key
            try:
                # Format 1: HEX format (64 chars = 32 bytes)
                if len(secret_key_str) == 64:
                    secret_key_bytes = bytes.fromhex(secret_key_str)
                    logger.debug("Using HEX format secret key (32 bytes)")
                # Format 2: Base64 format
                elif len(secret_key_str) == 44 or "=" in secret_key_str:
                    import base64

                    secret_key_bytes = base64.b64decode(secret_key_str)
                    logger.debug(f"Using Base64 format secret key ({len(secret_key_bytes)} bytes)")
                # Format 3: Raw string - take first 32 bytes
                # If longer than 64 hex chars, try to take first 64
                elif len(secret_key_str) >= 64:
                    secret_key_bytes = bytes.fromhex(secret_key_str[:64])
                    logger.debug("Using first 32 bytes of long HEX key")
                else:
                    # Fallback: encode string to bytes and pad/truncate to 32
                    secret_key_bytes = secret_key_str.encode("utf-8")[:32].ljust(32, b"\0")
                    logger.warning("Secret key format unknown, using padded bytes")
            except Exception as conv_error:
                logger.exception(f"Error converting secret key: {conv_error}")
                raise

            # Create Ed25519 signing key
            signing_key = nacl.signing.SigningKey(secret_key_bytes)

            # Sign the message
            signed = signing_key.sign(string_to_sign.encode("utf-8"))

            # Extract signature in hex format
            signature = signed.signature.hex()

            logger.debug(f"Generated signature: {signature[:20]}...")

            # Return headers with signature in DMarket format
            return {
                "X-Api-Key": self.public_key,
                "X-Request-Sign": f"dmar ed25519 {signature}",
                "X-Sign-Date": timestamp,
                "Content-Type": "application/json",
            }

        except Exception as e:
            logger.exception(f"Error generating signature: {e}")
            logger.exception(f"Traceback: {traceback.format_exc()}")
            # Fallback to old HMAC method if Ed25519 fails
            return self._generate_signature_hmac(method, path, body)

    def _generate_signature_hmac(
        self,
        method: str,
        path: str,
        body: str = "",
    ) -> dict[str, str]:
        """Fallback метод с HMAC-SHA256 (старый формат).

        Args:
            method: HTTP-метод
            path: Путь запроса
            body: Тело запроса

        Returns:
            dict: Заголовки с HMAC подписью

        """
        timestamp = str(int(time.time()))
        string_to_sign = timestamp + method + path

        if body:
            string_to_sign += body

        secret_key = (
            self.secret_key
            if isinstance(self.secret_key, bytes)
            else self.secret_key.encode("utf-8")
        )

        signature = hmac.new(
            secret_key,
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        return {
            "X-Api-Key": self.public_key,
            "X-Request-Sign": signature,
            "X-Sign-Date": timestamp,
            "Content-Type": "application/json",
        }

    def _generate_headers(
        self,
        method: str,
        target: str,
        body: str = "",
    ) -> dict[str, str]:
        """Alias for _generate_signature for test compatibility.

        Args:
            method: HTTP method
            target: Request path/target
            body: Request body

        Returns:
            dict: Headers with signature

        """
        return self._generate_signature(method, target, body)

    def _get_cache_key(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
    ) -> str:
        """Создает уникальный ключ для кэша на основе запроса.

        Args:
            method: HTTP-метод
            path: Путь запроса
            params: GET-параметры
            data: POST-данные

        Returns:
            str: Ключ кэша

        """
        key_parts = [method, path]

        if params:
            # Сортируем параметры для консистентного ключа
            sorted_params = sorted((str(k), str(v)) for k, v in params.items())
            key_parts.append(str(sorted_params))

        if data:
            # Для POST-данных используем хеш от JSON
            try:
                data_str = json.dumps(data, sort_keys=True)
                key_parts.append(hashlib.md5(data_str.encode()).hexdigest())
            except (TypeError, ValueError):
                key_parts.append(str(data))

        return hashlib.md5("|".join(key_parts).encode()).hexdigest()

    def _is_cacheable(self, method: str, path: str) -> tuple[bool, str]:
        """Определяет, можно ли кэшировать данный запрос и на какой период.

        Args:
            method: HTTP-метод
            path: Путь запроса

        Returns:
            Tuple[bool, str]: (можно_кэшировать, тип_ttl)

        """
        # GET-запросы можно кэшировать
        if method.upper() != "GET":
            return (False, "")

        # Определяем TTL на основе эндпоинта
        if any(
            endpoint in path
            for endpoint in [
                self.ENDPOINT_MARKET_META,
                self.ENDPOINT_MARKET_PRICE_AGGREGATED,
                "/meta",
                "/aggregated",
            ]
        ):
            return (True, "medium")  # Стабильные данные

        if any(
            endpoint in path
            for endpoint in [
                self.ENDPOINT_MARKET_ITEMS,
                self.ENDPOINT_USER_INVENTORY,
                self.ENDPOINT_MARKET_BEST_OFFERS,
                self.ENDPOINT_SALES_HISTORY,
                "/market/",
                "/items",
                "/inventory",
            ]
        ):
            return (True, "short")  # Часто меняющиеся данные

        if any(
            endpoint in path
            for endpoint in [
                self.ENDPOINT_BALANCE,
                self.ENDPOINT_BALANCE_LEGACY,
                self.ENDPOINT_ACCOUNT_DETAILS,
                "/balance",
                "/account/",
            ]
        ):
            return (True, "short")  # Финансовые данные - короткий кэш

        if any(
            endpoint in path
            for endpoint in [
                self.ENDPOINT_ITEM_PRICE_HISTORY,
                "/history",
                "/statistics",
            ]
        ):
            return (True, "long")  # Исторические данные - долгий кэш

        # По умолчанию - не кэшируем
        return (False, "")

    def _get_from_cache(self, cache_key: str) -> dict[str, Any] | None:
        """Получает данные из кэша, если они есть и не устарели.

        Args:
            cache_key: Ключ кэша

        Returns:
            Optional[Dict[str, Any]]: Данные из кэша или None

        """
        if not self.enable_cache:
            return None

        cache_entry = api_cache.get(cache_key)
        if not cache_entry:
            return None

        data, expire_time = cache_entry
        if time.time() < expire_time:
            logger.debug(f"Cache hit for key {cache_key[:8]}...")
            return data

        # Удаляем устаревшие данные
        logger.debug(f"Cache expired for key {cache_key[:8]}...")
        api_cache.pop(cache_key, None)
        return None

    def _save_to_cache(
        self,
        cache_key: str,
        data: dict[str, Any],
        ttl_type: str,
    ) -> None:
        """Сохраняет данные в кэш.

        Args:
            cache_key: Ключ кэша
            data: Данные для сохранения
            ttl_type: Тип TTL ('short', 'medium', 'long')

        """
        if not self.enable_cache:
            return

        ttl = CACHE_TTL.get(ttl_type, CACHE_TTL["short"])
        expire_time = time.time() + ttl
        api_cache[cache_key] = (data, expire_time)

        # Очистка кэша, если он слишком большой (более 500 записей)
        if len(api_cache) > 500:
            # Удаляем 20% старых записей
            time.time()
            keys_to_remove = sorted(
                api_cache.keys(),
                key=lambda k: api_cache[k][1],  # Сортировка по времени истечения
            )[:100]

            for key in keys_to_remove:
                api_cache.pop(key, None)

            logger.debug(f"Cache cleanup: removed {len(keys_to_remove)} old entries")

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Выполняет запрос к DMarket API с обработкой ошибок, повторными попытками и кешированием.

        Args:
            method: HTTP метод (GET, POST и т.д.)
            path: Путь API без базового URL
            params: Параметры запроса (для GET)
            data: Данные для запроса (для POST/PUT)
            force_refresh: Принудительно обновить кэш (если включен)

        Returns:
            Ответ API в виде словаря

        Raises:
            Exception: При ошибке запроса после всех повторных попыток

        """
        # Создаем клиента, если его нет
        client = await self._get_client()

        # Параметры по умолчанию
        if params is None:
            params = {}

        if data is None:
            data = {}

        # Полный URL запроса
        url = f"{self.api_url}{path}"

        # Определяем возможность кэширования и тип TTL заранее
        is_cacheable, ttl_type = self._is_cacheable(method, path)
        cache_key = ""

        # Проверяем кэш для GET запросов
        body_json = ""
        if method.upper() == "GET" and self.enable_cache and not force_refresh:
            cache_key = self._get_cache_key(method, path, params, data)

            # Пробуем получить из кэша
            if is_cacheable:
                cached_data = self._get_from_cache(cache_key)
                if cached_data is not None:
                    logger.debug(f"Использую кэшированные данные для {path}")
                    return cached_data

        # Формируем тело запроса для POST/PUT/PATCH
        if data and method.upper() in ("POST", "PUT", "PATCH"):
            body_json = json.dumps(data)

        # Генерируем заголовки с подписью
        headers = self._generate_signature(method.upper(), path, body_json)

        # Используем rate limiter чтобы не превысить лимиты API
        await self.rate_limiter.wait_if_needed(
            "market" if "market" in path else "account",
        )

        # Переменные для повторных попыток
        retries = 0
        last_error = None
        retry_delay = 1.0  # начальная задержка в секундах

        # Основной цикл запросов с повторами при ошибках
        while retries <= self.max_retries:
            try:
                # Выполняем запрос с нужным методом
                if method.upper() == "GET":
                    response = await call_with_circuit_breaker(
                        client.get, url, params=params, headers=headers
                    )
                elif method.upper() == "POST":
                    response = await call_with_circuit_breaker(
                        client.post, url, json=data, headers=headers
                    )
                elif method.upper() == "PUT":
                    response = await call_with_circuit_breaker(
                        client.put, url, json=data, headers=headers
                    )
                elif method.upper() == "DELETE":
                    response = await call_with_circuit_breaker(client.delete, url, headers=headers)
                else:
                    msg = f"Неподдерживаемый HTTP метод: {method}"
                    raise ValueError(msg)

                # Проверяем статус ответа
                response.raise_for_status()

                # Парсим JSON ответа
                try:
                    result = response.json()
                except Exception:
                    # Если не получается распарсить JSON, возвращаем текст
                    result = {
                        "text": response.text,
                        "status_code": response.status_code,
                    }

                # Сохраняем в кэш если нужно
                if method.upper() == "GET" and self.enable_cache and is_cacheable:
                    self._save_to_cache(cache_key, result, ttl_type)

                return result

            except CircuitBreakerError as e:
                logger.warning(f"Circuit breaker open for {method} {path}: {e}")
                last_error = e
                break

            except httpx.HTTPStatusError as e:
                status_code = e.response.status_code
                response_text = e.response.text

                # Подробное логирование ошибки
                logger.warning(
                    f"HTTP ошибка {status_code} при запросе {method} {path}: {response_text}",
                )

                # Получаем описание ошибки из словаря кодов ошибок
                error_description = self.ERROR_CODES.get(
                    status_code,
                    "Неизвестная ошибка",
                )
                logger.warning(f"Описание ошибки: {error_description}")

                # Проверяем, нужно ли повторить запрос
                if status_code in self.retry_codes:
                    retries += 1

                    # При ошибке 429 (Too Many Requests) используем экспоненциальную задержку
                    if status_code == 429:
                        retry_after = None
                        try:
                            # Пробуем получить значение Retry-After из заголовков
                            retry_after = int(
                                e.response.headers.get("Retry-After", "0"),
                            )
                        except (ValueError, TypeError):
                            retry_after = None

                        # Если нет Retry-After или он некорректный, используем экспоненциальную задержку
                        if not retry_after or retry_after <= 0:
                            retry_delay = min(
                                retry_delay * 2,
                                30,
                            )  # максимальная задержка 30 секунд
                        else:
                            retry_delay = retry_after

                        logger.info(
                            f"Rate limit превышен. Повторная попытка через {retry_delay} сек.",
                        )
                    else:
                        # Для других ошибок используем фиксированную задержку с небольшим случайным компонентом
                        retry_delay = 1.0 + retries * 0.5

                    if retries <= self.max_retries:
                        logger.info(
                            f"Повторная попытка {retries}/{self.max_retries} через {retry_delay} сек...",
                        )
                        await asyncio.sleep(retry_delay)
                        continue

                # Если это не ретраибл ошибка или исчерпаны попытки
                try:
                    error_json = e.response.json()
                    error_message = error_json.get("message", str(e))
                    error_code = error_json.get("code", status_code)
                except Exception:
                    error_message = response_text
                    error_code = status_code

                error_data = {
                    "error": True,
                    "code": error_code,
                    "message": error_message,
                    "status": status_code,
                    "description": error_description,
                }

                # Для некоторых ошибок возвращаем структурированный ответ вместо исключения
                if status_code in [400, 404]:
                    return error_data

                last_error = Exception(
                    f"DMarket API error: {error_message} (code: {error_code}, description: {error_description})",
                )
                break

            except (httpx.ConnectError, httpx.ReadError, httpx.WriteError) as e:
                # Сетевые ошибки
                logger.warning(f"Сетевая ошибка при запросе {method} {path}: {e!s}")
                retries += 1
                retry_delay = min(
                    retry_delay * 1.5,
                    10,
                )  # максимальная задержка 10 секунд

                if retries <= self.max_retries:
                    logger.info(
                        f"Повторная попытка {retries}/{self.max_retries} через {retry_delay} сек...",
                    )
                    await asyncio.sleep(retry_delay)
                    continue

                last_error = e
                break

            except Exception as e:
                # Другие ошибки
                logger.exception(
                    f"Непредвиденная ошибка при запросе {method} {path}: {e!s}",
                )
                logger.exception(traceback.format_exc())
                last_error = e
                break

        # Если были исчерпаны все попытки
        if last_error:
            error_message = str(last_error)
            return {
                "error": True,
                "message": error_message,
                "code": "REQUEST_FAILED",
            }

        # Эта часть кода никогда не должна выполняться, но для безопасности
        return {
            "error": True,
            "message": "Unknown error occurred during API request",
            "code": "UNKNOWN_ERROR",
        }

    async def clear_cache(self) -> None:
        """Очищает весь кэш API."""
        global api_cache
        api_cache = {}
        logger.info("API cache cleared")

    async def clear_cache_for_endpoint(self, endpoint_path: str) -> None:
        """Очищает кэш для конкретного эндпоинта.

        Args:
            endpoint_path: Путь эндпоинта

        """
        global api_cache
        keys_to_remove = []

        for key in api_cache:
            if endpoint_path in key:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            api_cache.pop(key, None)

        logger.info(
            f"Cleared {len(keys_to_remove)} cache entries for endpoint {endpoint_path}",
        )

    # Оставляем для обратной совместимости
    async def get_balance(self) -> dict[str, Any]:
        """Улучшенная версия метода получения баланса пользователя DMarket.
        Комбинирует все доступные методы для максимальной совместимости.

        Returns:
            Информация о балансе в формате:
            {
                "usd": {"amount": value_in_cents},
                "has_funds": True/False,
                "balance": value_in_dollars,
                "available_balance": value_in_dollars,
                "total_balance": value_in_dollars,
                "error": True/False,
                "error_message": "Сообщение об ошибке (если есть)"
            }

        """
        logger.debug("Запрос баланса пользователя DMarket через универсальный метод")

        # Проверяем наличие API ключей
        if not self.public_key or not self.secret_key:
            logger.error("Ошибка: API ключи не настроены (пустые значения)")
            return {
                "usd": {"amount": 0},
                "has_funds": False,
                "balance": 0.0,
                "available_balance": 0.0,
                "total_balance": 0.0,
                "error": True,
                "error_message": "API ключи не настроены",
                "status_code": 401,
                "code": "MISSING_API_KEYS",
            }

        try:
            # 2024 обновление: сначала пробуем прямой REST API запрос через requests
            # Этот подход может быть более надежен для некоторых эндпоинтов
            try:
                logger.debug("🔍 Пытаемся получить баланс через прямой REST API запрос...")
                direct_response = await self.direct_balance_request()
                logger.debug(f"🔍 Прямой ответ API: {direct_response}")

                if direct_response and direct_response.get("success", False):
                    logger.info("✅ Успешно получили баланс через прямой REST API запрос")

                    # Извлекаем данные из успешного ответа
                    balance_data = direct_response.get("data", {})
                    logger.debug(f"📊 Данные баланса: {balance_data}")

                    usd_amount = balance_data.get("balance", 0) * 100  # конвертируем в центы
                    usd_available = (
                        balance_data.get("available", balance_data.get("balance", 0)) * 100
                    )
                    usd_total = balance_data.get("total", balance_data.get("balance", 0)) * 100
                    usd_locked = balance_data.get("locked", 0) * 100
                    usd_trade_protected = balance_data.get("trade_protected", 0) * 100

                    # Определяем результат
                    min_required_balance = 1.0  # Минимальный требуемый баланс
                    # has_funds проверяем по ОБЩЕМУ балансу, а не только доступному
                    has_funds = usd_amount >= min_required_balance * 100

                    result = {
                        "usd": {"amount": usd_amount},
                        "has_funds": has_funds,
                        "balance": usd_amount / 100,
                        "available_balance": usd_available / 100,
                        "total_balance": usd_total / 100,
                        "locked_balance": usd_locked / 100,
                        "trade_protected_balance": usd_trade_protected / 100,
                        "error": False,
                        "additional_info": {
                            "method": "direct_request",
                            "raw_response": balance_data,
                        },
                    }

                    logger.info(
                        f"💰 Итоговый баланс (прямой запрос): ${result['balance']:.2f} USD "
                        f"(доступно: ${result['available_balance']:.2f}, заблокировано: ${result['locked_balance']:.2f})"
                    )
                    return result

                # Если прямой запрос не сработал, логируем ошибку и продолжаем с другими методами
                error_message = direct_response.get("error", "Неизвестная ошибка")
                logger.warning(f"⚠️ Прямой REST API запрос не удался: {error_message}")
                logger.debug(f"🔍 Полный ответ с ошибкой: {direct_response}")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка при прямом REST API запросе: {e!s}")
                logger.exception(f"📋 Детали исключения: {e}")

            # Если прямой запрос не удался, пробуем через внутренний API клиент
            # Пробуем все известные эндпоинты для получения баланса
            endpoints = [
                self.ENDPOINT_BALANCE,  # Актуальный эндпоинт согласно документации
                "/api/v1/account/wallet/balance",  # Альтернативный возможный эндпоинт
                "/exchange/v1/user/balance",  # Возможный эндпоинт биржи
                self.ENDPOINT_BALANCE_LEGACY,  # Старый эндпоинт (для обратной совместимости)
            ]

            response = None
            last_error = None
            successful_endpoint = None

            # Перебираем все эндпоинты, пока не получим корректный ответ
            for endpoint in endpoints:
                try:
                    logger.info(f"Пробуем получить баланс через эндпоинт {endpoint}")
                    response = await self._request(
                        "GET",
                        endpoint,
                    )

                    if (
                        response
                        and isinstance(response, dict)
                        and not ("error" in response or "code" in response)
                    ):
                        logger.info(f"Успешно получили баланс через {endpoint}")
                        successful_endpoint = endpoint
                        break

                except Exception as e:
                    last_error = e
                    logger.warning(f"Ошибка при запросе {endpoint}: {e!s}")
                    continue

            # Если не получили ответ ни от одного эндпоинта
            if not response:
                error_message = (
                    str(last_error)
                    if last_error
                    else "Не удалось получить баланс ни с одного эндпоинта"
                )
                logger.error(f"Критическая ошибка при запросе баланса: {error_message}")

                # Определяем код ошибки из сообщения
                status_code = 500
                error_code = "REQUEST_FAILED"
                if "404" in error_message or "not found" in error_message.lower():
                    status_code = 404
                    error_code = "NOT_FOUND"
                elif "401" in error_message or "unauthorized" in error_message.lower():
                    status_code = 401
                    error_code = "UNAUTHORIZED"

                return {
                    "usd": {"amount": 0},
                    "has_funds": False,
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "error": True,
                    "error_message": error_message,
                    "status_code": status_code,
                    "code": error_code,
                }

            # Проверяем на ошибки API
            if isinstance(response, dict) and ("error" in response or "code" in response):
                error_code = response.get("code", "unknown")
                error_message = response.get(
                    "message",
                    response.get("error", "Неизвестная ошибка"),
                )
                status_code = response.get("status", response.get("status_code", 500))

                logger.error(
                    f"Ошибка DMarket API при получении баланса: {error_code} - {error_message} (HTTP {status_code})",
                )

                # Если ошибка авторизации (401 Unauthorized)
                if error_code == "Unauthorized" or status_code == 401:
                    logger.error(
                        "Проблема с API ключами. Пожалуйста, проверьте правильность и актуальность ключей DMarket API",
                    )
                    return {
                        "usd": {"amount": 0},
                        "has_funds": False,
                        "balance": 0.0,
                        "available_balance": 0.0,
                        "total_balance": 0.0,
                        "error": True,
                        "error_message": "Ошибка авторизации: неверные ключи API",
                        "status_code": 401,
                        "code": "UNAUTHORIZED",
                    }

                return {
                    "usd": {"amount": 0},
                    "has_funds": False,
                    "balance": 0.0,
                    "available_balance": 0.0,
                    "total_balance": 0.0,
                    "error": True,
                    "error_message": error_message,
                    "status_code": status_code,
                    "code": error_code,
                }

            # Обработка успешного ответа
            usd_amount = 0  # общий баланс в центах
            usd_available = 0  # доступный баланс в центах
            usd_total = 0  # полный баланс в центах
            additional_info = {
                "endpoint": successful_endpoint,
            }  # дополнительная информация о балансе

            if response and isinstance(response, dict):
                logger.info(
                    f"🔍 RAW ОТВЕТ API БАЛАНСА (get_balance): {response}",
                )
                logger.info(
                    f"Анализ ответа баланса от {successful_endpoint}: {response}",
                )

                # Формат 0: Официальный формат согласно документации DMarket API (2024)
                # API возвращает: {"usd": "2550", "usdAvailableToWithdraw": "2550", "dmc": "0", "dmcAvailableToWithdraw": "0"}
                # Это ОСНОВНОЙ формат и должен проверяться ПЕРВЫМ
                if "usd" in response and "usdAvailableToWithdraw" in response:
                    try:
                        # Значения приходят как строки в центах
                        usd_str = response.get("usd", "0")
                        usd_available_str = response.get("usdAvailableToWithdraw", usd_str)

                        # Проверяем, что это строки (согласно документации)
                        if isinstance(usd_str, str) and isinstance(usd_available_str, str):
                            # Конвертируем из центов в доллары
                            usd_amount = float(usd_str)  # в центах
                            usd_available = float(usd_available_str)  # в центах
                            usd_total = usd_amount  # Обычно равны

                            logger.info(
                                f"Баланс из официального формата API (usd + usdAvailableToWithdraw): ${usd_amount / 100:.2f} USD",
                            )
                        else:
                            # Если не строки, пробуем как числа
                            usd_amount = float(usd_str) if usd_str else 0
                            usd_available = (
                                float(usd_available_str) if usd_available_str else usd_amount
                            )
                            usd_total = usd_amount

                            logger.info(
                                f"Баланс из формата API (числа): ${usd_amount / 100:.2f} USD",
                            )
                    except (ValueError, TypeError) as e:
                        logger.exception(
                            f"Ошибка при обработке официального формата API: {e}",
                        )
                        # Продолжаем проверку других форматов ниже
                        usd_amount = 0
                        usd_available = 0
                        usd_total = 0

                # Формат 1: Альтернативный формат (2024) с usdWallet в funds
                elif "funds" in response:
                    try:
                        funds = response["funds"]
                        if isinstance(funds, dict) and "usdWallet" in funds:
                            wallet = funds["usdWallet"]
                            if "balance" in wallet:
                                usd_amount = (
                                    float(wallet["balance"]) * 100
                                )  # обычно в долларах, конвертируем в центы
                            if "availableBalance" in wallet:
                                usd_available = float(wallet["availableBalance"]) * 100
                            if "totalBalance" in wallet:
                                usd_total = float(wallet["totalBalance"]) * 100

                            logger.info(
                                f"Баланс из funds.usdWallet: {usd_amount / 100:.2f} USD",
                            )
                    except (ValueError, TypeError) as e:
                        logger.exception(
                            f"Ошибка при обработке поля funds.usdWallet: {e}",
                        )

                # Новый формат по документации: balance/available/usd/dmc
                elif "balance" in response and isinstance(
                    response["balance"],
                    int | float | str,
                ):
                    try:
                        usd_amount = (
                            float(response["balance"]) * 100
                        )  # в долларах, конвертируем в центы
                        # Если есть поле available, используем его для доступного баланса
                        if "available" in response:
                            usd_available = float(response["available"]) * 100
                        else:
                            usd_available = usd_amount

                        # Если есть поле total, используем его для общего баланса
                        if "total" in response:
                            usd_total = float(response["total"]) * 100
                        else:
                            usd_total = usd_amount

                        logger.info(
                            f"Баланс из нового формата: {usd_amount / 100:.2f} USD",
                        )
                    except (ValueError, TypeError) as e:
                        logger.exception(
                            f"Ошибка при обработке баланса нового формата: {e}",
                        )

                # Формат 1: DMarket API 2023+ с usdAvailableToWithdraw и usd
                elif "usdAvailableToWithdraw" in response:
                    try:
                        usd_value = response["usdAvailableToWithdraw"]
                        if isinstance(usd_value, str):
                            # Строка может быть в формате "5.00" или "$5.00"
                            usd_available = float(usd_value.replace("$", "").strip()) * 100
                        else:
                            usd_available = float(usd_value) * 100

                        # Также проверяем общий баланс (если есть)
                        if "usd" in response:
                            usd_value = response["usd"]
                            if isinstance(usd_value, str):
                                usd_total = float(usd_value.replace("$", "").strip()) * 100
                            else:
                                usd_total = float(usd_value) * 100
                        else:
                            usd_total = usd_available

                        # Используем доступный баланс как основной
                        usd_amount = usd_available
                        logger.info(
                            f"Баланс из usdAvailableToWithdraw: {usd_amount / 100:.2f} USD",
                        )

                    except (ValueError, TypeError) as e:
                        logger.exception(
                            f"Ошибка при обработке поля usdAvailableToWithdraw: {e}",
                        )
                        # Продолжаем проверку других форматов

                # Формат 2: Старый формат DMarket API с полем usd.amount в центах
                elif "usd" in response:
                    try:
                        if isinstance(response["usd"], dict) and "amount" in response["usd"]:
                            # Формат {"usd": {"amount": 1234}}
                            usd_amount = float(response["usd"]["amount"])
                            usd_available = usd_amount
                            usd_total = usd_amount
                            logger.info(
                                f"Баланс из usd.amount: {usd_amount / 100:.2f} USD",
                            )
                        elif isinstance(response["usd"], int | float):
                            # Формат {"usd": 1234}
                            usd_amount = float(response["usd"])
                            usd_available = usd_amount
                            usd_total = usd_amount
                            logger.info(
                                f"Баланс из usd (прямое значение): {usd_amount / 100:.2f} USD",
                            )
                        elif isinstance(response["usd"], str):
                            # Формат {"usd": "$12.34"}
                            usd_amount = float(response["usd"].replace("$", "").strip()) * 100
                            usd_available = usd_amount
                            usd_total = usd_amount
                            logger.info(
                                f"Баланс из usd (строковое значение): {usd_amount / 100:.2f} USD",
                            )
                    except (ValueError, TypeError) as e:
                        logger.exception(f"Ошибка при обработке поля usd: {e}")

                # Формат 3: Формат с totalBalance как списком валют
                elif "totalBalance" in response and isinstance(
                    response["totalBalance"],
                    list,
                ):
                    for currency in response["totalBalance"]:
                        if isinstance(currency, dict) and currency.get("currency") == "USD":
                            usd_amount = float(currency.get("amount", 0))
                            usd_total = usd_amount
                            # Если есть доступный баланс
                            if "availableAmount" in currency:
                                usd_available = float(
                                    currency.get("availableAmount", 0),
                                )
                            else:
                                usd_available = usd_amount

                            logger.info(
                                f"Баланс из totalBalance: {usd_amount / 100:.2f} USD",
                            )
                            break

                # Формат 4: Формат с balance как объектом с валютами
                elif "balance" in response and isinstance(response["balance"], dict):
                    if "usd" in response["balance"]:
                        usd_value = response["balance"]["usd"]
                        if isinstance(usd_value, int | float):
                            usd_amount = float(usd_value)
                        elif isinstance(usd_value, str):
                            usd_amount = float(usd_value.replace("$", "").strip()) * 100
                        elif isinstance(usd_value, dict) and "amount" in usd_value:
                            usd_amount = float(usd_value["amount"])

                        usd_available = usd_amount
                        usd_total = usd_amount
                        logger.info(f"Баланс из balance.usd: {usd_amount / 100:.2f} USD")

                # Собираем дополнительную информацию для анализа
                for field in ["dmc", "dmcAvailableToWithdraw", "userData"]:
                    if field in response:
                        additional_info[field] = response[field]

                # Если не смогли найти баланс в известных форматах
                if usd_amount == 0 and usd_available == 0 and usd_total == 0:
                    logger.warning(
                        f"Не удалось разобрать данные о балансе из известных форматов: {response}",
                    )
                    # В качестве отладки сохраняем весь ответ API
                    additional_info["raw_response"] = response

            # Определяем результат
            min_required_balance = 1.0  # Минимальный требуемый баланс
            has_funds = (
                usd_available >= min_required_balance * 100
            )  # Проверяем, достаточно ли доступных средств

            # Если доступный баланс не определен, но есть общий баланс
            if usd_available == 0 and usd_amount > 0:
                usd_available = usd_amount

            # Если полный баланс не определен, используем максимум из доступного и общего
            if usd_total == 0:
                usd_total = max(usd_amount, usd_available)

            # Формируем результат
            result = {
                "usd": {"amount": usd_amount},
                "has_funds": has_funds,
                "balance": usd_amount / 100,  # Общий баланс в долларах
                "available_balance": usd_available / 100,  # Доступный баланс в долларах
                "total_balance": usd_total / 100,  # Полный баланс в долларах
                "error": False,
                "additional_info": additional_info,  # Сохраняем дополнительную информацию для отладки
            }

            logger.info(
                f"Итоговый баланс: ${result['balance']:.2f} USD (доступно: ${result['available_balance']:.2f}, всего: ${result['total_balance']:.2f})",
            )
            return result

        except Exception as e:
            logger.exception(f"Неожиданная ошибка при получении баланса: {e!s}")
            logger.exception(f"Стек вызовов: {traceback.format_exc()}")

            # Определяем код ошибки из сообщения исключения
            error_str = str(e)
            status_code = 500
            error_code = "EXCEPTION"
            if "404" in error_str or "not found" in error_str.lower():
                status_code = 404
                error_code = "NOT_FOUND"
            elif "401" in error_str or "unauthorized" in error_str.lower():
                status_code = 401
                error_code = "UNAUTHORIZED"

            return {
                "usd": {"amount": 0},
                "has_funds": False,
                "balance": 0.0,
                "available_balance": 0.0,
                "total_balance": 0.0,
                "error": True,
                "error_message": error_str,
                "status_code": status_code,
                "code": error_code,
            }

    async def get_user_balance(self) -> dict[str, Any]:
        """Получение баланса пользователя (устаревший метод).

        Этот метод оставлен для обратной совместимости.
        Рекомендуется использовать get_balance() вместо него.

        Returns:
            dict: Информация о балансе пользователя в том же формате, что и get_balance()

        """
        logger.warning(
            "Метод get_user_balance() устарел и может быть удален в будущих версиях. "
            "Пожалуйста, используйте get_balance() вместо него.",
        )
        return await self.get_balance()

    async def get_market_items(
        self,
        game: str = "csgo",
        limit: int = 100,
        offset: int = 0,
        currency: str = "USD",
        price_from: float | None = None,
        price_to: float | None = None,
        title: str | None = None,
        sort: str = "price",
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Get items from the marketplace.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            limit: Number of items to retrieve
            offset: Offset for pagination
            currency: Price currency (USD, EUR etc)
            price_from: Minimum price filter
            price_to: Maximum price filter
            title: Filter by item title
            sort: Sort options (price, price_desc, date, popularity)
            force_refresh: Force refresh cache

        Returns:
            Items as dict with 'objects' key containing list of items

        """
        # Build query parameters according to docs
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
            "currency": currency,
        }

        if price_from is not None:
            params["priceFrom"] = str(int(price_from * 100))  # Price in cents

        if price_to is not None:
            params["priceTo"] = str(int(price_to * 100))  # Price in cents

        if title:
            params["title"] = title

        if sort:
            params["orderBy"] = sort

        logger.debug(
            f"Запрос предметов с маркета: game={game}, limit={limit}, "
            f"price_from={price_from}, price_to={price_to}"
        )

        # Use correct endpoint from DMarket API docs
        try:
            response = await self._request(
                "GET",
                self.ENDPOINT_MARKET_ITEMS,
                params=params,
                force_refresh=force_refresh,
            )

            # Проверяем формат ответа
            if response and isinstance(response, dict):
                # DMarket API возвращает items в поле 'objects' (согласно документации)
                if "objects" in response:
                    items_count = len(response.get("objects", []))
                    logger.info(f"✅ Получено {items_count} предметов для игры {game}")
                elif "items" in response:
                    # Альтернативное название поля
                    items_count = len(response.get("items", []))
                    logger.info(
                        f"✅ Получено {items_count} предметов для игры {game} (через поле 'items')"
                    )
                else:
                    logger.warning(
                        f"⚠️ Ответ API не содержит поле 'objects' или 'items'. "
                        f"Доступные ключи: {list(response.keys())}"
                    )

            return response

        except Exception as e:
            logger.exception(f"❌ Ошибка при получении предметов: {e}")
            # Возвращаем пустой результат в случае ошибки
            return {"objects": [], "total": {"items": 0, "offers": 0}}

    async def get_all_market_items(
        self,
        game: str = "csgo",
        max_items: int = 1000,
        currency: str = "USD",
        price_from: float | None = None,
        price_to: float | None = None,
        title: str | None = None,
        sort: str = "price",
    ) -> list[dict[str, Any]]:
        """Get all items from the marketplace using pagination.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            max_items: Maximum number of items to retrieve
            currency: Price currency (USD, EUR etc)
            price_from: Minimum price filter
            price_to: Maximum price filter
            title: Filter by item title
            sort: Sort options (price, price_desc, date, popularity)

        Returns:
            List of all items as dict

        """
        all_items = []
        limit = 100  # Maximum limit per request
        offset = 0
        total_fetched = 0

        while total_fetched < max_items:
            response = await self.get_market_items(
                game=game,
                limit=limit,
                offset=offset,
                currency=currency,
                price_from=price_from,
                price_to=price_to,
                title=title,
                sort=sort,
            )

            items = response.get("items", [])
            if not items:
                break

            all_items.extend(items)
            total_fetched += len(items)
            offset += limit

            # If we received less than limit items, there are no more items
            if len(items) < limit:
                break

        return all_items[:max_items]

    async def buy_item(
        self,
        item_id: str,
        price: float,
        game: str = "csgo",
    ) -> dict[str, Any]:
        """Покупает предмет с указанным ID и ценой.

        Args:
            item_id: ID предмета для покупки
            price: Цена в USD (будет конвертирована в центы)
            game: Код игры (csgo, dota2, tf2, rust)

        Returns:
            Результат операции покупки

        """
        # Конвертируем цену из USD в центы
        price_cents = int(price * 100)

        # Формируем данные запроса согласно документации API
        data = {
            "itemId": item_id,
            "price": {
                "amount": price_cents,
                "currency": "USD",
            },
            "gameType": game,
        }

        # Выполняем запрос на покупку
        result = await self._request(
            "POST",
            self.ENDPOINT_PURCHASE,
            data=data,
        )

        # Очищаем кэш для инвентаря, т.к. он изменился
        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_INVENTORY)

        # Очищаем кэш для баланса, т.к. он также изменился
        await self.clear_cache_for_endpoint(self.ENDPOINT_BALANCE)
        await self.clear_cache_for_endpoint(self.ENDPOINT_BALANCE_LEGACY)

        return result

    async def sell_item(
        self,
        item_id: str,
        price: float,
        game: str = "csgo",
    ) -> dict[str, Any]:
        """Выставляет предмет на продажу.

        Args:
            item_id: ID предмета для продажи
            price: Цена в USD (будет конвертирована в центы)
            game: Код игры (csgo, dota2, tf2, rust)

        Returns:
            Результат операции продажи

        """
        # Конвертируем цену из USD в центы
        price_cents = int(price * 100)

        # Формируем данные запроса согласно документации API
        data = {
            "itemId": item_id,
            "price": {
                "amount": price_cents,
                "currency": "USD",
            },
        }

        # Выполняем запрос на продажу
        result = await self._request(
            "POST",
            self.ENDPOINT_SELL,
            data=data,
        )

        # Очищаем кэш для инвентаря и списка предложений, т.к. они изменились
        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_INVENTORY)
        await self.clear_cache_for_endpoint(self.ENDPOINT_USER_OFFERS)

        return result

    async def get_user_inventory(
        self,
        game: str = "csgo",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Get user inventory items.

        Args:
            game: Game name (csgo, dota2, tf2, rust etc)
            limit: Number of items to retrieve
            offset: Offset for pagination

        Returns:
            User inventory items as dict

        """
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
        }
        return await self._request(
            "GET",
            self.ENDPOINT_USER_INVENTORY,
            params=params,
        )

    async def get_suggested_price(
        self,
        item_name: str,
        game: str = "csgo",
    ) -> float | None:
        """Get suggested price for an item.

        Args:
            item_name: Item name
            game: Game name

        Returns:
            Suggested price as float or None if not found

        """
        # Find the item
        response = await self.get_market_items(
            game=game,
            title=item_name,
            limit=1,
        )

        items = response.get("items", [])
        if not items:
            return None

        item = items[0]
        suggested_price = item.get("suggestedPrice")

        if suggested_price:
            try:
                # Convert from cents to dollars
                return float(suggested_price) / 100
            except (ValueError, TypeError):
                try:
                    # Sometimes the API returns an object with amount and currency
                    amount = suggested_price.get("amount", 0)
                    return float(amount) / 100
                except (AttributeError, ValueError, TypeError):
                    return None

        return None

    # ==================== ACCOUNT METHODS ====================

    async def get_user_profile(self) -> dict[str, Any]:
        """Получает профиль пользователя согласно DMarket API.

        Returns:
            Dict[str, Any]: Информация о профиле пользователя

        Response format:
            {
                "id": "string",
                "username": "string",
                "email": "string",
                "isEmailVerified": true,
                "countryCode": "string",
                "publicKey": "string",
                ...
            }

        """
        return await self._request(
            "GET",
            "/account/v1/user",
        )

    async def get_account_details(self) -> dict[str, Any]:
        """Получает детали аккаунта пользователя.

        Returns:
            Dict[str, Any]: Информация об аккаунте

        """
        return await self._request(
            "GET",
            self.ENDPOINT_ACCOUNT_DETAILS,
        )

    # ==================== MARKETPLACE OPERATIONS ====================

    async def list_user_offers(
        self,
        game_id: str = "a8db",
        status: str = "OfferStatusActive",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Получить список предложений пользователя согласно DMarket API.

        Args:
            game_id: ID игры (a8db для CS:GO, 9a92 для Dota 2, tf2 для TF2, rust для Rust)
            status: Статус предложений (OfferStatusActive, OfferStatusSold, etc)
            limit: Количество результатов
            offset: Смещение для пагинации

        Returns:
            Dict[str, Any]: Список предложений

        Response format:
            {
                "Items": [...],
                "Total": {...},
                "Cursor": "string"
            }

        """
        params = {
            "GameID": game_id,
            "Status": status,
            "Limit": str(limit),
            "Offset": str(offset),
        }
        return await self._request(
            "GET",
            "/marketplace-api/v1/user-offers",
            params=params,
        )

    async def create_offers(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Создать предложения на продажу согласно DMarket API.

        Args:
            offers: Список предложений для создания
                Формат: [{"AssetID": "...", "Price": {"Amount": 100, "Currency": "USD"}}]

        Returns:
            Dict[str, Any]: Результат создания предложений

        """
        data = {"Offers": offers}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/create",
            data=data,
        )

    async def update_offer_prices(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Обновить цены предложений согласно DMarket API.

        Args:
            offers: Список предложений с новыми ценами
                Формат: [{"OfferID": "...", "Price": {"Amount": 100, "Currency": "USD"}}]

        Returns:
            Dict[str, Any]: Результат обновления

        """
        data = {"Offers": offers}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/edit",
            data=data,
        )

    async def remove_offers(
        self,
        offer_ids: list[str],
    ) -> dict[str, Any]:
        """Удалить предложения с продажи согласно DMarket API.

        Args:
            offer_ids: Список ID предложений для удаления

        Returns:
            Dict[str, Any]: Результат удаления

        """
        data = {"Offers": [{"OfferID": oid} for oid in offer_ids]}
        return await self._request(
            "POST",
            "/marketplace-api/v1/user-offers/delete",
            data=data,
        )

    async def deposit_assets(
        self,
        asset_ids: list[str],
    ) -> dict[str, Any]:
        """Депозит активов из Steam в DMarket согласно DMarket API v1.1.0.

        Args:
            asset_ids: Список ID активов для депозита

        Returns:
            Dict[str, Any]: ID депозита

        Response format:
            {"DepositID": "string"}

        Example:
            >>> result = await api.deposit_assets(["asset_id_1", "asset_id_2"])
            >>> deposit_id = result["DepositID"]
            >>> # Затем проверить статус:
            >>> status = await api.get_deposit_status(deposit_id)

        """
        data = {"AssetID": asset_ids}
        return await self._request(
            "POST",
            self.ENDPOINT_DEPOSIT_ASSETS,
            data=data,
        )

    async def get_deposit_status(
        self,
        deposit_id: str,
    ) -> dict[str, Any]:
        """Получить статус депозита согласно DMarket API v1.1.0.

        Args:
            deposit_id: ID депозита

        Returns:
            Dict[str, Any]: Статус депозита

        Response format:
            {
                "DepositID": "string",
                "Status": "TransferStatusPending | TransferStatusCompleted | TransferStatusFailed",
                "Assets": [...],
                "Error": "string" (если есть)
            }

        Example:
            >>> status = await api.get_deposit_status("deposit_123")
            >>> if status["Status"] == "TransferStatusCompleted":
            ...     print("Депозит завершен!")

        """
        path = f"{self.ENDPOINT_DEPOSIT_STATUS}/{deposit_id}"
        return await self._request("GET", path)

    async def withdraw_assets(
        self,
        asset_ids: list[str],
    ) -> dict[str, Any]:
        """Вывод активов из DMarket в Steam (API v1.1.0).

        Args:
            asset_ids: Список ID активов для вывода

        Returns:
            Dict[str, Any]: Результат операции вывода

        Example:
            >>> result = await api.withdraw_assets(["item_id_1", "item_id_2"])

        """
        data = {"AssetIDs": asset_ids}
        return await self._request(
            "POST",
            self.ENDPOINT_WITHDRAW_ASSETS,
            data=data,
        )

    async def sync_inventory(
        self,
        game_id: str = "a8db",
    ) -> dict[str, Any]:
        """Синхронизация инвентаря с внешними платформами (API v1.1.0).

        Args:
            game_id: ID игры для синхронизации

        Returns:
            Dict[str, Any]: Результат синхронизации

        Example:
            >>> result = await api.sync_inventory(game_id="a8db")
            >>> if result.get("success"):
            ...     print("Инвентарь синхронизирован")

        """
        data = {"GameID": game_id}
        return await self._request(
            "POST",
            self.ENDPOINT_INVENTORY_SYNC,
            data=data,
        )

    async def list_user_inventory(
        self,
        game_id: str = "a8db",
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Получить инвентарь пользователя согласно DMarket API.

        Args:
            game_id: ID игры
            limit: Количество результатов
            offset: Смещение для пагинации

        Returns:
            Dict[str, Any]: Список предметов в инвентаре

        """
        params = {
            "GameID": game_id,
            "Limit": str(limit),
            "Offset": str(offset),
        }
        return await self._request(
            "GET",
            "/marketplace-api/v1/user-inventory",
            params=params,
        )

    async def list_market_items(
        self,
        game_id: str = "a8db",
        limit: int = 100,
        offset: int = 0,
        order_by: str = "best_deal",
        order_dir: str = "desc",
        price_from: int | None = None,
        price_to: int | None = None,
        title: str | None = None,
    ) -> dict[str, Any]:
        """Получить список предметов на маркете согласно DMarket API.

        Args:
            game_id: ID игры (a8db для CS:GO, 9a92 для Dota 2)
            limit: Количество результатов (max 100)
            offset: Смещение для пагинации
            order_by: Сортировка (best_deal, price, date, discount)
            order_dir: Направление сортировки (asc, desc)
            price_from: Минимальная цена в центах
            price_to: Максимальная цена в центах
            title: Поиск по названию

        Returns:
            Dict[str, Any]: Список предметов на маркете

        Response format:
            {
                "Items": [...],
                "Total": {...},
                "Cursor": "string"
            }

        """
        params = {
            "GameID": game_id,
            "Limit": str(limit),
            "Offset": str(offset),
            "OrderBy": order_by,
            "OrderDir": order_dir,
        }

        if price_from is not None:
            params["PriceFrom"] = str(price_from)

        if price_to is not None:
            params["PriceTo"] = str(price_to)

        if title:
            params["Title"] = title

        return await self._request(
            "GET",
            "/marketplace-api/v1/market-items",
            params=params,
        )

    async def list_offers_by_title(
        self,
        game_id: str,
        title: str,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Получить предложения по названию предмета согласно DMarket API.

        Args:
            game_id: ID игры
            title: Название предмета
            limit: Количество результатов
            offset: Смещение для пагинации

        Returns:
            Dict[str, Any]: Список предложений

        """
        params = {
            "GameID": game_id,
            "Title": title,
            "Limit": str(limit),
            "Offset": str(offset),
        }
        return await self._request(
            "GET",
            "/marketplace-api/v1/offers-by-title",
            params=params,
        )

    async def buy_offers(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Купить предложения с маркета согласно DMarket API.

        Args:
            offers: Список предложений для покупки
                Формат: [{"offerId": "...", "price": {"amount": "100", "currency": "USD"}, "type": "dmarket"}]

        Returns:
            Dict[str, Any]: Результат покупки

        Response format:
            {
                "orderId": "string",
                "status": "TxPending",
                "txId": "string",
                ...
            }

        """
        data = {"offers": offers}
        return await self._request(
            "PATCH",
            "/exchange/v1/offers-buy",
            data=data,
        )

    async def get_aggregated_prices(
        self,
        titles: list[str],
        game_id: str = "a8db",
    ) -> dict[str, Any]:
        """Получить агрегированные цены для списка предметов согласно DMarket API.

        Устаревший метод, сохранен для обратной совместимости.
        Рекомендуется использовать get_aggregated_prices_bulk() вместо него.

        Args:
            titles: Список названий предметов
            game_id: ID игры

        Returns:
            Dict[str, Any]: Агрегированные цены

        """
        logger.warning(
            "Метод get_aggregated_prices() устарел. "
            "Используйте get_aggregated_prices_bulk() для API v1.1.0"
        )
        data = {
            "Titles": titles,
            "GameID": game_id,
        }
        return await self._request(
            "POST",
            "/marketplace-api/v1/aggregated-titles-by-games",
            data=data,
        )

    async def get_aggregated_prices_bulk(
        self,
        game: str,
        titles: list[str],
        limit: int = 100,
        cursor: str = "",
    ) -> dict[str, Any]:
        """Получить агрегированные цены для списка предметов (API v1.1.0).

        Новый метод согласно обновленной документации DMarket API.
        Позволяет получить лучшие цены покупки и продажи для множества предметов
        одним запросом с поддержкой пагинации.

        Args:
            game: Идентификатор игры (csgo, dota2, tf2, rust)
            titles: Список точных названий предметов
            limit: Лимит результатов на странице (max 100)
            cursor: Курсор для пагинации

        Returns:
            Dict[str, Any]: Агрегированные цены

        Response format:
            {
                "aggregatedPrices": [
                    {
                        "title": "Item Name",
                        "orderBestPrice": "1200",  # в центах
                        "orderCount": 15,
                        "offerBestPrice": "1250",  # в центах
                        "offerCount": 23
                    }
                ],
                "nextCursor": "..."
            }

        Example:
            >>> prices = await api.get_aggregated_prices_bulk(
            ...     game="csgo",
            ...     titles=["AK-47 | Redline (Field-Tested)", "AWP | Asiimov (Field-Tested)"]
            ... )
            >>> for item in prices["aggregatedPrices"]:
            ...     print(f"{item['title']}: Buy ${int(item['orderBestPrice'])/100:.2f}")

        """
        data = {
            "filter": {
                "game": game,
                "titles": titles,
            },
            "limit": str(limit),
            "cursor": cursor,
        }

        logger.debug(f"Запрос агрегированных цен для {len(titles)} предметов (игра: {game})")

        return await self._request(
            "POST",
            self.ENDPOINT_AGGREGATED_PRICES_POST,
            data=data,
        )

    async def get_sales_history_aggregator(
        self,
        game_id: str,
        title: str,
        limit: int = 20,
        offset: int = 0,
        filters: str | None = None,
        tx_operation_type: list[str] | None = None,
    ) -> dict[str, Any]:
        """Получить историю продаж предмета из агрегатора согласно DMarket API.

        Args:
            game_id: ID игры (a8db, 9a92, tf2, rust)
            title: Название предмета
            limit: Количество результатов (max 20)
            offset: Смещение для пагинации
            filters: Фильтры (например: "exterior[]=factory new,phase[]=phase-1")
            tx_operation_type: Типы операций (["Offer"], ["Target"], или обе)

        Returns:
            Dict[str, Any]: История продаж

        Response format:
            {
                "sales": [
                    {"price": "string", "date": "string", "txOperationType": "Offer", ...}
                ]
            }

        """
        params = {
            "gameId": game_id,
            "title": title,
            "limit": str(limit),
            "offset": str(offset),
        }

        if filters:
            params["filters"] = filters

        if tx_operation_type:
            params["txOperationType"] = tx_operation_type

        return await self._request(
            "GET",
            "/trade-aggregator/v1/last-sales",
            params=params,
        )

    async def get_market_best_offers(
        self,
        game: str = "csgo",
        title: str | None = None,
        limit: int = 50,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Получает лучшие предложения на маркете.

        Args:
            game: Идентификатор игры
            title: Название предмета (опционально)
            limit: Лимит результатов
            currency: Валюта цен

        Returns:
            Dict[str, Any]: Лучшие предложения

        """
        params = {
            "gameId": game,
            "limit": limit,
            "currency": currency,
        }

        if title:
            params["title"] = title

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_BEST_OFFERS,
            params=params,
        )

    async def get_market_aggregated_prices(
        self,
        game: str = "csgo",
        title: str | None = None,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Получает агрегированные цены на предметы.

        Args:
            game: Идентификатор игры
            title: Название предмета (опционально)
            currency: Валюта цен

        Returns:
            Dict[str, Any]: Агрегированные цены

        """
        params = {
            "gameId": game,
            "currency": currency,
        }

        if title:
            params["title"] = title

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_PRICE_AGGREGATED,
            params=params,
        )

    async def get_sales_history(
        self,
        game: str,
        title: str,
        days: int = 7,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Получает историю продаж предмета.

        Args:
            game: Идентификатор игры
            title: Название предмета
            days: Количество дней истории
            currency: Валюта цен

        Returns:
            Dict[str, Any]: История продаж

        """
        params = {
            "gameId": game,
            "title": title,
            "days": days,
            "currency": currency,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_SALES_HISTORY,
            params=params,
        )

    async def get_item_price_history(
        self,
        game: str,
        title: str,
        period: str = "last_month",
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Получает историю цен предмета.

        Args:
            game: Идентификатор игры
            title: Название предмета
            period: Период ("last_day", "last_week", "last_month", "last_year")
            currency: Валюта цен

        Returns:
            Dict[str, Any]: История цен

        """
        params = {
            "gameId": game,
            "title": title,
            "period": period,
            "currency": currency,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_ITEM_PRICE_HISTORY,
            params=params,
        )

    async def get_market_meta(
        self,
        game: str = "csgo",
    ) -> dict[str, Any]:
        """Получает метаданные маркета для указанной игры.

        Args:
            game: Идентификатор игры

        Returns:
            Dict[str, Any]: Метаданные маркета

        """
        params = {
            "gameId": game,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_MARKET_META,
            params=params,
        )

    async def edit_offer(
        self,
        offer_id: str,
        price: float,
        currency: str = "USD",
    ) -> dict[str, Any]:
        """Редактирует существующее предложение.

        Args:
            offer_id: ID предложения
            price: Новая цена
            currency: Валюта цены

        Returns:
            Dict[str, Any]: Результат редактирования

        """
        data = {
            "offerId": offer_id,
            "price": {
                "amount": int(price * 100),  # В центах
                "currency": currency,
            },
        }

        return await self._request(
            "POST",
            self.ENDPOINT_OFFER_EDIT,
            data=data,
        )

    async def delete_offer(
        self,
        offer_id: str,
    ) -> dict[str, Any]:
        """Удаляет предложение.

        Args:
            offer_id: ID предложения

        Returns:
            Dict[str, Any]: Результат удаления

        """
        data = {
            "offers": [offer_id],
        }

        return await self._request(
            "DELETE",
            self.ENDPOINT_OFFER_DELETE,
            data=data,
        )

    async def get_active_offers(
        self,
        game: str = "csgo",
        limit: int = 50,
        offset: int = 0,
        status: str = "active",
    ) -> dict[str, Any]:
        """Получает активные предложения пользователя.

        Args:
            game: Идентификатор игры
            limit: Лимит результатов
            offset: Смещение для пагинации
            status: Статус предложений ("active", "completed", "canceled")

        Returns:
            Dict[str, Any]: Активные предложения

        """
        params = {
            "gameId": game,
            "limit": limit,
            "offset": offset,
            "status": status,
        }

        return await self._request(
            "GET",
            self.ENDPOINT_ACCOUNT_OFFERS,
            params=params,
        )

    # ==================== МЕТОДЫ ДЛЯ РАБОТЫ С ТАРГЕТАМИ ====================

    async def create_targets(
        self,
        game_id: str,
        targets: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Создать таргеты (buy orders) для предметов.

        Args:
            game_id: Идентификатор игры (a8db, 9a92, tf2, rust)
            targets: Список таргетов для создания

        Returns:
            Результат создания таргетов

        Example:
            >>> targets = [{
            ...     'Title': 'AK-47 | Redline (Field-Tested)',
            ...     'Amount': 1,
            ...     'Price': {'Amount': 800, 'Currency': 'USD'}
            ... }]
            >>> result = await api.create_targets('a8db', targets)

        """
        data = {"GameID": game_id, "Targets": targets}

        return await self._request(
            "POST",
            "/marketplace-api/v1/user-targets/create",
            data=data,
        )

    async def get_user_targets(
        self,
        game_id: str,
        status: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """Получить список таргетов пользователя.

        Args:
            game_id: Идентификатор игры
            status: Фильтр по статусу (TargetStatusActive, TargetStatusInactive)
            limit: Лимит результатов
            offset: Смещение для пагинации

        Returns:
            Список таргетов пользователя

        """
        params = {"GameID": game_id, "Limit": str(limit), "Offset": str(offset)}

        if status:
            params["BasicFilters.Status"] = status

        return await self._request(
            "GET",
            "/marketplace-api/v1/user-targets",
            params=params,
        )

    async def delete_targets(
        self,
        target_ids: list[str],
    ) -> dict[str, Any]:
        """Удалить таргеты.

        Args:
            target_ids: Список ID таргетов для удаления

        Returns:
            Результат удаления

        """
        data = {"Targets": [{"TargetID": tid} for tid in target_ids]}

        return await self._request(
            "POST",
            "/marketplace-api/v1/user-targets/delete",
            data=data,
        )

    async def get_targets_by_title(
        self,
        game_id: str,
        title: str,
    ) -> dict[str, Any]:
        """Получить таргеты для конкретного предмета (агрегированные данные, API v1.1.0).

        Новый эндпоинт согласно обновленной документации DMarket API.
        Позволяет получить все активные заявки на покупку (buy orders/targets)
        для конкретной игры и названия предмета.

        Args:
            game_id: Идентификатор игры (csgo, dota2, tf2, rust)
            title: Точное название предмета в игре

        Returns:
            Dict[str, Any]: Список таргетов для предмета

        Response format:
            {
                "orders": [
                    {
                        "amount": 10,
                        "price": "1200",  # в центах
                        "title": "AK-47 | Redline (Field-Tested)",
                        "attributes": {
                            "exterior": "Field-Tested"
                        }
                    }
                ]
            }

        Example:
            >>> targets = await api.get_targets_by_title(
            ...     game_id="csgo",
            ...     title="AK-47 | Redline (Field-Tested)"
            ... )
            >>> for target in targets["orders"]:
            ...     print(f"Price: ${int(target['price'])/100:.2f}, Amount: {target['amount']}")

        """
        # URL-encode названия для правильной передачи
        from urllib.parse import quote

        encoded_title = quote(title)
        path = f"{self.ENDPOINT_TARGETS_BY_TITLE}/{game_id}/{encoded_title}"

        logger.debug(f"Запрос таргетов для '{title}' (игра: {game_id})")

        return await self._request("GET", path)

    async def get_closed_targets(
        self,
        limit: int = 50,
        status: str | None = None,
        from_timestamp: int | None = None,
        to_timestamp: int | None = None,
    ) -> dict[str, Any]:
        """Получить историю закрытых таргетов.

        Args:
            limit: Лимит результатов
            status: Фильтр по статусу (successful, reverted, trade_protected)
            from_timestamp: Начало периода (timestamp)
            to_timestamp: Конец периода (timestamp)

        Returns:
            История закрытых таргетов

        """
        params = {"Limit": str(limit), "OrderDir": "desc"}

        if status:
            params["Status"] = status

        if from_timestamp:
            params["TargetClosed.From"] = str(from_timestamp)

        if to_timestamp:
            params["TargetClosed.To"] = str(to_timestamp)

        return await self._request(
            "GET",
            "/marketplace-api/v1/user-targets/closed",
            params=params,
        )

    # ==================== КОНЕЦ МЕТОДОВ ТАРГЕТОВ ====================

    async def direct_balance_request(self) -> dict[str, Any]:
        """Выполняет прямой запрос баланса через REST API используя Ed25519.

        Этот метод используется как альтернативный способ получения баланса
        в случае проблем с основным методом.

        Returns:
            dict: Результат запроса баланса или словарь с ошибкой

        """
        try:
            # Актуальный эндпоинт баланса (2024) согласно документации DMarket
            endpoint = self.ENDPOINT_BALANCE
            base_url = self.api_url
            full_url = f"{base_url}{endpoint}"

            # Формируем timestamp для запроса
            timestamp = str(int(time.time()))

            # Build string to sign: GET + endpoint + timestamp
            string_to_sign = f"GET{endpoint}{timestamp}"

            logger.debug(f"Direct balance request - string to sign: {string_to_sign}")

            try:
                # Convert secret key from string to bytes
                if isinstance(self.secret_key, str):
                    secret_key_str = self._secret_key
                else:
                    secret_key_str = self.secret_key.decode("utf-8")

                # Try different formats for secret key
                try:
                    # Format 1: HEX format (64 chars = 32 bytes)
                    if len(secret_key_str) == 64:
                        secret_key_bytes = bytes.fromhex(secret_key_str)
                    # Format 2: Base64 format
                    elif len(secret_key_str) == 44 or "=" in secret_key_str:
                        import base64

                        secret_key_bytes = base64.b64decode(secret_key_str)
                    # Format 3: Take first 64 hex chars
                    elif len(secret_key_str) >= 64:
                        secret_key_bytes = bytes.fromhex(secret_key_str[:64])
                    else:
                        # Fallback
                        secret_key_bytes = secret_key_str.encode("utf-8")[:32].ljust(32, b"\0")
                except Exception as conv_error:
                    logger.exception(f"Error converting secret key in direct request: {conv_error}")
                    raise

                # Create Ed25519 signing key
                signing_key = nacl.signing.SigningKey(secret_key_bytes)

                # Sign the message
                signed = signing_key.sign(string_to_sign.encode("utf-8"))

                # Extract signature in hex format
                signature = signed.signature.hex()

                logger.debug("Direct balance request - signature generated")

            except Exception as sig_error:
                logger.exception(f"Error generating Ed25519 signature: {sig_error}")
                # Fallback to HMAC if Ed25519 fails
                secret_key = (
                    self.secret_key
                    if isinstance(self.secret_key, bytes)
                    else self.secret_key.encode("utf-8")
                )
                signature = hmac.new(
                    secret_key,
                    string_to_sign.encode(),
                    hashlib.sha256,
                ).hexdigest()

            # Формируем заголовки запроса согласно документации DMarket
            headers = {
                "X-Api-Key": self.public_key,
                "X-Sign-Date": timestamp,
                "X-Request-Sign": f"dmar ed25519 {signature}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            }

            logger.debug(f"Выполняем прямой запрос к {endpoint}")

            # Получаем клиент
            client = await self._get_client()

            # Выполняем запрос через httpx с circuit breaker
            response = await call_with_circuit_breaker(
                client.get, full_url, headers=headers, timeout=10
            )

            # Если запрос успешен (HTTP 200)
            if response.status_code == 200:
                try:
                    # Парсим JSON ответ
                    response_data = response.json()

                    # Проверяем структуру ответа согласно документации DMarket
                    if response_data:
                        logger.info(f"Успешный прямой запрос к {endpoint}")
                        logger.info(f"🔍 RAW ОТВЕТ API БАЛАНСА: {response_data}")
                        logger.debug(f"Ответ API баланса: {response_data}")

                        # Извлекаем значения баланса из ответа согласно официальной документации
                        # API возвращает: {"usd": "2550", "usdAvailableToWithdraw": "2550", "dmc": "0", "dmcAvailableToWithdraw": "0"}
                        # где значения в центах для USD и dimoshi для DMC (все как строки)

                        # Получаем USD баланс (в центах как строка)
                        usd_str = response_data.get("usd", "0")
                        usd_available_str = response_data.get("usdAvailableToWithdraw", "0")
                        usd_trade_protected_str = response_data.get("usdTradeProtected", "0")

                        # Конвертируем из строки в центы, затем в доллары
                        try:
                            balance_cents = float(usd_str)  # общий баланс в центах
                            available_cents = float(usd_available_str)  # доступный баланс в центах
                            trade_protected_cents = float(
                                usd_trade_protected_str
                            )  # защищенный в торговле

                            # Конвертируем центы в доллары
                            balance = balance_cents / 100
                            available = available_cents / 100
                            trade_protected = trade_protected_cents / 100

                            # Вычисляем заблокированные средства
                            locked = balance - available - trade_protected

                            total = balance  # Обычно total = balance

                            logger.info(
                                f"💰 Распарсен баланс: Всего ${balance:.2f} USD (доступно: ${available:.2f}, заблокировано: ${locked:.2f}, защищено торговлей: ${trade_protected:.2f})"
                            )
                        except (ValueError, TypeError) as e:
                            logger.exception(
                                f"Ошибка конвертации баланса: {e}, usd={usd_str}, usdAvailable={usd_available_str}"
                            )
                            balance = 0.0
                            available = 0.0
                            total = 0.0
                            locked = 0.0
                            trade_protected = 0.0

                        return {
                            "success": True,
                            "data": {
                                "balance": balance,
                                "available": available,
                                "total": total,
                                "locked": locked,
                                "trade_protected": trade_protected,
                            },
                        }
                except json.JSONDecodeError:
                    logger.warning(
                        f"Ошибка декодирования JSON при прямом запросе: {response.text}",
                    )

            # Если статус 401, значит проблема с авторизацией
            if response.status_code == 401:
                logger.error("Ошибка авторизации (401) при прямом запросе баланса")
                return {
                    "success": False,
                    "status_code": 401,
                    "error": "Ошибка авторизации: неверные ключи API",
                }

            # Для всех остальных ошибок
            logger.warning(
                f"Ошибка при прямом запросе: HTTP {response.status_code} - {response.text}",
            )
            return {
                "success": False,
                "status_code": response.status_code,
                "error": f"Ошибка HTTP {response.status_code}: {response.text}",
            }

        except CircuitBreakerError as e:
            logger.exception(f"Circuit breaker open for direct balance request: {e}")
            return {
                "success": False,
                "error": f"Circuit breaker open: {e}",
            }
        except Exception as e:
            logger.exception(f"Исключение при прямом запросе баланса: {e!s}")
            return {
                "success": False,
                "error": str(e),
            }
