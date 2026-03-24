import html
import logging
import re
import time

import markdown
import inspect
from camel.messages.system_messages import SystemMessage
from visualizer.app import send_msg


def now():
    """获取当前时间并格式化为 YYYYMMDDHHMMSS 格式的字符串。"""
    return time.strftime("%Y%m%d%H%M%S", time.localtime())


def log_visualize(role, content=None):
    """
    将角色和内容发送到 visualizer 服务器，以便在网页上实时显示日志。
    你可以不指定 role 而只传递 content，例如 log_visualize("messages")，此时 role 默认为 "System"。
    参数 (Args):
        role: 发送消息的代理/角色 (agent)
        content: 消息的内容

    返回 (Returns): None
    """
    if not content:
        logging.info(role + "\n")
        send_msg("System", role)
        print(role + "\n")
    else:
        print(str(role) + ": " + str(content) + "\n")
        logging.info(str(role) + ": " + str(content) + "\n")
        if isinstance(content, SystemMessage):
            records_kv = []
            content.meta_dict["content"] = content.content
            for key in content.meta_dict:
                value = content.meta_dict[key]
                value = escape_string(value)
                records_kv.append([key, value])
            content = "**[SystemMessage**]\n\n" + convert_to_markdown_table(records_kv)
        else:
            role = str(role)
            content = str(content)
        send_msg(role, content)


def convert_to_markdown_table(records_kv):
    """
    将键值对记录列表转换成 Markdown 格式的表格。
    """
    # Create the Markdown table header
    header = "| Parameter | Value |\n| --- | --- |"

    # Create the Markdown table rows
    rows = [f"| **{key}** | {value} |" for (key, value) in records_kv]

    # Combine the header and rows to form the final Markdown table
    markdown_table = header + "\n" + '\n'.join(rows)

    return markdown_table


def log_arguments(func):
    """
    装饰器：记录函数调用时传入的参数并输出到日志（以 Markdown 表格的形式）。
    """
    def wrapper(*args, **kwargs):
        sig = inspect.signature(func)
        params = sig.parameters

        all_args = {}
        all_args.update({name: value for name, value in zip(params.keys(), args)})
        all_args.update(kwargs)

        records_kv = []
        for name, value in all_args.items():
            if name in ["self", "chat_env", "task_type"]:
                continue
            value = escape_string(value)
            records_kv.append([name, value])
        records = f"**[{func.__name__}]**\n\n" + convert_to_markdown_table(records_kv)
        log_visualize("System", records)

        return func(*args, **kwargs)

    return wrapper

def escape_string(value):
    """
    对字符串进行转义操作，用于清洗要显示的网页/日志内容。
    """
    value = str(value)
    value = html.unescape(value)
    value = markdown.markdown(value)
    value = re.sub(r'<[^>]*>', '', value)
    value = value.replace("\n", " ")
    return value
