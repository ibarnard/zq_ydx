# zq.py - Core logic for Telegram bot

import asyncio
import json
import os
import random
import re
from collections import defaultdict

import config
import variable


async def zq_user(client, event):
    """处理用户输入的命令并执行相应操作。"""
    command_parts = event.raw_text.split(" ")
    if not command_parts:
        return

    cmd = command_parts[0]

    # 启动预设参数
    if cmd == "st" and len(command_parts) > 1:
        preset_key = command_parts[1]
        if preset_key in variable.ys:
            preset = variable.ys[preset_key]
            variable.continuous = int(preset[0])
            variable.lose_stop = int(preset[1])
            variable.lose_once = float(preset[2])
            variable.lose_twice = float(preset[3])
            variable.lose_three = float(preset[4])
            variable.lose_four = float(preset[5])
            variable.initial_amount = int(preset[6])
            message_text = f"启动\n{preset}"
            message = await client.send_message(config.user, message_text, parse_mode="markdown")
            asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 重置统计数据
    if cmd == "res":
        variable.win_total = 0
        variable.total = 0
        variable.earnings = 0
        message = await client.send_message(config.user, "重置成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 设置炸停参数
    if cmd == "set" and len(command_parts) >= 3:
        variable.explode = int(command_parts[1])
        variable.stop = int(command_parts[2])
        variable.stop_count = int(command_parts[2])
        message = await client.send_message(config.user, "设置成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 设置押注模式
    if cmd == "ms" and len(command_parts) > 1:
        variable.mode = int(command_parts[1])
        message = await client.send_message(config.user, "设置成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 开启自动押注
    if cmd == "open":
        variable.open_ydx = True
        await client.send_message(config.group, '/ydx')
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        return

    # 关闭自动押注
    if cmd == "off":
        variable.open_ydx = False
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        return

    # 清理指定群组的消息
    if cmd == "xx":
        groups = [-1002262543959, -1001833464786]
        for group_id in groups:
            messages = [msg.id async for msg in client.iter_messages(group_id, from_user='me')]
            await client.delete_messages(group_id, messages)
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
        message = await client.send_message(config.user, donation_text)
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 60))
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 60))
        return

    # 设置预设参数
    if cmd == "ys" and len(command_parts) >= 9:
        preset_key = command_parts[1]
        preset_values = [
            int(command_parts[2]), int(command_parts[3]), float(command_parts[4]),
            float(command_parts[5]), float(command_parts[6]), float(command_parts[7]),
            int(command_parts[8])
        ]
        variable.ys[preset_key] = preset_values
        message = await client.send_message(config.user, "设置成功", parse_mode="markdown")
        asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
        asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return

    # 查看或删除预设参数
    if cmd == "yss":
        if len(command_parts) > 2 and command_parts[1] == "dl":
            del variable.ys[command_parts[2]]
            message = await client.send_message(config.user, "删除成功", parse_mode="markdown")
            asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        if variable.ys:
            max_key_length = max(len(str(k)) for k in variable.ys.keys())
            preset_text = "\n".join(f"'{k.ljust(max_key_length)}': {v}" for k, v in variable.ys.items())
            message = await client.send_message(config.user, preset_text, parse_mode="markdown")
            asyncio.create_task(delete_later(client, event.chat_id, event.id, 60))
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 60))
        else:
            message = await client.send_message(config.user, "暂无预设", parse_mode="markdown")
            asyncio.create_task(delete_later(client, event.chat_id, event.id, 10))
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 10))
        return


async def zq_bet_on(client, event):
    """处理押注逻辑，决定是否押注及金额。"""
    await asyncio.sleep(5)
    if not (variable.bet_on or (variable.mode and variable.mode_stop) or (variable.mode == 2 and variable.mode_stop)):
        variable.bet = False
        return

    if not event.reply_markup:
        return

    print("开始押注！")
    check = (
        predict_next_combined_trend(variable.history) if variable.mode == 1 else
        predict_next_trend(variable.history) if variable.mode == 0 else
        chase_next_trend(variable.history)
    )
    print(f"本次押注：{check}")

    variable.bet_amount = calculate_bet_amount(
        variable.win_count, variable.lose_count, variable.initial_amount,
        variable.lose_stop, variable.lose_once, variable.lose_twice,
        variable.lose_three, variable.lose_four
    )
    combination = find_combination(variable.bet_amount)
    print(f"本次押注金额：{combination}")

    if combination:
        variable.bet = True
        await bet(check, combination, event)
        message_text = f"**⚡ 押注： {'押大' if check else '押小'}\n💵 金额： {variable.bet_amount}**"
        await client.send_message(config.user, message_text, parse_mode="markdown")
        variable.mark = True
    else:
        if variable.mark:
            variable.explode_count += 1
            print("触发停止押注")
            variable.mark = False
        variable.bet = False


