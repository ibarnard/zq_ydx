# config.py - Telegram bot configuration

# Telegram 客户端配置
api_id = ''  #书记
api_hash = ''
user_session = 'shuji_session'  # 多账号启动时请确保用户认证文件名不同

# 群组和用户
group = [-100234239, -10031786, 'me']  # 监控群组
zq_group = [-100259, -1786, 'me']  # zq菠菜群组
zq_bot = 123  # zq bot ID
user = 1234  # 自己的 ID

# 转账统计
name = "书记"
top = 200000  # 单次转账达此金额不打码

# 代理设置
proxy_enabled = True  # 是否启用代理,True 为启用，False 为禁用
proxy = {
    'type': 'socks5',  # 代理类型: socks5, socks4, http
    'host': '127.0.0.1',
    'port': 7890,
    'username': '',  # 可为空
    'password': ''   # 可为空
}


# -------------------- 转账话术模板 --------------------
# 这里定义多个场景下的转账提示语句，zq_shoot函数会根据情况调用
DONATION_TEMPLATES = {
    # 1) 自己转账给别人时使用
    "self_to_others": (
        "大哥赏了你 {count} 次 一共 {amount} 爱心！\n"
        "这是我的血汗钱，别乱花哦"
    ),
    # 2) 别人转给自己时，前半部分
    "other_to_self_head": (
        "```感谢 {user_name} 大佬赏赐的: {single_amount} 爱心\n"
        "大佬您共赏赐了小弟: {count} 次,共计: {total_amount} 爱心\n"
        "您是{name}个人打赏总榜的Top: {rank}\n\n"
        "当前{name}个人总榜Top: 5 为\n"
    ),
    # 3) 排行榜每行格式
    "other_to_self_rank_item": (
        "     总榜Top {rank}: {name} 大佬共赏赐小弟: {count} 次,"
        "共计: {amount} 爱心\n"
    ),
    # 4) 别人转给自己时，末尾部分
    "other_to_self_tail": (
        "\n单次打赏>={threshold}魔力查看打赏榜，感谢大佬，并期待您的下次打赏\n"
        "小弟给大佬您共孝敬了: {self_count} 次,共计: {self_amount} 爱心\n"
        "二狗哥出品，必属精品```"
    )
}
