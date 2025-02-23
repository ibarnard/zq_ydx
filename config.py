# config.py - Telegram bot configuration

# Telegram 客户端配置
api_id = ''
api_hash = ''
user_session = ''  # 多账号时注意文件名唯一，避免覆盖

# 群组和用户
group = [ 'me']  # 监控群组，需要自行查询添加
zq_group = [  'me']  # zq群组，需要自行查询添加
zq_bot = 123  # zq 秋人bot ID
user = 1234  # 自己的 ID

# 转账统计
name = "xx"
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
