# Cron Setup

## Crontab

每天 18:00 自动发送复习提醒：

```bash
0 18 * * * cd /path/to/workspace && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --channel feishu >> /tmp/review-reminder.log 2>&1
```

自定义时间示例：

```bash
0 8 * * * cd /path/to/workspace && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --channel feishu >> /tmp/review-reminder.log 2>&1
0 20 * * * cd /path/to/workspace && python3 skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --channel feishu >> /tmp/review-reminder.log 2>&1
```

## systemd Timer

### Service

```ini
[Unit]
Description=Mistake Notebook Daily Review Reminder
After=network.target

[Service]
Type=oneshot
User=ubuntu
WorkingDirectory=/path/to/workspace
ExecStart=/usr/bin/python3 /path/to/workspace/skills/mistake-notebook/scripts/daily-review-reminder.py --student <学生名> --channel feishu
```

### Timer

```ini
[Unit]
Description=Run Mistake Notebook Reminder Daily at 18:00

[Timer]
OnCalendar=*-*-* 18:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

## Channels

### 飞书

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel feishu
```

### 微信

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --channel openclaw-weixin
```

## Dry Run

先预览，不发送：

```bash
python3 skills/mistake-notebook/scripts/daily-review-reminder.py \
  --student 曲凌松 \
  --dry-run
```

## Verification

```bash
crontab -l
tail -f /tmp/review-reminder.log
```

## Notes

- 当前推荐流程是“提醒 -> 用户查看文字列表 -> 用户按需请求 PDF -> 用户说复习完了”
- 如果要接飞书或微信，先确认外部渠道本身已配置完成
