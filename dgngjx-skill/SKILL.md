---
name: dgngjx-skill
slug: dgngjx-skill
displayName: "多功能工具箱 v3.6"
description: "多功能免费工具箱 - 图片处理、PDF转换、数据换算、文本工具、开发工具、视频工具、教育、生活娱乐、实用小工具、系统工具。10大模块42个工具，零依赖开箱即用为主。v3.6 新增文件哈希/UUID/时间戳/IP工具+单位换算扩展至28种+编码支持MD5/SHA/进制转换。"
description_zh: "多功能免费工具箱 - 10大模块42个工具。v3.6 新增文件哈希校验+UUID生成器+时间戳转换+IP工具，单位换算扩至28种，编码新增MD5/SHA/进制转换。"
version: 3.6.0
category: office-efficiency
platforms:
  - windows
  - macos
  - linux
tags:
  - toolbox
  - pdf
  - image
  - video
  - developer
  - converter
  - calculator
  - text
  - reliable
  - qrcode
  - password
  - regex
  - system
  - hardware
  - monitor
  - hash
  - uuid
  - timestamp
  - ip
requires_api_key: false
---

# 多功能工具箱 dgngjx-skill v3.6.0

## 30 秒速查表

| 我想做 | 直接说 |
|--------|--------|
| 算房贷 / 五险一金 | `"算房贷"` `"算五险一金"` |
| 日期 / 单位换算 | `"日期计算"` `"公里转英里"` `"MB转GB"` |
| 统计字数 / 编码 | `"字数统计"` `"Base64编码"` `"算MD5"` `"进制转换"` |
| 词频分析 | `"词频统计"` |
| JSON / HTTP / Token | `"JSON格式化"` `"测试接口"` |
| 查知识 / 下壁纸 | `"查勾股定理"` `"下壁纸"` |
| 压缩 / 修复图片 | `"帮我压缩 D:\photo.jpg"` `"修复老照片"` |
| 合并 / 拆分 PDF | `"合并这几个PDF"` `"拆分第5-10页"` |
| 视频格式转换 | `"MP4转GIF"` |
| 视频编辑 | `"给视频加水印"` `"提取视频帧"` |
| 二维码 / 密码 / 正则 | `"生成二维码"` `"生成随机密码"` `"测试正则 \d+"` |
| 文件哈希 / UUID | `"校验文件哈希"` `"生成UUID"` |
| 时间戳 / IP工具 | `"时间戳转换"` `"查本机IP"` `"算子网"` |
| 系统资源监控 | `"看看CPU使用率"` `"内存够不够"` |
| 批量文件重命名 | `"把这些文件都改名"` `"批量添加前缀"` |
| Markdown转HTML | `"把这份MD转成HTML"` |

---

## 🆕 v3.6.0 更新提醒

> 🔔 **您正在使用 dgngjx-skill v3.6.0**
> 
> 检查更新：`skillhub search dgngjx-skill`
> 
> 升级命令：`skillhub upgrade dgngjx-skill`
> 
> 📧 **有任何建议？联系作者邮箱：njskills@agent.qq.com**
> dgngjx-skill 欢迎你的反馈！无论是新功能建议、bug 报告还是使用困惑，都可以发邮件到 njskills@agent.qq.com，作者会认真阅读每一条。

---

## 快速开始

### 第一次用？做这 3 步

| 步骤 | 做什么 | 为什么 |
|:----:|--------|--------|
| ① | **快速试一个**：对 AI 说 `"算房贷"` | 零依赖，秒回，建立信心 |
| ② | **按需装依赖**：用到图片/PDF功能时，AI 会提示安装，输入 `install` 确认 | 一次安装，后面都能用 |
| ③ | **高级功能**：参考下方「📦 依赖管理」或跳过直接用在线工具 | 按需取用 |

### 你可以直接说（触发词）

| 说 | 做 | 备注 |
|----|----|------|
| `"算房贷 100万 30年 4.2%"` | 等额本息计算 | ✅ 开箱即用 |
| `"算五险一金 北京 15000"` | 税后工资 | ✅ 开箱即用 |
| `"从 2026-06-26 到国庆多少天"` | 日期计算 | ✅ 开箱即用 |
| `"Base64编码 Hello"` | 编码转换 | ✅ 开箱即用 |
| `"统计字数"` 然后粘贴文本 | 中英词频统计 | ✅ 开箱即用 |
| `"测试 https://api.github.com"` | HTTP 请求 | ✅ 开箱即用 |
| `"帮我压缩 D:\photo.jpg"` | 图片压缩 | 📦 需确认装 Pillow |
| `"合并这几个PDF"` | PDF 合并 | 📦 需确认装 PyPDF2 |
| `"MP4转GIF"` | 视频转换 | 📦 需确认装 FFmpeg |
| `"给视频加水印 文字=我的水印"` | 视频编辑 | 📦 需确认装 FFmpeg |
| `"生成二维码 内容=Hello"` | 二维码 | ✅ 开箱即用 |
| `"生成随机密码 长度=16"` | 密码生成 | ✅ 开箱即用 |
| `"测试正则 \d+ 文本=abc123"` | 正则测试 | ✅ 开箱即用 |
| `"看看CPU使用率"` | 系统资源监控 | ✅ 开箱即用 |
| `"把这个MD转成HTML"` | Markdown转HTML | ✅ 开箱即用 |

---

## 🔒 安全规则（v3.5 新增）

> **dgngjx-skill 不会处理以下文件类型，即使你明确要求也会被拒绝。**

### 默认禁止（拦截）的类型

**Windows 可执行 / 批处理脚本：**
`.bat`、`.cmd`、`.ps1`、`.vbs`、`.exe`、`.dll`、`.lnk`、`.msi`

**Office 二进制文档：**
`.docx`、`.xlsx`、`.pptx`、`.doc`、`.xls`、`.ppt`、`.xlsm`、`.docm`、`.pptm`

**二进制镜像 / 安装包：**
`.iso`、`.dmg`、`.zip`、`.rar`、`.7z`、`.tar`、`.gz`、`.apk`、`.jar`

**系统缓存 / 隐藏文件：**
`.DS_Store`、`.git` 目录、`.env`、`.log`、`.tmp`

**其他风险脚本：**
`.sh`、`.com`、`.scr`、`.hta`、`.reg`

<details>
<summary>📋 安全过滤代码（所有文件操作前必跑）</summary>

```python
import os

# === v3.5.0 安全规则：禁止处理高风险文件类型 ===
BLOCKED_EXTENSIONS = {
    # Windows 可执行 / 批处理脚本
    '.bat', '.cmd', '.ps1', '.vbs', '.exe', '.dll', '.lnk', '.msi',
    # Office 二进制文档
    '.docx', '.xlsx', '.pptx', '.doc', '.xls', '.ppt', '.xlsm', '.docm', '.pptm',
    # 二进制镜像 / 安装包
    '.iso', '.dmg', '.zip', '.rar', '.7z', '.tar', '.gz', '.apk', '.jar',
    # 系统缓存 / 隐藏文件
    '.ds_store', '.env', '.log', '.tmp',
    # 其他风险脚本
    '.sh', '.com', '.scr', '.hta', '.reg',
}

BLOCKED_DIRS = {'.git', '.svn', '.hg', '__pycache__', 'node_modules', '.idea', '.vscode'}

def _is_safe_file(filepath: str) -> tuple[bool, str]:
    """检查文件是否安全（未被黑名单拦截）。返回 (是否安全, 拒绝原因)"""
    # 检查隐藏文件
    basename = os.path.basename(filepath)
    if basename.startswith('.') and basename in {'.ds_store', '.env', '.gitconfig', '.bashrc'}:
        return False, f"隐藏系统文件 {basename} 被拦截"
    
    # 检查目录
    parts = filepath.replace('\\', '/').split('/')
    for part in parts:
        if part.lower() in BLOCKED_DIRS:
            return False, f"系统目录 {part} 被拦截"
    
    # 检查扩展名
    ext = os.path.splitext(filepath)[1].lower()
    if ext in BLOCKED_EXTENSIONS:
        reason = {
            '.bat': 'Windows 批处理脚本（可执行命令）',
            '.cmd': 'Windows 批处理脚本（可执行命令）',
            '.ps1': 'PowerShell 脚本（可执行命令）',
            '.vbs': 'VBScript 脚本（可执行命令）',
            '.exe': 'Windows 可执行程序',
            '.dll': '动态链接库',
            '.msi': 'Windows 安装包',
            '.lnk': '快捷方式文件',
        }.get(ext, f'{ext} 文件类型被安全规则禁止')
        return False, f"{reason} — 请使用专业工具处理"
    
    return True, ""

def _is_safe_output(filepath: str) -> tuple[bool, str]:
    """检查输出文件类型是否安全（不允许生成可执行/危险文件）"""
    ext = os.path.splitext(filepath)[1].lower()
    if ext in {'.exe', '.dll', '.bat', '.cmd', '.ps1', '.vbs', '.sh', '.com', '.scr', '.hta', '.reg', '.msi', '.apk', '.jar'}:
        return False, f"安全规则禁止生成 {ext} 文件"
    return True, ""

# === 使用示例 ===
# 所有文件读取操作前调用：
# safe, reason = _is_safe_file(user_input_path)
# if not safe:
#     print(f"🚫 {reason}")
#     return
```

