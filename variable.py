# variable.py - 全局变量 for Telegram bot

# 游戏结果配置
consequence = "大"        # 预期结果（“大”或“小”）

# 开关控制
switch = True            # 总开关
open_ydx = False         # 开盘开关，默认关闭
bet = False              # 是否正在押注
bet_on = False           # 是否开始押注
mark = True              # 连续标记
mode_stop = True         # 模式暂停开关

# 历史和统计数据
history = []             # 历史结果（0=小，1=大）
total = 0                # 总押注局数
win_total = 0            # 胜利局数
earnings = 0             # 总收益
win_times = 0            # 连大次数
lose_times = 0           # 连小次数
message = None           # 主统计消息
message1 = None          # 最近 1000 局统计消息
message2 = None          # 押注统计消息
message3 = None          # 最近 200 局统计消息

# 押注模式和策略
mode = 1                 # 默认模式：0=反投，1=预测，2=追投
bet_type = 0             # 押注类型（0=小，1=大）
continuous = 30          # 默认连胜/连败阈值

# 金额和倍率配置
initial_amount = 10000   # 默认初始押注金额
bet_amount = 0           # 当前押注金额
lose_stop = 2            # 默认连输停止限制
lose_once = 1.0          # 默认输一次倍率
lose_twice = 1.0         # 默认输两次倍率
lose_three = 1.0         # 默认输三次倍率
lose_four = 1.0          # 默认输四次倍率
win_count = 0            # 连赢次数
lose_count = 0           # 连输次数

# 炸停机制
explode = 1              # 默认炸停次数阈值
stop = 30                # 默认炸停暂停局数
explode_count = 0        # 当前炸停次数
stop_count = 30          # 剩余暂停局数

# 盈利控制
profit = 1000000          # 默认盈利限额，达到后结束当前轮
period_profit = 0        # 全局累计盈利

# 轮、场、统计相关变量
round_number = 1         # 当前轮编号
round_profit = 0         # 当前轮盈利
round_start_time = None  # 轮开始时间（当天0点）
game_count = 0           # 当前轮场数
bet_count_per_game = 0   # 当前场押注次数
game_profit = 0          # 当前场盈利
explode_times = 0        # 一轮被炸次数
loss_amount = 0          # 一轮损失金额
max_consecutive_loss = 0 # 最高连输次数
current_consecutive_loss = 0  # 当前连输次数

# 新增变量
current_preset = None    # 当前预设名称（如“tz”），未设置时为 None
daily_profits = {}       # 当天每轮盈利，持久化存储，格式 {1: 1000000, 2: 500000}

# 预设参数
# 格式: [continuous, lose_stop, lose_once, lose_twice, lose_three, lose_four, initial_amount]
ys = {
    "5": ["2", "3", "3", "1.5", "1", "1", "50000"],
    "25": ["2", "3", "3", "1.5", "1", "1", "250000"],
    "50": ["2", "3", "3", "1.5", "1", "1", "500000"],
    "1002": ["2", "3", "3", "1.5", "1", "1", "1000000"],
    "1003": ["3", "3", "3", "1.5", "1", "1", "1000000"],
    "1004": ["4", "3", "3", "2", "1", "1", "1000000"],
    "1005": ["5", "3", "3", "2", "1", "1", "1000000"],
    "1006": ["6", "3", "3", "2", "1", "1", "1000000"],
    "tz": ["30", "1", "1", "1", "1", "1", "1000"],
    "yc": ["30", "8", "3", "3", "2", "2", "10000"],
    "zt": ["30", "5", "3", "2", "2", "2", "10000"],
    "cs": ["30", "1", "3", "3", "2", "2", "500"]
}

# 按钮映射
small_button = {         # 押小按钮：金额到索引
    500: 14,
    2000: 12,
    20000: 10,
    50000: 8,
    250000: 6,
    1000000: 4,
    5000000: 2,
    50000000: 0
}

big_button = {           # 押大按钮：金额到索引
    500: 15,
    2000: 13,
    20000: 11,
    50000: 9,
    250000: 7,
    1000000: 5,
    5000000: 3,
    50000000: 1
}