#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import calendar
import datetime
import json
import sys
import traceback


class StandardMCPServer(object):
    def __init__(self, name, version):
        """Initialize the MCP Server following official spec."""
        self.name = name
        self.version = version
        self.tools = {}
        self.resources = {}
        self.prompts = {}
        self.initialized = False

        # 调试日志
        self.debug_log("Standard MCP Server initialized: " + name)

    def debug_log(self, message):
        """写调试日志到文件."""
        try:
            with open("mcp_debug.log", "a") as f:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write("[" + timestamp + "] " + message + "\n")
                f.flush()
        except:
            pass

    def register_tool(self, name, description, input_schema, handler):
        """Register a tool following MCP standard."""
        self.tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
            "handler": handler
        }
        self.debug_log("Tool registered: " + name)

    def register_resource(self, name, uri, description, mime_type, handler):
        """Register a resource following MCP standard."""
        self.resources[name] = {
            "uri": uri,
            "name": name,
            "description": description,
            "mimeType": mime_type,
            "handler": handler
        }
        self.debug_log("Resource registered: " + name)

    def register_prompt(self, name, description, arguments, handler):
        """Register a prompt following MCP standard."""
        self.prompts[name] = {
            "name": name,
            "description": description,
            "arguments": arguments,
            "handler": handler
        }
        self.debug_log("Prompt registered: " + name)

    def handle_request(self, request):
        """Handle incoming request following MCP standard."""
        method = request.get("method")
        params = request.get("params", {})
        request_id = request.get("id")

        self.debug_log("Handling request: " + method)

        try:
            # Standard MCP methods
            if method == "initialize":
                result = self._handle_initialize(params)
            elif method == "notifications/initialized":
                self.initialized = True
                self.debug_log("Server initialized")
                return None  # No response for notifications
            elif method == "tools/list":
                result = self._handle_list_tools()
            elif method == "tools/call":
                result = self._handle_call_tool(params)
            elif method == "resources/list":
                result = self._handle_list_resources()
            elif method == "resources/read":
                result = self._handle_read_resource(params)
            elif method == "resources/templates/list":
                result = self._handle_list_resource_templates()
            elif method == "prompts/list":
                result = self._handle_list_prompts()
            elif method == "prompts/get":
                result = self._handle_get_prompt(params)
            else:
                result = {"error": {"code": -32601, "message": "Method not found: " + method}}

            if request_id is not None:
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": result
                }
                self.debug_log("Sending response: " + str(response))
                return response
        except Exception as e:
            self.debug_log("Error handling request: " + str(e))
            self.debug_log("Traceback: " + traceback.format_exc())
            if request_id is not None:
                return {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {"code": -32603, "message": str(e)}
                }
        return None

    def _handle_initialize(self, params):
        """Handle initialize request with standard capabilities."""
        result = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "experimental": {},
                "prompts": {
                    "listChanged": False
                },
                "resources": {
                    "subscribe": False,
                    "listChanged": False
                },
                "tools": {
                    "listChanged": False
                }
            },
            "serverInfo": {
                "name": self.name,
                "version": self.version
            }
        }
        self.debug_log("Initialize result: " + str(result))
        return result

    def _handle_list_tools(self):
        """Handle tools/list request."""
        tools_list = []
        for tool_name, tool_info in self.tools.items():
            tools_list.append({
                "name": tool_info["name"],
                "description": tool_info["description"],
                "inputSchema": tool_info["inputSchema"]
            })
        result = {"tools": tools_list}
        self.debug_log("Tools list: " + str(result))
        return result

    def _handle_call_tool(self, params):
        """Handle tools/call request."""
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        self.debug_log("Calling tool: " + tool_name + " with args: " + str(arguments))

        if tool_name not in self.tools:
            raise Exception("Tool not found: " + tool_name)

        handler = self.tools[tool_name]["handler"]
        try:
            result_content = handler(arguments)

            # 标准化响应格式
            if isinstance(result_content, dict) and "error" in result_content:
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": "Error: " + str(result_content["error"])
                        }
                    ],
                    "isError": True
                }
            else:
                content_text = json.dumps(result_content, ensure_ascii=False) if isinstance(result_content,
                                                                                            dict) else str(
                    result_content)
                return {
                    "content": [
                        {
                            "type": "text",
                            "text": content_text
                        }
                    ],
                    "isError": False
                }
        except Exception as e:
            return {
                "content": [
                    {
                        "type": "text",
                        "text": "Tool execution error: " + str(e)
                    }
                ],
                "isError": True
            }

    def _handle_list_resources(self):
        """Handle resources/list request."""
        resources_list = []
        for resource_name, resource_info in self.resources.items():
            resources_list.append({
                "uri": resource_info["uri"],
                "name": resource_info["name"],
                "description": resource_info["description"],
                "mimeType": resource_info["mimeType"]
            })
        return {"resources": resources_list}

    def _handle_read_resource(self, params):
        """Handle resources/read request."""
        uri = params.get("uri")
        # 简化实现，实际应该根据 URI 找到对应的资源
        return {
            "contents": [
                {
                    "uri": uri,
                    "mimeType": "text/plain",
                    "text": "Resource content for: " + uri
                }
            ]
        }

    def _handle_list_resource_templates(self):
        """Handle resources/templates/list request."""
        return {"resourceTemplates": []}

    def _handle_list_prompts(self):
        """Handle prompts/list request."""
        prompts_list = []
        for prompt_name, prompt_info in self.prompts.items():
            prompts_list.append({
                "name": prompt_info["name"],
                "description": prompt_info["description"],
                "arguments": prompt_info["arguments"]
            })
        return {"prompts": prompts_list}

    def _handle_get_prompt(self, params):
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})

        if name not in self.prompts:
            raise Exception("Prompt not found: " + name)

        handler = self.prompts[name]["handler"]
        result = handler(arguments)

        return {
            "description": self.prompts[name]["description"],
            "messages": result.get("messages", [])
        }

    def run(self):
        """Run the MCP server."""
        self.debug_log("Standard MCP Server starting...")

        try:
            while True:
                line = sys.stdin.readline()
                if not line:
                    self.debug_log("EOF received, exiting")
                    break

                line = line.strip()
                if not line:
                    continue

                self.debug_log("Received: " + line)

                try:
                    request = json.loads(line)
                    response = self.handle_request(request)

                    if response:
                        response_str = json.dumps(response, ensure_ascii=False)
                        sys.stdout.write(response_str + "\n")
                        sys.stdout.flush()
                        self.debug_log("Sent: " + response_str)

                except ValueError as e:
                    self.debug_log("JSON parse error: " + str(e))
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32700, "message": "Parse error: " + str(e)}
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()
                except Exception as e:
                    self.debug_log("Request handling error: " + str(e))
                    self.debug_log("Traceback: " + traceback.format_exc())
                    error_response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32603, "message": "Internal error: " + str(e)}
                    }
                    sys.stdout.write(json.dumps(error_response) + "\n")
                    sys.stdout.flush()

        except Exception as e:
            self.debug_log("Server error: " + str(e))
            self.debug_log("Traceback: " + traceback.format_exc())


