# 🛠️ Руководство по внедрению паттернов Copilot SDK

**Дата**: 23 января 2026 г.  
**Версия**: 1.0  
**Статус**: Готово к использованию

---

## 📋 Обзор

Это руководство показывает, как внедрить паттерны из DMarket-Telegram-Bot в ваш проект для улучшения работы с GitHub Copilot.

---

## 🚀 Быстрый старт (15 минут)

### Шаг 1: Создайте структуру директорий

```bash
mkdir -p .github/instructions
mkdir -p .github/prompts
mkdir -p .github/workflows
```

### Шаг 2: Скопируйте базовые инструкции

Скопируйте из этого репозитория:
- `.github/instructions/master.instructions.md` → ваш проект
- `.github/copilot-instructions.md` → ваш проект

### Шаг 3: Адаптируйте под свой проект

Отредактируйте `master.instructions.md`:
```markdown
# Master Instructions

## Project Info
- **Name**: Your Project Name
- **Tech Stack**: Your stack (e.g., TypeScript, React, Node.js)
- **Version**: 1.0.0

## Code Style
- Use TypeScript strict mode
- Prefer async/await over callbacks
- Use ESLint + Prettier
```

### Шаг 4: Добавьте file-pattern instructions

Создайте `.github/instructions/typescript.instructions.md`:
```markdown
# TypeScript Instructions

Apply to: `src/**/*.ts`, `src/**/*.tsx`

## Rules
- Use strict TypeScript (noImplicitAny: true)
- Prefer interfaces over types
- Always add JSDoc comments for public APIs
- Use Zod for runtime validation

## Example
```typescript
interface UserData {
  id: string;
  email: string;
  createdAt: Date;
}

/**
 * Fetch user by ID
 * @param userId - User identifier
 * @returns User data or null if not found
 */
async function getUserById(userId: string): Promise<UserData | null> {
  // Implementation
}
```
```

### Шаг 5: Тестируйте

Откройте любой `.ts` файл в VS Code и спросите Copilot:
```
"Generate a function following the project guidelines"
```

Copilot должен автоматически применить инструкции!

---

## 📚 Компонент 1: File-Pattern Instructions

### Что это?

Автоматическое применение инструкций на основе паттернов файлов.

### Как работает?

1. GitHub Copilot сканирует `.github/instructions/`
2. При открытии файла применяются подходящие инструкции
3. Разработчик не тратит время на объяснение контекста

### Пример структуры

```
.github/instructions/
├── master.instructions.md        # Общие правила (все файлы)
├── typescript.instructions.md    # src/**/*.ts
├── react.instructions.md         # src/**/*.tsx
├── testing.instructions.md       # tests/**/*.test.ts
├── api.instructions.md           # src/api/**/*.ts
└── database.instructions.md      # src/db/**/*.ts
```

### Шаблон instruction файла

```markdown
# [Technology] Instructions

Apply to: `pattern/to/match/**/*.ext`

## Overview
Brief description of what this instruction covers.

## Code Style
- Rule 1
- Rule 2
- Rule 3

## Best Practices
- Practice 1
- Practice 2

## Example
```[language]
// Example code following the rules
```

## Anti-patterns
❌ Don't do this
✅ Do this instead
```

### Реальный пример из DMarket Bot

**Файл**: `.github/instructions/python-style.instructions.md`

```markdown
# Python Code Style Instructions

Apply to: `src/**/*.py`

## Type Annotations
- Use Python 3.11+ syntax: `list[str]` not `List[str]`
- Use `|` for union types: `str | None` not `Optional[str]`

## Async Code
- Use `async def` for all I/O operations
- Use `await` for all async calls
- Use `asyncio.gather()` for parallel execution

## Example
```python
async def fetch_data(url: str) -> dict[str, any] | None:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.json()
```
```

---

## 🎨 Компонент 2: Prompt Library

### Что это?

Библиотека переиспользуемых промпт-шаблонов для типовых задач.

### Структура

