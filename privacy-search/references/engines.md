# 搜索引擎适配器文档

本文档说明各搜索引擎的实现细节和解析规则。

## 引擎列表

| 引擎名称 | 标识 | 类型 | 隐私友好 | 特殊说明 |
|---------|------|------|---------|---------|
| 百度 | `baidu` | HTML 解析 | ❌ | 国内最大搜索引擎，需要处理反爬机制 |
| 必应中国 | `bing` | HTML 解析 | ❌ | 微软搜索，国内可访问 |
| 搜狗 | `sogou` | HTML 解析 | ❌ | 腾讯旗下，QQ输入法合作 |
| 360搜索 | `360` | HTML 解析 | ❌ | 奇虎360旗下 |
| DuckDuckGo | `duckduckgo` | HTML 解析 | ✅ | 隐私搜索引擎，不追踪用户 |
| SearXNG | `searxng` | JSON API | ✅ | 本地元搜索，query不出本机 |

## 适配器架构

```
EngineAdapter (基类)
├── BaiduAdapter      ←→ https://www.baidu.com/s
├── BingAdapter       ←→ https://cn.bing.com/search
├── SogouAdapter      ←→ https://www.sogou.com/web
├── So360Adapter      ←→ https://www.so.com/s
├── DuckDuckGoAdapter ←→ https://html.duckduckgo.com/html/
└── SearXNGAdapter    ←→ http://127.0.0.1:8888/search (本地)
```

## 请求策略

### 超时控制
- 所有请求统一 10s 超时
- 超时自动降级，不影响其他引擎

### 频率控制
- 每日上限：单引擎 200 次
- 请求间隔：1-5s 随机延迟
- 超限自动跳过该引擎

### 请求头
| 引擎 | User-Agent | DNT | Cookie | Referer |
|------|-----------|-----|--------|---------|
| 百度 | ✅ 标准UA | ❌ | ❌ | ❌ |
| 必应 | ✅ 标准UA | ❌ | ❌ | ❌ |
| 搜狗 | ✅ 标准UA | ❌ | ❌ | ❌ |
| 360 | ✅ 标准UA | ❌ | ❌ | ❌ |
| DuckDuckGo | ✅ 标准UA | **✅ DNT=1** | ❌ | ❌ |
| SearXNG | ✅ 标准UA | ❌ | ❌ | ❌ |

## 解析规则

### 百度
- 容器：`div.result`
- 标题：`h3 a`
- 摘要：`div.c-abstract` / `div.content-right_8Zs40`

### 必应
- 容器：`li.b_algo`
- 标题：`h2 a`
- 摘要：`p`

### DuckDuckGo (HTML)
- 容器：`div.result`
- 标题：`a.result__a`
- 摘要：`a.result__snippet`

### SearXNG (JSON)
- 端点：`GET /search?q=...&format=json`
- 响应：`results[].title / url / content`

## SimHash 去重

使用简化版 SimHash 算法：

1. 取 title + snippet 前 128 字符
2. 生成 3-gram 特征
3. 每个 n-gram 计算 MD5 后异或合并
4. 汉明距离 ≤ 3 视为重复

## 交叉验证排序

综合得分 = 引擎覆盖数 × 10 - 最佳排名

- 出现在越多引擎的结果排名越靠前
- 综合分相同时按原始排名加权

## 扩展指南

如需新增引擎：

1. 继承 `EngineAdapter`
2. 实现 `search()` 和 `parse()` 方法
3. 在 `SearchOrchestrator._init_engines()` 中注册
4. 添加对应单元测试

```python
class NewEngineAdapter(EngineAdapter):
    def __init__(self):
        super().__init__("newengine", timeout=10)

    async def search(self, session, query, num=10):
        # 实现搜索请求
        pass

    def parse(self, html, num):
        # 实现 HTML 解析
        pass
```
