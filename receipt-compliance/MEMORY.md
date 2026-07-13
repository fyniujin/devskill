# MEMORY.md - receipt-compliance 修改记录

## 最近修改

### v3.4.0 (2026-07-13) - 安全修复（腾讯云鼎实验室安全评估）

#### 修复内容

**1. 供应链风险修复**
- 移除 install_tesseract.ps1 中指向个人 Gitee 仓库的下载源（gitee.com/woaini0919/tesseract-ocr）
- 移除 check_env.py 中 Gitee 镜像推荐
- 替换为 winget/scoop 官方源和 GitHub 官方 Release 下载

**2. 审批链接修复**
- 将 approval_abstract.py 中 `apply_url` 从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 approval_abstract.py 中 `reference_url` 从 `https://open.duxiaoman.com/document` 改为 `https://open-dev.dingtalk.com/document`
- 将 api-endpoints.md 中钉钉网址从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 setup-guide.md 中钉钉登录地址从 `https://open.duxiaoman.com` 改为 `https://open-dev.dingtalk.com`
- 将 example-approval.md 中 `reference_url` 从 `https://open.duxiaoman.com/document` 改为 `https://open-dev.dingtalk.com/document`

**3. 命令执行风险修复**
- verify_engine.py 中 `subprocess.Popen` 移除 `shell=True`，改为 `['cmd', '/c', 'start', short_url]` 列表形式

#### 对应安全评估问题

| 评估发现问题 | 修复措施 |
|------------|---------|
| 审批接口链接指向无关第三方平台 | 全部替换为钉钉官方 open-dev.dingtalk.com |
| 从个人 Gitee 仓库下载二进制文件 | 移除 Gitee 个人镜像，替换为官方源 |
| 不受限的 shell 执行器 | 移除 shell=True，使用列表参数形式 |

---

### v3.3.0 (2026-07-13) - 更名

- 插件文件夹名从 `tax-receipt-compliance` 改为 `receipt-compliance`
- displayName 从 `财税合规全链路助手` 改为 `会计助手`
- description、标题同步更新为"会计助手"
