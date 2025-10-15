import os
import re
import schedule
import time
import requests
from datetime import datetime
from pathlib import Path
import glob
import subprocess

from config_manager import ConfigManager

class LatexGenerator:
    def __init__(self, config_file="config.yaml"):
        # 加载配置
        self.config_manager = ConfigManager(config_file)
        self.config = self.config_manager.config
        
        # API设置
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.api_config = self.config_manager.get_api_config()
        
        # 文件路径设置
        self.paths_config = self.config_manager.get_paths_config()
        self.resource_path = self.paths_config['resource']
        self.input_dir = self.paths_config['input_dir']
        self.output_dir = self.paths_config['output_dir']
        
        # 监控设置
        self.monitor_config = self.config_manager.get_monitor_config()
        self.check_interval_minutes = self.monitor_config['check_interval_minutes']
        
        # 文件模式设置
        self.file_patterns_config = self.config_manager.get_file_patterns_config()
        
        # LaTeX设置
        self.latex_config = self.config_manager.get_latex_config()
    
    def find_input_files(self):
        """查找所有符合日期规则的文件"""
        # 匹配格式: YYYYMMDD.txt (如20250924.txt)
        pattern = os.path.join(self.input_dir, self.file_patterns_config['input'])
        all_files = glob.glob(pattern)
        
        # 过滤出符合日期格式的文件
        date_files = []
        date_pattern = re.compile(r'(\d{8})\.txt$')  # 匹配8位数字.txt
        
        for file_path in all_files:
            filename = os.path.basename(file_path)
            match = date_pattern.search(filename)
            if match:
                date_str = match.group(1)
                # 验证日期是否有效
                try:
                    datetime.strptime(date_str, "%Y%m%d")
                    date_files.append(file_path)
                except ValueError:
                    continue
        
        print(f"找到 {len(date_files)} 个符合日期规则的文件")
        return sorted(date_files)  # 按文件名排序
    
    def read_input_file(self, file_path):
        """读取输入文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"文件未找到: {file_path}")
            return None
        except Exception as e:
            print(f"读取文件时出错: {e}")
            return None
    
    def read_resource_file(self, filename):
        """读取资源文件"""
        file_path = os.path.join(self.resource_path, filename)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"资源文件未找到: {file_path}")
            return None
        except Exception as e:
            print(f"读取资源文件时出错: {e}")
            return None
    
    def extract_date_from_filename(self, filename):
        """从文件名中提取日期并格式化为中文"""
        date_pattern = re.compile(r'(\d{4})(\d{2})(\d{2})')
        match = date_pattern.search(filename)
        if match:
            year, month, day = match.groups()
            # 去除月份和日期的前导零
            month = str(int(month))
            day = str(int(day))
            return f"{year}年{month}月{day}日"
        return None
    
    def call_deepseek_api(self, prompt):
        """调用DeepSeek API"""
        if not self.api_key:
            print("错误: 未设置DEEPSEEK_API_KEY环境变量")
            return None
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }
        
        data = {
            "model": self.api_config['model'],
            "messages": [
                {
                    "role": "system",
                    "content": "你是一个专业的LaTeX文档生成助手，擅长将学习反馈内容转换为结构化的LaTeX文档。请确保生成的LaTeX代码可以直接编译。"
                },
                {
                    "role": "user", 
                    "content": prompt
                }
            ],
            "temperature": self.api_config['temperature'],
            "max_tokens": self.api_config['max_tokens']
        }
        
        try:
            print("正在调用DeepSeek API...")
            response = requests.post(self.api_config['url'], headers=headers, json=data, timeout=60)
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content']
        except Exception as e:
            print(f"API调用失败: {e}")
            return None
    
    def extract_latex_content(self, text):
        """从API响应中提取LaTeX内容"""
        # 尝试提取```latex ... ```之间的内容
        latex_pattern = r'```latex\s*(.*?)\s*```'
        matches = re.findall(latex_pattern, text, re.DOTALL)
        
        if matches:
            print("检测到LaTeX代码块，提取内容...")
            return matches[0]
        
        # 如果没有代码块标记，尝试提取\begin{document} ... \end{document}之间的内容
        doc_pattern = r'\begin\{document\}.*?\end\{document\}'
        matches = re.findall(doc_pattern, text, re.DOTALL)
        
        if matches:
            print("检测到document环境，提取内容...")
            return matches[0]
        
        # 如果都没有，返回原始文本
        print("未检测到特定格式，返回原始响应...")
        return text
    
    def generate_latex_prompt(self, input_text, style_content, example_content, date_str):
        """生成API提示词"""
        prompt = f"""