```
.github/prompts/
├── test-generator.prompt.md      # Генерация тестов
├── component-generator.prompt.md # Генерация компонентов
├── api-endpoint.prompt.md        # Генерация API endpoints
├── error-handling.prompt.md      # Обработка ошибок
└── documentation.prompt.md       # Генерация документации
```

### Шаблон prompt файла

```markdown
# [Task Name] Prompt

## Purpose
What this prompt helps generate.

## Template
```[language]
[code template with placeholders]
```

## Variables
- `${variable1}`: Description
- `${variable2}`: Description

## Usage
How to use this prompt with Copilot.

## Example Input
Sample input data.

## Example Output
Expected generated code.
```

### Пример: Test Generator

**Файл**: `.github/prompts/test-generator.prompt.md`

```markdown
# Test Generator Prompt

## Purpose
Generate unit tests following AAA pattern (Arrange-Act-Assert).

## Template
```typescript
describe('${functionName}', () => {
  it('should ${expectedBehavior} when ${condition}', async () => {
    // Arrange
    const ${mockData} = createMock${DataType}();
    
    // Act
    const result = await ${functionName}(${mockData});
    
    // Assert
    expect(result).toBe(${expectedResult});
  });
});
```

## Variables
- `functionName`: Name of function to test
- `expectedBehavior`: What should happen
- `condition`: When it should happen
- `mockData`: Test data variable name
- `DataType`: Type of test data
- `expectedResult`: Expected output

## Usage
1. Open test file
2. Type: "Generate tests for [function] using test-generator prompt"
3. Copilot will use this template

## Example

Input:
```typescript
async function calculateTotal(items: Item[]): Promise<number> {
  return items.reduce((sum, item) => sum + item.price, 0);
}
```

Generated Test:
```typescript
describe('calculateTotal', () => {
  it('should return sum of all item prices when given array of items', async () => {
    // Arrange
    const mockItems = [
      { id: '1', price: 10 },
      { id: '2', price: 20 },
    ];
    
    // Act
    const result = await calculateTotal(mockItems);
    
    // Assert
    expect(result).toBe(30);
  });
  
  it('should return 0 when given empty array', async () => {
    // Arrange
    const mockItems: Item[] = [];
    
    // Act
    const result = await calculateTotal(mockItems);
    
    // Assert
    expect(result).toBe(0);
  });
});
```
```

### Как использовать prompts

#### Метод 1: Явный запрос
```
"Generate a React component using component-generator prompt with name=UserProfile"
```

#### Метод 2: Контекстный запрос
Откройте файл рядом с `.github/prompts/` и Copilot автоматически предложит использовать подходящий промпт.

#### Метод 3: Snippet triggers
В VS Code настройте сниппеты:
```json
{
  "Generate Test": {
    "prefix": "gentest",
    "body": [
      "// Using test-generator.prompt.md",
      "// Function: $1",
      "// Expected: $2"
    ]
  }
}
```

---

## 🤖 Компонент 3: AI Skills System

### Что это?

Стандартизированный формат SKILL.md для описания модульных AI-возможностей.

### Структура SKILL.md

```markdown
# Skill: [Skill Name]

## Category
[Category name: Data & AI, DevOps, Security, etc.]

## Description
Brief description of what this skill does.

## Dependencies
- Dependency 1: version
- Dependency 2: version

## Installation
```bash
npm install [package]
```

## API
```[language]
// How to use this skill
```

## Performance Metrics
- Throughput: [ops/sec]
- Latency: [ms] (p50/p95/p99)
- Accuracy: [percentage]

## Examples
### Example 1: [Use case]
```[language]
// Code example
```

## Testing
```bash
# How to test this skill
```

## License
MIT
```

### Пример: API Client Generator Skill

**Файл**: `src/codegen/SKILL_API_CLIENT_GENERATOR.md`

```markdown
# Skill: API Client Generator

## Category
Development Tools

## Description
Automatically generates TypeScript API clients from OpenAPI/Swagger specifications with full type safety, error handling, and retry logic.

## Dependencies
- TypeScript 5.0+
- openapi-typescript 6.0+
- axios 1.6+

## Installation
```bash
npm install openapi-typescript axios
```

## API
```typescript
import { generateAPIClient } from './api-client-generator';

