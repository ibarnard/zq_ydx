# main.py - Telegram bot entry point

from telethon import TelegramClient, events, functions
import logging

import config
import zq

# 设置日志
logging.basicConfig(level=logging.INFO)
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
    chats=config.zq_group,
    pattern=r"内容: (.*)\n灵石: .*\n剩余: .*\n大善人: (.*)",
    from_users=config.zq_bot
))
async def zq_red_packet_handler(event):
    await zq.qz_red_packet(client, event, functions)


@client.on(events.NewMessage(
    chats=config.zq_group,
    pattern=r"\[近 40 次结果\]\[由近及远\]\[0 小 1 大\].*",
    from_users=config.zq_bot
))
async def zq_bet_on_handler(event):
    await zq.zq_bet_on(client, event)


@client.on(events.NewMessage(
    chats=config.zq_group,
    pattern=r"已结算: 结果为 (\d+) ([大|小])",
    from_users=config.zq_bot
))
async def zq_settle_handler(event):
    await zq.zq_settle(client, event)


@client.on(events.NewMessage(chats=config.user))
async def zq_user_handler(event):
    await zq.zq_user(client, event)


@client.on(events.NewMessage(
    chats=config.zq_group,
    pattern=r"转账成功.*",
    from_users=config.zq_bot
))
async def zq_shoot_handler(event):
    await zq.zq_shoot(client, event)


# 启动
logger.info("Connecting to Telegram...")
if config.proxy_enabled:
    logger.info(f"Using proxy: {config.proxy['type']}://{config.proxy['host']}:{config.proxy['port']}")
else:
    logger.info("No proxy configured")
client.start()
logger.info("Client started, listening for messages...")
with client:
    client.run_until_disconnected()