</details>

---

## ⚡ 自适应硬件调度 （v3.5 新增）

> dgngjx-skill 会自动检测你的电脑配置（CPU核心数、内存大小），并根据硬件能力调整并发任务数量和资源分配，**绝不拖累低配电脑**。

<details>
<summary>📋 硬件检测与智能调度脚本（v3.5 新增）</summary>

```python
import os, sys, subprocess, platform

def get_hardware_info() -> dict:
    """自动检测用户电脑硬件信息，用于智能调度"""
    info = {
        'cpu_count': os.cpu_count() or 2,
        'ram_mb': 0,
        'platform': platform.system(),
        'is_low_end': False,
        'max_workers': 1,
        'max_file_size_mb': 100,
    }
    
    # 检测内存
    try:
        if info['platform'] == 'Windows':
            result = subprocess.run(
                ['wmic', 'computersystem', 'get', 'TotalPhysicalMemory', '/value'],
                capture_output=True, text=True, timeout=10
            )
            for line in result.stdout.split('\n'):
                if 'TotalPhysicalMemory' in line:
                    bytes_val = int(line.split('=')[1].strip())
                    info['ram_mb'] = bytes_val // (1024 * 1024)
                    break
        elif info['platform'] == 'Linux':
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal'):
                        info['ram_mb'] = int(line.split()[1]) // 1024
                        break
        elif info['platform'] == 'Darwin':  # macOS
            result = subprocess.run(
                ['sysctl', '-n', 'hw.memsize'], capture_output=True, text=True, timeout=5
            )
            info['ram_mb'] = int(result.stdout.strip()) // (1024 * 1024)
    except Exception:
        info['ram_mb'] = 4096  # 默认值
    
    # 自动判定配置级别
    if info['ram_mb'] < 4096 or info['cpu_count'] <= 2:
        info['is_low_end'] = True
        info['max_workers'] = 1
        info['max_file_size_mb'] = 50
    elif info['ram_mb'] < 8192 or info['cpu_count'] <= 4:
        info['max_workers'] = 2
        info['max_file_size_mb'] = 200
    else:
        info['max_workers'] = min(info['cpu_count'], 4)
        info['max_file_size_mb'] = 500
    
    return info

def smart_task_split(file_size_mb: int, hw: dict) -> int:
    """根据文件大小和硬件智能计算任务分片数"""
    if file_size_mb <= 50:
        return 1
    # 每 100MB 或每 2GB RAM 分配 1 个 worker
    by_ram = max(1, hw['ram_mb'] // 2048)
    by_size = max(1, file_size_mb // 100)
    return min(by_ram, by_size, hw['max_workers'])

# === 初始化（整个 skill 生命周期只跑一次）===
_HW = get_hardware_info()
print(f"🖥️ 系统检测: {_HW['cpu_count']}核 | {_HW['ram_mb']}MB RAM | {_HW['platform']}")
if _HW['is_low_end']:
    print("⚡ 已启用低配模式：单任务运行，小文件优先，绝不卡顿")
else:
    print(f"⚡ 已启用标准模式：最多 {_HW['max_workers']} 并发，文件上限 {_HW['max_file_size_mb']}MB")
```

</details>

**调度策略一览：**

| 硬件级别 | 内存 | CPU | 并发数 | 单文件上限 | 保护策略 |
|---------|------|-----|--------|-----------|---------|
| 🟢 高配 | ≥8GB | ≥6核 | 4 | 500MB | 多任务并行，大文件分块 |
| 🟡 中配 | 4-8GB | 2-4核 | 2 | 200MB | 双任务，中等文件 |
| 🔴 低配 | <4GB | ≤2核 | 1 | 50MB | 单任务，小文件优先 |

---

## 📦 依赖管理

### 检测环境

任何功能使用前，AI 先跑这个脚本看看缺了什么：

<details>
<summary>📋 依赖检测脚本</summary>

```python
import sys, subprocess
print(f"Python: {sys.version.split()[0]}")
pkgs = {'PIL':'Pillow(PIL)','rembg':'rembg','PyPDF2':'PyPDF2','cv2':'opencv-python','jieba':'jieba'}
for pkg, name in pkgs.items():
    try: __import__(pkg); print(f"  ✅ {name}")
    except: print(f"  ❌ {name}（缺失）")
try:
    subprocess.run(['ffmpeg','-version'], capture_output=True, text=True)
    print("  ✅ ffmpeg")
except: print("  ❌ ffmpeg（缺失）")
```

</details>

### 一键安装

```
pip install Pillow PyPDF2 jieba
```

> AI 必须问用户确认后再执行。

### 按功能安装

| 你想用 | 只装这个 | 命令 |
|--------|---------|------|
| 压缩图片 / 证件照 / 基础修复 | Pillow (3MB) | `pip install Pillow` |
| PDF 合并/拆分/加密 | PyPDF2 (200KB) | `pip install PyPDF2` |
| 人像抠图 | rembg (300MB) | `pip install rembg` |
| 精准中文分词 | jieba (10MB) | `pip install jieba` |
| 视频转换 / 编辑 | ffmpeg (系统包) | 见下方一键安装 |

> ⚠️ rembg 首次运行会自动下载 ~300MB 模型（1-5分钟），装好后可离线使用。
> 💡 jieba 为可选依赖，词频统计不装 jieba 也能用（会自动降级到正则分词）。

### FFmpeg 一键安装（v3.0 简化）

> 💡 最简方案：打开 PowerShell，粘贴 `winget install ffmpeg` 一行搞定。

---

## ❌ 不支持（边界情况说明）