def predict_next_combined_trend(history):
    """结合长短期趋势预测下一次结果。"""
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
    """追投策略：根据上一次结果决定下一次押注。"""
    return random.choice([0, 1]) if not history else (1 if history[-1] else 0)


def predict_next_trend(history):
    """反投策略：与上一次结果相反。"""
    return 0 if history and history[-1] else 1


def calculate_bet_amount(win_count, lose_count, initial_amount, lose_stop, lose_once, lose_twice, lose_three, lose_four):
    """计算押注金额。"""
    if win_count >= 0 and lose_count == 0:
        return closest_multiple_of_500(initial_amount)
    if (lose_count + 1) > lose_stop:
        return 0
    multipliers = [lose_once, lose_twice, lose_three, lose_four]
    current_multiplier = multipliers[min(lose_count - 1, 3)]
    return closest_multiple_of_500(variable.bet_amount * current_multiplier * 1.01)


def find_combination(target):
    """将目标金额分解为指定按钮值的组合。"""
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
    """返回最接近的 500 的倍数。"""
    return round(n / 500) * 500


async def bet(check, combination, event):
    """执行押注操作。"""
    variable.total += 1
    buttons = variable.big_button if check else variable.small_button
    for amount in combination:
        await event.click(buttons[amount])
        await asyncio.sleep(1.5)
    variable.bet_type = 1 if check else 0


async def zq_settle(client, event):
    """处理结算逻辑并更新统计信息。"""
    if not event.pattern_match:
        return

    result_value = event.pattern_match.group(1)
    result_text = event.pattern_match.group(2)
    print(f"{result_value} {result_text}")

    if variable.open_ydx:
        await client.send_message(config.group, '/ydx')

    # 更新历史记录
    if len(variable.history) >= 1000:
        del variable.history[:5]
    is_win = result_text == variable.consequence
    variable.history.append(1 if is_win else 0)
    variable.win_times = variable.win_times + 1 if is_win else 0
    variable.lose_times = variable.lose_times + 1 if not is_win else 0
    whether_bet_on(variable.win_times, variable.lose_times)

    # 处理炸停逻辑
    if variable.explode_count >= variable.explode:
        if variable.stop_count > 1:
            variable.stop_count -= 1
            variable.bet_on = False
            variable.mode_stop = False
            message = await client.send_message('me', f"还剩 {variable.stop_count} 局恢复押注", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 30))
        else:
            variable.explode_count = 0
            variable.stop_count = variable.stop
            variable.mode_stop = True
            variable.win_count = 0
            variable.lose_count = 0
            message = await client.send_message('me', "恢复押注", parse_mode="markdown")
            asyncio.create_task(delete_later(client, message.chat_id, message.id, 30))

    # 更新统计消息
    if variable.message:
        await variable.message.delete()
    await update_stat_messages(client)


