#!/usr/bin/env python3
import os
from config_manager import ConfigManager

def setup():
    """初始化设置"""
    print("=== LaTeX生成器初始化设置 ===")
    
    # 检查资源目录
    if not os.path.exists("./resource"):
        print("创建资源目录: ./resource")
        os.makedirs("./resource")
        print("请将 xydailystudy.sty 和 20250924.tex 放入 resource 目录")
    
    # 创建默认配置文件
    config_manager = ConfigManager()
    if not os.path.exists("config.yaml"):
        config_manager.create_default_config()
        print("已创建默认配置文件: config.yaml")
    else:
        print("配置文件已存在: config.yaml")
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("\n警告: 未设置 DEEPSEEK_API_KEY 环境变量")
        print("请运行: export DEEPSEEK_API_KEY='your_api_key_here'")
    
    print("\n初始化完成!")

if __name__ == "__main__":
    setup()