# 标准化的示例服务器实现
class WeatherMCPServer(StandardMCPServer):
    def __init__(self):
        super(WeatherMCPServer, self).__init__("weather-server", "1.6.0")
        self._register_tools()
        self._register_resources()
        self._register_prompts()

    def _register_tools(self):
        """Register standard tools."""

        # 天气预报工具
        self.register_tool(
            "get_forecast",
            "Get weather forecast for a location.\n\nArgs:\n    latitude: Latitude of the location\n    longitude: Longitude of the location",
            {
                "type": "object",
                "properties": {
                    "latitude": {
                        "title": "Latitude",
                        "type": "number"
                    },
                    "longitude": {
                        "title": "Longitude",
                        "type": "number"
                    }
                },
                "required": ["latitude", "longitude"],
                "title": "get_forecastArguments"
            },
            self._get_forecast
        )

        # 天气警报工具
        self.register_tool(
            "get_alerts",
            "Get weather alerts for a US state.\n\nArgs:\n    state: Two-letter US state code (e.g. CA, NY)",
            {
                "type": "object",
                "properties": {
                    "state": {
                        "title": "State",
                        "type": "string"
                    }
                },
                "required": ["state"],
                "title": "get_alertsArguments"
            },
            self._get_alerts
        )

        # 时间工具
        self.register_tool(
            "get_time",
            "Get current time and date information",
            {
                "type": "object",
                "properties": {},
                "required": [],
                "title": "get_timeArguments"
            },
            self._get_time
        )

        # 计算工具
        self.register_tool(
            "calculate",
            "Perform mathematical calculations safely",
            {
                "type": "object",
                "properties": {
                    "expression": {
                        "title": "Expression",
                        "type": "string",
                        "description": "Mathematical expression to evaluate"
                    }
                },
                "required": ["expression"],
                "title": "calculateArguments"
            },
            self._calculate
        )

    def _register_resources(self):
        """Register standard resources."""
        # 可以添加资源，如配置文件、数据文件等
        pass

    def _register_prompts(self):
        """Register standard prompts."""
        # 可以添加提示模板
        pass

    def _get_forecast(self, args):
        """模拟天气预报数据."""
        latitude = args.get("latitude", 0)
        longitude = args.get("longitude", 0)

        # 模拟天气数据
        forecast_data = """
Today:
Temperature: 64°F
Wind: 2 to 18 mph S
Forecast: Mostly sunny. High near 64, with temperatures falling to around 62 in the afternoon. South wind 2 to 18 mph, with gusts as high as 30 mph.

---

Tonight:
Temperature: 57°F
Wind: 12 to 17 mph S
Forecast: Mostly cloudy. Low around 57, with temperatures rising to around 59 overnight. South wind 12 to 17 mph, with gusts as high as 29 mph.

---

Saturday:
Temperature: 78°F
Wind: 12 to 21 mph SW
Forecast: Partly sunny, with a high near 78. Southwest wind 12 to 21 mph, with gusts as high as 32 mph.

---

Location: {:.4f}, {:.4f}
""".format(latitude, longitude)

        return forecast_data

    def _get_alerts(self, args):
        """模拟天气警报数据."""
        state = args.get("state", "")

        return {
            "state": state,
            "alerts": [],
            "message": "No active weather alerts for " + state
        }

    def _get_time(self, args):
        """获取当前时间."""
        now = datetime.datetime.now()
        utc_now = datetime.datetime.utcnow()
        timestamp = calendar.timegm(now.timetuple())

        return {
            "local_time": now.strftime("%Y-%m-%d %H:%M:%S"),
            "utc_time": utc_now.strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": timestamp,
            "timezone": "Local",
            "formatted": "Current Date and Time: " + now.strftime("%Y-%m-%d %H:%M:%S")
        }

    def _calculate(self, args):
        """安全的数学计算."""
        expression = args.get("expression", "")
        try:
            # 安全检查
            allowed_chars = set("0123456789+-*/()., ")
            if not all(c in allowed_chars for c in expression):
                return {"error": "Invalid characters in expression"}

            # 检查危险操作
            dangerous_words = ["import", "exec", "eval", "__", "open", "file"]
            if any(dangerous in expression for dangerous in dangerous_words):
                return {"error": "Dangerous operation not allowed"}

            result = eval(expression)
            return {
                "expression": expression,
                "result": result,
                "formatted": "Result: " + str(result)
            }
        except Exception as e:
            return {"error": str(e)}


if __name__ == "__main__":
    try:
        # 清空之前的调试日志
        try:
            with open("mcp_debug.log", "w") as f:
                f.write("=== Standard MCP Server Starting at " +
                        datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " ===\n")
        except:
            pass

        server = WeatherMCPServer()
        server.debug_log("=== Standard MCP Server Ready ===")
        server.run()
    except Exception as e:
        # 确保错误被记录
        try:
            with open("mcp_debug.log", "a") as f:
                f.write("FATAL ERROR: " + str(e) + "\n")
                f.write(traceback.format_exc() + "\n")
        except:
            pass
        print("FATAL ERROR: " + str(e))
        traceback.print_exc()
        raise