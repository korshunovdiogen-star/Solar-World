[CmdletBinding()]
param(
    [string]$Repo,
    [string]$Message,
    [switch]$Reset,
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Set-Location $Root
$Host.UI.RawUI.WindowTitle = 'Solar-World - Git Push'

try {
    $null = chcp 65001
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
}
catch { }

$ConfigDir = Join-Path $env:APPDATA 'Solar-World'
$ConfigPath = Join-Path $ConfigDir 'git-push.json'
$script:Git = $null

function Write-Header {
    Write-Host ''
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host '  Solar-World - публикация на GitHub' -ForegroundColor Cyan
    Write-Host "  Папка проекта: $Root" -ForegroundColor DarkGray
    Write-Host '============================================================' -ForegroundColor Cyan
    Write-Host ''
}

function Write-Step {
    param([string]$Number, [string]$Text)
    Write-Host "[$Number] $Text" -ForegroundColor Cyan
}

function Write-Ok   { param([string]$Text) Write-Host "      $Text" -ForegroundColor Green }
function Write-Warn { param([string]$Text) Write-Host "      $Text" -ForegroundColor Yellow }
function Write-Err  { param([string]$Text) Write-Host "      $Text" -ForegroundColor Red }

function Wait-AnyKey {
    if ($NoPause) { return }
    Write-Host ''
    Write-Host 'Нажмите любую клавишу для выхода...' -ForegroundColor DarkGray
    try {
        $null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
    }
    catch {
        Read-Host | Out-Null
    }
}

function Exit-WithError {
    param([string]$Text)
    Write-Host ''
    Write-Err $Text
    Write-Host ''
    Wait-AnyKey
    exit 1
}

function Find-Git {
    $cmd = Get-Command git -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }

    $candidates = @()
    if ($env:ProgramFiles) {
        $candidates += (Join-Path $env:ProgramFiles 'Git\cmd\git.exe')
    }
    if (${env:ProgramFiles(x86)}) {
        $candidates += (Join-Path ${env:ProgramFiles(x86)} 'Git\cmd\git.exe')
    }
    if ($env:LOCALAPPDATA) {
        $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe')
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate) { return $candidate }
    }
    return $null
}

function Invoke-Git {
    param([string[]]$GitArgs)
    & $script:Git @GitArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Команда git $($GitArgs -join ' ') завершилась с ошибкой (код $LASTEXITCODE)."
    }
}

function Test-GitRepo {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Container)) { return $false }
    $output = & $script:Git -C $Path rev-parse --is-inside-work-tree 2>$null
    if ($LASTEXITCODE -ne 0) { return $false }
    return (($output | Out-String).Trim() -eq 'true')
}

function Read-SavedRepo {
    if (-not (Test-Path -LiteralPath $ConfigPath)) { return $null }
    try {
        $config = Get-Content -LiteralPath $ConfigPath -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($config.repo) { return [string]$config.repo }
    }
    catch { }
    return $null
}

function Save-SavedRepo {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $ConfigDir)) {
        New-Item -ItemType Directory -Path $ConfigDir -Force | Out-Null
    }
    $data = [ordered]@{
        repo    = $Path
        savedAt = (Get-Date).ToString('s')
    }
    $data | ConvertTo-Json | Set-Content -LiteralPath $ConfigPath -Encoding UTF8
}

function Remove-SavedRepo {
    if (Test-Path -LiteralPath $ConfigPath) {
        Remove-Item -LiteralPath $ConfigPath -Force
    }
}

function Initialize-IfNeeded {
    param([string]$Path)
    if (Test-GitRepo $Path) { return $Path }

    Write-Warn "Папка не является git-репозиторием: $Path"
    $answer = Read-Host 'Инициализировать репозиторий здесь? (y/N)'
    if ($answer -notmatch '^(y|yes|д|да)$') { return $null }

    Invoke-Git @('-C', $Path, 'init') | Out-Null
    Write-Ok 'Репозиторий инициализирован.'
    return $Path
}

function Normalize-RemoteUrl {
    param([string]$Url)
    if ([string]::IsNullOrWhiteSpace($Url)) { return '' }
    $value = $Url.Trim().TrimEnd('/')
    $value = $value -replace '\.git$', ''
    return $value.ToLowerInvariant()
}

function Test-RemoteMatches {
    param([string]$Path, [string]$Url)

    if (-not (Test-GitRepo $Path)) { return $false }

    $needle = Normalize-RemoteUrl $Url
    if (-not $needle) { return $false }

    $remotes = @(& $script:Git -C $Path remote -v 2>$null)
    foreach ($line in $remotes) {
        $parts = $line -split '\s+'
        if ($parts.Count -ge 2 -and (Normalize-RemoteUrl $parts[1]) -eq $needle) {
            return $true
        }
    }
    return $false
}

