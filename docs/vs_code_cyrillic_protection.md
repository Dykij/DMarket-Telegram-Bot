# 🔤 Защита от кириллических символов в VS Code и терминале

**Дата**: 19 ноября 2025 г.
**Версия**: 2.0
**Последнее обновление**: Актуализировано для Windows Terminal и PowerShell 7+

---

## 📋 Проблема

При работе с GitHub Copilot и русской раскладкой клавиатуры часто возникает проблема случайной вставки кириллических символов вместо латинских в командах терминала:

| Проблемная команда | Правильная команда | Ошибка                |
| ------------------ | ------------------ | --------------------- |
| `рутеst`           | `pytest`           | русские «р», «у», «е» |
| `рip install`      | `pip install`      | русская «р»           |
| `руthоn`           | `python`           | русские «р», «у», «о» |
| `гuff check`       | `ruff check`       | русская «г»           |
| `соde .`           | `code .`           | русская «с» и «о»     |

---

## 🛡️ Комплексное решение

### 1. Настройка Windows для предотвращения проблемы

#### Включить индикатор языка в трее
```powershell
# Через PowerShell
Set-WinUserLanguageList -LanguageList "en-US", "ru-RU" -Force
```

**Или через интерфейс:**
1. Параметры → Время и язык → Язык
2. Параметры клавиатуры → Показывать индикатор языка на панели задач

#### Настройка горячих клавиш
- `Win + Пробел` - переключение языка
- `Alt + Shift` - альтернативная комбинация
- `Ctrl + Shift` - классическая комбинация

### 2. Автопереключение раскладки по приложению

#### Punto Switcher (бесплатно)
```
Скачать: https://yandex.ru/soft/punto/
Настройки:
- Автопереключение → Включить
- Добавить приложения:
  • WindowsTerminal.exe
  • powershell.exe
  • Code.exe
  • Code - Insiders.exe
```

#### AutoHotkey скрипт
```autohotkey
; Автоматическое переключение на английский при фокусе в терминал/VS Code
#IfWinActive, ahk_exe WindowsTerminal.exe
Send, {Alt down}{Shift down}{Shift up}{Alt up}
#IfWinActive

#IfWinActive, ahk_exe Code.exe
Send, {Alt down}{Shift down}{Shift up}{Alt up}
#IfWinActive

#IfWinActive, ahk_exe powershell.exe
Send, {Alt down}{Shift down}{Shift up}{Alt up}
#IfWinActive
```

### 3. Лучшие шрифты для различения символов

