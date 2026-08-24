#!/usr/bin/env python3
"""
contract_ledger.py v5.2
合同台账与履约提醒引擎
功能：SQLite 台账管理、审查完成自动抽取回填、schtasks 每日扫描提醒、企微 webhook 推送
v5.2 新增：合同台账与履约提醒
"""

import json
import logging
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === 路径 ===
LEDGER_DB_PATH = Path.home() / '.contract-review' / 'ledger.db'
CONFIG_PATH = Path.home() / '.contract-review' / 'ledger_config.json'


class ContractLedger:
    """合同台账管理器 — SQLite + 自动抽取 + 提醒"""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or LEDGER_DB_PATH
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    # ---------- 数据库初始化 ----------
    def _init_db(self):
        """初始化 SQLite 表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_no TEXT UNIQUE,
                    title TEXT NOT NULL,
                    counterparty TEXT,
                    amount REAL,
                    currency TEXT DEFAULT 'CNY',
                    payment_nodes TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    status TEXT DEFAULT 'active',
                    source TEXT DEFAULT 'auto',
                    contract_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    contract_id INTEGER,
                    remind_date TEXT,
                    days_before INTEGER,
                    type TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (contract_id) REFERENCES contracts(id)
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_status ON contracts(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_contracts_end_date ON contracts(end_date)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(remind_date)
            """)
            conn.commit()

    # ---------- 自动抽取回填 ----------
    def auto_fill_from_review(self, contract_text: str, review_result: Dict[str, Any]) -> Optional[int]:
        """
        从审查结果自动抽取关键信息回填台账
        
        Args:
            contract_text: 合同原文
            review_result: 审查结果（含 contract_info, risks 等）
            
        Returns:
            台账记录 ID，失败返回 None
        """
        try:
            contract_info = review_result.get('contract_info', {})
            
            # 提取合同号（从标题或原文中匹配）
            contract_no = self._extract_contract_no(contract_text, contract_info)
            
            # 提取对方主体
            counterparty = self._extract_counterparty(contract_text, contract_info)
            
            # 提取金额
            amount = self._extract_amount(contract_text, contract_info)
            
            # 提取付款节点
            payment_nodes = self._extract_payment_nodes(contract_text)
            
            # 提取日期
            start_date, end_date = self._extract_dates(contract_text)
            
            # 检查是否已存在
            existing = self.get_contract_by_no(contract_no)
            if existing:
                # 更新现有记录
                self.update_contract(
                    existing['id'],
                    title=contract_info.get('title', ''),
                    counterparty=counterparty,
                    amount=amount,
                    payment_nodes=payment_nodes,
                    start_date=start_date,
                    end_date=end_date,
                    contract_type=contract_info.get('contract_type', ''),
                )
                logger.info(f"台账已更新: {contract_no}")
                return existing['id']
            else:
                # 新建记录
                contract_id = self.add_contract(
                    contract_no=contract_no,
                    title=contract_info.get('title', '未知合同'),
                    counterparty=counterparty,
                    amount=amount,
                    payment_nodes=payment_nodes,
                    start_date=start_date,
                    end_date=end_date,
                    contract_type=contract_info.get('contract_type', ''),
                    source='auto',
                )
                logger.info(f"台账已新建: {contract_no}")
                return contract_id
                
        except Exception as e:
            logger.error(f"自动回填失败: {e}")
            return None

    def _extract_contract_no(self, text: str, info: Dict) -> str:
        """提取合同号"""
        # 常见格式：合同编号、合同号、No.
        patterns = [
            r'合同编号[：:]\s*([A-Za-z0-9\-]+)',
            r'合同号[：:]\s*([A-Za-z0-9\-]+)',
            r'No\.[：:]\s*([A-Za-z0-9\-]+)',
            r'编号[：:]\s*([A-Za-z0-9\-]+)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1)
        # 使用标题 + 日期生成
        title = info.get('title', 'unknown')
        date_str = datetime.now().strftime('%Y%m%d')
        return f"{title[:10]}_{date_str}"

    def _extract_counterparty(self, text: str, info: Dict) -> str:
        """提取对方主体"""
        # 从 parties 提取
        parties = info.get('parties', [])
        if parties:
            names = [p.get('name', '') for p in parties if p.get('name')]
            return '/'.join(names)
        
        # 从原文匹配
        patterns = [
            r'乙方[：:]\s*([^\n，,。；;]+)',
            r'买方[：:]\s*([^\n，,。；;]+)',
            r'承租方[：:]\s*([^\n，,。；;]+)',
            r'承包方[：:]\s*([^\n，,。；;]+)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return m.group(1).strip()
        return ''

    def _extract_amount(self, text: str, info: Dict) -> Optional[float]:
        """提取合同金额"""
        patterns = [
            r'合同金额[：:]\s*[¥￥]?\s*([\d,]+(?:\.\d+)?)',
            r'总价[：:]\s*[¥￥]?\s*([\d,]+(?:\.\d+)?)',
            r'总价款[：:]\s*[¥￥]?\s*([\d,]+(?:\.\d+)?)',
            r'金额[：:]\s*[¥￥]?\s*([\d,]+(?:\.\d+)?)',
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                return float(m.group(1).replace(',', ''))
        return None

    def _extract_payment_nodes(self, text: str) -> List[Dict[str, Any]]:
        """提取付款节点"""
        nodes = []
        # 匹配"X% 于 Y 支付"模式
        patterns = [
            r'(\d+)%[^\n]*?于[^\n]*?支付',
            r'预付[^\n]*?(\d+)%',
            r'首付[^\n]*?(\d+)%',
            r'尾款[^\n]*?(\d+)%',
        ]
        for p in patterns:
            for m in re.finditer(p, text):
                nodes.append({
                    'percent': int(m.group(1)),
                    'description': m.group(0)[:50],
                })
        return nodes

    def _extract_dates(self, text: str) -> tuple:
        """提取开始和结束日期"""
        date_pattern = r'(\d{4})[年\-/](\d{1,2})[月\-/](\d{1,2})'
        dates = re.findall(date_pattern, text)
        
        if len(dates) >= 2:
            start = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}"
            end = f"{dates[1][0]}-{dates[1][1].zfill(2)}-{dates[1][2].zfill(2)}"
            return start, end
        elif len(dates) == 1:
            date_str = f"{dates[0][0]}-{dates[0][1].zfill(2)}-{dates[0][2].zfill(2)}"
            return date_str, None
        
        return None, None

    # ---------- CRUD ----------
    def add_contract(
        self,
        contract_no: str,
        title: str,
        counterparty: str = '',
        amount: Optional[float] = None,
        payment_nodes: Optional[List[Dict]] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        contract_type: str = '',
        source: str = 'manual',
    ) -> int:
        """添加合同到台账"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                INSERT INTO contracts 
                (contract_no, title, counterparty, amount, payment_nodes, 
                 start_date, end_date, contract_type, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contract_no,
                    title,
                    counterparty,
                    amount,
                    json.dumps(payment_nodes, ensure_ascii=False) if payment_nodes else None,
                    start_date,
                    end_date,
                    contract_type,
                    source,
                ),
            )
            conn.commit()
            return cursor.lastrowid

    def update_contract(self, contract_id: int, **kwargs) -> bool:
        """更新合同信息"""
        allowed_fields = {
            'title', 'counterparty', 'amount', 'payment_nodes',
            'start_date', 'end_date', 'status', 'contract_type',
        }
        updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
        if not updates:
            return False
        
        set_clause = ', '.join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values())
        values.append(contract_id)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE contracts SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                values,
            )
            conn.commit()
            return True

    def get_contract_by_no(self, contract_no: str) -> Optional[Dict]:
        """按合同号查询"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM contracts WHERE contract_no = ?",
                (contract_no,),
            ).fetchone()
            return dict(row) if row else None

    def list_contracts(
        self,
        status: Optional[str] = None,
        counterparty: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict]:
        """列出合同"""
        query = "SELECT * FROM contracts WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = ?"
            params.append(status)
        if counterparty:
            query += " AND counterparty LIKE ?"
            params.append(f"%{counterparty}%")
        
        query += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]

    def delete_contract(self, contract_id: int) -> bool:
        """删除合同"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM reminders WHERE contract_id = ?", (contract_id,))
            conn.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
            conn.commit()
            return True

    # ---------- 提醒引擎 ----------
    def generate_reminders(self, days_before: List[int] = None) -> List[Dict]:
        """
        生成到期提醒清单
        
        Args:
            days_before: 提前提醒天数，默认 [30, 7, 1]
            
        Returns:
            待办清单列表
        """
        if days_before is None:
            days_before = [30, 7, 1]
        
        reminders = []
        today = datetime.now().date()
        
        contracts = self.list_contracts(status='active')
        
        for contract in contracts:
            end_date_str = contract.get('end_date')
            if not end_date_str:
                continue
            
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                continue
            
            days_until = (end_date - today).days
            
            for days in days_before:
                if days_until == days:
                    reminders.append({
                        'contract_id': contract['id'],
                        'contract_no': contract['contract_no'],
                        'title': contract['title'],
                        'counterparty': contract['counterparty'],
                        'end_date': end_date_str,
                        'days_until': days_until,
                        'amount': contract['amount'],
                        'type': 'expiry',
                    })
                    break
        
        return reminders

    def register_schtasks_reminder(self) -> bool:
        """
        注册 Windows 计划任务，每日扫描到期提醒
        
        安全增强（v5.2.1）：
        - 打印任务名称、触发时间与影响范围
        - 取得用户确认后再执行注册
        - 不再自动调用，仅作为独立显式命令
        """
        try:
            script_path = Path(__file__).resolve()
            python_path = sys.executable
            task_name = "ContractReviewReminder"
            
            # 打印任务详情，取得用户确认
            print("\n" + "=" * 60)
            print("计划任务注册确认")
            print("=" * 60)
            print(f"任务名称：{task_name}")
            print(f"触发时间：每日 09:00")
            print(f"执行命令：{python_path} {script_path} --scan-reminders")
            print(f"影响范围：每日扫描到期合同，生成待办清单")
            print(f"持久化：任务注册后持续执行，直到手动删除")
            print("=" * 60)
            
            confirm = input("确认注册此计划任务？(yes/no): ").strip().lower()
            if confirm not in ('yes', 'y'):
                print("已取消注册")
                return False
            
            # 创建计划任务 XML
            task_xml = f"""<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-01T09:00:00</StartBoundary>
      <Enabled>true</Enabled>
      <ScheduleByDay>
        <DaysInterval>1</DaysInterval>
      </ScheduleByDay>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>{python_path}</Command>
      <Arguments>{script_path} --scan-reminders</Arguments>
    </Exec>
  </Actions>
  <Settings>
    <MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>
    <DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>
    <StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>
    <ExecutionTimeLimit>PT1H</ExecutionTimeLimit>
  </Settings>