// Generate client from OpenAPI spec
const client = await generateAPIClient({
  specUrl: 'https://api.example.com/openapi.json',
  outputDir: './src/generated',
  includeTypes: true,
  includeRetry: true,
  timeout: 10000
});

// Use generated client
const users = await client.users.getAll();
```

## Performance Metrics
- Throughput: 100 specs/minute
- Generation time: 2-5 seconds per spec
- Accuracy: 99% (type coverage)

## Examples

### Example 1: Generate GitHub API Client
```typescript
const githubClient = await generateAPIClient({
  specUrl: 'https://api.github.com/openapi.json',
  outputDir: './src/clients/github',
  clientName: 'GitHubClient',
  options: {
    retry: {
      maxAttempts: 3,
      backoffMultiplier: 2
    },
    timeout: 30000,
    headers: {
      'User-Agent': 'MyApp/1.0'
    }
  }
});

// Usage
const repos = await githubClient.repos.list({
  org: 'microsoft',
  type: 'public'
});
```

### Example 2: Custom Error Handling
```typescript
const client = await generateAPIClient({
  specUrl: './openapi.yaml',
  outputDir: './src/api',
  errorHandler: (error) => {
    if (error.status === 429) {
      // Handle rate limiting
      return retry({ delay: error.headers['retry-after'] * 1000 });
    }
    throw error;
  }
});
```

## Testing
```bash
# Run skill tests
npm test -- src/codegen/api-client-generator.test.ts

# Test with real OpenAPI specs
npm run test:integration -- --spec https://petstore.swagger.io/v2/swagger.json
```

## License
MIT
```

### Как создать свой Skill

1. **Определите категорию**
   - Data & AI
   - Development Tools
   - DevOps & Infrastructure
   - Security
   - Testing

2. **Создайте SKILL.md файл**
   ```bash
   touch src/your-module/SKILL_[NAME].md
   ```

3. **Заполните секции**
   - Description (что делает)
   - API (как использовать)
   - Performance (метрики)
   - Examples (примеры)

4. **Добавьте тесты**
   - Unit tests
   - Integration tests
   - Performance tests

5. **Документируйте**
   - README в модуле
   - API docs
   - Changelog

---

## 🧪 Компонент 4: Advanced Testing

### VCR.py Pattern (HTTP Recording)

**Цель**: Записывать HTTP-запросы один раз, воспроизводить в тестах.

#### Setup (Python)

```python
# conftest.py
import pytest
import vcr

@pytest.fixture
def vcr_config():
    return {
        "cassette_library_dir": "tests/cassettes",
        "record_mode": "once",
        "match_on": ["uri", "method"],
        "filter_headers": ["authorization", "x-api-key"],
    }

@pytest.fixture
def api_vcr(vcr_config):
    return vcr.VCR(**vcr_config)
```

#### Usage

```python
@pytest.mark.asyncio
async def test_fetch_user(api_vcr):
    """Test user fetch with recorded response."""
    with api_vcr.use_cassette("user_fetch.yaml"):
        api = UserAPI()
        user = await api.fetch_user("123")
        assert user.id == "123"
```

#### Setup (JavaScript/TypeScript)

```typescript
// Use Polly.js for HTTP recording
import { Polly } from '@pollyjs/core';
import NodeHttpAdapter from '@pollyjs/adapter-node-http';
import FSPersister from '@pollyjs/persister-fs';

Polly.register(NodeHttpAdapter);
Polly.register(FSPersister);

describe('API Tests', () => {
  let polly: Polly;

  beforeEach(() => {
    polly = new Polly('API Recording', {
      adapters: ['node-http'],
      persister: 'fs',
      persisterOptions: {
        fs: {
          recordingsDir: './tests/recordings'
        }
      }
    });
  });

  afterEach(async () => {
    await polly.stop();
  });

  it('fetches user data', async () => {
    const response = await fetch('https://api.example.com/users/1');
    const data = await response.json();
    expect(data.id).toBe(1);
  });
});
```