function Clone-Repository {
    param([string]$Url)

    $name = ($Url.TrimEnd('/') -split '[/:]')[-1] -replace '\.git$', ''
    if ([string]::IsNullOrWhiteSpace($name)) { $name = 'repository' }
    $default = Join-Path (Split-Path $Root -Parent) $name

    if (Test-Path -LiteralPath $default) {
        if ((Get-ChildItem -LiteralPath $default -Force | Measure-Object).Count -gt 0) {
            $default = "$default-clone"
        }
    }

    Write-Host 'Локальной копии нет. Куда клонировать?'
    Write-Host "  Enter — $default" -ForegroundColor DarkGray
    $answer = Read-Host 'Папка'
    $destination = if ([string]::IsNullOrWhiteSpace($answer)) { $default } else { $answer.Trim().Trim('"') }

    if (Test-Path -LiteralPath $destination) {
        if ((Get-ChildItem -LiteralPath $destination -Force | Measure-Object).Count -gt 0) {
            Write-Warn "Папка не пуста: $destination"
            Write-Warn 'Укажите пустую папку или путь к уже существующему локальному репозиторию.'
            return $null
        }
    }

    Invoke-Git @('clone', $Url, $destination) | Out-Null
    Write-Ok "Склонировано в $destination"
    return (Resolve-Path -LiteralPath $destination).Path
}

function Get-RepoFromInput {
    param([string]$Value)

    $value = $Value.Trim().Trim('"').Trim("'")
    if ([string]::IsNullOrWhiteSpace($value)) { return $null }

    if (Test-Path -LiteralPath $value -PathType Container) {
        $path = (Resolve-Path -LiteralPath $value).Path
        return (Initialize-IfNeeded $path)
    }

    $relative = Join-Path $Root $value
    if (Test-Path -LiteralPath $relative -PathType Container) {
        $path = (Resolve-Path -LiteralPath $relative).Path
        return (Initialize-IfNeeded $path)
    }

    if ($value -match '^(https?://|git@|ssh://)') {
        if (Test-RemoteMatches -Path $Root -Url $value) {
            Write-Ok "URL совпадает с текущим проектом — использую $Root"
            return $Root
        }
        return (Clone-Repository $value)
    }

    Write-Warn "Путь не найден: $value"
    return $null
}

function Get-CurrentBranch {
    param([string]$Path)
    $branch = (& $script:Git -C $Path branch --show-current 2>$null | Out-String).Trim()
    if (-not $branch) {
        $branch = (& $script:Git -C $Path symbolic-ref --short HEAD 2>$null | Out-String).Trim()
    }
    return $branch
}

function Test-UnpushedCommits {
    param([string]$Path, [string]$Branch)

    & $script:Git -C $Path rev-parse --verify --quiet HEAD 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { return $false }

    $remoteRef = "refs/remotes/origin/$Branch"
    & $script:Git -C $Path rev-parse --verify --quiet $remoteRef 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) { return $true }

    $count = (& $script:Git -C $Path rev-list --count "$remoteRef..HEAD" 2>$null | Out-String).Trim()
    return ([int]$count -gt 0)
}

function Select-Repository {
    $saved = Read-SavedRepo
    if ($saved) {
        if (Test-GitRepo $saved) { return $saved }
        Write-Warn "Сохранённый репозиторий недоступен: $saved"
        Remove-SavedRepo
    }

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        Write-Host 'Укажите локальную папку git-репозитория или URL GitHub.'
        Write-Host 'Пример: C:\Projects\Solar-World или https://github.com/user/repo.git' -ForegroundColor DarkGray
        $answer = Read-Host 'Репозиторий'
        $resolved = Get-RepoFromInput $answer
        if ($resolved) { return $resolved }
        Write-Warn 'Не удалось определить репозиторий. Попробуйте ещё раз.'
    }

    return $null
}

Write-Header

