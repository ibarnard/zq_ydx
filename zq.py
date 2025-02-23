# zq.py - Telegram 机器人核心逻辑

import asyncio
import json
import os
import random
import re
import config
import variable
from collections import defaultdict



# --------------------- 用户命令处理 ---------------------
async def zq_user(client, event):
    """处理用户输入的命令，从收藏夹接收"""
    command_parts = event.raw_text.split(" ")
    if not command_parts:
        return

    cmd = command_parts[0]

    # 显示帮助信息
    if cmd == "help":
        help_text = (
            "以下是支持的命令：\n"
            "- **st <preset_key>**：启动预设参数（如 'st tz'）\n"
            "- **res**：重置统计数据\n"
            "- **set <explode> <profit> <stop>**：设置炸停和盈利参数（如 'set 3 300000 10'）\n"
            "- **ms <mode>**：设置押注模式（0=反投, 1=预测, 2=追投，如 'ms 1'）\n"
            "- **open**：开启自动押注\n"
            "- **off**：关闭自动押注\n"
            "- **xx**：清理赢大小群消息\n"
            "- **top**：显示捐赠排行榜 Top 20\n"
            "- **ys <key> <values>**：设置预设参数（如 'ys my 30 2 1 1 1 1 20000'）\n"
            "- **yss**：查看所有预设，'yss dl <key>' 删除预设\n"
            "- **xc**：查询当天和本轮盈利\n"
            "- **test <name>**：运行测试场景（bet, zhuanzhang, notify）"
        )
        message = await client.send_message('me', help_text, parse_mode="markdown")
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 60))
        return

    # 测试场景
    if cmd == "test" and len(command_parts) > 1:
        await test_scenarios(client, event, command_parts[1])
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 60))
        return

    # 启动预设参数
    if cmd == "st":
        if len(command_parts) != 2:
            await client.send_message('me', "命令失败，格式错误：st <preset_key>")
            return
        preset_key = command_parts[1]
        if preset_key in variable.ys:
            preset = variable.ys[preset_key]
            variable.current_preset = preset_key
            variable.continuous = int(preset[0])
            variable.lose_stop = int(preset[1])
            variable.lose_once = float(preset[2])
            variable.lose_twice = float(preset[3])
            variable.lose_three = float(preset[4])
            variable.lose_four = float(preset[5])
            variable.initial_amount = int(preset[6])
            message = await client.send_message('me', f"启动预设 '{preset_key}' 成功：{preset}", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        else:
            await client.send_message('me', f"命令失败，无效预设：{preset_key}")
        return

    # 重置统计数据
    if cmd == "res":
        variable.win_total = 0
        variable.total = 0
        variable.earnings = 0
        variable.period_profit = 0
        variable.round_number = 1
        variable.round_profit = 0
        variable.game_count = 0
        variable.bet_count_per_game = 0
        variable.game_profit = 0
        variable.explode_times = 0
        variable.loss_amount = 0
        variable.max_consecutive_loss = 0
        variable.current_consecutive_loss = 0
        variable.daily_profits.clear()
        data = load_data_from_file()
        data["daily_profits"] = variable.daily_profits
        save_data_to_file(data)
        message = await client.send_message('me', "重置统计数据成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 设置炸停和盈利参数
    if cmd == "set":
        if len(command_parts) != 4:
            await client.send_message('me', "命令失败，格式错误：set <explode> <profit> <stop>")
            return
        try:
            explode = int(command_parts[1])
            profit = int(command_parts[2])
            stop = int(command_parts[3])
            if explode <= 0 or profit <= 0 or stop <= 0:
                await client.send_message('me', "命令失败，参数无效：所有值需为正整数")
                return
            variable.explode = explode
            variable.profit = profit
            variable.stop = stop
            variable.stop_count = stop
            message = await client.send_message('me', f"设置炸停 {explode}、盈利限额 {profit}、暂停 {stop} 成功", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        except ValueError:
            await client.send_message('me', "命令失败，参数无效：需为整数")
        return

    # 设置押注模式
    if cmd == "ms":
        if len(command_parts) != 2:
            await client.send_message('me', "命令失败，格式错误：ms <mode>")
            return
        try:
            mode = int(command_parts[1])
            if mode not in [0, 1, 2]:
                await client.send_message('me', f"命令失败，参数无效：模式 {mode}，范围：0-2")
                return
            variable.mode = mode
            mode_names = {0: "反投模式", 1: "预测模式", 2: "追投模式"}
            message = await client.send_message('me', f"切换{mode_names[mode]}成功", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        except ValueError:
            await client.send_message('me', "命令失败，参数无效：模式需为整数")
        return

    # 开启自动押注
    if cmd == "open":
        if len(command_parts) != 1:
            await client.send_message('me', "命令失败，格式错误：open 无需参数")
            return
        variable.open_ydx = True
        try:
            await client.send_message(config.zq_group, '/ydx')  # 发送到朱雀菠菜群
            message = await client.send_message('me', "开启自动押注成功", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        except Exception as e:
            message = await client.send_message('me', f"开启自动押注失败：{str(e)}", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 关闭自动押注
    if cmd == "off":
        if len(command_parts) != 1:
            await client.send_message('me', "命令失败，格式错误：off 无需参数")
            return
        variable.open_ydx = False
        message = await client.send_message('me', "关闭自动押注成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 清理赢大小群消息
    if cmd == "xx":
        if len(command_parts) != 1:
            await client.send_message('me', "命令失败，格式错误：xx 无需参数")
            return
        try:
            messages = [msg.id async for msg in client.iter_messages(config.zq_group, from_user='me')]
            if messages:
                await client.delete_messages(config.zq_group, messages)
                message = await client.send_message('me', "清理赢大小群消息成功", parse_mode="markdown")
                asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
            else:
                message = await client.send_message('me', "赢大小群无消息可清理", parse_mode="markdown")
                asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        except Exception as e:
            message = await client.send_message('me', f"清理赢大小群消息失败：{str(e)}", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 3))
        return

    # 显示捐赠排行榜
    if cmd == "top":
        data = load_data_from_file()
        bot_data = data.get(str(config.zq_bot), [])
        sorted_data = sorted(bot_data, key=lambda x: x['amount'], reverse=True)
        donation_text = f"```当前{config.name}个人总榜Top: 20 为\n"
        for i, item in enumerate(sorted_data[:20], start=1):
            donation_text += (
                f"     总榜Top {i}: {item['name']} 大佬共赏赐小弟: {item['count']} 次,"
                f"共计: {format_number(int(item['amount']))} 爱心\n"
                f"     {config.name} 共赏赐 {item['name']} 小弟： {item['-count']} 次,"
                f"共计： {format_number(int(item['-amount']))} 爱心\n"
            )
        donation_text += "```"
        message = await client.send_message('me', donation_text)
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 60))
        return

    # 设置预设参数
    if cmd == "ys":
        if len(command_parts) != 9:
            await client.send_message('me', "命令失败，格式错误：ys <key> <continuous> <lose_stop> <lose_once> <lose_twice> <lose_three> <lose_four> <initial_amount>")
            return
        try:
            preset_key = command_parts[1]
            preset_values = [
                int(command_parts[2]),   # continuous
                int(command_parts[3]),   # lose_stop
                float(command_parts[4]), # lose_once
                float(command_parts[5]), # lose_twice
                float(command_parts[6]), # lose_three
                float(command_parts[7]), # lose_four
                int(command_parts[8])    # initial_amount
            ]
            if preset_values[0] <= 0 or preset_values[1] <= 0 or preset_values[2] <= 0 or preset_values[6] <= 0:
                await client.send_message('me', "命令失败，参数无效：continuous, lose_stop, lose_once, initial_amount 需为正数")
                return
            variable.ys[preset_key] = preset_values
            message = await client.send_message('me', f"设置‘{preset_key}’预设 {preset_values} 成功", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        except ValueError:
            await client.send_message('me', "命令失败，参数无效：需为数值")
        return

    # 查看或删除预设
    if cmd == "yss":
        if len(command_parts) > 2 and command_parts[1] == "dl":
            if len(command_parts) != 3:
                await client.send_message('me', "格式错误：yss dl <key>")
                return
            key = command_parts[2]
            if key in variable.ys:
                del variable.ys[key]
                message = await client.send_message('me', f"删除预设 '{key}' 成功", parse_mode="markdown")
                asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
            else:
                await client.send_message('me', f"删除预设失败，无效预设：{key}")
        elif len(command_parts) == 1:
            if variable.ys:
                max_key_length = max(len(str(k)) for k in variable.ys.keys())
                preset_text = "\n".join(f"'{k.ljust(max_key_length)}': {v}" for k, v in variable.ys.items())
                message = await client.send_message('me', preset_text, parse_mode="markdown")
                asyncio.create_task(delete_later(client, message.chat_id, message.id, 60))
            else:
                message = await client.send_message('me', "暂无预设", parse_mode="markdown")
                asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        else:
            await client.send_message('me', "格式错误：yss 或 yss dl <key>")
        return

    # 查询盈利
    if cmd == "xc":
        if len(command_parts) != 1:
            await client.send_message('me', "命令失败，格式错误：xc 无需参数")
            return
        if not variable.daily_profits:
            await client.send_message('me', "你今天赌没赌，你心里没数吗？", parse_mode="markdown")
        else:
            msg = "查询盈利情况：\n💰 **当天盈利：**\n"
            for round_num, profit in variable.daily_profits.items():
                msg += f"- **{variable.round_start_time.strftime('%m月%d日')}的第{round_num}轮：** {format_number(profit)}\n"
            total_daily = sum(variable.daily_profits.values())
            msg += f"- **当天总盈利：** {format_number(total_daily)}\n"
            msg += f"📊 **本轮盈利（第{variable.round_number}轮）：** {format_number(variable.round_profit)}"
            await client.send_message('me', msg, parse_mode="markdown")
        return

# --------------------- 测试场景处理 ---------------------
async def test_scenarios(client, event, test_name):
    """处理测试场景，发送到收藏夹"""
    if test_name == "zhuanzhang":
        # 测试自己转账给别人
        test_data = {"5697370563": [{"id": 123, "-count": 3, "-amount": 3000}]}
        self_text = config.DONATION_TEMPLATES["self_to_others"].format(
            count=test_data["5697370563"][0]['-count'],
            amount=format_number(test_data["5697370563"][0]['-amount'])
        )
        await client.send_message('me', "测试自己转账话术：\n" + self_text)

        # 测试收到他人转账
        bot_data = [
            {"id": 111, "name": "User1", "count": 10, "amount": 10000, "-count": 0, "-amount": 0},
            {"id": 123, "name": "TestUser", "count": 5, "amount": 5000, "-count": 2, "-amount": 2000},
            {"id": 222, "name": "User2", "count": 3, "amount": 3000, "-count": 0, "-amount": 0},
        ]
        test_amount = 5000
        test_rank = 2
        donation_text = config.DONATION_TEMPLATES["other_to_self_head"].format(
            user_name="TestUser", single_amount=format_number(test_amount), count=5,
            total_amount=format_number(5000), name=config.name, rank=test_rank
        )
        for i, item in enumerate(bot_data[:5], 1):
            donation_text += config.DONATION_TEMPLATES["other_to_self_rank_item"].format(
                rank=i, name=item["name"], count=item["count"], amount=format_number(int(item["amount"]))
            )
        donation_text += config.DONATION_TEMPLATES["other_to_self_tail"].format(
            threshold=format_number(config.top), self_count=2, self_amount=format_number(2000)
        )
        await client.send_message('me', "测试收到他人转账话术：\n" + donation_text)

    elif test_name == "bet":
        # 测试单次押注通知
        await client.send_message('me', "⚡ 押注：押大\n💵 金额：20000")
        await client.send_message('me', "第1轮第0场第1次：赢 19,800元，当前连输0次")
        await client.send_message('me', "📉 输赢统计：赢 19,800\n🎲 结果：大")
        await client.send_message('me', "测试押注通知：模拟单次赢19800元")

    elif test_name == "notify":
        # 测试所有通知场景
        await client.send_message('me', "⚡ 押注：押大\n💵 金额：20000")
        await client.send_message('me', "第1轮第0场第1次：赢 19,800元，当前连输0次")
        await client.send_message('me', "📉 输赢统计：赢 19,800\n🎲 结果：大")
        await send_notification(client, "game_end", 'me',
            round_start_time=variable.round_start_time,
            round_number=1, game_count=0, bet_count_per_game=2,
            game_profit=1980, consecutive_loss=0
        )
        await send_notification(client, "explode", 'me',
            round_start_time=variable.round_start_time,
            round_number=1, game_count=1, game_profit=-5000,
            round_profit=-2000, stop=30
        )
        await send_notification(client, "round_end", 'me',
            round_start_time=variable.round_start_time,
            round_number=1, game_count=12, round_profit=1000000,
            total=50, explode_times=3, loss_amount=15000,
            max_consecutive_loss=5
        )
        await client.send_message('me', "测试通知：模拟单次、场结束、被炸、轮结束通知")

    else:
        await client.send_message('me', f"未知测试场景：{test_name}，支持：zhuanzhang, bet, notify")

# --------------------- 押注相关 ---------------------
async def zq_bet_on(client, event):
    """处理押注逻辑，决定是否押注及金额"""
    await asyncio.sleep(5)  # 延迟模拟处理
    if not (variable.bet_on or (variable.mode and variable.mode_stop) or (variable.mode == 2 and variable.mode_stop)):
        variable.bet = False
        return

    if not event.reply_markup:
        return

    # 记录场内押注次数
    variable.bet_count_per_game += 1

    # 预测和计算押注
    check = (
        predict_next_combined_trend(variable.history) if variable.mode == 1 else
        predict_next_trend(variable.history) if variable.mode == 0 else
        chase_next_trend(variable.history)
    )
    variable.bet_amount = calculate_bet_amount(
        variable.win_count, variable.lose_count, variable.initial_amount,
        variable.lose_stop, variable.lose_once, variable.lose_twice,
        variable.lose_three, variable.lose_four
    )
    combination = find_combination(variable.bet_amount)

    # 执行押注并发送通知
    if combination:
        variable.bet = True
        await client.send_message('me', f"⚡ 押注：{'押大' if check else '押小'}\n💵 金额：{format_number(variable.bet_amount)}", parse_mode="markdown")
        await bet(check, combination, event)
    else:
        if variable.mark:
            variable.explode_count += 1
            variable.explode_times += 1
            variable.mark = False
        variable.bet = False

def predict_next_combined_trend(history):
    """结合长短期趋势预测下一次结果"""
    if len(history) < 10:
        return random.choice([0, 1])
    short_term = sum(history[-3:])
    long_term = sum(history[-10:])
    if len(history) < 1000:
        if short_term >= 2 and long_term >= 6:
            return 1
        elif short_term <= 1 and long_term <= 4:
            return 0
        return random.choice([0, 1])
    term = sum(history[-1000:]) / 40
    if short_term >= 2 and long_term >= 6:
        return 0 if term >= 0.55 else 1
    elif short_term <= 1 and long_term <= 4:
        return 1 if term <= 0.45 else 0
    return random.choice([0, 1])

def chase_next_trend(history):
    """追投策略：根据上一次结果押注"""
    return random.choice([0, 1]) if not history else (1 if history[-1] else 0)

def predict_next_trend(history):
    """反投策略：与上一次结果相反"""
    return random.choice([0, 1]) if not history else (0 if history[-1] else 1)

def calculate_bet_amount(win_count, lose_count, initial_amount, lose_stop, lose_once, lose_twice, lose_three, lose_four):
    """计算押注金额，含微调优化"""
    if win_count >= 0 and lose_count == 0:
        return closest_multiple_of_500(initial_amount)
    if (lose_count + 1) > lose_stop:
        return 0
    multipliers = [lose_once, lose_twice, lose_three, lose_four]
    current_multiplier = multipliers[min(lose_count - 1, 3)]
    return closest_multiple_of_500(variable.bet_amount * current_multiplier * 1.01)

def find_combination(target):
    """将目标金额分解为按钮组合"""
    numbers = [500, 2000, 20000, 50000, 250000, 1000000, 5000000, 50000000]
    numbers.sort(reverse=True)
    combination = []
    remaining = target
    for num in numbers:
        while remaining >= num:
            combination.append(num)
            remaining -= num
    return combination if remaining == 0 else None

def closest_multiple_of_500(n):
    """取最接近的500倍数"""
    return round(n / 500) * 500

async def bet(check, combination, event):
    """执行押注操作"""
    variable.total += 1
    buttons = variable.big_button if check else variable.small_button
    for amount in combination:
        await event.click(buttons[amount])
        await asyncio.sleep(1.5)
    variable.bet_type = 1 if check else 0

# --------------------- 结算相关 ---------------------
async def zq_settle(client, event):
    """处理结算逻辑并更新统计"""
    if not event.pattern_match:
        return

    # 提取结果
    result_value = event.pattern_match.group(1)
    result_text = event.pattern_match.group(2)
    if variable.open_ydx:
        try:
            await client.send_message(config.zq_group, '/ydx')  # 发送到朱雀菠菜群
        except Exception as e:
            await client.send_message('me', f"发送 '/ydx' 失败：{str(e)}", parse_mode="markdown")

    # 更新历史
    if len(variable.history) >= 1000:
        variable.history.pop(0)  # 移除最早记录
    is_win = result_text == variable.consequence
    variable.history.append(1 if is_win else 0)
    variable.win_times = variable.win_times + 1 if is_win else 0
    variable.lose_times = variable.lose_times + 1 if not is_win else 0
    whether_bet_on(variable.win_times, variable.lose_times)

    # 计算胜负并发送通知
    if variable.bet:
        if is_win:
            variable.win_total += 1
            win_amount = int(variable.bet_amount * 0.99)
            variable.earnings += win_amount
            variable.period_profit += win_amount
            variable.round_profit += win_amount
            variable.game_profit += win_amount
            variable.win_count += 1
            variable.lose_count = 0
            variable.current_consecutive_loss = 0
        else:
            loss = variable.bet_amount
            variable.earnings -= loss
            variable.period_profit -= loss
            variable.round_profit -= loss
            variable.game_profit -= loss
            variable.win_count = 0
            variable.lose_count += 1
            variable.current_consecutive_loss += 1
            variable.loss_amount += loss
            variable.max_consecutive_loss = max(
                variable.max_consecutive_loss, variable.current_consecutive_loss
            )

        # 发送单次下注通知（新旧格式分别发送）
        amount = win_amount if is_win else loss
        await client.send_message('me', (
            f"第{variable.round_number}轮第{variable.game_count}场第{variable.bet_count_per_game}次："
            f"{'赢' if is_win else '输'} {format_number(amount)}元，当前连输{variable.current_consecutive_loss}次"
        ), parse_mode="markdown")
        await client.send_message('me', (
            f"📉 输赢统计：{'赢' if is_win else '输'} {format_number(amount)}\n"
            f"🎲 结果：{result_text}"
        ), parse_mode="markdown")

        # 发送盈利情况通知
        win_rate = (variable.win_total / variable.total * 100) if variable.total > 0 else 0
        await client.send_message('me', (
            f"🎯 押注次数：{variable.total}\n"
            f"🏆 胜率：{win_rate:.2f}%\n"
            f"💰 收益：{format_number(variable.earnings)}"
        ), parse_mode="markdown")

    # 场结束判断
    game_ended = False
    if is_win and variable.bet:
        game_ended = True
        await send_notification(client, "game_end", 'me',
            round_start_time=variable.round_start_time,
            round_number=variable.round_number,
            game_count=variable.game_count,
            bet_count_per_game=variable.bet_count_per_game,
            game_profit=variable.game_profit,
            consecutive_loss=variable.current_consecutive_loss
        )
    elif variable.explode_count >= variable.explode:
        game_ended = True
        await send_notification(client, "explode", 'me',
            round_start_time=variable.round_start_time,
            round_number=variable.round_number,
            game_count=variable.game_count,
            game_profit=variable.game_profit,
            round_profit=variable.round_profit,
            stop=variable.stop
        )
    elif variable.current_consecutive_loss >= variable.lose_stop or variable.current_consecutive_loss >= variable.continuous:
        game_ended = True
        await send_notification(client, "game_end", 'me',
            round_start_time=variable.round_start_time,
            round_number=variable.round_number,
            game_count=variable.game_count,
            bet_count_per_game=variable.bet_count_per_game,
            game_profit=variable.game_profit,
            consecutive_loss=variable.current_consecutive_loss
        )

    if game_ended:
        variable.game_count += 1
        variable.bet_count_per_game = 0
        variable.game_profit = 0
        variable.bet = False

    # 暂停逻辑（仅被炸触发）
    if variable.explode_count >= variable.explode:
        if variable.stop_count > 1:
            variable.stop_count -= 1
            variable.bet_on = False
            variable.mode_stop = False
        else:
            variable.explode_count = 0
            variable.stop_count = variable.stop
            variable.bet_on = True
            variable.mode_stop = True
            variable.mark = True

    # 轮结束判断
    if variable.round_profit >= variable.profit:
        variable.daily_profits[variable.round_number] = variable.round_profit
        data = load_data_from_file()
        data["daily_profits"] = variable.daily_profits
        save_data_to_file(data)
        await send_notification(client, "round_end", 'me',
            round_start_time=variable.round_start_time,
            round_number=variable.round_number,
            game_count=variable.game_count,
            round_profit=variable.round_profit,
            total=variable.total,
            explode_times=variable.explode_times,
            loss_amount=variable.loss_amount,
            max_consecutive_loss=variable.max_consecutive_loss
        )
        # 重置轮相关变量
        variable.round_number += 1
        variable.round_profit = 0
        variable.game_count = 0
        variable.bet_count_per_game = 0
        variable.game_profit = 0
        variable.explode_times = 0
        variable.loss_amount = 0
        variable.max_consecutive_loss = 0
        variable.current_consecutive_loss = 0

    # 更新统计消息
    if variable.message:
        await variable.message.delete()
    await update_stat_messages(client)

async def update_stat_messages(client):
    """更新并发送策略统计消息到收藏夹"""
    if len(variable.history) > 3 and len(variable.history) % 5 == 0:
        for msg in [variable.message1, variable.message3]:
            if msg:
                await msg.delete()
        result_counts = count_consecutive(variable.history)
        msg1_text = (
            f"📊 **最近 1000 局：**\n"
            f"🔴 **连“小”结果：**\n{format_counts(result_counts['小'], '小')}\n"
            f"🟢 **连“大”结果：**\n{format_counts(result_counts['大'], '大')}"
        )
        variable.message1 = await client.send_message('me', msg1_text, parse_mode="markdown")

        result_counts = count_consecutive(variable.history[-200:])
        msg3_text = (
            f"📊 **最近 200 局：**\n"
            f"🔴 **连“小”结果：**\n{format_counts(result_counts['小'], '小')}\n"
            f"🟢 **连“大”结果：**\n{format_counts(result_counts['大'], '大')}"
        )
        variable.message3 = await client.send_message('me', msg3_text, parse_mode="markdown")

    reversed_data = ["✅" if x == 1 else "❌" for x in variable.history[-40:][::-1]]
    preset_name = variable.current_preset if variable.current_preset else "自定义"
    preset_values = variable.ys.get(variable.current_preset, [variable.continuous, variable.lose_stop, variable.lose_once, variable.lose_twice, variable.lose_three, variable.lose_four, variable.initial_amount])
    mode_names = {0: "反投模式", 1: "预测模式", 2: "追投模式"}
    msg_text = (
        f"📊 **近期 40 次结果**（由近及远）\n✅：大（1）  ❌：小（0）\n"
        f"{os.linesep.join(' '.join(reversed_data[i:i + 10]) for i in range(0, len(reversed_data), 10))}\n\n"
        f"———————————————\n"
        f"🎯 **策略设定**\n"
        f"💡 **当前模式**: {mode_names.get(variable.mode, '未知')}\n"
        f"📋 **参数**: {preset_name} {preset_values}\n"
        f"💰 **首注金额**: {format_number(variable.initial_amount)}\n"
        f"🔄 **几连反压**: {variable.continuous} 连\n"
        f"🎲 **反压押注**: 连续 {variable.lose_stop} 次停止\n"
        f"💥 **炸停**: 炸 {variable.explode} 次,暂停 {variable.stop} 局\n"
        f"📉 **押注倍率**: {variable.lose_once} / {variable.lose_twice} / {variable.lose_three} / {variable.lose_four}\n"
        f"💰 **盈利限额**: {format_number(variable.profit)}\n"
        f"📊 **本轮盈利**: {format_number(variable.round_profit)}"
    )
    variable.message = await client.send_message('me', msg_text, parse_mode="markdown")

# --------------------- 通知函数 ---------------------
async def send_notification(client, type, target, **kwargs):
    """统一处理通知消息，所有金额加千位分隔符，发送到收藏夹"""
    if type == "game_end":
        month_day = kwargs['round_start_time'].strftime('%m月%d日')
        msg = (f"{month_day}的第{kwargs['round_number']}轮的第{kwargs['game_count']}场，"
               f"押注了{kwargs['bet_count_per_game']}次，盈利{format_number(kwargs['game_profit'])}元，"
               f"本场连输{kwargs['consecutive_loss']}次")
        await client.send_message(target, msg, parse_mode="markdown")
    elif type == "explode":
        month_day = kwargs['round_start_time'].strftime('%m月%d日')
        msg = (f"{month_day}的第{kwargs['round_number']}轮的第{kwargs['game_count']}场，"
               f"因为被炸了，盈利{format_number(kwargs['game_profit'])}元，"
               f"截止目前总盈利{format_number(kwargs['round_profit'])}元，暂停{kwargs['stop']}局后继续莽！")
        await client.send_message(target, msg, parse_mode="markdown")
    elif type == "round_end":
        month_day = kwargs['round_start_time'].strftime('%m月%d日')
        msg = (f"{month_day}的第{kwargs['round_number']}轮共下注{kwargs['game_count']}场，"
               f"总盈利{format_number(kwargs['round_profit'])}元，共押注{kwargs['total']}次，"
               f"其中被炸了{kwargs['explode_times']}次，损失{format_number(kwargs['loss_amount'])}元，"
               f"最高连输{kwargs['max_consecutive_loss']}次")
        await client.send_message(target, msg, parse_mode="markdown")

def whether_bet_on(win_times, lose_times):
    """判断是否开始押注"""
    threshold = variable.continuous
    if (win_times >= threshold or lose_times >= threshold) and len(variable.history) >= threshold:
        variable.bet_on = True
    else:
        variable.bet_on = False
        if variable.mode == 0:
            variable.win_count = variable.lose_count = 0

def count_consecutive(data):
    """统计历史中连续次数"""
    counts = {"大": defaultdict(int), "小": defaultdict(int)}
    if not data:
        return counts
    current_value, current_count = data[0], 1
    for i in range(1, len(data)):
        if data[i] == current_value:
            current_count += 1
        else:
            label = "大" if current_value else "小"
            counts[label][current_count] += 1
            current_value, current_count = data[i], 1
    label = "大" if current_value else "小"
    counts[label][current_count] += 1
    return counts

def format_counts(counts, label):
    """格式化连续次数输出"""
    return os.linesep.join(f"{key} 连“{label}” : {counts[key]} 次" for key in sorted(counts.keys(), reverse=True))

# --------------------- 红包处理 ---------------------
async def qz_red_packet(client, event, functions):
    """处理抢红包逻辑，监听 config.group 列表中的群组"""
    if not event.reply_markup:
        return
    print("消息包含按钮！")
    for row in event.reply_markup.rows:
        for button in row.buttons:
            if hasattr(button, 'data'):
                print(f"发现内联按钮：{button.text}, 数据：{button.data}")
            else:
                print(f"发现普通按钮：{button.text}")
            for _ in range(30):
                if event.reply_markup.rows[0].buttons[0].data:
                    await event.click(0)
                    response = await client(functions.messages.GetBotCallbackAnswerRequest(
                        peer=event.chat_id,
                        msg_id=event.id,
                        data=button.data
                    ))
                    if response.message:
                        bonus_match = re.search(r"已获得 (\d+) 灵石", response.message)
                        if bonus_match:
                            bonus = bonus_match.group(1)
                            await client.send_message('me', f"🎉 抢到红包{bonus}灵石！", parse_mode="markdown")
                            print("你成功领取了灵石！")
                            return
                        if re.search("不能重复领取", response.message):
                            await client.send_message('me', "⚠️ 抢到红包，但无法重复领取！", parse_mode="markdown")
                            print("不能重复领取的提示")
                            return
                    await asyncio.sleep(1)

# --------------------- 转账处理 ---------------------
async def zq_shoot(client, event):
    """处理转账统计并发送消息到收藏夹"""
    reply_id = event.reply_to_msg_id
    if not reply_id:
        return
    message1 = await client.get_messages(event.chat_id, ids=reply_id)
    data = load_data_from_file()
    if message1.sender_id == config.user and message1.reply_to_msg_id:
        message2 = await client.get_messages(event.chat_id, ids=message1.reply_to_msg_id)
        user_id, user_name = message2.sender.id, message2.sender.first_name
        amount = int(re.search(r"\+(\d+)", message1.raw_text).group(1))
        update_user_data(data, event.sender_id, user_id, user_name, 0, amount)
        data["daily_profits"] = variable.daily_profits
        save_data_to_file(data)
        donation_text = config.DONATION_TEMPLATES["self_to_others"].format(
            count=data[str(event.sender_id)][-1]['-count'],
            amount=format_number(data[str(event.sender_id)][-1]['-amount'])
        )
        ms = await client.send_message(event.chat_id, donation_text, reply_to=message2.id)
        await asyncio.sleep(20)
        await ms.delete()
    elif message1.reply_to_msg_id and (await client.get_messages(event.chat_id, ids=message1.reply_to_msg_id)).from_id.user_id == config.user:
        user_id, user_name = message1.sender.id, message1.sender.first_name
        amount = int(re.search(r"\+(\d+)", message1.raw_text).group(1))
        update_user_data(data, event.sender_id, user_id, user_name, amount, 0)
        data["daily_profits"] = variable.daily_profits
        save_data_to_file(data)
        await send_donation_message(client, event, data, user_id, user_name, amount)

def update_user_data(data, bot_id, user_id, user_name, amount, minus_amount):
    """更新用户转账数据"""
    bot_key = str(bot_id)
    ls = data.setdefault(bot_key, [])
    user = next((u for u in ls if u["id"] == user_id), None)
    if not user:
        user = {"id": user_id, "name": user_name, "amount": 0, "count": 0, "-amount": 0, "-count": 0}
        ls.append(user)
    user["name"] = user_name
    user["amount"] += amount
    user["-amount"] += minus_amount
    user["count"] += 1 if amount else 0
    user["-count"] += 1 if minus_amount else 0

async def send_donation_message(client, event, data, user_id, user_name, amount):
    """发送捐赠排行榜消息"""
    bot_data = data.get(str(event.sender_id), [])
    sorted_data = sorted(bot_data, key=lambda x: x['amount'], reverse=True)
    user = next(u for u in bot_data if u["id"] == user_id)
    rank = next(i for i, item in enumerate(sorted_data) if item["id"] == user_id) + 1
    donation_text = config.DONATION_TEMPLATES["other_to_self_head"].format(
        user_name=user_name,
        single_amount=format_number(amount),
        count=user['count'],
        total_amount=format_number(user['amount']),
        name=config.name,
        rank=rank
    )
    for i, item in enumerate(sorted_data[:5], 1):
        donation_text += config.DONATION_TEMPLATES["other_to_self_rank_item"].format(
            rank=i,
            name=mask_if_less(amount, config.top, item['name']),
            count=mask_if_less(amount, config.top, item['count']),
            amount=mask_if_less(amount, config.top, format_number(int(item['amount'])))
        )
    donation_text += config.DONATION_TEMPLATES["other_to_self_tail"].format(
        threshold=format_number(config.top),
        self_count=user['-count'],
        self_amount=format_number(user['-amount'])
    )
    ms = await client.send_message(event.chat_id, donation_text, reply_to=event.reply_to_msg_id)
    await asyncio.sleep(20)
    await ms.delete()

def format_number(number):
    """格式化数字带千位分隔符"""
    return f"{number:,}"

def mask_if_less(num1, num2, s):
    """若 num1 < num2，则用星号掩盖字符串"""
    return "*" * len(str(s)) if num1 < num2 else str(s)

# --------------------- 工具函数 ---------------------
async def delete_later(client, chat_id, msg_id, delay):
    """延迟删除消息"""
    await asyncio.sleep(delay)
    await client.delete_messages(chat_id, msg_id)

def save_data_to_file(data, filename="data.json"):
    """保存数据到 JSON 文件，保留转账和盈利数据"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"数据已保存到 {filename}")

def load_data_from_file(filename="data.json"):
    """从 JSON 文件加载数据，默认包含 daily_profits"""
    initial_data = {"daily_profits": {}}
    if not os.path.exists(filename):
        print(f"文件 {filename} 未找到，使用初始数据")
        return initial_data
    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
            if "daily_profits" not in loaded_data:
                loaded_data["daily_profits"] = {}
            return loaded_data if loaded_data else initial_data
    except json.JSONDecodeError:
        print(f"文件 {filename} 格式错误，使用初始数据")
        return initial_data