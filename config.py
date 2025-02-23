# config.py - Telegram bot configuration

# Telegram 客户端配置
api_id = ''
api_hash = ''
user_session = ''  # 多账号时注意文件名唯一，避免覆盖

# 群组和用户
group = [-1002262543959, -1001833464786, 'me']  # 监控群组
zq_group = [-1002262543959, -1001833464786, 'me']  # 朱雀群组
zq_bot = 5697370563  # 朱雀 bot ID
user = 5697370563  # 自己的 ID

# 转账统计
name = "R哥"
top = 200000  # 单次转账达此金额不打码

# 代理设置
proxy_enabled = False  # 是否启用代理
proxy = {
    'type': 'socks5',  # 代理类型: socks5, socks4, http
    'host': '127.0.0.1',
    'port': 1080,
    'username': '',  # 可为空
    'password': ''   # 可为空
}