try {
    Write-Step '1/4' 'Поиск Git...'
    $script:Git = Find-Git
    if (-not $script:Git) {
        Exit-WithError 'Git не найден. Установите его: winget install --id Git.Git -e'
    }
    Write-Ok "Git: $script:Git"

    if ($Reset) {
        Remove-SavedRepo
        Write-Ok 'Сохранённый репозиторий забыт.'
    }

    Write-Step '2/4' 'Выбор репозитория...'
    $repoPath = $null
    if (-not [string]::IsNullOrWhiteSpace($Repo)) {
        $repoPath = Get-RepoFromInput $Repo
    }
    else {
        $repoPath = Select-Repository
    }
    if (-not $repoPath) {
        Exit-WithError 'Репозиторий не выбран.'
    }

    Save-SavedRepo $repoPath
    Write-Ok "Репозиторий: $repoPath"

    $remotes = @(& $script:Git -C $repoPath remote 2>$null)
    if ($remotes -notcontains 'origin') {
        Write-Warn 'У репозитория нет remote origin.'
        $url = Read-Host 'URL удалённого репозитория GitHub (Enter — отмена)'
        if ([string]::IsNullOrWhiteSpace($url)) {
            Exit-WithError 'Без remote origin отправка невозможна.'
        }
        Invoke-Git @('-C', $repoPath, 'remote', 'add', 'origin', $url.Trim()) | Out-Null
        Write-Ok 'remote origin добавлен.'
    }

    $userName = (& $script:Git -C $repoPath config user.name 2>$null | Out-String).Trim()
    $userEmail = (& $script:Git -C $repoPath config user.email 2>$null | Out-String).Trim()
    if (-not $userName -or -not $userEmail) {
        Exit-WithError @'
Не настроены автор коммита.
Выполните один раз:
  git config --global user.name "Ваше Имя"
  git config --global user.email "you@example.com"
'@
    }

    $branch = Get-CurrentBranch $repoPath
    if (-not $branch) { $branch = 'main' }

    $status = @(& $script:Git -C $repoPath status --porcelain 2>$null)
    if ($status.Count -eq 0) {
        if (Test-UnpushedCommits $repoPath $branch) {
            Write-Ok 'Незакоммиченных изменений нет, но есть неотправленные коммиты.'
            Write-Step '4/4' "Отправка в origin/$branch..."
            Invoke-Git @('-C', $repoPath, 'push', '-u', 'origin', $branch)
            Write-Ok 'Готово: изменения отправлены на GitHub.'
            Wait-AnyKey
            exit 0
        }
        Write-Warn 'Нет изменений для коммита.'
        Wait-AnyKey
        exit 0
    }

    # demo_data/ не проверяем: демо-база и фикстура оставлены в репозитории
    # намеренно (см. demo_data/README.md и README.md).
    $risky = @('venv', 'env', '__pycache__', '.pytest_cache', '.coverage', 'media')
    $notIgnored = @()
    $ignoredButTracked = @()
    $trackedNotIgnored = @()

    foreach ($item in $risky) {
        $full = Join-Path $repoPath $item
        if (-not (Test-Path -LiteralPath $full)) { continue }

        # --no-index проверяет сами правила игнорирования, не глядя в индекс.
        # Без него Git считает отслеживаемые файлы неигнорируемыми, даже если правило есть.
        & $script:Git -C $repoPath check-ignore --no-index -q -- $item 2>$null
        $hasIgnoreRule = ($LASTEXITCODE -eq 0)
        if (-not $hasIgnoreRule) {
            # Для каталогов Git иногда требует путь со слешем (например, env/).
            & $script:Git -C $repoPath check-ignore --no-index -q -- "$item/" 2>$null
            $hasIgnoreRule = ($LASTEXITCODE -eq 0)
        }

        $trackedFiles = @(& $script:Git -C $repoPath ls-files -- $item 2>$null)
        $isTracked = ($trackedFiles.Count -gt 0)

        if ($hasIgnoreRule -and $isTracked) {
            $ignoredButTracked += $item
        }
        elseif ($hasIgnoreRule) {
            # Правило есть, файлы не отслеживаются — Git их не добавит.
        }
        elseif ($isTracked) {
            $trackedNotIgnored += $item
        }
        else {
            $notIgnored += $item
        }
    }

    if ($ignoredButTracked.Count -gt 0) {
        Write-Warn ('В .gitignore правило есть, но файлы уже отслеживаются: ' + ($ignoredButTracked -join ', '))
        Write-Warn 'Пока они в индексе, правило не действует. Убрать из индекса, не удаляя с диска:'
        foreach ($item in $ignoredButTracked) {
            Write-Warn ("  git -C `"$repoPath`" rm -r --cached $item")
        }
    }

    if ($trackedNotIgnored.Count -gt 0) {
        Write-Warn ('Отслеживаются, хотя правила в .gitignore нет: ' + ($trackedNotIgnored -join ', '))
        Write-Warn 'Изменения этих файлов попадут в коммит.'
    }

    if ($notIgnored.Count -gt 0) {
        Write-Warn ('Не покрыты .gitignore: ' + ($notIgnored -join ', '))
        Write-Warn 'При git add -A они попадут в коммит и могут сильно увеличить репозиторий.'
    }

    if (($ignoredButTracked.Count + $trackedNotIgnored.Count + $notIgnored.Count) -gt 0) {
        $answer = Read-Host 'Продолжить? (y/N)'
        if ($answer -notmatch '^(y|yes|д|да)$') {
            Exit-WithError 'Отменено пользователем.'
        }
    }

    $commitMessage = $Message
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        $commitMessage = Read-Host 'Введите сообщение коммита'
    }
    if ([string]::IsNullOrWhiteSpace($commitMessage)) {
        Exit-WithError 'Сообщение коммита не может быть пустым.'
    }

    Write-Step '3/4' 'Коммит...'
    Invoke-Git @('-C', $repoPath, 'add', '-A') | Out-Null
    & $script:Git -C $repoPath diff --cached --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Warn 'Нет изменений для коммита.'
        Wait-AnyKey
        exit 0
    }

    Invoke-Git @('-C', $repoPath, 'commit', '-m', $commitMessage) | Out-Null
    Write-Ok 'Коммит создан.'

    Write-Step '4/4' "Отправка в origin/$branch..."
    Invoke-Git @('-C', $repoPath, 'push', '-u', 'origin', $branch)
    Write-Ok 'Готово: изменения отправлены на GitHub.'
}
catch {
    Exit-WithError $_.Exception.Message
}

Write-Host ''
Write-Host '============================================================' -ForegroundColor Green
Write-Host '  Публикация завершена.' -ForegroundColor Green
Write-Host '============================================================' -ForegroundColor Green
Wait-AnyKey
