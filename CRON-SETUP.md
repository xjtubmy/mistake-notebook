# 智能提醒配置说明

## 📅 定时任务设置

### 方式一：Crontab（推荐）

#### 1. 编辑 crontab

```bash
crontab -e
```

#### 2. 添加定时任务

**每天 18:00 自动提醒**：

```bash
0 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1
```

**自定义时间**：

```bash
# 每天早上 8:00
0 8 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1

# 每天晚上 20:00
0 20 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1
```

#### 3. 验证 crontab

```bash
# 查看已配置的定时任务
crontab -l

# 查看日志
tail -f /tmp/review-reminder.log
```

---

### 方式二：systemd Timer（高级）

#### 1. 创建 service 文件

```bash
sudo nano /etc/systemd/system/mistake-notebook-reminder.service
```

内容：
```ini
[Unit]
Description=Mistake Notebook Daily Review Reminder
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/home/ubuntu/clawd
ExecStart=/usr/bin/python3 /home/ubuntu/clawd/skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu
```

#### 2. 创建 timer 文件

```bash
sudo nano /etc/systemd/system/mistake-notebook-reminder.timer
```

内容：
```ini
[Unit]
Description=Run Mistake Notebook Reminder Daily at 18:00

[Timer]
OnCalendar=*-*-* 18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

#### 3. 启用 timer

```bash
sudo systemctl daemon-reload
sudo systemctl enable mistake-notebook-reminder.timer
sudo systemctl start mistake-notebook-reminder.timer

# 查看状态
sudo systemctl status mistake-notebook-reminder.timer
```

---

## 📱 消息渠道配置

### 飞书 (feishu)

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel feishu
```

### 微信 (openclaw-weixin)

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel openclaw-weixin
```

---

## 🧪 测试

### 手动测试（不发送）

```bash
# 预览今日提醒
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --dry-run

# 预览指定日期的提醒
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --date 2026-04-01 \
  --dry-run
```

### 手动发送测试

```bash
# 发送到飞书
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel feishu
```

---

## 📝 消息示例

### 有复习任务时

```
📅 **复习提醒**

**学生**：曲凌松  
**日期**：2026-04-01  
**待复习**：4 道

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**📚 数学**（1 道）

• 程序运算与不等式组（第 1 轮）🟡 今日

**📚 物理**（3 道）

• 牛顿第一定律（外力消失时的运动状态）（第 1 轮）🟡 今日
• 牛顿第一定律与惯性概念（第 1 轮）🟡 今日
• 力的合成（第 1 轮）🟡 今日

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 **复习建议**

1️⃣ **盖住答案**：先独立重做题目
2️⃣ **对照解析**：核对答案，理解思路
3️⃣ **记录进度**：在复习记录表上打勾
4️⃣ **举一反三**：完成相似题练习

📊 **复习轮次说明**：
• 第 1 轮：录入后 1 天（关键复习）
• 第 2 轮：录入后 3 天
• 第 3 轮：录入后 7 天
• 第 4 轮：录入后 15 天
• 第 5 轮：录入后 30 天（永久记忆）

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⏰ 预计用时：10-15 分钟

加油！坚持就是胜利！💪
```

### 无复习任务时

```
🎉 **好消息！**

**学生**：曲凌松  
**日期**：2026-04-01

✅ 今日没有待复习的错题！

继续保持，按时复习哦！💪
```

---

## ⚙️ 高级配置

### 多学生支持

如果有多个学生，配置多个定时任务：

```bash
# 学生 1 - 每天 18:00
0 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --channel feishu >> /tmp/review-reminder.log 2>&1

# 学生 2 - 每天 18:30
30 18 * * * cd /home/ubuntu/clawd && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲小松 --channel feishu >> /tmp/review-reminder.log 2>&1
```

### 逾期提醒增强

修改脚本，对逾期错题添加特殊标记：

```python
# 已在脚本中实现
if r['days_overdue'] > 0:
    urgency = f"🔴 逾期{r['days_overdue']}天"
elif r['days_overdue'] == 0:
    urgency = "🟡 今日"
else:
    urgency = "🟢 提前"
```

---

## 🔧 故障排查

### 问题 1：收不到提醒

**检查**：
```bash
# 查看 crontab 是否配置
crontab -l

# 查看日志
tail -f /tmp/review-reminder.log

# 手动测试
python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student 曲凌松 --dry-run
```

### 问题 2：消息发送失败

**检查**：
```bash
# 检查 OpenClaw 配置
openclaw status

# 检查渠道配置
cat ~/.openclaw/credentials/feishu
```

### 问题 3：找不到错题

**检查**：
```bash
# 检查数据目录
ls -la data/mistake-notebook/students/曲凌松/mistakes/

# 检查错题元数据
cat data/mistake-notebook/students/曲凌松/mistakes/physics/.../mistake.md | grep due-date
```

---

## 📊 监控与统计

### 查看发送历史

```bash
# 查看日志
cat /tmp/review-reminder.log

# 统计发送次数
grep "✅ 复习提醒已发送" /tmp/review-reminder.log | wc -l
```

### 查看复习完成率

```bash
# 查看已完成的复习
cat data/mistake-notebook/students/曲凌松/mistakes/.../analysis.md | grep "复习记录"
```

---

**最后更新**：2026-03-31
