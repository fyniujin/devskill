# 安装脚本 - Windows PowerShell
# 检测并安装Tesseract OCR引擎

Set-Location (Split-Path -Path $MyInvocation.MyCommand.Definition -Parent)

Write-Host "=== 财税合规Skill安装脚本 ===" -ForegroundColor Green
Write-Host ""

# 检查Python版本
function Check-Python {
    try {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if ($python) {
            $version = python --version 2>&1
            Write-Host "✓ Python: $version" -ForegroundColor Green
            return "python"
        }
        
        $python3 = Get-Command python3 -ErrorAction SilentlyContinue
        if ($python3) {
            $version = python3 --version 2>&1
            Write-Host "✓ Python3: $version" -ForegroundColor Green
            return "python3"
        }
        
        Write-Host "✗ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
        Write-Host "  下载地址: https://www.python.org/downloads/"
        exit 1
    }
    catch {
        Write-Host "✗ 未找到Python，请先安装Python 3.8+" -ForegroundColor Red
        exit 1
    }
}

# 检查Tesseract
function Check-Tesseract {
    try {
        $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
        if ($tesseract) {
            $version = tesseract --version 2>&1 | Select-Object -First 1
            Write-Host "✓ Tesseract: $version" -ForegroundColor Green
            return $true
        }
    }
    catch { }
    
    Write-Host "✗ Tesseract未安装" -ForegroundColor Red
    return $false
}

# 安装Python依赖
function Install-PythonDeps {
    param($PythonCmd)
    
    Write-Host ""
    Write-Host "正在安装Python依赖..." -ForegroundColor Yellow
    
    & $PythonCmd -m pip install --upgrade pip
    & $PythonCmd -m pip install Pillow pytesseract openpyxl pyyaml
    
    # PDF支持（可选）
    $poppler = Get-Command pdftoppm -ErrorAction SilentlyContinue
    if ($poppler) {
        & $PythonCmd -m pip install pdf2image
        Write-Host "✓ PDF支持已启用" -ForegroundColor Green
    }
    else {
        Write-Host "⚠ poppler未安装，PDF支持不可用" -ForegroundColor Yellow
        Write-Host "  可手动下载: https://github.com/oschwartz10612/poppler-windows/releases"
    }
}

# 验证安装
function Verify-Installation {
    param($PythonCmd)
    
    Write-Host ""
    Write-Host "=== 验证安装 ===" -ForegroundColor Green
    
    # 验证Tesseract
    try {
        $tesseract = Get-Command tesseract -ErrorAction SilentlyContinue
        if ($tesseract) {
            Write-Host "✓ Tesseract: $(tesseract --version 2>&1 | Select-Object -First 1)" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Tesseract: 未安装" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "✗ Tesseract: 未安装" -ForegroundColor Red
    }
    
    # 验证Python模块
    & $PythonCmd -c "
import sys
modules = ['PIL', 'pytesseract', 'openpyxl']
missing = []
for mod in modules:
    try:
        __import__(mod)
        print(f'✓ {mod}')
    except ImportError:
        missing.append(mod)
        print(f'✗ {mod}')
if missing:
    print(f'请运行: pip install {\" \".join(missing)}')
"
}

# 主流程
$python = Check-Python

if (-not (Check-Tesseract)) {
    Write-Host ""
    Write-Host "Tesseract未安装，请手动安装:" -ForegroundColor Yellow
    Write-Host "  1. 下载: https://github.com/UB-Mannheim/tesseract/wiki"
    Write-Host "  2. 安装时勾选中文语言包(chi_sim)"
    Write-Host "  3. 将Tesseract路径添加到系统PATH"
    Write-Host ""
    Write-Host "是否已手动安装？(y/n)" -NoNewline
    $answer = Read-Host
    if ($answer -ne 'y') {
        exit 1
    }
}

Install-PythonDeps -PythonCmd $python
Verify-Installation -PythonCmd $python

Write-Host ""
Write-Host "=== 安装完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "使用方法:" -ForegroundColor Yellow
Write-Host "1. 首次使用请编辑 config.yaml 配置企业信息"
Write-Host "2. 识别发票: python scripts/ocr_engine.py --input 发票.png --output receipt.json"
Write-Host "3. 查验真伪: python scripts/verify_abstract.py --config config.yaml --receipt receipt.json"
Write-Host "4. 生成报销单: python scripts/template_matcher.py fill --config config.yaml --receipt receipt.json --template templates/expense_basic.xlsx"