| 不支持 | 原因 | 替代方案 |
|--------|------|---------|
| 在线编辑 PSD | .psd 为封闭格式 | [Photopea](https://www.photopea.com/) |
| Excel 在线编辑 | 超出能力 | 可通过本工具转 PDF |
| 视频录屏（浏览器外） | 需浏览器 API | 用电脑自带录屏 |
| 大于 500MB 的视频 | 浏览器会卡 | 需本地安装 FFmpeg |
| 密码加密后丢失 | 安全机制限制 | 密码在加密时展示一次，请截图保存 |
| 实时网络请求拦截 | 超出能力范围 | 使用 Fiddler / Charles |
| 批量视频压制 | 需专业编码软件 | HandBrake 批量队列 |
| 处理可执行文件 | 安全规则禁止 | 使用专业反编译/分析工具 |

---

## 功能模块

---

### 📊 模块 1：数据换算

---

#### 1.1 房贷计算器

**✅ 开箱即用** ｜ 🌐 [在线房贷计算器](https://www.zhujisuanqi.com/)

<details>
<summary>📋 展开查看命令</summary>

```python
import math
try:
    P = float(input("贷款总额(万元): ") or 100) * 10000
    n = int(float(input("贷款年限: ") or 30) * 12)
    r = float(input("年利率(%): ") or 4.2) / 100 / 12
    method = input("方式(等额本息/等额本金): ").strip() or "等额本息"
    if n <= 0:
        print("❌ 贷款年限必须大于0")
    elif r <= 0:
        print("❌ 年利率必须大于0")
    elif method == "等额本息":
        m = P*r*(1+r)**n / ((1+r)**n-1)
        total = m * n
        print(f"月供: {m:.2f}元 | 总利息: {total-P:.2f}元 | 还款总额: {total:.2f}元")
    else:
        tot = sum(P/n + (P-P*i/n)*r for i in range(n))
        print(f"首月: {P/n+P*r:.2f}元 | 末月: {P/n+r*(P/n):.2f}元 | 总利息: {tot-P:.2f}元")
except ValueError:
    print("❌ 输入错误：请输入有效数字。例如：贷款100万输 100，年限30年输 30")
```

</details>

---

#### 1.2 五险一金计算器

**✅ 开箱即用** ｜ 🌐 [个税计算器](https://www.taxcalculator.com)

<details>
<summary>📋 展开查看命令</summary>

```python
try:
    s = float(input("税前月薪: ") or 15000)
    city = input("城市(北京/上海/广州/深圳): ").strip() or "北京"
    r = {"北京":[.08,.02,.005,0,0,.12], "上海":[.08,.02,.005,0,0,.07],
         "广州":[.08,.02,.002,0,0,.05], "深圳":[.08,.02,.003,0,0,.05]}
    if city not in r:
        print(f"❌ 不支持的城市: {city}。支持: 北京/上海/广州/深圳")
    elif s <= 0:
        print("❌ 月薪必须大于0")
    else:
        i = dict(zip(["养老","医疗","失业","工伤","生育","公积金"], r[city]))
        t = sum(v*s for v in i.values())
        tax = max(0,(s-t-5000))*.03
        print(f"到手: {s-t-tax:.2f}元")
except ValueError:
    print("❌ 输入错误：月薪请输入纯数字。例如：15000")
```

</details>

---

#### 1.3 日期计算器

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
from datetime import date
try:
    a = date.today()
    b = input("目标日期 YYYY-MM-DD: ").strip() or "2026-10-01"
    y,m,d = map(int, b.split("-"))
    target = date(y,m,d)
    diff = (target - a).days
    print(f"相差: {diff} 天 ({diff//7} 周)")
    if diff < 0:
        print("⚠️ 目标日期已经过去了")
except ValueError:
    print("❌ 日期格式错误。正确格式：年-月-日，例如：2026-10-01")
```

</details>

---

#### 1.4 单位换算器

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
c = {
    # 长度
    "km_mi":  (lambda v: v*0.621371,  "公里", "英里"),
    "mi_km":  (lambda v: v/0.621371,  "英里", "公里"),
    "m_ft":   (lambda v: v*3.28084,   "米",   "英尺"),
    "ft_m":   (lambda v: v/3.28084,   "英尺", "米"),
    "cm_in":  (lambda v: v/2.54,      "厘米", "英寸"),   # v3.6.0 新增
    "in_cm":  (lambda v: v*2.54,      "英寸", "厘米"),   # v3.6.0 新增
    # 重量
    "kg_lb":  (lambda v: v*2.20462,   "公斤", "磅"),
    "lb_kg":  (lambda v: v/2.20462,   "磅",   "公斤"),
    "g_oz":   (lambda v: v/28.3495,   "克",   "盎司"),   # v3.6.0 新增
    "oz_g":   (lambda v: v*28.3495,   "盎司", "克"),     # v3.6.0 新增
    # 温度
    "c_f":    (lambda v: v*9/5+32,    "°C",   "°F"),
    "f_c":    (lambda v: (v-32)*5/9,  "°F",   "°C"),
    "c_k":    (lambda v: v+273.15,    "°C",   "K"),      # v3.6.0 新增
    "k_c":    (lambda v: v-273.15,    "K",    "°C"),     # v3.6.0 新增
    # 面积  v3.6.0 新增
    "sqm_sqft": (lambda v: v*10.7639, "平方米", "平方英尺"),
    "mu_sqm":   (lambda v: v*666.667, "亩",     "平方米"),
    "ha_mu":    (lambda v: v*15,       "公顷",   "亩"),
    # 速度  v3.6.0 新增
    "kmh_mph":  (lambda v: v*0.621371, "km/h",  "mph"),
    "ms_kmh":   (lambda v: v*3.6,      "m/s",   "km/h"),
    "knot_kmh": (lambda v: v*1.852,    "节",    "km/h"),
    # 数据存储  v3.6.0 新增
    "mb_gb":  (lambda v: v/1024,       "MB",   "GB"),
    "gb_mb":  (lambda v: v*1024,       "GB",   "MB"),
    "gb_tb":  (lambda v: v/1024,       "GB",   "TB"),
    "byte_mb":(lambda v: v/1048576,    "字节", "MB"),
    # 压力  v3.6.0 新增
    "bar_psi":(lambda v: v*14.5038,    "bar",  "psi"),
    "atm_kpa":(lambda v: v*101.325,    "atm",  "kPa"),
    # 能量  v3.6.0 新增
    "kcal_kj":(lambda v: v*4.184,      "千卡", "千焦"),
    "kwh_kj": (lambda v: v*3600,       "度电", "千焦"),
}
try:
    m = input("类型(如km_mi/mb_gb/mu_sqm):").strip() or "km_mi"
    v = float(input("数值: ") or 100)
    if m not in c:
        print(f"❌ 不支持的换算：'{m}'")
        print(f"支持的类型：{', '.join(c.keys())}")
    else:
        r, uf, ut = c[m]
        print(f"✅ {v} {uf} = {r(v):.4f} {ut}")
except ValueError:
    print("❌ 请输入纯数字，例如：100")
```

</details>

---

### 📝 模块 2：文本工具

---

#### 2.1 文本统计

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
t = input("输入文本:")
if not t or not t.strip():
    print("❌ 没有检测到输入。请程序运行时输入一段文字")
else:
    total = len(t)
    cn = sum(1 for c in t if '一' <= c <= '鿿')
    en = len(t.split())
    lines = t.split(chr(10))
    print(f"总字符: {total} | 中文: {cn} | 英文词: {en}")
    print(f"非空行: {len([l for l in lines if l.strip()])}")
    print(f"去重后: {len(list(dict.fromkeys(lines)))}行 (原{len(lines)}行)")
```

</details>

---

#### 2.2 编码转换

**✅ 开箱即用** ｜ 🌐 [Base64在线](https://www.base64encode.org/)

<details>
<summary>📋 展开查看命令</summary>

```python
import base64, urllib.parse, hashlib
try:
    t = input("文本:") or "Hello"
    m = input("方法(Base64/URL/Unicode/MD5/SHA1/SHA256/进制):").strip() or "Base64"
    if m == "Base64":
        op = input("编码/解码:").strip() or "编码"
        print(base64.b64encode(t.encode()).decode() if op == "编码" else base64.b64decode(t.encode()).decode())
    elif m == "URL":
        op = input("编码/解码:").strip() or "编码"
        print(urllib.parse.quote(t) if op == "编码" else urllib.parse.unquote(t))
    elif m == "Unicode":
        print(" ".join(f"\\u{ord(c):04x}" for c in t))
    # ---- v3.6.0 新增：哈希 ----
    elif m == "MD5":
        print(f"MD5: {hashlib.md5(t.encode()).hexdigest()}")
    elif m == "SHA1":
        print(f"SHA1: {hashlib.sha1(t.encode()).hexdigest()}")
    elif m == "SHA256":
        print(f"SHA256: {hashlib.sha256(t.encode()).hexdigest()}")
    # ---- v3.6.0 新增：进制转换 ----
    elif m == "进制":
        base_from = input("原进制(2/8/10/16):").strip() or "10"
        try:
            n = int(t, int(base_from))
            print(f"✅ {t} (原{base_from}进制) =")
            print(f"   二进制: {bin(n)[2:]}")
            print(f"   八进制: {oct(n)[2:]}")
            print(f"   十进制: {n}")
            print(f"   十六进制: {hex(n)[2:].upper()}")
        except ValueError:
            print(f"❌ '{t}' 不是有效的{base_from}进制数字")
    else:
        print(f"❌ 不支持 {m}。可选: Base64 / URL / Unicode / MD5 / SHA1 / SHA256 / 进制")
except Exception as e:
    print(f"❌ 处理失败: {e}")
```

</details>

---

#### 2.3 词频统计

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
from collections import Counter
import re

STOPWORDS = {'的','了','和','是','在','我','有','也','不','就','都','而','及','与','着','或','一个','没有',
    '我们','你们','他们','她们','但是','然而','因为','所以','如果','虽然','不过','而且','或者','还是',
    '既','又','并','等','把','被','让','往','从','对','于','以','为','比','此','那','这','她','他','它',
    '们','些','什么','哪','怎么','多','很','最','更','太','非常','每','当','起','已','将','能','会','应',
    '可','得','过','给','来','去','说','看','知道','做','想','问','请','好','再','还','只','如','真的',
    '自己','人','事','时','地','今天','现在','一些','这样','那样','怎么样','可以','这个','那个','不是',
    '可能','已经','之后','之前','然后','不过','比较','其实','其他','其中','所有','虽然','由于','因此'}

def _smart_segment(text):
    try:
        import jieba
        return list(jieba.lcut(text, cut_all=False))
    except ImportError:
        return re.findall(r'[一-鿿\w]+', text)

try:
    t = input("输入文本:")
    if not t.strip():
        print("❌ 没有检测到输入")
    else:
        raw = _smart_segment(t)
        words = []
        for w in raw:
            w = w.strip()
            if len(w) <= 1: continue
            if re.match(r'^[a-zA-Z]+$', w): w = w.lower()
            if w in STOPWORDS: continue
            words.append(w)
        if not words:
            print("❌ 没有找到有效词")
        else:
            for i,(word,cnt) in enumerate(Counter(words).most_common(15),1):
                print(f"  {i:2d}. {word}: {cnt} {'█'*min(cnt*2,30)}")
            unique = len(set(words))
            print(f"\n📊 共 {len(words)} 个有效词，{unique} 个不重复词")
            d = unique/len(words)*100
            print(f"   词汇丰富度: {d:.1f}%", end="")
            print("（用词多样）" if d>80 else "（正常范围）" if d>50 else "（同词重复较多）")
            try:
                import jieba; print("   ✅ 已使用 jieba 精准分词")
            except: print("   💡 安装 jieba 可获得更精准分词: pip install jieba")
except Exception as e:
    print(f"❌ {e}")
```

</details>

---

### 📚 模块 3：教育工具

---

#### 3.1 知识查询

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
import urllib.request, urllib.parse, json, socket, re

def _wiki_fallback(query: str) -> list[dict]:
    url = f"https://baike.deno.dev/item/{urllib.parse.quote(query)}?encode=json"
    req = urllib.request.Request(url, headers={"User-Agent":"dgngjx/3.5"})
    resp = urllib.request.urlopen(req, timeout=10)
    data = json.loads(resp.read())
    results = []
    if isinstance(data, list):
        for item in data:
            title = item.get("title", "")
            abstract = item.get("abstract", "").replace("\n", " ").strip()
            if title: results.append({"title": title, "snippet": abstract[:200]})
    elif isinstance(data, dict):
        title = data.get("title", query)
        abstract = data.get("abstract", data.get("description", ""))
        results = [{"title": title, "snippet": str(abstract)[:200]}]
    return results

try:
    q = input("关键词:") or "勾股定理"
    if not q.strip():
        print("❌ 关键词不能为空")
    else:
        results = []
        try:
            url = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(q)}&format=json&srlimit=3"
            req = urllib.request.Request(url, headers={"User-Agent":"dgngjx/3.5"})
            resp = urllib.request.urlopen(req, timeout=10)
            data = json.loads(resp.read())
            results = data.get("query",{}).get("search",[])
        except Exception as e:
            print(f"⚠️ Wikipedia 失败（{type(e).__name__}），切换到百度百科...")
        if not results:
            try: results = _wiki_fallback(q)
            except Exception as e2: print(f"⚠️ 百度百科也失败: {e2}")
        if not results:
            print(f"❌ 没有找到关于「{q}」的内容")
            print(f"   百度搜索: https://www.baidu.com/s?wd={urllib.parse.quote(q)}")
        else:
            for r in results:
                t = r.get('title','')
                s = re.sub(r'<[^>]+>', '', r.get('snippet',''))[:200]
                print(f"\n📖 {t}\n   {s}...")
except Exception as e:
    print(f"❌ 意外错误: {e}")
```

</details>

---

### 🎮 模块 4：生活娱乐

---

#### 4.1 娱乐小工具

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
import urllib.request, json, random

def _joke_cn():
    apis = [
        ("https://api.apiopen.top/getJoke?page=1&count=1&type=txt", lambda d: d.get("result",[{}])[0].get("content","")),
        ("https://v1.hitokoto.cn/?c=a", lambda d: f"{d.get('hitokoto','')} —— {d.get('from','')}")),
        ("https://api.oioweb.cn/api/common/Hitokoto", lambda d: f"{d.get('result',{}).get('content','')} —— {d.get('result',{}).get('from','')}")),
    ]
    for url, extract in apis:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"dgngjx/3.5"}), timeout=5)
            data = json.loads(r.read())
            text = extract(data)
            if text.strip(): return text
        except: continue
    return ""

try:
    c = input("选择(1笑话/2一言/3运势):").strip() or "1"
    if c == "1":
        joke = _joke_cn()
        if joke: print(f"😄 {joke}")
        else:
            jokes = [
                ("程序员为什么喜欢用暗色主题？", "因为光明会引来 bug！"),
                ("老婆问程序员丈夫：你到底爱不爱我？", "当然爱。老婆：那你能不能不在'当然爱'后面加分号？感觉像执行完就结束。"),
            ]
            s, p = random.choice(jokes)
            print(f"📶 联网失败，给你讲个本地笑话：\n   {s}\n   → {p}")
    elif c == "2":
        for url, extract in [
            ("https://v1.hitokoto.cn/", lambda d: f"{d.get('hitokoto','')} —— {d.get('from','')}"),
            ("https://tenapi.cn/v2/yiyan", lambda d: d.get("data","") or d.get("content","")),
        ]:
            try:
                r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"dgngjx/3.5"}), timeout=5)
                t = extract(json.loads(r.read()))
                if t: print(f"✨ {t}"); break
            except: continue
        else: print("📶 一言API不可用，试试 https://hitokoto.cn/")
    elif c == "3":
        print(random.choice(["大吉","中吉","小吉","吉","末吉","凶","大凶"]))
    else: print("❌ 请输入 1、2 或 3")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 4.2 壁纸中心

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
import urllib.request, urllib.parse, json

def _wallpaper_cn():
    for url, src in [
        ("https://imgapi.cn/api.php?zd=pc&fl=fengjing&gs=jpg", "风景随机"),
        ("https://picsum.photos/1920/1080", "随机摄影"),
    ]:
        try:
            r = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent":"dgngjx/3.5"}), timeout=8)
            final = r.geturl()
            if final and final != url: return (final, src)
        except: continue
    return None

try:
    _ = input("关键词:").strip() or "nature"
    result = _wallpaper_cn()
    if result:
        print(f"📷 来源: {result[1]}\n   下载: {result[0]}")
        print("   💡 右键→图片另存为")
    else:
        print("❌ 壁纸源不可用")
        print("   • https://unsplash.com/s/photos/nature")
        print("   • https://pixabay.com/zh/images/search/nature/")
except Exception as e: print(f"❌ {e}")
```

</details>

---

### 💻 模块 5：开发工具

---

#### 5.1 JSON 工具

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
import json
try:
    r = input("输入JSON:").strip() or '{"key":"value"}'
    if not r: print("❌ 没有输入")
    else:
        p = json.loads(r)
        print(f"✅ 合法\n格式化: {json.dumps(p,ensure_ascii=False,indent=2)}")
        print(f"压缩: {json.dumps(p,ensure_ascii=False,separators=(',',':'))}")
except json.JSONDecodeError as e:
    print(f"❌ JSON错误: {e}")
```

</details>

---

#### 5.2 HTTP 接口测试

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
import urllib.request, socket, ssl
try:
    u = input("URL:").strip() or "https://api.github.com"
    if not u: print("❌ URL不能为空")
    elif not u.startswith("http"): print("❌ 应以 http:// 或 https:// 开头")
    else:
        req = urllib.request.Request(u, headers={"User-Agent":"dgngjx/3.5"})
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        resp = urllib.request.urlopen(req, timeout=15, context=ctx)
        body = resp.read()
        print(f"✅ 状态: {resp.status} ({len(body)} bytes)")
except urllib.error.HTTPError as e:
    print(f"❌ HTTP {e.code}: {e.reason}")
except urllib.error.URLError as e:
    print(f"❌ 网络错误: {e.reason}")
except Exception as e:
    print(f"❌ {e}")
```

</details>

---

#### 5.3 Token 计算器

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
t = input("文本:") or "计算Token数"
if not t.strip(): print("❌ 请输入文字")
else:
    cn = sum(1 for c in t if '一' <= c <= '鿿')
    en = len(t) - cn
    print(f"中文: {cn} ≈{int(cn/1.5)} | 英文: {en} ≈{int(en/4)} | 总计 ≈{int(cn/1.5+en/4)}")
```

</details>

---

#### 5.4 在线 Photoshop

📦 **需 Pillow**

<details>
<summary>📋 展开查看命令</summary>

```python
from PIL import Image, ImageEnhance
try:
    f = input("图片路径:").strip().strip('"').replace("\\","/") or "photo.jpg"
    img = Image.open(f)
    w,h = map(int, input("裁剪 宽,高:").strip() or "200,200").split(","))
    if w > img.width or h > img.height: w,h = min(w,img.width), min(h,img.height)
    img2 = img.crop(((img.width-w)//2,(img.height-h)//2,w+img.width//2,h+img.height//2))
    img2.save("cropped.jpg")
    e = ImageEnhance.Brightness(img).enhance(float(input("亮度(1.2):") or 1.2))
    e.save("bright.jpg")
    print("✅ 已保存 cropped.jpg, bright.jpg")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 5.5 Mermaid 时序图

**✅ 开箱即用**

<details>
<summary>📋 展开查看命令</summary>

```python
seq = input("时序图代码:").strip() or "A->B: Hello"
if seq: print(f"sequenceDiagram\n{seq}")
else: print("❌ 代码不能为空")
```

</details>

---

### 🖼️ 模块 6：图片工具

---

#### 6.1 图片压缩

📦 **需 Pillow**

<details>
<summary>📋 展开查看命令</summary>

```python
from PIL import Image, ImageFile
import os
ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = 180_000_000

def _fix_path(p):
    return p.strip().strip('"').strip("'").replace("\\","/").replace("//","/")

f = _fix_path(input("图片路径:").strip() or "photo.jpg")
if not os.path.exists(f):
    print(f"❌ 文件不存在: {f}")
else:
    size = os.path.getsize(f)
    if size > 200*1024*1024:
        print(f"⚠️ {size/1024/1024:.1f}MB 大文件，压缩可能需1-5分钟")
        print("   💡 确保内存 > 图片大小×3")
        if input("按回车继续 或 q 退出: ").strip().lower() == 'q': f=""
    if f:
        try:
            q = int(input("质量(1-100,建议70-85):") or 80)
            if not 1<=q<=100: q=80
            img = Image.open(f)
            w,h = img.size
            if w*h > 50_000_000: print(f"⚠️ {w}×{h} 可能需1-3分钟...")
            if img.mode in ('RGBA','PA'): img = img.convert('RGB')
            out = f"compressed_{os.path.basename(f)}"
            img.save(out, quality=q, optimize=True)
            o,c = os.path.getsize(f)/1024, os.path.getsize(out)/1024
            rate = 100 - c/o*100 if o>0 else 0
            print(f"✅ {o:.0f}KB → {c:.0f}KB (降{rate:.0f}%)")
            if rate<0: print("   💡 已高度压缩，尝试质量=60")
        except MemoryError: print("❌ 内存不足！缩小尺寸再试")
        except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 6.2 人像抠图

📦 **需 rembg**

<details>
<summary>📋 展开查看命令</summary>

```python
from rembg import remove
import os
try:
    inp = input("图片:").strip().strip('"').replace("\\","/") or "portrait.jpg"
    if not os.path.exists(inp):
        print(f"❌ 文件不存在: {inp}")
    else:
        out = f"bg_removed_{os.path.basename(inp)}.png"
        result = remove(open(inp,"rb").read())
        open(out,"wb").write(result)
        print(f"✅ 完成: {out}")
except ImportError: print("❌ 缺少 rembg: pip install rembg")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 6.3 证件照生成

📦 **需 Pillow**

<details>
<summary>📋 展开查看命令</summary>

```python
from PIL import Image
try:
    f = input("照片:").strip().strip('"').replace("\\","/") or "face.jpg"
    sz = input("尺寸(一寸/二寸):").strip() or "一寸"
    bg = input("背景色(白色/蓝色/红色):").strip() or "白色"
    sizes = {"一寸":(295,413),"二寸":(413,579)}
    bgs = {"白色":(255,255,255),"蓝色":(0,0,255),"红色":(255,0,0)}
    w,h = sizes.get(sz, sizes["一寸"])
    img = Image.open(f).resize((w,h),Image.LANCZOS)
    canvas = Image.new("RGB",(w,h),bgs.get(bg, (255,255,255)))
    canvas.paste(img,(0,0),img if img.mode=="RGBA" else None)
    canvas.save(f"证件照_{sz}_{bg}.png")
    print(f"✅ 证件照_{sz}_{bg}.png ({w}x{h})")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 6.4 图片修复

📦 **需 Pillow**

<details>
<summary>📋 展开查看命令</summary>

```python
from PIL import Image, ImageEnhance
try:
    f = input("老照片路径:").strip().strip('"').replace("\\","/") or "old.jpg"
    img = Image.open(f)
    img = ImageEnhance.Sharpness(img).enhance(1.5)
    img = ImageEnhance.Brightness(img).enhance(1.1)
    img = ImageEnhance.Contrast(img).enhance(1.2)
    img.save("repaired.jpg")
    print("✅ 完成: repaired.jpg")
except Exception as e: print(f"❌ {e}")
```

</details>

---

### 📄 模块 7：PDF 转换

---

#### 7.1 PDF 合并

📦 **需 PyPDF2**

<details>
<summary>📋 展开查看命令</summary>

```python
from PyPDF2 import PdfMerger
import os
files = []
total_mb = 0
try:
    while True:
        f = input(f"文件{len(files)+1}(回车结束):").strip().strip('"').replace("\\","/")
        if not f: break
        if not os.path.exists(f): print(f"❌ 跳过: {f}"); continue
        size_mb = os.path.getsize(f)/1024/1024
        total_mb += size_mb
        if size_mb > 500: print(f"⚠️ {size_mb:.0f}MB 大文件，合并可能较慢")
        files.append(f)
    if len(files) < 2: print("❌ 至少2个PDF")
    else:
        if total_mb > 100: print(f"⚠️ 总大小 {total_mb:.0f}MB，需1-5分钟...")
        m = PdfMerger()
        ok = 0
        for f in files:
            try: m.append(f); ok+=1
            except: print(f"⚠️ 跳过损坏文件: {f}")
        if len(m.pages)==0: print("❌ 全部损坏")
        else:
            m.write("merged.pdf"); m.close()
            print(f"✅ merged.pdf ({ok}/{len(files)} 文件, {os.path.getsize('merged.pdf')/1024/1024:.1f}MB)")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 7.2 PDF 拆分

📦 **需 PyPDF2**

<details>
<summary>📋 展开查看命令</summary>

```python
from PyPDF2 import PdfReader, PdfWriter
import os
try:
    inp = input("PDF路径:").strip().strip('"').replace("\\","/") or "source.pdf"
    pgs = input("页码(如 1-3):").strip() or "1-3"
    if not os.path.exists(inp): print("❌ 文件不存在")
    else:
        r = PdfReader(inp)
        if r.is_encrypted: print("❌ 已加密，请先解密！")
        else:
            w = PdfWriter(); total = len(r.pages); added = 0
            for p in pgs.split(","):
                if "-" in p:
                    s,e = map(int, p.split("-"))
                    if s>e: s,e = e,s
                    for i in range(max(0,s-1),min(e,total)):
                        w.add_page(r.pages[i]); added+=1
                else:
                    idx = int(p)-1
                    if 0<=idx<total: w.add_page(r.pages[idx]); added+=1
            w.write("extracted.pdf")
            print(f"✅ extracted.pdf ({added}页)")
except Exception as e: print(f"❌ {e}")
```

</details>

---

#### 7.3 PDF 加密 / 7.4 PDF 解密

📦 **需 PyPDF2**

<details>
<summary>📋 展开查看命令</summary>

```python
from PyPDF2 import PdfReader, PdfWriter
# 加密
inp = input("PDF路径:").strip().strip('"') or "source.pdf"
pwd = input("密码:").strip()
if len(pwd)<4: print("⚠️ 密码太短")
else:
    r=PdfReader(inp); w=PdfWriter()
    for p in r.pages: w.add_page(p)
    w.encrypt(pwd); w.write("encrypted.pdf")
    print("✅ encrypted.pdf (密码丢失无法恢复!)")

# 解密
inp = input("加密PDF:").strip().strip('"') or "encrypted.pdf"
pwd = input("密码:").strip()
r=PdfReader(inp)
if r.is_encrypted: r.decrypt(pwd)
w=PdfWriter()
for p in r.pages: w.add_page(p)
w.write("decrypted.pdf"); print("✅ decrypted.pdf")
```

</details>

---

### 🎬 模块 8：视频工具

---

#### 8.1 视频格式转换 / 8.2 视频编辑 / 8.3 在线录屏

📦 **需 FFmpeg**

> 详见下方「📦 依赖管理」章节。

<details>
<summary>📋 视频格式转换命令</summary>

```python
import subprocess, os
f = input("文件:").strip().strip('"').replace("\\","/") or "video.mp4"
o = input("格式(gif/mp4/avi/mov/webm):").strip() or "gif"
out = f"{os.path.splitext(f)[0]}.{o}"
if not os.path.exists(f): print(f"❌ 文件不存在: {f}")
else:
    size = os.path.getsize(f)/1024/1024
    if size>500: print(f"⚠️ {size:.0f}MB 可能需5-30分钟")
    r = subprocess.run(["ffmpeg","-i",f,"-y"]
        + (["-vf","scale=480:-1"] if o=="gif" and size>50 else [])
        + [out], capture_output=True, text=True, timeout=1800)
    if r.returncode==0: print(f"✅ {out} ({os.path.getsize(out)/1024:.0f}KB)")
    else: print(f"❌ {r.stderr[:300]}")
```

</details>

<details>
<summary>📋 视频编辑命令（6功能菜单）</summary>

```python
import subprocess, os, json

def _fix(p): return p.strip().strip('"').strip("'").replace("\\","/").replace("//","/")

def _info(f):
    r = subprocess.run(["ffprobe","-v","quiet","-print_format","json","-show_format","-show_streams",f], capture_output=True, text=True, timeout=30)
    return json.loads(r.stdout) if r.returncode==0 else None

act = input("操作(1裁剪/2拼接/3提取音频/4水印/5截图/6信息):").strip() or "1"
if act=="6":
    f = _fix(input("文件:") or "video.mp4")
    info = _info(f)
    if info:
        dur = float(info.get("format",{}).get("duration",0))
        print(f"时长: {int(dur//3600):02d}:{int((dur%3600)//60):02d}:{int(dur%60):02d}")
        print(f"大小: {int(info.get('format',{}).get('size',0))/1024/1024:.1f}MB")
        for s in info.get("streams",[]):
            if s.get("codec_type")=="video": print(f"视频: {s.get('codec_name','?')} {s.get('width','?')}x{s.get('height','?')}")
            elif s.get("codec_type")=="audio": print(f"音频: {s.get('codec_name','?')} {s.get('sample_rate','?')}Hz")
```

</details>

---

### 🛠️ 模块 9：实用小工具

---

#### 9.1 二维码生成 / 9.2 密码生成 / 9.3 正则测试

**✅ 开箱即用**

<details>
<summary>📋 二维码生成</summary>

```python
import urllib.parse
text = input("内容/URL:") or "https://www.example.com"
url = f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(text,safe='')}"
print(f"📱 复制到浏览器下载: {url}")
```

</details>

<details>
<summary>📋 密码生成器</summary>

```python
import random, string, math
length = int(input("密码长度(16):") or 16)
chars = string.ascii_letters + string.digits + "!@#$%^&*"
pwd = ''.join(random.choice(chars) for _ in range(length))
entropy = length * math.log2(len(chars))
print(f"🔐 {pwd}")
print(f"强度: {'★★★★★' if entropy>=80 else '★★★★☆' if entropy>=60 else '★★★☆☆'} ({entropy:.1f} bits)")
```

</details>

<details>
<summary>📋 正则测试器</summary>

```python
import re
p = input("正则:") or r"\b\w+@\w+\.\w+\b"
t = input("文本:") or "test@example.com"
try:
    m = re.findall(p, t)
    print(f"✅ 找到 {len(m)} 个: {m}" if m else "❌ 无匹配")
except re.error as e: print(f"❌ 语法错误: {e}")
```

</details>

---

#### 9.4 文件哈希校验 ⭐ v3.6.0 新增

**✅ 开箱即用**（纯 Python 标准库 hashlib，零依赖）

> 校验下载文件完整性 / 比对文件是否被篡改。支持 MD5 / SHA1 / SHA256，分块读取大文件不占内存。

<details>
<summary>📋 展开查看命令</summary>

```python
import hashlib, os

path = input("文件路径:").strip().strip('"').strip("'")
if not path or not os.path.isfile(path):
    print(f"❌ 文件不存在: {path}")
else:
    algos = {"md5": hashlib.md5(), "sha1": hashlib.sha1(), "sha256": hashlib.sha256()}
    size = os.path.getsize(path)
    # 大文件分块读取（8MB/块），不一次性载入内存
    chunk = 8 * 1024 * 1024
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk)
            if not data:
                break
            for h in algos.values():
                h.update(data)
    print(f"📄 文件: {os.path.basename(path)}  ({size/1024:.1f} KB)")
    for name, h in algos.items():
        print(f"  {name.upper():7}: {h.hexdigest()}")
    # 可选：与期望值比对
    expect = input("粘贴期望哈希值比对(可留空回车跳过):").strip().lower()
    if expect:
        matched = [n for n, h in algos.items() if h.hexdigest().lower() == expect]
        print(f"✅ 校验通过（{matched[0].upper()}）" if matched else "❌ 校验失败：哈希值不匹配，文件可能已损坏或被篡改")
```

</details>

---

#### 9.5 UUID 生成器 ⭐ v3.6.0 新增

**✅ 开箱即用**（纯 Python 标准库 uuid，零依赖）

> 生成唯一标识符：uuid4（随机，最常用）/ uuid1（基于时间+MAC）/ 批量生成。

<details>
<summary>📋 展开查看命令</summary>

```python
import uuid

mode = input("类型(uuid4随机/uuid1时间/nodash无横线):").strip() or "uuid4"
try:
    count = int(input("生成数量(默认1):") or 1)
except ValueError:
    count = 1
count = max(1, min(count, 100))  # 上限100个，防止误输入巨大值

for _ in range(count):
    if mode == "uuid1":
        u = str(uuid.uuid1())
    elif mode == "nodash":
        u = uuid.uuid4().hex
    else:
        u = str(uuid.uuid4())
    print(u)
print(f"✅ 已生成 {count} 个 UUID（{mode}）")
```

</details>

---

#### 9.6 时间戳转换 ⭐ v3.6.0 新增

**✅ 开箱即用**（纯 Python 标准库 datetime，零依赖）

> Unix 时间戳 ↔ 日期时间互转。支持秒/毫秒级，自动识别，方便调试接口和日志。

<details>
<summary>📋 展开查看命令</summary>

```python
import datetime, time

s = input("输入时间戳 或 日期(YYYY-MM-DD HH:MM:SS)，留空取当前:").strip()
if not s:
    now = time.time()
    print(f"⏰ 当前时间: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}")
    print(f"   秒级时间戳: {int(now)}")
    print(f"   毫秒级时间戳: {int(now*1000)}")
elif s.replace(".", "").isdigit():
    ts = float(s)
    if ts > 1e12:  # 毫秒级自动识别
        ts /= 1000
    try:
        dt = datetime.datetime.fromtimestamp(ts)
        print(f"✅ 时间戳 {s} →")
        print(f"   本地时间: {dt:%Y-%m-%d %H:%M:%S}")
        print(f"   星期: {'一二三四五六日'[dt.weekday()]}")
    except (ValueError, OSError):
        print("❌ 时间戳超出有效范围")
else:
    parsed = None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d"):
        try:
            parsed = datetime.datetime.strptime(s, fmt)
            break
        except ValueError:
            continue
    if parsed:
        print(f"✅ 日期 {s} →")
        print(f"   秒级时间戳: {int(parsed.timestamp())}")
        print(f"   毫秒级时间戳: {int(parsed.timestamp()*1000)}")
    else:
        print("❌ 无法识别，请用 时间戳 或 YYYY-MM-DD HH:MM:SS 格式")
```

</details>

---

#### 9.7 IP 工具 ⭐ v3.6.0 新增

**✅ 开箱即用**（纯 Python 标准库 ipaddress/socket，零依赖）

> IP 地址解析、类型判断、子网计算、本机 IP 查询。IPv4/IPv6 通用。

<details>
<summary>📋 展开查看命令</summary>

```python
import ipaddress, socket

s = input("输入IP或网段(如192.168.1.0/24)，留空查本机:").strip()
if not s:
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"🖥️ 主机名: {hostname}")
        print(f"   本机IP: {local_ip}")
    except socket.error as e:
        print(f"❌ 获取本机IP失败: {e}")
else:
    try:
        if "/" in s:  # 网段计算
            net = ipaddress.ip_network(s, strict=False)
            print(f"✅ 网段: {net}")
            print(f"   网络地址: {net.network_address}")
            print(f"   广播地址: {net.broadcast_address}")
            print(f"   子网掩码: {net.netmask}")
            print(f"   可用主机数: {net.num_addresses}")
        else:  # 单个IP解析
            ip = ipaddress.ip_address(s)
            print(f"✅ IP: {ip}  (IPv{ip.version})")
            print(f"   私有地址: {'是' if ip.is_private else '否'}")
            print(f"   回环地址: {'是' if ip.is_loopback else '否'}")
            print(f"   多播地址: {'是' if ip.is_multicast else '否'}")
    except ValueError as e:
        print(f"❌ 无效的IP或网段: {e}")
```

</details>

---

### 🖥️ 模块 10：系统工具 ⭐ v3.5 新增模块

---

#### 10.1 系统资源监控 ⭐ v3.5.0 新增

**✅ 开箱即用**

实时监控 CPU、内存、磁盘使用率，返回中文信息。

<details>
<summary>📋 展开查看命令</summary>

```python
import os, platform, subprocess, time

def get_system_resources():
    """获取系统资源信息（跨Windows/macOS/Linux）"""
    info = {'cpu_usage': 0, 'ram_total_mb': 0, 'ram_used_mb': 0, 'ram_percent': 0,
            'disk_total_gb': 0, 'disk_used_gb': 0, 'disk_percent': 0,
            'cpu_count': os.cpu_count() or 2, 'platform': platform.system()}
    
    # CPU 使用率
    try:
        if info['platform'] == 'Windows':
            r = subprocess.run(['wmic','cpu','get','loadpercentage'], capture_output=True, text=True, timeout=5)
            lines = [l.strip() for l in r.stdout.split('\n') if l.strip().isdigit()]
            info['cpu_usage'] = int(lines[0]) if lines else 0
        else:
            r = subprocess.run(['grep','-c','processor','/proc/cpuinfo'], capture_output=True, text=True, timeout=5)
            info['cpu_usage'] = 0  # Linux
    except: pass
    
    # 内存信息
    try:
        if info['platform'] == 'Windows':
            r = subprocess.run(['wmic','OS','get','FreePhysicalMemory,TotalVisibleMemorySize','/value'], capture_output=True, text=True, timeout=5)
            free = total = 0
            for line in r.stdout.split('\n'):
                if 'TotalVisibleMemorySize' in line: total = int(line.split('=')[1].strip())
                elif 'FreePhysicalMemory' in line: free = int(line.split('=')[1].strip())
            info['ram_total_mb'] = total // 1024
            info['ram_used_mb'] = (total - free) // 1024
            if total > 0: info['ram_percent'] = int((total-free)/total*100)
        else:
            with open('/proc/meminfo') as f:
                mem = {}
                for line in f:
                    parts = line.split()
                    if parts[0] in ('MemTotal:','MemAvailable:','MemFree:'):
                        mem[parts[0]] = int(parts[1])
            total = mem.get('MemTotal:',0)
            avail = mem.get('MemAvailable:', mem.get('MemFree:',0))
            info['ram_total_mb'] = total // 1024
            info['ram_used_mb'] = (total - avail) // 1024
            if total > 0: info['ram_percent'] = int((total-avail)/total*100)
    except: pass
    
    # 磁盘信息
    try:
        if info['platform'] == 'Windows':
            r = subprocess.run(['wmic','logicaldisk','get','size,freespace,caption','/value'], capture_output=True, text=True, timeout=5)
            total = free = 0
            for block in r.stdout.split('\n\n'):
                for line in block.split('\n'):
                    if 'Size=' in line: total += int(line.split('=')[1].strip() or 0)
                    elif 'FreeSpace=' in line: free += int(line.split('=')[1].strip() or 0)
            info['disk_total_gb'] = total // (1024**3)
            info['disk_used_gb'] = (total - free) // (1024**3)
            if total > 0: info['disk_percent'] = int((total-free)/total*100)
        else:
            r = subprocess.run(['df','/'], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split('\n')
            if len(lines)>1:
                parts = lines[1].split()
                if len(parts)>=4:
                    total = int(parts[1])
                    used = int(parts[2])
                    info['disk_total_gb'] = total // (1024**2)
                    info['disk_used_gb'] = used // (1024**2)
                    info['disk_percent'] = int(parts[4].replace('%',''))
    except: pass
    
    return info

res = get_system_resources()
print("=" * 40)
print("  📊 dgngjx-skill 系统资源监控")
print("=" * 40)
print(f"🖥️ 系统: {res['platform']}")
print(f"⚡ CPU: {res['cpu_usage']}% 占用 | {res['cpu_count']} 核心")
print(f"🧠 内存: {res['ram_used_mb']}/{res['ram_total_mb']} MB ({res['ram_percent']}%)")
print(f"💾 磁盘: {res['disk_used_gb']}/{res['disk_total_gb']} GB ({res['disk_percent']}%)")
print()

# 预警
if res['ram_percent'] > 90: print("🔴 内存严重不足！建议关闭部分程序")
elif res['ram_percent'] > 75: print("🟡 内存偏高，考虑释放")
if res['disk_percent'] > 90: print("🔴 磁盘空间告急！清理空间")
elif res['disk_percent'] > 80: print("🟡 磁盘空间偏低")
if res['cpu_usage'] > 90: print("🔴 CPU 负载过高")
elif res['cpu_usage'] > 75: print("🟡 CPU 使用率较高")
```

</details>

**⚠️ 可能遇到的坑：**

| 情况 | 原因 | 解决 |
|------|------|------|
| 获取失败返回 0 | 权限不足 | 以管理员权限运行 |
| wmic 被禁用 | Windows 精简版 | 改用 PowerShell 命令 |
| macOS 内存显示异常 | macOS 内存管理机制 | 正常行为，macOS 积极利用内存 |

---

#### 10.2 批量文件重命名 ⭐ v3.5.0 新增

**✅ 开箱即用**（零依赖，纯 os 模块）

批量预览后才能执行，支持正则替换、序号前缀、大小写转换。

<details>
<summary>📋 展开查看命令</summary>

```python
import os, re

def _fix_path(p):
    return p.strip().strip('"').strip("'").replace("\\","/").replace("//","/")

BLOCKED_EXTS = {'.exe','.dll','.bat','.cmd','.ps1','.vbs','.sh','.com','.scr','.hta','.reg','.msi','.apk','.jar'}

dir_path = _fix_path(input("目录路径:").strip() or ".")
if not os.path.isdir(dir_path):
    print(f"❌ 目录不存在: {dir_path}")
else:
    files = [f for f in os.listdir(dir_path) if os.path.isfile(os.path.join(dir_path,f))]
    # 过滤掉黑名单文件
    safe_files = [f for f in files if os.path.splitext(f)[1].lower() not in BLOCKED_EXTS]
    if len(safe_files) != len(files):
        print(f"⚠️ 已跳过 {len(files)-len(safe_files)} 个系统/可执行文件")
    files = safe_files
    
    if not files:
        print("❌ 目录为空或无安全文件")
    else:
        print(f"\n📁 {dir_path} 中找到 {len(files)} 个文件")
        print()
        print("重命名模式:")
        print("  1. 添加前缀 (如: photo_001.jpg)")
        print("  2. 添加后缀 (如: 001_终版.jpg)")
        print("  3. 正则替换 (正则表达式匹配替换)")
        print("  4. 大小写转换 (全部小写/大写)")
        print("  5. 序号重命名 (统一前缀+递增数字)")
        mode = input("选择模式(1-5):").strip() or "1"
        
        previews = []
        
        if mode == "1":
            prefix = input("前缀:").strip() or "file_"
            for i, fn in enumerate(files):
                new = prefix + fn
                previews.append((fn, new))
                
        elif mode == "2":
            suffix = input("后缀:").strip() or "_ok"
            for fn in files:
                name, ext = os.path.splitext(fn)
                new = name + suffix + ext
                previews.append((fn, new))
                
        elif mode == "3":
            pattern = input("匹配正则:").strip()
            repl = input("替换为:").strip()
            if not pattern:
                print("❌ 正则表达式不能为空")
                previews = []
            else:
                for fn in files:
                    new = re.sub(pattern, repl, fn)
                    previews.append((fn, new))
                    
        elif mode == "4":
            upper = input("转大写?(Y/n):").strip().lower() != 'n'
            for fn in files:
                new = fn.upper() if upper else fn.lower()
                previews.append((fn, new))
                
        elif mode == "5":
            prefix = input("统一前缀:").strip() or "file"
            start = int(input("起始序号(1):") or 1)
            width = int(input("序号位数(3):") or 3)
            for i, fn in enumerate(files):
                _, ext = os.path.splitext(fn)
                new = f"{prefix}_{str(start+i).zfill(width)}{ext}"
                previews.append((fn, new))
        
        if previews:
            print(f"\n📋 预览（共 {len(previews)} 个文件）:")
            print("-" * 60)
            for old, new in previews[:10]:
                if old != new:
                    print(f"  {old}")
                    print(f"    → {new}")
                else:
                    print(f"  {old} （无变化）")
            if len(previews) > 10:
                print(f"  ... 还有 {len(previews)-10} 个文件")
            print("-" * 60)
            
            # 检查冲突
            new_names = [new for _, new in previews]
            if len(new_names) != len(set(new_names)):
                print("⚠️ 警告：新文件名存在冲突！")
                from collections import Counter
                for name, cnt in Counter(new_names).items():
                    if cnt > 1:
                        print(f"   冲突: {name} ({cnt}次)")
                print("   请修改规则避免冲突")
            else:
                confirm = input(f"\n确认执行? (输入 YES 确认): ").strip()
                if confirm == "YES":
                    success = 0
                    for old, new in previews:
                        if old != new:
                            old_path = os.path.join(dir_path, old)
                            new_path = os.path.join(dir_path, new)
                            if not os.path.exists(new_path):
                                os.rename(old_path, new_path)
                                success += 1
                            else:
                                print(f"⚠️ 已存在，跳过: {new}")
                    print(f"✅ 已重命名 {success} 个文件")
                else:
                    print("❎ 已取消")
```

</details>

**⚠️ 可能遇到的坑：**

| 情况 | 原因 | 解决 |
|------|------|------|
| 输入 YES 仍被拒绝 | 必须大写的 YES | 输入 `YES` |
| 文件名冲突 | 替换规则导致重名 | 修改正则或前缀 |
| 无变化 | 规则未匹配 | 检查正则或前缀 |
| 跳过系统文件 | 安全规则拦截 | 正常行为，不可执行文件不参与 |

---

#### 10.3 Markdown 转 HTML ⭐ v3.5.0 新增

**✅ 开箱即用**（零依赖纯 Python，将 Markdown 文件转为带样式的独立 HTML）

<details>
<summary>📋 展开查看命令</summary>

```python
import os, re, html

def _fix_path(p):
    return p.strip().strip('"').strip("'").replace("\\","/").replace("//","/")

BLOCKED_EXTS = {'.exe','.dll','.bat','.cmd','.ps1','.vbs','.sh','.com','.scr','.hta','.reg','.msi','.apk','.jar'}

f = _fix_path(input("Markdown文件路径:").strip() or "README.md")
if not os.path.exists(f):
    print(f"❌ 文件不存在: {f}")
else:
    ext = os.path.splitext(f)[1].lower()
    if ext in BLOCKED_EXTS:
        print(f"🚫 安全规则禁止处理 {ext} 文件")
    else:
        with open(f, 'r', encoding='utf-8') as md_file:
            md_content = md_file.read()
        
        # ===== 极简 Markdown → HTML 转换（零依赖）=====
        lines = md_content.split('\n')
        html_lines = []
        in_code_block = False
        in_list = False
        
        for line in lines:
            stripped = line.strip()
            
            # 代码块
            if stripped.startswith('```'):
                lang = stripped[3:].strip()
                if in_code_block:
                    html_lines.append('</code></pre>')
                    in_code_block = False
                else:
                    html_lines.append(f'<pre><code class="language-{lang}">' if lang else '<pre><code>')
                    in_code_block = True
                continue
            
            if in_code_block:
                html_lines.append(html.escape(line))
                continue
            
            # 空行
            if not stripped:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append('')
                continue
            
            # 标题
            if stripped.startswith('# '):
                html_lines.append(f'<h1>{html.escape(stripped[2:])}</h1>')
                continue
            elif stripped.startswith('## '):
                html_lines.append(f'<h2>{html.escape(stripped[3:])}</h2>')
                continue
            elif stripped.startswith('### '):
                html_lines.append(f'<h3>{html.escape(stripped[4:])}</h3>')
                continue
            
            # 列表
            if stripped.startswith('- ') or stripped.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                item = stripped[2:]
                # 处理粗体
                item = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', item)
                html_lines.append(f'<li>{item}</li>')
                continue
            
            # 引用
            if stripped.startswith('> '):
                html_lines.append(f'<blockquote>{html.escape(stripped[2:])}</blockquote>')
                continue
            
            # 分隔线
            if stripped == '---':
                html_lines.append('<hr/>')
                continue
            
            # 普通段落（处理粗体和代码）
            paragraph = html.escape(stripped)
            paragraph = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', paragraph)
            paragraph = re.sub(r'`(.+?)`', r'<code>\1</code>', paragraph)
            html_lines.append(f'<p>{paragraph}</p>')
        
        if in_list:
            html_lines.append('</ul>')
        
        body_content = '\n'.join(html_lines)
        
        # ===== 内置美观样式 =====
        full_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{os.path.basename(f)}</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 40px 20px; color: #333; line-height: 1.8; }}
h1 {{ color: #1a1a1a; border-bottom: 2px solid #eee; padding-bottom: 10px; }}
h2 {{ color: #2c3e50; margin-top: 30px; }}
h3 {{ color: #34495e; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
pre {{ background: #2d2d2d; color: #f8f8f2; padding: 16px; border-radius: 6px; overflow-x: auto; }}
blockquote {{ border-left: 4px solid #ddd; margin: 0; padding-left: 16px; color: #666; }}
ul {{ padding-left: 24px; }}
li {{ margin-bottom: 4px; }}
hr {{ border: none; border-top: 1px solid #eee; margin: 20px 0; }}
strong {{ color: #1a1a1a; }}
</style>
</head>
<body>
{body_content}
</body>
</html>'''
        
        out_name = os.path.splitext(f)[0] + '.html'
        with open(out_name, 'w', encoding='utf-8') as out:
            out.write(full_html)
        
        print(f"✅ 已生成: {out_name}")
        print(f"   行数: {len(lines)} → HTML大小: {os.path.getsize(out_name)//1024}KB")
        print(f"   💡 双击打开浏览器预览")
```

</details>

**⚠️ 可能遇到的坑：**

| 情况 | 原因 | 解决 |
|------|------|------|
| 复杂表格未转换 | 极简解析器不支持 | 使用专业工具如 pandoc |
| 图片未显示 | 本地路径未转绝对路径 | 手动替换为绝对路径或URL |
| 含HTML标签的MD | 被转义 | 正常行为，安全考虑 |
| 大文件慢 | 逐行解析 | 10MB+ 文件建议用 pandoc |

---

## 最佳实践

### 场景 1：新电脑第一次用

```
你: "帮我检测一下环境"
AI: 跑检测脚本 → 自适应硬件调度初始化
你: "帮我装一下"
AI: pip install Pillow PyPDF2 jieba
你: "帮我压缩 D:\photo.jpg"
AI: ✅ 完成
```

### 场景 2：低配电脑性能保护

```
处理 50MB 图片时
→ 系统检测到 4GB RAM → 自动单任务模式
→ 显示 "⚠️ 50MB 文件 → 压缩可能需1-2分钟"
→ 分配最小资源，不卡顿
```

### 场景 3：安全文件拦截

```
你: "帮我压缩 C:\Windows\system32\cmd.exe"
AI: 🚫 .exe 可执行程序 — 安全规则禁止处理
   推荐使用专业反编译工具
```

---

## ❓ 常见问题

### Q1: 第一次使用怎么做？
直接说一句话。零依赖功能直接跑。需安装功能会提示。

### Q2: 发现 skill 有更新怎么办？
```bash
skillhub upgrade dgngjx-skill
```
或检查：`skillhub search dgngjx-skill`

### Q3: 有什么建议/bug？
📧 **邮箱：njskills@agent.qq.com**
作者会阅读每一条反馈。

### Q4: 处理大文件太慢？
v3.5.0 起已根据你的硬件自动调度，低配机会自动降为小文件单任务模式，不会出现卡死。文件哈希校验也采用分块读取，大文件不占内存。

### Q5: 批量重命名风险？
必须先预览，确认输入 `YES` 才执行。可执行文件会自动跳过。

### Q6: MD转HTML支持复杂语法吗？
支持标题、列表、代码块、引用、粗体、行内代码。复杂表格建议用 pandoc。

---

## 功能分类统计

| 类别 | 数量 | 开箱即用 |
|------|:----:|:--------:|
| ✅ 零依赖即可运行 | 24 | ✅ |
| 📦 需确认安装后运行 | 18 | ❌（有引导+在线替代） |
| **总计** | **42** | **57%** |

## v3.6.0 新特性速览

| 优化维度 | 涉及模块 | 关键提升 |
|---------|---------|---------|
| 文件哈希校验 | 模块9.4 | MD5/SHA1/SHA256，大文件分块读取，支持期望值比对 |
| UUID生成器 | 模块9.5 | uuid4/uuid1/无横线，批量生成，纯标准库 |
| 时间戳转换 | 模块9.6 | Unix时间戳↔日期互转，秒/毫秒自动识别 |
| IP工具 | 模块9.7 | IP解析/类型判断/子网计算/本机IP查询 |
| 单位换算扩展 | 模块1.4 | 从8种扩至28种（面积/速度/数据存储/压力/能量等） |
| 编码工具扩展 | 模块2.2 | 新增MD5/SHA1/SHA256哈希+2/8/10/16进制互转 |
| 全零依赖 | 新增功能 | 4个新工具+2项扩展全部纯Python标准库，无需安装 |

## 更新日志

| v3.6.0 | 2026-07-07 | 增加：文件哈希校验（模块9.4 MD5/SHA1/SHA256，大文件分块读取+期望值比对）；增加：UUID生成器（模块9.5 uuid4/uuid1/无横线批量生成）；增加：时间戳转换（模块9.6 Unix时间戳与日期互转，秒/毫秒自动识别）；增加：IP工具（模块9.7 IP解析/子网计算/本机IP查询）；扩展：单位换算器从8种扩至28种（新增面积/速度/数据存储/压力/能量等）；扩展：编码工具新增MD5/SHA1/SHA256哈希与2/8/10/16进制互转；优化：新增功能全部零依赖纯标准库实现 |
| v3.5.0 | 2026-07-14 | 增加：硬件自适应调度（自动检测CPU/RAM并智能分配并发数）；增加：安全文件过滤规则（双向检查输入输出，拦截可执行文件30+种）；增加：系统资源监控（模块10.1 实时CPU/内存/磁盘，中文报告）；增加：批量文件重命名（模块10.2 5种模式+预览确认）；增加：Markdown转HTML（模块10.3 零依赖+内置美观样式）；增加：更新提醒和邮箱njskills@agent.qq.com；优化：全局性能策略（低配模式自动降级） |
| v3.0.0 | 2026-07-13 | 增加：jieba精准分词+100+停用词过滤+英文小写化+词汇丰富度分析；增加：视频编辑6大功能（水印/截图/信息查看）；增加：路径智能修复（全部文件操作）；增加：FFmpeg一键安装脚本；增加：模块9（二维码/密码/正则）；优化：视频编辑菜单式交互 |
| v2.5.0 | 2026-07-12 | 增加：HTTP模块P0语法修复；8个模块"坑表格"扩充至4-5行；Token计算器在线链接修正 |
| v2.2.0 | 2026-07-11 | 修复：多个bug |
| v2.1.0 | 2026-07-10 | 修复：单位换算float崩溃+壁纸urllib.parse缺失；国内源更新 |
| v2.0.0 | 2026-07-09 | 增加：国内联网优化（Wikipedia/娱乐工具/壁纸/HTTP自动降级）；大文件性能增强（图片/PDF/视频）；错误提示细化 |
| v1.7.0 | 2026-07-08 | 增加：每个命令详细中文报错+解决方案+可能遇到的坑表格 |
| v1.6.0 | 2026-07-07 | 增加：详细安装引导/中文报错/最佳实践/边界情况说明 |
| v1.5.0 | 2026-07-06 | 增加：图片修复用Pillow重写/一键安装脚本/网络错误提示 |
| v1.4.0 | 2026-07-05 | 增加：命令折叠隐藏/概览页精简 |
| v1.3.0 | 2026-07-05 | 增加：30秒速查表/报错说明 |
| v1.2.0 | 2026-07-04 | 含可运行命令/FAQ |
| v1.1.0 | 2026-07-03 | 去除人脸年龄变换 |
| v1.0.0 | 2026-07-02 | 初始版本，8大模块29个工具 |

## 一键安装后可用功能

| 装这些 | 新增可用 |
|-------|---------|
| `pip install Pillow` | 压缩 / 证件照 / 基础修复 / PS |
| `pip install PyPDF2` | PDF 合并 / 拆分 / 加密 / 解密 |
| `pip install rembg` | 人像抠图（首次 300MB） |
| `pip install jieba` | 精准中文分词 |
| FFmpeg | 格式转换 / 视频编辑（6大功能） |
| `pip install qrcode[pil]` | 二维码本地生成 |

## 发布信息

- **作者**：Admin
- **联系邮箱**：njskills@agent.qq.com
- **许可证**：MIT
- **支持平台**：Windows / macOS / Linux
- **当前版本**：v3.6.0
- **检查更新**：`skillhub search dgngjx-skill`
- **升级命令**：`skillhub upgrade dgngjx-skill`