</Task>"""
            
            # 保存 XML 文件
            xml_path = Path.home() / '.contract-review' / 'reminder_task.xml'
            xml_path.parent.mkdir(parents=True, exist_ok=True)
            with open(xml_path, 'w', encoding='utf-16') as f:
                f.write(task_xml)
            
            # 注册任务（需要管理员权限）
            result = subprocess.run(
                ['schtasks', '/Create', '/TN', task_name, '/XML', str(xml_path), '/F'],
                capture_output=True,
                text=True,
            )
            
            if result.returncode == 0:
                logger.info("计划任务注册成功")
                return True
            else:
                logger.warning(f"计划任务注册失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"注册计划任务失败: {e}")
            return False

    def send_wecom_webhook(self, message: str, webhook_url: str) -> bool:
        """
        发送企微 webhook 推送
        
        Args:
            message: 消息内容（Markdown 格式）
            webhook_url: 企微 webhook URL
            
        Returns:
            是否发送成功
        """
        try:
            import urllib.request
            
            payload = json.dumps({
                'msgtype': 'markdown',
                'markdown': {
                    'content': message,
                },
            }).encode('utf-8')
            
            req = urllib.request.Request(
                webhook_url,
                data=payload,
                headers={'Content-Type': 'application/json'},
            )
            
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if result.get('errcode') == 0:
                    logger.info("企微推送成功")
                    return True
                else:
                    logger.warning(f"企微推送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"企微推送失败: {e}")
            return False

    def get_config(self) -> Dict:
        """获取配置"""
        if CONFIG_PATH.exists():
            with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {'webhook_url': '', 'remind_days': [30, 7, 1]}

    def save_config(self, config: Dict):
        """保存配置"""
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)


# ---------- 便捷函数 ----------
_default_ledger: Optional[ContractLedger] = None


def get_ledger() -> ContractLedger:
    """获取全局单例"""
    global _default_ledger
    if _default_ledger is None:
        _default_ledger = ContractLedger()
    return _default_ledger


def scan_and_notify():
    """扫描到期提醒并推送（供计划任务调用）"""
    ledger = get_ledger()
    config = ledger.get_config()
    
    reminders = ledger.generate_reminders(config.get('remind_days', [30, 7, 1]))
    
    if not reminders:
        return
    
    # 生成待办清单
    lines = ["## 📋 合同到期提醒\n"]
    for r in reminders:
        lines.append(f"- **{r['title']}**（{r['contract_no']}）")
        lines.append(f"  对方：{r['counterparty']} | 到期：{r['end_date']} | 还有 {r['days_until']} 天")
        if r['amount']:
            lines.append(f"  金额：¥{r['amount']:,.2f}")
        lines.append("")
    
    message = "\n".join(lines)
    
    # 输出到控制台
    print(message)
    
    # 推送企微
    webhook_url = config.get('webhook_url', '')
    if webhook_url:
        ledger.send_wecom_webhook(message, webhook_url)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='合同台账与履约提醒 v5.2')
    subparsers = parser.add_subparsers(dest='command', help='子命令')
    
    # list 子命令
    list_parser = subparsers.add_parser('list', help='列出台账')
    list_parser.add_argument('--status', help='按状态过滤')
    list_parser.add_argument('--counterparty', help='按对方主体过滤')
    
    # add 子命令
    add_parser = subparsers.add_parser('add', help='手工添加合同')
    add_parser.add_argument('--no', required=True, help='合同号')
    add_parser.add_argument('--title', required=True, help='合同标题')
    add_parser.add_argument('--counterparty', help='对方主体')
    add_parser.add_argument('--amount', type=float, help='金额')
    add_parser.add_argument('--end-date', help='到期日 (YYYY-MM-DD)')
    
    # scan 子命令
    subparsers.add_parser('scan', help='扫描到期提醒')
    
    # register 子命令
    subparsers.add_parser('register', help='注册计划任务')
    
    # config 子命令
    config_parser = subparsers.add_parser('config', help='配置')
    config_parser.add_argument('--webhook', help='企微 webhook URL')
    config_parser.add_argument('--remind-days', help='提醒天数，逗号分隔')
    
    args = parser.parse_args()
    ledger = get_ledger()
    
    if args.command == 'list':
        contracts = ledger.list_contracts(
            status=args.status,
            counterparty=args.counterparty,
        )
        if not contracts:
            print("台账为空")
        else:
            print(f"{'=' * 60}")
            print(f"📋 合同台账 ({len(contracts)} 条)")
            print(f"{'=' * 60}")
            for c in contracts:
                print(f"\n  📄 {c['title']}")
                print(f"     合同号: {c['contract_no']}")
                print(f"     对方: {c['counterparty']}")
                print(f"     金额: {c['amount']}")
                print(f"     到期: {c['end_date']}")
                print(f"     状态: {c['status']}")
    
    elif args.command == 'add':
        contract_id = ledger.add_contract(
            contract_no=args.no,
            title=args.title,
            counterparty=args.counterparty or '',
            amount=args.amount,
            end_date=args.end_date,
            source='manual',
        )
        print(f"✅ 已添加，ID: {contract_id}")
    
    elif args.command == 'scan':
        scan_and_notify()
    
    elif args.command == 'register':
        if ledger.register_schtasks_reminder():
            print("✅ 计划任务注册成功")
        else:
            print("❌ 计划任务注册失败（可能需要管理员权限）")
    
    elif args.command == 'config':
        config = ledger.get_config()
        if args.webhook:
            config['webhook_url'] = args.webhook
        if args.remind_days:
            config['remind_days'] = [int(d) for d in args.remind_days.split(',')]
        ledger.save_config(config)
        print("✅ 配置已保存")
    
    else:
        parser.print_help()
