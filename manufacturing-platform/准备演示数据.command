#!/bin/bash
cd "$(dirname "$0")"
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
echo '请先启动制造平台。本操作加入本机演示账号、设备和订单，不清空已有数据。'
if python3 scripts/seed_demo.py; then
 echo '完成。打开平台，使用上方演示账号登录。'
else
 echo '操作未完成，请确认平台已启动；详情见上方信息。'
fi
read -r -p '按回车关闭'
