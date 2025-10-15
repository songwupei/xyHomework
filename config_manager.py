import os
import yaml
from pathlib import Path

class ConfigManager:
    def __init__(self, config_file="config.yaml"):
        self.config_file = config_file
        self.config = self.load_config()
        
    def load_config(self):
        """加载YAML配置文件"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # 扩展路径中的波浪号
            config['paths']['input_dir'] = os.path.expanduser(config['paths']['input_dir'])
            config['paths']['output_dir'] = os.path.expanduser(config['paths']['output_dir'])
            
            # 确保输出目录存在
            os.makedirs(config['paths']['output_dir'], exist_ok=True)
            
            return config
        except FileNotFoundError:
            print(f"配置文件 {self.config_file} 未找到，使用默认配置")
            return self.get_default_config()
        except Exception as e:
            print(f"加载配置文件时出错: {e}，使用默认配置")
            return self.get_default_config()
    
    def get_default_config(self):
        """获取默认配置"""
        return {
            'api': {
                'url': 'https://api.deepseek.com/v1/chat/completions',
                'model': 'deepseek-chat',
                'temperature': 0.3,
                'max_tokens': 4000
            },
            'paths': {
                'resource': './resource',
                'input_dir': os.path.expanduser('~/NustoreFiles/6-XY/2025年8月幼小衔接/'),
                'output_dir': './output'
            },
            'monitor': {
                'check_interval_minutes': 60
            },
            'file_patterns': {
                'input': '*.txt',
                'output': '*.tex'
            },
            'latex': {
                'document_class': 'article',
                'font_size': '14pt',
                'style_file': 'xydailystudy.sty'
            }
        }
    
    def get_api_config(self):
        """获取API配置"""
        return self.config.get('api', {})
    
    def get_paths_config(self):
        """获取路径配置"""
        return self.config.get('paths', {})
    
    def get_monitor_config(self):
        """获取监控配置"""
        return self.config.get('monitor', {})
    
    def get_file_patterns_config(self):
        """获取文件模式配置"""
        return self.config.get('file_patterns', {})
    
    def get_latex_config(self):
        """获取LaTeX配置"""
        return self.config.get('latex', {})
    
    def save_config(self, config=None):
        """保存配置到文件"""
        if config is None:
            config = self.config
        
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True, indent=2)
            print(f"配置已保存到 {self.config_file}")
            return True
        except Exception as e:
            print(f"保存配置时出错: {e}")
            return False
    
    def create_default_config(self):
        """创建默认配置文件"""
        default_config = self.get_default_config()
        return self.save_config(default_config)