### Hypothesis Pattern (Property-Based Testing)

**Цель**: Генерировать тысячи тестовых случаев автоматически.

#### Python Example

```python
from hypothesis import given, strategies as st

@given(
    price=st.floats(min_value=0.01, max_value=10000.0),
    quantity=st.integers(min_value=1, max_value=1000)
)
def test_calculate_total_properties(price, quantity):
    """Test total calculation satisfies mathematical properties."""
    total = calculate_total(price, quantity)
    
    # Property 1: Total should be positive
    assert total > 0
    
    # Property 2: Total should equal price * quantity
    assert abs(total - (price * quantity)) < 0.01
    
    # Property 3: Doubling quantity doubles total
    double_total = calculate_total(price, quantity * 2)
    assert abs(double_total - (total * 2)) < 0.01
```

#### TypeScript Example (using fast-check)

```typescript
import fc from 'fast-check';

describe('calculateTotal', () => {
  it('should satisfy mathematical properties', () => {
    fc.assert(
      fc.property(
        fc.float({ min: 0.01, max: 10000 }),
        fc.integer({ min: 1, max: 1000 }),
        (price, quantity) => {
          const total = calculateTotal(price, quantity);
          
          // Properties
          expect(total).toBeGreaterThan(0);
          expect(Math.abs(total - price * quantity)).toBeLessThan(0.01);
        }
      ),
      { numRuns: 1000 } // Run 1000 random test cases
    );
  });
});
```

### Pact Pattern (Contract Testing)

**Цель**: Тестировать договор между consumer и provider API.

#### Consumer Test (TypeScript)

```typescript
import { PactV3 } from '@pact-foundation/pact';
import path from 'path';

const provider = new PactV3({
  consumer: 'UserService',
  provider: 'APIGateway',
  dir: path.resolve(process.cwd(), 'pacts'),
});

describe('User API Contract', () => {
  it('should fetch user by ID', async () => {
    await provider
      .given('user 123 exists')
      .uponReceiving('a request for user 123')
      .withRequest({
        method: 'GET',
        path: '/users/123',
        headers: { Accept: 'application/json' },
      })
      .willRespondWith({
        status: 200,
        headers: { 'Content-Type': 'application/json' },
        body: {
          id: '123',
          name: 'John Doe',
          email: 'john@example.com',
        },
      });

    await provider.executeTest(async (mockServer) => {
      const api = new UserAPI(mockServer.url);
      const user = await api.getUser('123');
      
      expect(user.id).toBe('123');
      expect(user.name).toBe('John Doe');
    });
  });
});
```

---

## ⚙️ Компонент 5: CI/CD Integration

### GitHub Actions Example

**Файл**: `.github/workflows/copilot-validation.yml`

```yaml
name: Copilot Configuration Validation

on:
  pull_request:
    paths:
      - '.github/instructions/**'
      - '.github/prompts/**'
      - '.github/copilot-instructions.md'
  push:
    branches: [main]
    paths:
      - '.github/instructions/**'
      - '.github/prompts/**'

jobs:
  validate-instructions:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Validate Markdown Files
        run: |
          # Check all .md files are valid
          find .github/instructions -name "*.md" -exec \
            markdown-link-check {} \;
          
          find .github/prompts -name "*.md" -exec \
            markdown-link-check {} \;
      
      - name: Validate File Patterns
        run: |
          # Ensure patterns match expected files
          python scripts/validate_patterns.py
      
      - name: Check for Duplicates
        run: |
          # Check for duplicate instructions
          python scripts/check_duplicates.py

  test-with-copilot:
    runs-on: ubuntu-latest
    needs: validate-instructions
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Test Code Generation
        run: |
          # Test that Copilot can use instructions
          npm run test:copilot-integration
```

### Validation Scripts

**Файл**: `scripts/validate_patterns.py`

