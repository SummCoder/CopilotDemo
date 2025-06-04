# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render


def index(request):
    """MCP介绍页面主视图"""
    context = {
        'title': 'Model Context Protocol (MCP) - 全面介绍',
        'features': [
            {
                'title': '标准化协议',
                'description': 'MCP提供了一个标准化的方式来连接AI助手和各种数据源',
                'icon': '🔗'
            },
            {
                'title': '工具集成',
                'description': '轻松集成各种工具和服务，扩展AI助手的能力',
                'icon': '🛠️'
            },
            {
                'title': '资源访问',
                'description': '安全地访问和操作各种外部资源和数据',
                'icon': '📊'
            },
            {
                'title': '模块化设计',
                'description': '采用模块化架构，便于扩展和维护',
                'icon': '🧩'
            }
        ],
        'use_cases': [
            {
                'title': '数据库查询',
                'description': '连接到数据库并执行复杂查询，获取实时数据',
                'example': 'SELECT * FROM users WHERE created_date > \'2023-01-01\''
            },
            {
                'title': '文件系统操作',
                'description': '读取、写入和管理文件系统中的文件和目录',
                'example': '读取配置文件，生成报告，批量处理文档'
            },
            {
                'title': 'API集成',
                'description': '调用REST API、GraphQL接口等外部服务',
                'example': '获取天气信息，发送邮件，社交媒体集成'
            },
            {
                'title': '监控与日志',
                'description': '实时监控系统状态，分析日志文件',
                'example': '服务器性能监控，错误日志分析，告警通知'
            }
        ],
        'architecture': {
            'client': 'AI助手或应用程序',
            'protocol': 'MCP协议层',
            'server': 'MCP服务器',
            'resources': '外部资源（数据库、API、文件等）'
        }
    }
    return render(request, 'mcp_intro/index.html', context)
