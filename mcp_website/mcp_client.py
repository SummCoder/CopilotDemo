#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-

import json
import subprocess
import threading
import time


class SimpleMCPClient:
    def __init__(self, command, args):
        """Initialize the MCP Client."""
        self.command = command
        self.args = args
        self.server_process = None
        self.request_id = 0
        self.responses = {}
        self.response_events = {}
        self.lock = threading.Lock()
        self.reader_thread = None
        self.is_connected = False

    def connect(self):
        """Connect to MCP server."""
        try:
            full_command = [self.command] + self.args

            # 🔧 最简单的进程创建方式
            self.server_process = subprocess.Popen(
                full_command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
                # 不使用任何特殊标志
            )

            # 等待一下让进程启动
            time.sleep(0.5)

            # 检查进程是否还在运行
            if self.server_process.poll() is not None:
                print("Server process exited immediately")
                return False

            # Start reader thread
            self.reader_thread = threading.Thread(target=self._read_responses)
            self.reader_thread.daemon = True
            self.reader_thread.start()

            # Initialize the connection
            init_response = self.initialize()
            if init_response and "result" in init_response:
                self.notify_initialized()
                self.is_connected = True
                return True
            return False
        except Exception as e:
            print("Failed to connect: " + str(e))
            import traceback
            traceback.print_exc()  # 打印详细错误信息
            return False

    def _read_responses(self):
        """Continuously read responses from the server."""
        while self.server_process and self.server_process.poll() is None:
            try:
                response_str = self.server_process.stdout.readline()
                if not response_str:
                    continue

                response_str = response_str.strip()
                if not response_str:
                    continue

                response = json.loads(response_str)
                print("Received response: " + str(response))  # 调试输出

                if "id" in response:
                    req_id = response["id"]
                    with self.lock:
                        self.responses[req_id] = response
                        if req_id in self.response_events:
                            self.response_events[req_id].set()
            except ValueError as e:
                print("JSON decode error: " + str(e))
                print("Raw response: " + repr(response_str))
                continue
            except Exception as e:
                print("Error reading response: " + str(e))
                break

    def send_request(self, method, params=None, timeout=10):  # 减少超时时间
        """Send a request to the MCP server."""
        if not self.server_process or self.server_process.poll() is not None:
            raise Exception("Server process is not running")

        request = {
            "method": method,
            "jsonrpc": "2.0"
        }

        if params:
            request["params"] = params

        # For notifications, we don't expect a response
        if method == "notifications/initialized":
            request_str = json.dumps(request) + "\n"
            print("Sending notification: " + request_str.strip())  # 调试输出
            try:
                self.server_process.stdin.write(request_str)
                self.server_process.stdin.flush()
                return {"success": True}
            except Exception as e:
                raise Exception("Failed to send notification: " + str(e))

        # For regular requests, we expect a response
        with self.lock:
            req_id = self.request_id
            self.request_id += 1
            request["id"] = req_id
            event = threading.Event()
            self.response_events[req_id] = event

        request_str = json.dumps(request) + "\n"
        print("Sending request: " + request_str.strip())  # 调试输出

        try:
            self.server_process.stdin.write(request_str)
            self.server_process.stdin.flush()
        except Exception as e:
            with self.lock:
                self.response_events.pop(req_id, None)
            raise Exception("Failed to send request: " + str(e))

        # Wait for the response
        print("Waiting for response to request " + str(req_id))
        if not event.wait(timeout):
            with self.lock:
                self.response_events.pop(req_id, None)
            raise Exception("Request timed out")

        with self.lock:
            response = self.responses.pop(req_id, None)
            self.response_events.pop(req_id, None)

        return response

    def initialize(self):
        """Initialize the MCP connection."""
        params = {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "clientInfo": {
                "name": "Django-MCP-Client",
                "version": "1.0.0"
            }
        }
        return self.send_request("initialize", params)

    def notify_initialized(self):
        """Send the initialized notification."""
        return self.send_request("notifications/initialized")

    def list_tools(self):
        """List available tools."""
        return self.send_request("tools/list")

    def call_tool(self, name, arguments):
        """Call a specific tool."""
        params = {
            "name": name,
            "arguments": arguments
        }
        return self.send_request("tools/call", params)

    def close(self):
        """Close the connection to the server."""
        self.is_connected = False
        if self.server_process:
            try:
                self.server_process.terminate()
                self.server_process.wait()
            except:
                try:
                    self.server_process.kill()
                except:
                    pass
            self.server_process = None

    def __enter__(self):
        """Context manager entry."""
        if self.connect():
            return self
        raise Exception("Failed to connect to MCP server")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