```python
#!/usr/bin/env python3
"""Validate that instruction patterns match expected files."""

import glob
import re
from pathlib import Path

def extract_pattern(instruction_file: Path) -> str | None:
    """Extract file pattern from instruction file."""
    content = instruction_file.read_text()
    
    # Look for "Apply to: pattern" or "Applies to: pattern"
    match = re.search(r'Apply(?:s)? to:\s*`([^`]+)`', content)
    if match:
        return match.group(1)
    return None

def validate_patterns():
    """Validate all instruction patterns."""
    instructions_dir = Path('.github/instructions')
    errors = []
    
    for instruction_file in instructions_dir.glob('*.md'):
        if instruction_file.name == 'master.instructions.md':
            continue
        
        pattern = extract_pattern(instruction_file)
        if not pattern:
            errors.append(f"No pattern found in {instruction_file}")
            continue
        
        # Check if pattern matches any files
        matching_files = list(glob.glob(pattern, recursive=True))
        if not matching_files:
            errors.append(
                f"Pattern '{pattern}' in {instruction_file} matches no files"
            )
    
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  ❌ {error}")
        exit(1)
    else:
        print("✅ All patterns validated successfully")

if __name__ == '__main__':
    validate_patterns()
```

---

## 📊 Компонент 6: Performance Profiling

### Python Implementation

```python
# utils/profiler.py
import time
import functools
from typing import Callable, Any
import structlog

logger = structlog.get_logger(__name__)

class PerformanceProfiler:
    """Track performance metrics for functions."""
    
    _metrics: dict[str, list[float]] = {}
    
    @classmethod
    def record(cls, name: str, duration_ms: float):
        """Record execution time."""
        if name not in cls._metrics:
            cls._metrics[name] = []
        cls._metrics[name].append(duration_ms)
    
    @classmethod
    def get_stats(cls, name: str) -> dict[str, float]:
        """Get percentile statistics."""
        if name not in cls._metrics:
            return {}
        
        values = sorted(cls._metrics[name])
        count = len(values)
        
        return {
            'count': count,
            'p50': values[int(count * 0.50)],
            'p95': values[int(count * 0.95)],
            'p99': values[int(count * 0.99)],
            'min': values[0],
            'max': values[-1],
        }

def profile(name: str | None = None):
    """Decorator to profile function execution."""
    def decorator(func: Callable) -> Callable:
        profile_name = name or func.__name__
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                
                PerformanceProfiler.record(profile_name, elapsed_ms)
                logger.debug(
                    'function_profiled',
                    name=profile_name,
                    duration_ms=elapsed_ms
                )
                
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    'function_error',
                    name=profile_name,
                    duration_ms=elapsed_ms,
                    error=str(e)
                )
                raise
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed_ms = (time.perf_counter() - start) * 1000
                
                PerformanceProfiler.record(profile_name, elapsed_ms)
                logger.debug(
                    'function_profiled',
                    name=profile_name,
                    duration_ms=elapsed_ms
                )
                
                return result
            except Exception as e:
                elapsed_ms = (time.perf_counter() - start) * 1000
                logger.error(
                    'function_error',
                    name=profile_name,
                    duration_ms=elapsed_ms,
                    error=str(e)
                )
                raise
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator

# Usage
@profile('fetch_user')
async def fetch_user(user_id: str):
    # Implementation
    pass

# Get stats
stats = PerformanceProfiler.get_stats('fetch_user')
print(f"P95 latency: {stats['p95']}ms")
```

### TypeScript Implementation

```typescript
// utils/profiler.ts
export class PerformanceProfiler {
  private static metrics: Map<string, number[]> = new Map();

  static record(name: string, durationMs: number): void {
    if (!this.metrics.has(name)) {
      this.metrics.set(name, []);
    }
    this.metrics.get(name)!.push(durationMs);
  }

  static getStats(name: string): PerformanceStats | null {
    const values = this.metrics.get(name);
    if (!values || values.length === 0) {
      return null;
    }

    const sorted = [...values].sort((a, b) => a - b);
    const count = sorted.length;

    return {
      count,
      p50: sorted[Math.floor(count * 0.50)],
      p95: sorted[Math.floor(count * 0.95)],
      p99: sorted[Math.floor(count * 0.99)],
      min: sorted[0],
      max: sorted[count - 1],
    };
  }
}

interface PerformanceStats {
  count: number;
  p50: number;
  p95: number;
  p99: number;
  min: number;
  max: number;
}

export function profile(name?: string) {
  return function (
    target: any,
    propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;
    const profileName = name || `${target.constructor.name}.${propertyKey}`;

    descriptor.value = async function (...args: any[]) {
      const start = performance.now();
      try {
        const result = await originalMethod.apply(this, args);
        const duration = performance.now() - start;
        
        PerformanceProfiler.record(profileName, duration);
        console.debug(`[PROFILE] ${profileName}: ${duration.toFixed(2)}ms`);
        
        return result;
      } catch (error) {
        const duration = performance.now() - start;
        console.error(`[PROFILE ERROR] ${profileName}: ${duration.toFixed(2)}ms`, error);
        throw error;
      }
    };

    return descriptor;
  };
}

// Usage
class UserService {
  @profile('UserService.fetchUser')
  async fetchUser(userId: string): Promise<User> {
    // Implementation
  }
}

// Get stats
const stats = PerformanceProfiler.getStats('UserService.fetchUser');
console.log(`P95 latency: ${stats?.p95}ms`);
```

---

## 🔒 Компонент 7: Security Patterns

### Circuit Breaker Pattern

```typescript
// utils/circuit-breaker.ts
export class CircuitBreaker {
  private failures = 0;
  private lastFailureTime?: number;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  constructor(
    private readonly failureThreshold: number = 5,
    private readonly recoveryTimeout: number = 60000 // 60 seconds
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailureTime! > this.recoveryTimeout) {
        this.state = 'half-open';
      } else {
        throw new Error('Circuit breaker is OPEN');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = 'closed';
  }

  private onFailure(): void {
    this.failures++;
    this.lastFailureTime = Date.now();

    if (this.failures >= this.failureThreshold) {
      this.state = 'open';
      console.warn(`Circuit breaker opened after ${this.failures} failures`);
    }
  }
}

// Usage
const breaker = new CircuitBreaker(5, 60000);

async function fetchDataWithCircuitBreaker() {
  return breaker.execute(async () => {
    const response = await fetch('https://api.example.com/data');
    return response.json();
  });
}
```

### DRY_RUN Mode Pattern

```typescript
// config/dry-run.ts
export class DryRunManager {
  private static isDryRun = process.env.DRY_RUN === 'true';

  static isEnabled(): boolean {
    return this.isDryRun;
  }

  static execute<T>(
    operation: () => Promise<T>,
    dryRunResult: T,
    description: string
  ): Promise<T> {
    if (this.isDryRun) {
      console.log(`[DRY-RUN] ${description}`);
      console.log(`[DRY-RUN] Would return:`, dryRunResult);
      return Promise.resolve(dryRunResult);
    }

    return operation();
  }
}

// Usage in API client
class TradingAPI {
  async buyItem(itemId: string, price: number): Promise<OrderResult> {
    return DryRunManager.execute(
      // Real operation
      async () => {
        const response = await this.client.post('/orders', {
          itemId,
          price,
          action: 'buy'
        });
        return response.data;
      },
      // Dry-run result
      {
        orderId: 'DRY-RUN-' + Date.now(),
        status: 'simulated',
        itemId,
        price
      },
      `Buy item ${itemId} for $${price}`
    );
  }
}
```

---

## 📖 Полезные ресурсы

### Документация
- [COPILOT_SDK_README.md](COPILOT_SDK_README.md) - Главная навигация
- [COPILOT_SDK_QUICKREF.md](COPILOT_SDK_QUICKREF.md) - Быстрый справочник
- [COPILOT_SDK_INTEGRATION_ANALYSIS.md](COPILOT_SDK_INTEGRATION_ANALYSIS.md) - Полный анализ

### Примеры из DMarket Bot
- `.github/instructions/` - 10 instruction файлов
- `.github/prompts/` - 9 prompt файлов
- `src/utils/skill_profiler.py` - Performance profiler
- `src/utils/skill_orchestrator.py` - Skill orchestration

### Внешние ресурсы
- [GitHub Copilot Documentation](https://docs.github.com/copilot)
- [SkillsMP.com](https://skillsmp.com) - AI Skills Marketplace
- [VCR.py](https://vcrpy.readthedocs.io/)
- [Hypothesis](https://hypothesis.readthedocs.io/)
- [Pact](https://docs.pact.io/)

---

## 🎯 Чеклист внедрения

### Phase 1: Базовая настройка (1 час)
- [ ] Создать `.github/instructions/` директорию
- [ ] Создать `.github/prompts/` директорию
- [ ] Скопировать `master.instructions.md`
- [ ] Адаптировать под свой проект
- [ ] Протестировать с Copilot

### Phase 2: File-Pattern Instructions (2-4 часа)
- [ ] Создать instruction для основного языка
- [ ] Создать instruction для тестов
- [ ] Создать instruction для API
- [ ] Добавить примеры в каждый файл
- [ ] Валидировать с командой

### Phase 3: Prompt Library (2-4 часа)
- [ ] Создать test-generator prompt
- [ ] Создать component-generator prompt
- [ ] Создать error-handling prompt
- [ ] Добавить примеры использования
- [ ] Документировать в README

### Phase 4: Advanced Features (1-2 недели)
- [ ] Внедрить VCR.py для HTTP тестов
- [ ] Добавить property-based тесты
- [ ] Настроить performance profiling
- [ ] Добавить circuit breaker
- [ ] Настроить DRY_RUN mode

### Phase 5: CI/CD (1 неделя)
- [ ] Создать validation workflow
- [ ] Добавить automated testing
- [ ] Настроить security scanning
- [ ] Документировать процесс

---

## 💡 Советы и best practices

### DO ✅
- Начните с малого (1-2 instruction файла)
- Тестируйте с реальными примерами
- Собирайте feedback от команды
- Итеративно улучшайте
- Документируйте изменения

### DON'T ❌
- Не создавайте слишком много instructions сразу
- Не делайте instructions слишком длинными
- Не забывайте обновлять при изменениях
- Не игнорируйте feedback от Copilot
- Не копируйте инструкции без адаптации

### Измерение успеха
- Время на генерацию кода: ↓30-50%
- Количество правок после генерации: ↓40%
- Консистентность стиля: ↑90%+
- Satisfaction score от команды: ↑

---

## 🆘 Troubleshooting

### Проблема: Copilot не применяет instructions

**Решение**:
1. Проверьте путь: `.github/instructions/`
2. Проверьте формат файла: `*.instructions.md`
3. Проверьте паттерн в файле: `Apply to: pattern`
4. Перезагрузите VS Code
5. Проверьте GitHub Copilot extension version

### Проблема: Prompts не работают

**Решение**:
1. Убедитесь что файлы в `.github/prompts/`
2. Используйте явный синтаксис: "using [prompt-name]"
3. Проверьте формат markdown
4. Обновите Copilot extension

### Проблема: Слишком много context

**Решение**:
1. Разделите большие instructions на несколько файлов
2. Используйте более специфичные patterns
3. Уберите дубликаты
4. Сократите примеры

---

## 🔄 Roadmap

### Q1 2026
- [x] Создание базовой документации
- [x] Примеры implementation
- [ ] Автоматизация setup
- [ ] CLI tool для scaffolding

### Q2 2026
- [ ] VS Code extension
- [ ] Template repository
- [ ] Community examples
- [ ] Best practices guide

### Q3 2026
- [ ] Integration testing framework
- [ ] Performance benchmarks
- [ ] Security audit tools
- [ ] Migration guides

### Q4 2026
- [ ] Advanced analytics
- [ ] Team collaboration features
- [ ] Marketplace integration
- [ ] Enterprise support

---

**Создано**: 23 января 2026 г.  
**Версия**: 1.0  
**License**: MIT  
**Maintained by**: DMarket Bot Team

Начните с быстрого старта (15 минут) и постепенно внедряйте продвинутые паттерны! 🚀
