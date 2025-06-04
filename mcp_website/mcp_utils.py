# -*- coding: utf-8 -*-

import json
import os
import sys
import re
from .mcp_client import SimpleMCPClient

# 设置默认编码为 UTF-8
reload(sys)
sys.setdefaultencoding('utf-8')


class MCPChatBot:
    def __init__(self):
        self.client = None

    def connect(self):
        """连接到 MCP 服务器."""
        try:
            # 获取服务器脚本路径
            server_path = os.path.join(os.path.dirname(__file__), 'mcp_server.py')

            # 创建客户端
            self.client = SimpleMCPClient('D:\\2025_06\\DjangoMCP\\venv\\Scripts\\python.exe', [server_path])

            if self.client.connect():
                return True
            return False
        except Exception as e:
            print("MCP connection failed: " + str(e))
            return False

    def get_response(self, user_message):
        """获取聊天响应."""
        if not self.client or not self.client.is_connected:
            if not self.connect():
                return self._fallback_response(user_message)

        try:
            # 列出可用工具
            tools_response = self.client.list_tools()
            available_tools = []

            if tools_response and "result" in tools_response:
                tools = tools_response["result"].get("tools", [])
                available_tools = [tool["name"] for tool in tools]

            # 根据用户消息选择合适的工具
            tool_name, arguments = self._analyze_message(user_message, available_tools)

            if tool_name:
                # 调用工具
                tool_response = self.client.call_tool(tool_name, arguments)
                if tool_response and "result" in tool_response:
                    content = tool_response["result"].get("content", [])
                    is_error = tool_response["result"].get("isError", False)
                    if content and len(content) > 0:
                        return self._format_tool_response(tool_name, content[0].get("text", ""), is_error)

            return self._fallback_response(user_message)

        except Exception as e:
            print("MCP tool call failed: " + str(e))
            import traceback
            traceback.print_exc()
            return self._fallback_response(user_message)

    def _analyze_message(self, message, available_tools):
        """分析用户消息，确定需要调用的工具."""
        message_lower = message.lower()

        # 时间查询
        if any(word in message_lower for word in ['时间', '现在', '几点', 'time', 'clock']):
            return 'get_time', {}

        # 天气预报查询 - 检查经纬度
        elif any(word in message_lower for word in ['天气', '预报', 'weather', 'forecast']):
            # 提取经纬度
            lat_lon = self._extract_coordinates(message)
            if lat_lon:
                return 'get_forecast', lat_lon
            else:
                # 如果没有提供坐标，使用默认位置（北京）
                return 'get_forecast', {'latitude': 39.9042, 'longitude': 116.4074}

        # 天气警报查询
        elif any(word in message_lower for word in ['警报', '预警', 'alert', '州']):
            # 提取州代码
            state = self._extract_state_code(message)
            if state:
                return 'get_alerts', {'state': state}
            else:
                # 默认查询加州
                return 'get_alerts', {'state': 'CA'}

        # 数学计算
        elif any(word in message_lower for word in ['计算', '算', '+', '-', '*', '/', '=', 'calculate']):
            # 提取数学表达式
            expr_match = re.search(r'[\d+\-*/().\s]+', message)
            if expr_match:
                expression = expr_match.group().strip()
                if len(expression) > 1 and any(op in expression for op in ['+', '-', '*', '/']):
                    return 'calculate', {'expression': expression}

        # 检查是否包含纯数学表达式
        elif re.search(r'^\s*[\d+\-*/().\s]+\s*$', message):
            return 'calculate', {'expression': message.strip()}

        return None, {}

    def _extract_coordinates(self, message):
        """从消息中提取经纬度坐标."""
        # 匹配类似 "39.9042,116.4074" 或 "39.9042 116.4074" 的格式
        coord_pattern = r'(-?\d+\.?\d*)[,\s]+(-?\d+\.?\d*)'
        match = re.search(coord_pattern, message)
        if match:
            try:
                lat = float(match.group(1))
                lon = float(match.group(2))
                # 简单验证经纬度范围
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return {'latitude': lat, 'longitude': lon}
            except ValueError:
                pass

        # 预定义的一些城市坐标
        city_coords = {
            u'北京': {'latitude': 39.9042, 'longitude': 116.4074},
            u'上海': {'latitude': 31.2304, 'longitude': 121.4737},
            u'广州': {'latitude': 23.1291, 'longitude': 113.2644},
            u'深圳': {'latitude': 22.3193, 'longitude': 114.1694},
            u'杭州': {'latitude': 30.2741, 'longitude': 120.1551},
            u'成都': {'latitude': 30.5728, 'longitude': 104.0668},
            '北京': {'latitude': 39.9042, 'longitude': 116.4074},
            '上海': {'latitude': 31.2304, 'longitude': 121.4737},
            '广州': {'latitude': 23.1291, 'longitude': 113.2644},
            '深圳': {'latitude': 22.3193, 'longitude': 114.1694},
            '杭州': {'latitude': 30.2741, 'longitude': 120.1551},
            '成都': {'latitude': 30.5728, 'longitude': 104.0668},
            'beijing': {'latitude': 39.9042, 'longitude': 116.4074},
            'shanghai': {'latitude': 31.2304, 'longitude': 121.4737},
            'new york': {'latitude': 40.7128, 'longitude': -74.0060},
            'london': {'latitude': 51.5074, 'longitude': -0.1278},
            'tokyo': {'latitude': 35.6762, 'longitude': 139.6503}
        }

        message_lower = message.lower()
        for city, coords in city_coords.items():
            if city in message_lower:
                return coords

        return None

    def _extract_state_code(self, message):
        """从消息中提取美国州代码."""
        # 常见的州代码映射
        state_mapping = {
            'california': 'CA', 'ca': 'CA', u'加州': 'CA', '加州': 'CA',
            'new york': 'NY', 'ny': 'NY', u'纽约': 'NY', '纽约': 'NY',
            'texas': 'TX', 'tx': 'TX', u'德州': 'TX', '德州': 'TX',
            'florida': 'FL', 'fl': 'FL', u'佛罗里达': 'FL', '佛罗里达': 'FL',
            'illinois': 'IL', 'il': 'IL', u'伊利诺伊': 'IL', '伊利诺伊': 'IL'
        }

        message_lower = message.lower()

        # 首先查找直接的两字母州代码
        state_code_match = re.search(r'\b([A-Z]{2})\b', message.upper())
        if state_code_match:
            return state_code_match.group(1)

        # 然后查找州名映射
        for state_name, code in state_mapping.items():
            if state_name in message_lower:
                return code

        return None

    def _format_tool_response(self, tool_name, response_text, is_error=False):
        """格式化工具响应."""
        try:
            if is_error:
                return u"## ❌ 错误\n\n{}".format(response_text)

            if tool_name == 'get_time':
                response_data = json.loads(response_text)
                local_time = response_data.get('local_time', '')
                utc_time = response_data.get('utc_time', '')
                formatted = response_data.get('formatted', '')

                return u"""## 🕐 当前时间

**本地时间：** {}
**UTC 时间：** {}
**格式化：** {}

您还有什么需要帮助的吗？""".format(local_time, utc_time, formatted)

            elif tool_name == 'get_forecast':
                # 天气预报是纯文本格式
                return u"""## 🌤️ 天气预报

{}

*数据来源：模拟天气服务*
*需要其他地区的天气吗？请提供城市名称或经纬度坐标。*""".format(response_text)

            elif tool_name == 'get_alerts':
                try:
                    response_data = json.loads(response_text)
                    state = response_data.get('state', '')
                    message = response_data.get('message', '')
                    alerts = response_data.get('alerts', [])

                    if alerts:
                        alert_text = "\n".join([u"- {}".format(alert) for alert in alerts])
                        return u"""## ⚠️ 天气警报 - {}

{}

{}""".format(state, alert_text, message)
                    else:
                        return u"""## ✅ 天气警报 - {}

{}""".format(state, message)
                except:
                    return u"## ⚠️ 天气警报\n\n{}".format(response_text)

            elif tool_name == 'calculate':
                response_data = json.loads(response_text)
                if 'error' in response_data:
                    return u"## ❌ 计算错误\n\n{}\n\n请检查您的表达式是否正确。".format(response_data['error'])
                else:
                    expr = response_data.get('expression', '')
                    result = response_data.get('result', '')
                    formatted = response_data.get('formatted', '')
                    return u"""## 🧮 计算结果

**表达式：** `{}`
**结果：** `{}`
**格式化：** {}""".format(expr, result, formatted)

            else:
                return u"## 🤖 工具响应\n\n```\n{}\n```".format(response_text)

        except Exception as e:
            print("Format error: " + str(e))
            return u"## 🤖 工具响应\n\n{}".format(response_text)

    def _fallback_response(self, message):
        """备用响应."""
        return u"""## 🤖 MCP 智能助手

我现在可以为您提供以下服务：

### 🛠️ 可用功能：
- ⏰ **时间查询**：问我"现在几点"
- 🌤️ **天气预报**：查询"北京天气"或"39.9042,116.4074天气"
- ⚠️ **天气警报**：查询"加州天气警报"或"CA警报"
- 🧮 **数学计算**：让我计算"2+3*4"
- 💬 **MCP 问答**：关于 MCP 协议的问题

### 💡 示例用法：
- "现在几点了？"
- "北京的天气怎么样？"
- "查询加州的天气警报"
- "帮我计算 (10+5)*2"
- "39.9042,116.4074 的天气预报"

请告诉我您需要什么帮助！

*提示：您刚才说了"{}"{}{} """.format(
            message[:50] + "..." if len(message) > 50 else message,
            "，我没有完全理解。" if len(message) > 0 else "",
            "您可以尝试上面的示例用法。" if len(message) > 0 else ""
        )

    def close(self):
        """关闭连接."""
        if self.client:
            self.client.close()
            self.client = None


# 全局实例
mcp_bot = MCPChatBot()