async def update_stat_messages(client):
    """更新统计信息并发送消息。"""
    # 最近结果统计
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
        variable.message1 = await client.send_message(config.user, msg1_text, parse_mode="markdown")

        result_counts = count_consecutive(variable.history[-200:])
        msg3_text = (
            f"📊 **最近 200 局：**\n"
            f"🔴 **连“小”结果：**\n{format_counts(result_counts['小'], '小')}\n"
            f"🟢 **连“大”结果：**\n{format_counts(result_counts['大'], '大')}"
        )
        variable.message3 = await client.send_message(config.user, msg3_text, parse_mode="markdown")

    # 近期结果及策略信息
    reversed_data = ["✅" if x == 1 else "❌" for x in variable.history[-40:][::-1]]
    msg_text = (
        f"📊 **近期 40 次结果**（由近及远）\n✅：大（1）  ❌：小（0）\n"
        f"{os.linesep.join(' '.join(reversed_data[i:i + 10]) for i in range(0, len(reversed_data), 10))}\n\n"
        f"———————————————\n🎯 **策略设定**\n💰 **初始金额**：{variable.initial_amount}\n"
    )
    mode_texts = {
        0: f"🎰 **押注模式 反投**\n🔄 **{variable.continuous} 连反压**\n⏹ **押 {variable.lose_stop} 次停止**\n",
        1: f"🎰 **押注模式 预测**\n⏹ **押 {variable.lose_stop} 次停止**\n",
        2: f"🎰 **押注模式 追投**\n⏹ **押 {variable.lose_stop} 次停止**\n"
    }
    msg_text += mode_texts.get(variable.mode, "")
    msg_text += (
        f"💥 **炸 {variable.explode} 次暂停**\n🚫 **暂停 {variable.stop} 局**\n"
        f"📉 **输 1 次：倍数 {variable.lose_once}**\n📉 **输 2 次：倍数 {variable.lose_twice}**\n"
        f"📉 **输 3 次：倍数 {variable.lose_three}**\n📉 **输 4 次：倍数 {variable.lose_four}**"
    )
    variable.message = await client.send_message(config.user, msg_text, parse_mode="markdown")

    # 更新押注统计
    if variable.bet:
        await update_bet_stats(client, variable.history[-1])


async def update_bet_stats(client, last_result):
    """更新押注结果统计。"""
    is_win = (variable.bet_type == 1 and last_result == 1) or (variable.bet_type == 0 and last_result == 0)
    if is_win:
        variable.win_total += 1
        variable.earnings += int(variable.bet_amount * 0.99)
        variable.win_count += 1
        variable.lose_count = 0
    else:
        variable.earnings -= variable.bet_amount
        variable.win_count = 0
        variable.lose_count += 1

    if variable.message2:
        await variable.message2.delete()
    win_rate = variable.win_total / variable.total * 100 if variable.total > 0 else 0
    msg2_text = f"**🎯 押注次数：{variable.total}\n🏆 胜率：{win_rate:.2f}%\n💰 收益：{variable.earnings}**"
    variable.message2 = await client.send_message(config.user, msg2_text, parse_mode="markdown")

    status_text = "赢" if is_win else "输"
    amount_text = int(variable.bet_amount * 0.99) if is_win else variable.bet_amount
    await client.send_message(
        config.user,
        f"**📉 输赢统计： {status_text} {amount_text}\n🎲 结果： {variable.consequence if last_result else '小'}**",
        parse_mode="markdown"
    )


async def qz_red_packet(client, event, functions):
    """抢红包逻辑。"""
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
                            await client.send_message(config.user, f"🎉 抢到红包{bonus}灵石！")
                            print("你成功领取了灵石！")
                            return
                        if re.search("不能重复领取", response.message):
                            await client.send_message(config.user, "⚠️ 抢到红包，但是没有获取到灵石数量！")
                            print("不能重复领取的提示")
                            return
                    await asyncio.sleep(1)


def whether_bet_on(win_times, lose_times):
    """判断是否开始押注。"""
    threshold = variable.continuous
    if (win_times >= threshold or lose_times >= threshold) and len(variable.history) >= threshold:
        variable.bet_on = True
    else:
        variable.bet_on = False
        if variable.mode == 0:
            variable.win_count = variable.lose_count = 0


def count_consecutive(data):
    """统计连续出现的次数。"""
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
    """格式化连续次数统计输出。"""
    return os.linesep.join(f"{key} 连“{label}” : {counts[key]} 次" for key in sorted(counts.keys(), reverse=True))


