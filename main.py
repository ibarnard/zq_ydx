# main.py - Telegram bot entry point

from telethon import TelegramClient, events, functions
import logging
from datetime import datetime, time  # 用于设置当天0点

import config
import zq
import variable

# 设置日志（WARNING 级别，避免冗余 INFO 输出）
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# 配置代理
proxy = None
if config.proxy_enabled:
    proxy = (
        config.proxy['type'],
        config.proxy['host'],
        config.proxy['port'],
        config.proxy['username'] or None,
        config.proxy['password'] or None
    )

# 初始化 Telegram 客户端
client = TelegramClient(
    config.user_session,
    config.api_id,
    config.api_hash,
    proxy=proxy
)

# 事件处理器
@client.on(events.NewMessage(
    chats=config.zq_group,  # 监听单一赢大小群
    pattern=r"内容: (.*)\n灵石: .*\n剩余: .*\n大善人: (.*)",
    from_users=config.zq_bot
))
async def zq_red_packet_handler(event):
    """处理红包消息"""
    await zq.qz_red_packet(client, event, functions)

@client.on(events.NewMessage(
    chats=config.zq_group,  # 监听单一赢大小群
    pattern=r"\[近 40 次结果\]\[由近及远\]\[0 小 1 大\].*",
    from_users=config.zq_bot
))
async def zq_bet_on_handler(event):
    """处理押注开始消息"""
    await zq.zq_bet_on(client, event)

@client.on(events.NewMessage(
    chats=config.zq_group,  # 监听单一赢大小群
    pattern=r"已结算: 结果为 (\d+) ([大|小])",
    from_users=config.zq_bot
))
async def zq_settle_handler(event):
    """处理结算消息"""
    await zq.zq_settle(client, event)

@client.on(events.NewMessage(chats=config.user))
async def zq_user_handler(event):
    """处理用户命令，从收藏夹接收"""
    await zq.zq_user(client, event)

@client.on(events.NewMessage(
    chats=config.zq_group,  # 监听单一赢大小群
    pattern=r"转账成功.*",
    from_users=config.zq_bot
))
async def zq_shoot_handler(event):
    """处理转账消息"""
    await zq.zq_shoot(client, event)

# 异步启动函数
async def start_bot():
    """启动客户端"""
    logger.warning("正在启动 Telegram...")
    if config.proxy_enabled:
        logger.warning(f"正在使用代理: {config.proxy['type']}://{config.proxy['host']}:{config.proxy['port']}")
    else:
        logger.warning("未使用代理")

    # 初始化轮开始时间为当天0点
    today = datetime.now().date()
    variable.round_start_time = datetime.combine(today, time(0, 0))

    # 加载持久化数据（如 daily_profits）
    data = zq.load_data_from_file()
    variable.daily_profits = data.get("daily_profits", {})

    # 启动客户端
    await client.start()
    logger.warning("客户端已启动，正在监听指定群组消息...")

# 主程序入口
if __name__ == "__main__":
    # 运行异步启动函数
    with client:
        client.loop.run_until_complete(start_bot())
        client.run_until_disconnected()