| Шрифт                        | Ссылка                                            | Особенности                            |
| ---------------------------- | ------------------------------------------------- | -------------------------------------- |
| **JetBrains Mono Nerd Font** | [nerdfonts.com](https://www.nerdfonts.com/)       | Максимальное различие «р»/«p», «с»/«c» |
| **Fira Code Nerd Font**      | [nerdfonts.com](https://www.nerdfonts.com/)       | Популярный, с лигатурами               |
| **Cascadia Code NF**         | Встроен в Windows Terminal                        | По умолчанию в Windows                 |
| **Iosevka Nerd Font**        | [typeof.net/Iosevka](https://typeof.net/Iosevka/) | Узкий, много вариантов                 |

### 4. Настройки VS Code

#### settings.json
```json
{
  // Шрифты
  "editor.fontFamily": "'JetBrains Mono NF', 'Fira Code NF', 'Cascadia Code NF', monospace",
  "terminal.integrated.fontFamily": "'Cascadia Code NF', 'JetBrains Mono NF'",
  "editor.fontSize": 14,
  "terminal.integrated.fontSize": 14,

  // Отображение скрытых символов
  "editor.renderWhitespace": "all",
  "editor.renderControlCharacters": true,
  "editor.unicodeHighlight.nonBasicASCII": true,
  "editor.unicodeHighlight.invisibleCharacters": true,
  "editor.unicodeHighlight.ambiguousCharacters": true,

  // Подсветка проблем
  "errorLens.enabledDiagnosticLevels": ["error", "warning", "info"],
  "errorLens.enabled": true,

  // Автосохранение
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000,

  // Интеграция с терминалом
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.profiles.windows": {
    "PowerShell": {
      "source": "PowerShell",
      "args": ["-NoLogo"]
    }
  }
}
```

#### Рекомендуемые расширения

```json
{
  "recommendations": [
    "charliermarsh.ruff",
    "ms-python.python",
    "ms-python.black-formatter",
    "ms-python.mypy-type-checker",
    "usernamehw.errorlens",
    "ban.spellright",
    "streetsidesoftware.code-spell-checker",
    "streetsidesoftware.code-spell-checker-russian",
    "wmaurer.change-case",
    "alefragnani.project-manager"
  ]
}
```

### 5. Настройки Windows Terminal

#### settings.json (Windows Terminal)
```json
{
  "defaults": {
    "font": {
      "face": "Cascadia Code NF",
      "size": 12,
      "weight": "normal"
    },
    "colorScheme": "Campbell Powershell",
    "highlightBadCharacters": true,
    "experimental.detectURLs": true,
    "bellStyle": "visual",
    "copyOnSelect": false,
    "padding": "8, 8, 8, 8",
    "scrollbarState": "visible",
    "snapOnInput": true,
    "altGrAliasing": true,
    "antialiasingMode": "grayscale",
    "closeOnExit": "graceful",
    "cursorShape": "bar",
    "historySize": 9001,
    "startingDirectory": "%USERPROFILE%"
  },

  "profiles": {
    "defaults": {},
    "list": [
      {
        "guid": "{574e775e-4f2a-5b96-ac1e-a2962a402336}",
        "name": "PowerShell",
        "source": "Windows.Terminal.PowershellCore",
        "startingDirectory": "%USERPROFILE%",
        "commandline": "pwsh.exe -NoLogo",
        "icon": "ms-appx:///ProfileIcons/{574e775e-4f2a-5b96-ac1e-a2962a402336}.png"
      }
    ]
  }
}
```

### 6. PowerShell профиль с защитой

#### Создание профиля
```powershell
# Создать профиль если не существует
if (!(Test-Path -Path $PROFILE)) {
  New-Item -Type File -Path $PROFILE -Force
}

# Открыть для редактирования
notepad $PROFILE
```

#### Содержимое профиля ($PROFILE)
```powershell
# Функция проверки кириллицы
function Test-Cyrillic {
    param([string]$Command)

    if ($Command -match '[а-яё]') {
        Write-Host "⚠️  ВНИМАНИЕ: Обнаружена кириллица в команде!" -ForegroundColor Red
        Write-Host "Команда: $Command" -ForegroundColor Yellow

        # Попытка автозамены
        $fixed = $Command -replace 'р', 'p' -replace 'у', 'u' -replace 'е', 'e' -replace 'с', 'c' -replace 'о', 'o' -replace 'г', 'r'
        Write-Host "Возможное исправление: $fixed" -ForegroundColor Green

        return $false
    }
    return $true
}

# Алиасы для безопасности
Set-Alias -Name pyt -Value 'python -m pytest'
Set-Alias -Name rf -Value 'ruff'
Set-Alias -Name rfc -Value 'ruff check'
Set-Alias -Name rff -Value 'ruff format'
Set-Alias -Name mypy -Value 'mypy'
Set-Alias -Name pipi -Value 'pip install'

# Функция безопасного выполнения
function Invoke-SafeCommand {
    param([string]$Command)

    if (Test-Cyrillic $Command) {
        Invoke-Expression $Command
    } else {
        Read-Host "Нажмите Enter чтобы продолжить или Ctrl+C для отмены"
    }
}

# Переменные для разработки
$env:PYTHONPATH = "$PWD"
$env:PYTHONUNBUFFERED = "1"

# Приветствие
Write-Host "🛡️ PowerShell с защитой от кириллицы загружен" -ForegroundColor Green
Write-Host "Используйте Test-Cyrillic 'команда' для проверки" -ForegroundColor Cyan
```

### 7. Расширения VS Code для защиты

#### Highlight Bad Chars
```json
{
  "highlight-bad-chars.additionalUnicodeChars": [
    "а", "б", "в", "г", "д", "е", "ё", "ж", "з", "и", "й", "к", "л", "м",
    "н", "о", "п", "р", "с", "т", "у", "ф", "х", "ц", "ч", "ш", "щ", "ъ",
    "ы", "ь", "э", "ю", "я",
    "А", "Б", "В", "Г", "Д", "Е", "Ё", "Ж", "З", "И", "Й", "К", "Л", "М",
    "Н", "О", "П", "Р", "С", "Т", "У", "Ф", "Х", "Ц", "Ч", "Ш", "Щ", "Ъ",
    "Ы", "Ь", "Э", "Ю", "Я"
  ],
  "highlight-bad-chars.borderColor": "red",
  "highlight-bad-chars.backgroundColor": "rgba(255, 0, 0, 0.3)"
}
```

#### Code Spell Checker (защита от опечаток)
```json
{
  "cSpell.language": "en,ru",
  "cSpell.enabledLanguageIds": [
    "markdown",
    "python",
    "json",
    "yaml",
    "toml"
  ],
  "cSpell.words": [
    "pytest",
    "mypy",
    "ruff",
    "asyncio",
    "dmarket",
    "copilot"
  ]
}
```

### 8. Полезные горячие клавиши

| Действие         | VS Code            | Windows Terminal |
| ---------------- | ------------------ | ---------------- |
| Увеличить шрифт  | `Ctrl + =`         | `Ctrl + =`       |
| Уменьшить шрифт  | `Ctrl + -`         | `Ctrl + -`       |
| Сбросить размер  | `Ctrl + 0`         | `Ctrl + 0`       |
| Выделить всё     | `Ctrl + A`         | `Ctrl + A`       |
| Переключить язык | `Win + Пробел`     | `Win + Пробел`   |
| Показать команды | `Ctrl + Shift + P` | -                |
| Открыть терминал | `Ctrl + ` `        | -                |

### 9. Проверка настроек

#### Скрипт диагностики
```powershell
# Сохранить как check-cyrillic-protection.ps1
Write-Host "🔍 Проверка защиты от кириллических символов" -ForegroundColor Cyan

# Проверка шрифта терминала
$font = (Get-ItemProperty "HKCU:\Console" -Name FaceName -ErrorAction SilentlyContinue).FaceName
Write-Host "Шрифт терминала: $font" -ForegroundColor Yellow

# Проверка языков ввода
$languages = Get-WinUserLanguageList
Write-Host "Языки ввода:" -ForegroundColor Yellow
$languages | ForEach-Object { Write-Host "  - $($_.LanguageTag)" }

# Проверка VS Code
$vscodePath = Get-Command code -ErrorAction SilentlyContinue
if ($vscodePath) {
    Write-Host "✅ VS Code найден: $($vscodePath.Source)" -ForegroundColor Green
} else {
    Write-Host "❌ VS Code не найден" -ForegroundColor Red
}

# Тест кириллицы
$testCommands = @("рутest", "рip", "руthоn", "гuff", "соde")
Write-Host "`nТест обнаружения кириллицы:" -ForegroundColor Yellow
foreach ($cmd in $testCommands) {
    if ($cmd -match '[а-яё]') {
        Write-Host "  ❌ $cmd - содержит кириллицу" -ForegroundColor Red
    } else {
        Write-Host "  ✅ $cmd - чистый" -ForegroundColor Green
    }
}

Write-Host "`n🛡️ Диагностика завершена" -ForegroundColor Cyan
```

#### Запуск диагностики
```powershell
# Сохранить скрипт и запустить
PowerShell -ExecutionPolicy Bypass -File check-cyrillic-protection.ps1
```

### 10. Чек-лист полной защиты

- [ ] **Включен индикатор языка** в трее Windows
- [ ] **Настроены горячие клавиши** переключения раскладки
- [ ] **Установлен Nerd Font** (JetBrains Mono NF или Cascadia Code NF)
- [ ] **Настроен VS Code** с правильными шрифтами
- [ ] **Установлены расширения** Highlight Bad Chars, Error Lens
- [ ] **Настроен Windows Terminal** с подсветкой плохих символов
- [ ] **Создан PowerShell профиль** с функцией проверки
- [ ] **Настроен Punto Switcher** или AutoHotkey для автопереключения
- [ ] **Протестирована диагностика** на проблемных командах
- [ ] **Выработана привычка** проверять команды перед Enter

---

## 🎯 Быстрое решение "в одну команду"

Если нужно быстро настроить базовую защиту:

```powershell
# Установить рекомендуемый шрифт (требует админ права)
winget install --id=JetBrains.JetBrainsMono

# Создать базовый PowerShell профиль
@"
function Test-Cyrillic { param([string]`$c); if (`$c -match '[а-яё]') { Write-Warning 'Кириллица: `$c'; return `$false }; return `$true }
Set-Alias pyt 'python -m pytest'
Set-Alias rf 'ruff'
Write-Host '🛡️ Защита от кириллицы активна' -ForegroundColor Green
"@ | Out-File -FilePath $PROFILE -Encoding UTF8 -Force

# Настроить VS Code (если установлен)
if (Get-Command code -ErrorAction SilentlyContinue) {
    code --install-extension usernamehw.errorlens
    code --install-extension charliermarsh.ruff
    Write-Host "✅ VS Code настроен" -ForegroundColor Green
}

Write-Host "🎉 Базовая защита настроена!" -ForegroundColor Cyan
Write-Host "Перезапустите терминал для применения изменений" -ForegroundColor Yellow
```

---

## 📚 Дополнительные ресурсы

- [Windows Terminal Documentation](https://docs.microsoft.com/en-us/windows/terminal/)
- [PowerShell Profile Guide](https://docs.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_profiles)
- [VS Code Fonts and Encoding](https://code.visualstudio.com/docs/editor/settings)
- [Nerd Fonts Download](https://www.nerdfonts.com/font-downloads)
- [AutoHotkey Documentation](https://www.autohotkey.com/docs/)

---

**Помните**: Лучшая защита от кириллических символов — это формирование привычки всегда переключаться на английскую раскладку при работе с командами терминала!