async def zq_shoot(client, event):
    """处理转账统计逻辑。"""
    reply_id = event.reply_to_msg_id
    if not reply_id:
        return

    message1 = await client.get_messages(event.chat_id, ids=reply_id)
    data = load_data_from_file()

    # 自己转账给别人
    if message1.sender_id == config.user and message1.reply_to_msg_id:
        message2 = await client.get_messages(event.chat_id, ids=message1.reply_to_msg_id)
        user_id, user_name = message2.sender.id, message2.sender.first_name
        amount = int(re.search(r"\+(\d+)", message1.raw_text).group(1))
        update_user_data(data, event.sender_id, user_id, user_name, 0, int(amount))
        save_data_to_file(data)
        donation_text = (
            f"大哥赏了你 {data[str(event.sender_id)][-1]['-count']} 次 "
            f"一共 {format_number(data[str(event.sender_id)][-1]['-amount'])} 爱心！\n"
            f"这可是我的血汗钱，别乱花哦"
        )
        ms = await client.send_message(event.chat_id, donation_text, reply_to=message2.id)
        await asyncio.sleep(20)
        await ms.delete()

    # 收到他人转账
    elif message1.reply_to_msg_id and (await client.get_messages(event.chat_id, ids=message1.reply_to_msg_id)).from_id.user_id == config.user:
        user_id, user_name = message1.sender.id, message1.sender.first_name
        amount = int(re.search(r"\+(\d+)", message1.raw_text).group(1))
        update_user_data(data, event.sender_id, user_id, user_name, int(amount), 0)
        save_data_to_file(data)
        await send_donation_message(client, event, data, user_id, user_name, amount)


def update_user_data(data, bot_id, user_id, user_name, amount, minus_amount):
    """更新用户转账数据。"""
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
    """发送捐赠排行榜消息。"""
    bot_data = data.get(str(event.sender_id), [])
    sorted_data = sorted(bot_data, key=lambda x: x['amount'], reverse=True)
    user = next(u for u in bot_data if u["id"] == user_id)
    rank = next(i for i, item in enumerate(sorted_data) if item["id"] == user_id) + 1
    total_amount = sum(int(item['amount']) for item in bot_data)
    donation_text = (
        f"```感谢 {user_name} 大佬赏赐的: {format_number(amount)} 爱心\n"
        f"大佬您共赏赐了小弟: {user['count']} 次,共计: {format_number(user['amount'])} 爱心\n"
        f"您是{config.name}个人打赏总榜的Top: {rank}\n\n"
        f"当前{config.name}个人总榜Top: 5 为\n"
    )
    for i, item in enumerate(sorted_data[:5], 1):
        donation_text += (
            f"     总榜Top {i}: {mask_if_less(amount, config.top, item['name'])} 大佬共赏赐小弟: "
            f"{mask_if_less(amount, config.top, item['count'])} 次,"
            f"共计: {mask_if_less(amount, config.top, format_number(int(item['amount'])))} 爱心\n"
        )
    donation_text += (
        f"\n单次打赏>={format_number(config.top)}魔力查看打赏榜，感谢大佬，并期待您的下次打赏\n"
        f"小弟给大佬您共孝敬了: {user['-count']} 次,共计: {format_number(user['-amount'])} 爱心\n"
        f"二狗哥出品，必属精品```"
    )
    ms = await client.send_message(event.chat_id, donation_text, reply_to=event.reply_to_msg_id)
    await asyncio.sleep(20)
    await ms.delete()


def format_number(number):
    """格式化数字为带千位分隔符的字符串。"""
    return f"{number:,}"


def mask_if_less(num1, num2, s):
    """如果 num1 < num2，则将 s 替换为等长星号。"""
    return "*" * len(str(s)) if num1 < num2 else str(s)


async def delete_later(client, chat_id, msg_id, delay):
    """延迟删除消息。"""
    await asyncio.sleep(delay)
    await client.delete_messages(chat_id, msg_id)


def save_data_to_file(data, filename="data.json"):
    """保存数据到 JSON 文件。"""
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)
    print(f"数据已保存到 {filename}")


def load_data_from_file(filename="data.json"):
    """从 JSON 文件加载数据。"""
    initial_data = {}
    if not os.path.exists(filename):
        print(f"文件 {filename} 未找到，使用初始数据")
        return initial_data
    try:
        with open(filename, 'r') as f:
            loaded_data = json.load(f)
            return loaded_data if loaded_data else initial_data
    except json.JSONDecodeError:
        print(f"文件 {filename} 格式错误，使用初始数据")
        return initial_data