请基于以下输入内容生成一个完整的LaTeX文档：

输入内容：
{input_text}

样式文件内容 ({self.latex_config['style_file']})：
{style_content}

示例文件内容 (20250924.tex)：
{example_content}

要求：
0. 首先对输入内容整理，确保通顺、没有错别字，并注意区分汉字和英文引号格式，并确保是引号一对，而不是””(全部左引号) 或““（全部右引号）
1. 根据整理后的内容生成完整的LaTeX文档，使用{self.latex_config['document_class']}文档类
2. 使用提供的样式文件格式和命令
3. 将"今日小任务"等课后作业要求内容复制一份，放到作业记录部分
4. 保持与示例相同的结构和格式
5. 日期格式使用"{date_str}"
6. 只显示有内容的作业项目，使用\\homeworkrecord命令
7. 确保生成的LaTeX代码可以直接编译，不要包含任何解释文本
8. 记得在\\begin{{mathbox}}等下一行段首加上\\par,确保首行缩进。

请直接输出完整的LaTeX代码，包含\\documentclass和\\begin{{document}}...\\end{{document}}。
"""
        return prompt
    
    def compile_latex_file(self, latex_file_path):
        """编译LaTeX文件为PDF"""
        try:
            # 获取当前文件的绝对路径的上一级文件夹
            absolute_dir = Path(__file__).resolve().parent
            # 确保输出目录存在
            output_dir = "/".join([str(absolute_dir),os.path.dirname(latex_file_path)])
            latex_file_path = "/".join([str(absolute_dir),latex_file_path])

            
            # 构建xelatex命令
            command = [
                'xelatex',
                '-interaction=nonstopmode',
                '-output-directory', output_dir,
                latex_file_path
            ]
            print(command)
            
            print(f"正在编译LaTeX文件: {os.path.basename(latex_file_path)}")
            
            # 执行编译命令
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                cwd=output_dir
            )
            
            if result.returncode == 0:
                print(f"LaTeX编译成功")
                
                # 清理编译生成的临时文件
                self.clean_latex_temp_files(latex_file_path)
                return True
            else:
                print(f"LaTeX编译失败，返回码: {result.returncode}")
                if result.stderr:
                    print(f"错误输出: {result.stderr}")
                return False
                
        except FileNotFoundError:
            print("错误: 未找到xelatex命令，请确保LaTeX环境已安装")
            return False
        except Exception as e:
            print(f"编译LaTeX文件时出错: {e}")
            return False
    
    def clean_latex_temp_files(self, latex_file_path):
        """清理LaTeX编译生成的临时文件"""
        try:
            base_name = os.path.splitext(latex_file_path)[0]
            temp_extensions = ['.aux', '.log', '.out', '.toc']
            
            for ext in temp_extensions:
                temp_file = base_name + ext
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    print(f"已清理临时文件: {os.path.basename(temp_file)}")
        except Exception as e:
            print(f"清理临时文件时出错: {e}")
    
    def move_files_to_target_dirs(self, input_file_path, latex_file_path):
        """将生成的文件移动到目标目录"""
        try:
            # 目标主目录
            target_base_dir = "/home/song/NutstoreFiles/6-XY/2025年8月幼小衔接"
            
            # 目标子目录
            pdf_target_dir = os.path.join(target_base_dir, "2-每日反馈")
            tex_target_dir = os.path.join(target_base_dir, "3-每日反馈tex")
            txt_target_dir = os.path.join(target_base_dir, "2-每日反馈txt")
            
            # 确保目标目录存在
            os.makedirs(pdf_target_dir, exist_ok=True)
            os.makedirs(tex_target_dir, exist_ok=True)
            os.makedirs(txt_target_dir, exist_ok=True)
            
            filename_base = os.path.basename(input_file_path).replace('.txt', '')
            
            # 移动PDF文件
            pdf_source_path = latex_file_path.replace('.tex', '.pdf')
            pdf_target_path = os.path.join(pdf_target_dir, f"{filename_base}.pdf")
            
            if os.path.exists(pdf_source_path):
                os.rename(pdf_source_path, pdf_target_path)
                print(f"PDF文件已移动到: {pdf_target_path}")
            
            # 移动TEX文件
            tex_target_path = os.path.join(tex_target_dir, f"{filename_base}.tex")
            if os.path.exists(latex_file_path):
                os.rename(latex_file_path, tex_target_path)
                print(f"TEX文件已移动到: {tex_target_path}")
            
            # 移动TXT文件
            txt_target_path = os.path.join(txt_target_dir, f"{filename_base}.txt")
            if os.path.exists(input_file_path):
                os.rename(input_file_path, txt_target_path)
                print(f"TXT文件已移动到: {txt_target_path}")
            
            return True
            
        except Exception as e:
            print(f"移动文件时出错: {e}")
            return False
    
    def generate_latex_for_file(self, input_file_path):
        """为单个文件生成LaTeX"""
        print(f"\n处理文件: {os.path.basename(input_file_path)}")
        
        # 从文件名提取日期
        filename = os.path.basename(input_file_path)
        date_str = self.extract_date_from_filename(filename)
        if not date_str:
            print(f"无法从文件名提取日期: {filename}")
            return False
        
        print(f"提取的日期: {date_str}")
        
        # 读取输入文件
        input_text = self.read_input_file(input_file_path)
        if not input_text:
            print("无法读取输入文件，跳过处理")
            return False
        
        print(f"成功读取输入文件，内容长度: {len(input_text)} 字符")
        
        # 读取资源文件
        style_content = self.read_resource_file(self.latex_config['style_file'])
        example_content = self.read_resource_file("20250924.tex")
        
        if not style_content:
            print("无法读取样式文件，跳过处理")
            return False
            
        if not example_content:
            print("无法读取示例文件，跳过处理")
            return False
        
        print("成功读取资源文件")
        
        # 生成提示词
        prompt = self.generate_latex_prompt(input_text, style_content, example_content, date_str)
        
        # 调用API
        api_response = self.call_deepseek_api(prompt)
        
        if not api_response:
            print("API调用失败，跳过处理")
            return False
        
        print("API调用成功，处理响应...")
        
        # 提取LaTeX内容
        latex_content = self.extract_latex_content(api_response)
        
        # 从文件名提取年份和月份
        filename = os.path.basename(input_file_path)
        output_filename = filename.replace('.txt', '.tex')
        
        # 默认输出目录
        latex_output_path = os.path.join(self.output_dir, output_filename)
        
        # 保存样式文件到输出目录（如果不存在）
        style_output_path = os.path.join(self.output_dir, self.latex_config['style_file'])
        if not os.path.exists(style_output_path):
            with open(style_output_path, 'w', encoding='utf-8') as f:
                f.write(style_content)
            print(f"样式文件已保存: {style_output_path}")
        
        print(f"输出目录: {self.output_dir}")
    
        # 保存生成的LaTeX文件
        with open(latex_output_path, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"LaTeX文件已保存: {latex_output_path}")
        
        # 显示生成的文件大小
        file_size = os.path.getsize(latex_output_path)
        print(f"生成的LaTeX文件大小: {file_size} 字节")
        
        # 自动编译生成的LaTeX文件
        if self.compile_latex_file(latex_output_path):
            print(f"LaTeX文件编译成功: {output_filename.replace('.tex', '.pdf')}")
            
            # 移动文件到目标目录
            if self.move_files_to_target_dirs(input_file_path, latex_output_path):
                print("文件移动完成")
            else:
                print("文件移动失败")
            
            return True
        else:
            print(f"LaTeX文件编译失败: {output_filename}")
            return False
    
    def generate_all_latex_files(self):
        """生成所有文件的LaTeX"""
        print("开始批量生成LaTeX文件...")
        
        # 查找所有符合日期规则的文件
        input_files = self.find_input_files()
        
        if not input_files:
            print("未找到符合日期规则的文件")
            return False
        
        success_count = 0
        for file_path in input_files:
            if self.generate_latex_for_file(file_path):
                success_count += 1
        
        print(f"\n处理完成: 成功 {success_count}/{len(input_files)} 个文件")
        return success_count > 0
    
    def check_files_modification(self):
        """检查文件是否被修改"""
        input_files = self.find_input_files()
        modified_files = []
        
        for file_path in input_files:
            # 检查对应的输出文件是否存在
            filename = os.path.basename(file_path)
            output_filename = filename.replace('.txt', '.tex')
            
            # 构建对应的输出路径
            date_match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
            if date_match:
                year = date_match.group(1)
                month = date_match.group(2)
                month_str = f"{year}年{int(month)}月"
                output_path = os.path.join(self.output_dir, f"{year}年", f"{month_str}幼小衔接", output_filename)
            else:
                output_path = os.path.join(self.output_dir, output_filename)
            
            # 如果输出文件不存在，或者输入文件比输出文件新，则需要处理
            if not os.path.exists(output_path) or \
               os.path.getmtime(file_path) > os.path.getmtime(output_path):
                modified_files.append(file_path)
        
        return modified_files
    
    def scheduled_task(self):
        """定时任务"""
        print(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - 执行定时检查...")
        
        modified_files = self.check_files_modification()
        
        if modified_files:
            print(f"检测到 {len(modified_files)} 个文件需要处理")
            success_count = 0
            for file_path in modified_files:
                if self.generate_latex_for_file(file_path):
                    success_count += 1
            
            print(f"处理完成: 成功 {success_count}/{len(modified_files)} 个文件")
        else:
            print("没有文件需要处理")
    
    def start_monitoring(self, interval_minutes=None):
        """启动定时监控"""
        if interval_minutes is None:
            interval_minutes = self.check_interval_minutes
            
        print(f"启动定时监控，每{interval_minutes}分钟检查一次...")
        print(f"监控目录: {self.input_dir}")
        print(f"输出目录: {self.output_dir}")
        print("按Ctrl+C停止监控")
        
        # 立即执行一次
        self.scheduled_task()
        
        # 设置定时任务
        schedule.every(interval_minutes).minutes.do(self.scheduled_task)
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n监控已停止")
    
    def run_once(self):
        """单次运行所有文件"""
        print("执行批量生成...")
        success = self.generate_all_latex_files()
        if success:
            print("LaTeX文件生成完成!")
        else:
            print("LaTeX文件生成失败!")
        return success
    
    def run_single(self, date_str):
        """运行单个日期文件"""
        # 构建文件名
        filename = f"{date_str}.txt"
        file_path = os.path.join(self.input_dir, filename)
        
        if not os.path.exists(file_path):
            print(f"文件不存在: {file_path}")
            return False
        
        return self.generate_latex_for_file(file_path)
    
    def show_config(self):
        """显示当前配置"""
        print("当前配置:")
        print(f"  API URL: {self.api_config['url']}")
        print(f"  模型: {self.api_config['model']}")
        print(f"  输入目录: {self.input_dir}")
        print(f"  输出目录: {self.output_dir}")
        print(f"  资源目录: {self.resource_path}")
        print(f"  监控间隔: {self.check_interval_minutes} 分钟")

def main():
    print("=== LaTeX文档生成器 ===")
    
    # 检查API密钥
    if not os.getenv('DEEPSEEK_API_KEY'):
        print("错误: 请设置环境变量 DEEPSEEK_API_KEY")
        print("例如: export DEEPSEEK_API_KEY='your_api_key_here'")
        return
    
    # 检查命令行参数
    import sys
    config_file = "config.yaml"
    
    # 处理配置相关参数
    if len(sys.argv) > 1 and sys.argv[1] == "--config":
        if len(sys.argv) > 2:
            config_file = sys.argv[2]
        else:
            print("请指定配置文件路径")
            return
    
    generator = LatexGenerator(config_file)
    generator.show_config()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--monitor":
            # 可以指定监控间隔
            interval = int(sys.argv[2]) if len(sys.argv) > 2 else None
            generator.start_monitoring(interval)
        elif sys.argv[1] == "--batch":
            generator.run_once()
        elif sys.argv[1] == "--single" and len(sys.argv) > 2:
            generator.run_single(sys.argv[2])
        elif sys.argv[1] == "--config" and len(sys.argv) > 3:
            # 已经处理过config参数，跳过
            pass
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print("用法:")
            print("  python latex_generator.py --batch           # 批量处理所有日期文件")
            print("  python latex_generator.py --single YYYYMMDD # 处理单个日期文件")
            print("  python latex_generator.py --monitor        # 启动定时监控（默认60分钟）")
            print("  python latex_generator.py --monitor 30     # 启动定时监控（30分钟间隔）")
            print("  python latex_generator.py --config path    # 指定配置文件路径")
            print("  python latex_generator.py --help           # 显示帮助")
        else:
            print("未知参数，使用 --help 查看用法")
    else:
        # 默认批量运行
        print("未指定参数，执行批量处理...")
        generator.run_once()

if __name__ == "__main__":
    main()
