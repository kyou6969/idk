"""
中文情感分析系统 GUI控制面板

使用说明：
1. 环境要求：
   - Python 3.8+
   - 依赖包: tkinter, uvicorn, fastapi, psutil, aiohttp, numpy
   安装依赖: pip install -r requirements.txt

2. 启动方式：
   - 直接运行: python run.py
   - 或在IDE中运行此文件

3. 主要功能：
   - 服务器控制（启动/停止）
   - 文本情感分析
   - 语音情感分析
   - 对比分析
   - 实时分析
   - 批量处理

4. 配置文件：
   - server_config.json 自动创建
   - 可配置端口、主机等
"""

import uvicorn
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import sys
import os
import logging
import psutil
import json
import asyncio
import aiohttp
import numpy as np
from datetime import datetime
import signal
from typing import Optional, Dict, Any, List
from pathlib import Path

# 配置日志
log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"app_{datetime.now().strftime('%Y%m%d')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class ServerConfig:
    """服务器配置管理类"""
    def __init__(self):
        self.config_file = 'server_config.json'
        self.load_config()

    def load_config(self):
        """加载配置文件，如果不存在则创建默认配置"""
        default_config = {
            'host': '127.0.0.1',
            'port': 8000,
            'auto_open_browser': True,
            'environment': 'development',
            'last_run': None,
            'max_batch_size': 100,
            'analysis_timeout': 30,
            'enable_real_time': True,
            'audio_formats': ['wav', 'pcm', 'amr'],
            'sample_rates': ['8000', '16000', '44100', '48000']
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
                # 确保所有默认配置项都存在
                for key, value in default_config.items():
                    if key not in self.config:
                        self.config[key] = value
            else:
                self.config = default_config
                self.save_config()
                logger.info("Created default configuration file")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = default_config

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
            logger.info("Configuration saved successfully")
        except Exception as e:
            logger.error(f"Error saving config: {e}")

    def update_config(self, key: str, value: Any):
        """更新单个配置项"""
        try:
            self.config[key] = value
            self.save_config()
            logger.info(f"Updated config: {key} = {value}")
        except Exception as e:
            logger.error(f"Error updating config {key}: {e}")


class ServerGUI:
    pass


class AnalysisResult:
    """分析结果显示类"""
    def __init__(self, window: tk.Toplevel, title: str = "分析结果"):
        self.window = window
        self.window.title(title)
        self.window.geometry("600x500")
        self.setup_ui()

    def setup_ui(self):
        """设置结果显示界面"""
        # 创建notebook用于分页显示
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # 基础结果页
        self.basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.basic_frame, text="基础分析")

        # 详细分析页
        self.detail_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.detail_frame, text="详细分析")

        # 图表页面
        self.chart_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.chart_frame, text="可视化")

        self.setup_basic_frame()
        self.setup_detail_frame()
        self.setup_chart_frame()

    def setup_basic_frame(self):
        """设置基础分析结果页面"""
        # 基础结果文本框
        self.basic_text = tk.Text(self.basic_frame, wrap=tk.WORD)
        self.basic_text.pack(fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.basic_frame, orient=tk.VERTICAL, command=self.basic_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.basic_text['yscrollcommand'] = scrollbar.set

    def setup_detail_frame(self):
        """设置详细分析结果页面"""
        # 详细结果文本框
        self.detail_text = tk.Text(self.detail_frame, wrap=tk.WORD)
        self.detail_text.pack(fill=tk.BOTH, expand=True)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(self.detail_frame, orient=tk.VERTICAL, command=self.detail_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.detail_text['yscrollcommand'] = scrollbar.set

    def setup_chart_frame(self):
        """设置图表显示页面"""
        # 图表区域（后续实现）
        self.chart_canvas = tk.Canvas(self.chart_frame)
        self.chart_canvas.pack(fill=tk.BOTH, expand=True)

    def update_basic_result(self, text: str):
        """更新基础分析结果"""
        self.basic_text.delete('1.0', tk.END)
        self.basic_text.insert(tk.END, text)
        self.basic_text.config(state=tk.DISABLED)

    def update_detail_result(self, text: str):
        """更新详细分析结果"""
        self.detail_text.delete('1.0', tk.END)
        self.detail_text.insert(tk.END, text)
        self.detail_text.config(state=tk.DISABLED)

    def update_chart(self, data: Dict[str, Any]):
        """更新图表显示（后续实现）"""
        pass

    class ServerGUI:
        """情感分析服务器GUI主类"""

        def __init__(self):
            try:
                self.config = ServerConfig()
                self.server_thread = None
                self.should_stop = False

                # 创建主窗口
                self.root = tk.Tk()
                self.root.title("情感分析服务器控制面板")
                self.root.geometry("900x700")

                # 状态变量
                self.server_status = tk.StringVar(value="已停止")
                self.port = tk.StringVar(value=str(self.config.config['port']))
                self.real_time_enabled = tk.BooleanVar(value=self.config.config['enable_real_time'])

                # 批处理变量
                self.batch_files = []
                self.is_processing = False

                # 设置UI
                self.setup_ui()

                # 初始化异步支持
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)

                # 绑定关闭事件
                self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

                # 初始化分析会话
                self.analysis_session = None
                self.root.after(100, lambda: self.loop.run_until_complete(self.init_analysis_session()))

                logger.info("GUI initialized successfully")

            except Exception as e:
                logger.error(f"Error initializing GUI: {str(e)}")
                raise

        async def init_analysis_session(self):
            """初始化异步HTTP会话"""
            if self.analysis_session is None or self.analysis_session.closed:
                self.analysis_session = aiohttp.ClientSession()
                logger.info("Analysis session initialized")

        def setup_ui(self):
            """设置UI界面布局"""
            # 创建主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 服务器控制区
            self.setup_server_control(main_frame)

            # 分析功能区
            self.setup_analysis_panel(main_frame)

            # 批量处理区
            self.setup_batch_panel(main_frame)

            # 实时分析区
            self.setup_realtime_panel(main_frame)

            # 日志区
            self.setup_log_panel(main_frame)

            # 配置网格权重
            self.root.columnconfigure(0, weight=1)
            self.root.rowconfigure(0, weight=1)
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(5, weight=1)

        def setup_server_control(self, parent):
            """设置服务器控制面板"""
            control_frame = ttk.LabelFrame(parent, text="服务器控制", padding="10")
            control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

            # 启动按钮
            self.start_btn = ttk.Button(
                control_frame,
                text="启动服务器",
                command=self.start_server
            )
            self.start_btn.grid(row=0, column=0, padx=5)

            # 停止按钮
            self.stop_btn = ttk.Button(
                control_frame,
                text="停止服务器",
                command=self.stop_server,
                state=tk.DISABLED
            )
            self.stop_btn.grid(row=0, column=1, padx=5)

            # 端口配置
            ttk.Label(control_frame, text="端口:").grid(row=0, column=2, padx=5)
            port_entry = ttk.Entry(control_frame, textvariable=self.port, width=10)
            port_entry.grid(row=0, column=3, padx=5)

            # 自动打开浏览器选项
            self.auto_open_var = tk.BooleanVar(value=self.config.config['auto_open_browser'])
            auto_open_check = ttk.Checkbutton(
                control_frame,
                text="自动打开浏览器",
                variable=self.auto_open_var,
                command=self.save_auto_open
            )
            auto_open_check.grid(row=0, column=4, padx=5)

            # 打开浏览器按钮
            self.browser_btn = ttk.Button(
                control_frame,
                text="打开浏览器",
                command=self.open_browser
            )
            self.browser_btn.grid(row=0, column=5, padx=5)

            # 状态显示
            ttk.Label(control_frame, textvariable=self.server_status).grid(
                row=0, column=6, padx=5
            )

        def setup_analysis_panel(self, parent):
            """设置分析功能面板"""
            analysis_frame = ttk.LabelFrame(parent, text="分析功能", padding="10")
            analysis_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

            # 文本分析区域
            text_frame = ttk.LabelFrame(analysis_frame, text="文本分析", padding="5")
            text_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))

            self.text_input = tk.Text(text_frame, height=3, width=50)
            self.text_input.grid(row=0, column=0, padx=5, pady=5)

            ttk.Button(
                text_frame,
                text="分析文本",
                command=lambda: self.loop.run_until_complete(self.analyze_text())
            ).grid(row=0, column=1, padx=5)

            # 语音分析区域
            audio_frame = ttk.LabelFrame(analysis_frame, text="语音分析", padding="5")
            audio_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))

            self.file_label = ttk.Label(audio_frame, text="未选择文件")
            self.file_label.grid(row=0, column=0, padx=5)

            ttk.Button(
                audio_frame,
                text="选择文件",
                command=self.select_audio_file
            ).grid(row=0, column=1, padx=5)

            ttk.Label(audio_frame, text="格式:").grid(row=0, column=2)
            self.format_var = tk.StringVar(value="wav")
            format_combo = ttk.Combobox(
                audio_frame,
                textvariable=self.format_var,
                values=self.config.config['audio_formats'],
                state="readonly",
                width=10
            )
            format_combo.grid(row=0, column=3, padx=5)

            ttk.Label(audio_frame, text="采样率:").grid(row=0, column=4)
            self.rate_var = tk.StringVar(value="16000")
            rate_combo = ttk.Combobox(
                audio_frame,
                textvariable=self.rate_var,
                values=self.config.config['sample_rates'],
                state="readonly",
                width=10
            )
            rate_combo.grid(row=0, column=5, padx=5)

            self.analyze_btn = ttk.Button(
                audio_frame,
                text="分析语音",
                command=lambda: self.loop.run_until_complete(self.analyze_audio()),
                state=tk.DISABLED
            )
            self.analyze_btn.grid(row=0, column=6, padx=5)

        def setup_batch_panel(self, parent):
            """设置批量处理面板"""
            batch_frame = ttk.LabelFrame(parent, text="批量处理", padding="10")
            batch_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))

            # 文件选择
            ttk.Button(
                batch_frame,
                text="选择文件",
                command=self.select_batch_files
            ).grid(row=0, column=0, padx=5)

            self.batch_label = ttk.Label(batch_frame, text="未选择文件")
            self.batch_label.grid(row=0, column=1, padx=5)

            # 进度显示
            self.batch_progress = ttk.Progressbar(
                batch_frame,
                mode='determinate',
                length=300
            )
            self.batch_progress.grid(row=0, column=2, padx=5)

            # 开始处理按钮
            self.batch_start_btn = ttk.Button(
                batch_frame,
                text="开始批处理",
                command=lambda: self.loop.run_until_complete(self.process_batch()),
                state=tk.DISABLED
            )
            self.batch_start_btn.grid(row=0, column=3, padx=5)

        def setup_realtime_panel(self, parent):
            """设置实时分析面板"""
            realtime_frame = ttk.LabelFrame(parent, text="实时分析", padding="10")
            realtime_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))

            ttk.Checkbutton(
                realtime_frame,
                text="启用实时分析",
                variable=self.real_time_enabled,
                command=self.toggle_realtime
            ).grid(row=0, column=0, padx=5)

            self.realtime_status = ttk.Label(realtime_frame, text="实时分析已停止")
            self.realtime_status.grid(row=0, column=1, padx=5)

            # 实时分析结果显示
            self.realtime_result = ttk.Label(realtime_frame, text="")
            self.realtime_result.grid(row=0, column=2, padx=5)

        def setup_log_panel(self, parent):
            """设置日志面板"""
            log_frame = ttk.LabelFrame(parent, text="日志", padding="10")
            log_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            self.log_text['yscrollcommand'] = scrollbar.set

        def log_message(self, message: str):
            """记录日志消息"""
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            logger.info(message)

            # ServerGUI类的功能实现部分（续）

            def save_auto_open(self):
                """保存自动打开浏览器设置"""
                try:
                    self.config.update_config('auto_open_browser', self.auto_open_var.get())
                except Exception as e:
                    self.log_message(f"保存设置失败: {str(e)}")

            def start_server(self):
                """启动服务器"""
                try:
                    port = int(self.port.get())
                    if not (1024 <= port <= 65535):
                        raise ValueError("端口号必须在1024-65535之间")

                    self.config.update_config('port', port)

                    self.should_stop = False
                    self.server_thread = threading.Thread(
                        target=self.run_server,
                        args=(self.config.config['host'], port)
                    )
                    self.server_thread.daemon = True
                    self.server_thread.start()

                    self.server_status.set("运行中")
                    self.start_btn['state'] = tk.DISABLED
                    self.stop_btn['state'] = tk.NORMAL

                    self.log_message(f"服务器已启动 (端口: {port})")

                    if self.auto_open_var.get():
                        self.open_browser()

                except Exception as e:
                    self.log_message(f"启动失败: {str(e)}")
                    messagebox.showerror("错误", str(e))

            def stop_server(self):
                """停止服务器"""
                try:
                    self.should_stop = True

                    # 停止所有相关进程
                    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                        try:
                            if proc.info['cmdline'] and 'uvicorn' in proc.info['cmdline'][0].lower():
                                proc.send_signal(signal.SIGTERM)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue

                    self.server_status.set("已停止")
                    self.start_btn['state'] = tk.NORMAL
                    self.stop_btn['state'] = tk.DISABLED

                    self.log_message("服务器已停止")

                except Exception as e:
                    self.log_message(f"停止服务器时出错: {str(e)}")

            def run_server(self, host: str, port: int):
                """运行服务器进程"""
                try:
                    config = uvicorn.Config(
                        "app.main:app",
                        host=host,
                        port=port,
                        reload=True,
                        log_level="info"
                    )
                    server = uvicorn.Server(config)
                    server.run()
                except Exception as e:
                    self.log_message(f"服务器运行错误: {str(e)}")
                    self.server_status.set("错误")
                    self.start_btn['state'] = tk.NORMAL
                    self.stop_btn['state'] = tk.DISABLED

            def open_browser(self):
                """打开浏览器访问API文档"""
                try:
                    port = int(self.port.get())
                    url = f"http://{self.config.config['host']}:{port}/docs"
                    webbrowser.open(url)
                    self.log_message(f"已打开浏览器: {url}")
                except Exception as e:
                    self.log_message(f"无法打开浏览器: {str(e)}")
                    messagebox.showerror("错误", str(e))

            async def analyze_text(self):
                """分析文本"""
                try:
                    text = self.text_input.get("1.0", tk.END).strip()
                    if not text:
                        messagebox.showerror("错误", "请输入文本")
                        return

                    self.log_message("开始文本分析...")
                    url = f"http://{self.config.config['host']}:{self.port.get()}/analyze/text"

                    async with self.analysis_session.post(url, json={"text": text}) as response:
                        if response.status == 200:
                            result = await response.json()
                            self.show_analysis_result(result, "文本分析结果")
                            self.log_message("文本分析完成")
                        else:
                            raise Exception(await response.text())

                except Exception as e:
                    self.log_message(f"文本分析错误: {str(e)}")
                    messagebox.showerror("错误", str(e))

            async def analyze_audio(self):
                """分析音频"""
                if not hasattr(self, 'audio_file_path'):
                    messagebox.showerror("错误", "请先选择音频文件")
                    return

                try:
                    self.analyze_btn['state'] = tk.DISABLED
                    self.log_message("开始分析语音...")

                    with open(self.audio_file_path, 'rb') as f:
                        data = aiohttp.FormData()
                        data.add_field('file',
                                       f,
                                       filename=os.path.basename(self.audio_file_path),
                                       content_type=f'audio/{self.format_var.get()}'
                                       )
                        data.add_field('format', self.format_var.get())
                        data.add_field('rate', self.rate_var.get())

                        url = f"http://{self.config.config['host']}:{self.port.get()}/analyze/audio"
                        async with self.analysis_session.post(url, data=data) as response:
                            if response.status == 200:
                                result = await response.json()
                                self.show_analysis_result(result, "语音分析结果")
                                self.log_message("语音分析完成")
                            else:
                                raise Exception(await response.text())

                except Exception as e:
                    self.log_message(f"语音分析错误: {str(e)}")
                    messagebox.showerror("错误", str(e))
                finally:
                    self.analyze_btn['state'] = tk.NORMAL

            def select_audio_file(self):
                """选择音频文件"""
                try:
                    file_path = filedialog.askopenfilename(
                        title="选择语音文件",
                        filetypes=[
                            ("音频文件", "*.wav;*.pcm;*.amr"),
                            ("WAV文件", "*.wav"),
                            ("PCM文件", "*.pcm"),
                            ("AMR文件", "*.amr"),
                            ("所有文件", "*.*")
                        ]
                    )
                    if file_path:
                        self.audio_file_path = file_path
                        self.file_label.config(text=os.path.basename(file_path))
                        self.analyze_btn['state'] = tk.NORMAL
                        self.log_message(f"已选择文件: {file_path}")
                except Exception as e:
                    self.log_message(f"选择文件失败: {str(e)}")
                    messagebox.showerror("错误", str(e))

            def select_batch_files(self):
                """选择批量处理文件"""
                try:
                    files = filedialog.askopenfilenames(
                        title="选择批量处理文件",
                        filetypes=[
                            ("文本文件", "*.txt"),
                            ("所有文件", "*.*")
                        ]
                    )
                    if files:
                        self.batch_files = files
                        self.batch_label.config(text=f"已选择 {len(files)} 个文件")
                        self.batch_start_btn['state'] = tk.NORMAL
                        self.log_message(f"已选择批量处理文件: {len(files)} 个")
                except Exception as e:
                    self.log_message(f"选择批量文件失败: {str(e)}")
                    messagebox.showerror("错误", str(e))

            async def process_batch(self):
                """批量处理文件"""
                if not hasattr(self, 'batch_files') or not self.batch_files:
                    messagebox.showerror("错误", "请先选择批处理文件")
                    return

                try:
                    self.is_processing = True
                    self.batch_start_btn['state'] = tk.DISABLED
                    self.log_message("开始批量处理...")

                    total_files = len(self.batch_files)
                    self.batch_progress['maximum'] = total_files
                    self.batch_progress['value'] = 0

                    results = []
                    for i, file_path in enumerate(self.batch_files):
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                text = f.read().strip()

                            url = f"http://{self.config.config['host']}:{self.port.get()}/analyze/text"
                            async with self.analysis_session.post(url, json={"text": text}) as response:
                                if response.status == 200:
                                    result = await response.json()
                                    results.append({
                                        'file': os.path.basename(file_path),
                                        'result': result
                                    })
                                else:
                                    self.log_message(f"处理文件失败: {file_path}")
                        except Exception as e:
                            self.log_message(f"处理文件出错 {file_path}: {str(e)}")

                        self.batch_progress['value'] = i + 1
                        self.root.update_idletasks()

                    self.show_batch_results(results)
                    self.log_message("批量处理完成")

                except Exception as e:
                    self.log_message(f"批量处理错误: {str(e)}")
                    messagebox.showerror("错误", str(e))
                finally:
                    self.is_processing = False
                    self.batch_start_btn['state'] = tk.NORMAL
                    self.batch_progress['value'] = 0

            def toggle_realtime(self):
                """切换实时分析状态"""
                if self.real_time_enabled.get():
                    self.start_realtime_analysis()
                else:
                    self.stop_realtime_analysis()

            def start_realtime_analysis(self):
                """启动实时分析"""
                self.realtime_status.config(text="实时分析运行中")
                self.config.update_config('enable_real_time', True)
                self.log_message("启动实时分析")

            def stop_realtime_analysis(self):
                """停止实时分析"""
                self.realtime_status.config(text="实时分析已停止")
                self.config.update_config('enable_real_time', False)
                self.log_message("停止实时分析")

            def show_analysis_result(self, result: dict, title: str):
                """显示分析结果"""
                window = tk.Toplevel(self.root)
                result_display = AnalysisResult(window, title)

                # 更新基础分析结果
                basic_text = self.format_basic_result(result)
                result_display.update_basic_result(basic_text)

                # 更新详细分析结果
                detail_text = self.format_detail_result(result)
                result_display.update_detail_result(detail_text)

            def show_batch_results(self, results: List[Dict]):
                """显示批量处理结果"""
                window = tk.Toplevel(self.root)
                window.title("批量处理结果")
                window.geometry("700x500")

                notebook = ttk.Notebook(window)
                notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

                # 创建汇总页面
                summary_frame = ttk.Frame(notebook)
                notebook.add(summary_frame, text="汇总")

                # 创建详细页面
                details_frame = ttk.Frame(notebook)
                notebook.add(details_frame, text="详细")

                # 显示汇总信息
                summary_text = tk.Text(summary_frame, wrap=tk.WORD)
                summary_text.pack(fill=tk.BOTH, expand=True)

                # 计算统计信息
                total = len(results)
                positive = sum(1 for r in results if r['result']['sentiment'] == 2)
                negative = sum(1 for r in results if r['result']['sentiment'] == 0)
                neutral = total - positive - negative

                summary = f"""批量处理结果汇总：

        总文件数: {total}
        积极: {positive} ({positive / total:.1%})
        消极: {negative} ({negative / total:.1%})
        中性: {neutral} ({neutral / total:.1%})
        """
                summary_text.insert(tk.END, summary)
                summary_text.config(state=tk.DISABLED)

                # 显示详细结果
                details_text = tk.Text(details_frame, wrap=tk.WORD)
                details_text.pack(fill=tk.BOTH, expand=True)

                for result in results:
                    details_text.insert(tk.END, f"\n文件: {result['file']}\n")
                    details_text.insert(tk.END, self.format_basic_result(result['result']))
                    details_text.insert(tk.END, "\n" + "=" * 50 + "\n")

                details_text.config(state=tk.DISABLED)

            def format_basic_result(self, result: dict) -> str:
                """格式化基础分析结果"""
                sentiment_map = {0: "消极", 1: "中性", 2: "积极"}
                basic_result = f"""分析结果：

        情感倾向: {sentiment_map.get(result['sentiment'], '未知')}
        置信度: {result['confidence']:.2%}
        积极概率: {result['positive_prob']:.2%}
        消极概率: {result['negative_prob']:.2%}
        """
                if 'text' in result:
                    basic_result += f"\n文本内容: {result['text']}"
                return basic_result

            def format_detail_result(self, result: dict) -> str:
                """格式化详细分析结果"""
                detail_result = "详细分析：\n\n"

                if 'emotion_weights' in result:
                    detail_result += "情感权重分析：\n"
                    for emotion in result['emotion_weights']:
                        detail_result += f"\n{emotion['emotion']}: {emotion['weight']:.2%}"
                        if emotion['keywords']:
                            detail_result += f"\n关键词: {', '.join(emotion['keywords'])}"
                        detail_result += "\n"

                if 'acoustic_features' in result:
                    detail_result += "\n声学特征分析：\n"
                    af = result['acoustic_features']
                    detail_result += f"\n音高: {af['pitch']:.2f}"
                    detail_result += f"\n音量: {af['volume']:.2f}"
                    detail_result += f"\n语速: {af['speed']:.2f}"
                    detail_result += f"\n能量: {af['energy']:.2f}"

                return detail_result

            def on_closing(self):
                """窗口关闭处理"""
                try:
                    if messagebox.askokcancel("退出", "确定要退出吗？"):
                        self.stop_server()
                        if self.analysis_session:
                            self.loop.run_until_complete(self.analysis_session.close())
                        self.root.destroy()
                        logger.info("Application closed")
                        sys.exit(0)
                except Exception as e:
                    logger.error(f"Error during shutdown: {str(e)}")
                    sys.exit(1)

            def run(self):
                """运行GUI"""
                try:
                    logger.info("Starting GUI main loop")
                    self.root.mainloop()
                except Exception as e:
                    logger.error(f"Error in GUI main loop: {str(e)}")
                    raise

            def ensure_correct_directory():
                """确保在正确的目录中运行"""
                try:
                    script_path = os.path.abspath(__file__)
                    script_dir = os.path.dirname(script_path)

                    logger.info(f"Script path: {script_path}")
                    logger.info(f"Changing directory to: {script_dir}")

                    # 改变工作目录到脚本所在位置
                    os.chdir(script_dir)

                    # 添加项目根目录到 Python 路径
                    if script_dir not in sys.path:
                        sys.path.insert(0, script_dir)
                        logger.info(f"Added {script_dir} to Python path")

                    # 确保日志目录存在
                    os.makedirs(log_dir, exist_ok=True)
                    logger.info(f"Ensured log directory exists: {log_dir}")

                except Exception as e:
                    logger.error(f"Error in ensure_correct_directory: {str(e)}")
                    raise

            def check_dependencies():
                """检查必要的依赖包"""
                required_packages = {
                    'tkinter': 'python3-tk',
                    'uvicorn': 'uvicorn',
                    'fastapi': 'fastapi',
                    'psutil': 'psutil',
                    'aiohttp': 'aiohttp',
                    'numpy': 'numpy'
                }

                missing_packages = []
                for package, pip_name in required_packages.items():
                    try:
                        __import__(package)
                        logger.info(f"Package {package} is available")
                    except ImportError:
                        missing_packages.append((package, pip_name))
                        logger.error(f"Missing required package: {package}")

                if missing_packages:
                    error_msg = "缺少必要的包:\n\n"
                    install_cmd = "pip install"

                    for package, pip_name in missing_packages:
                        if package == 'tkinter':
                            error_msg += f"{package}: 请安装 {pip_name}\n"
                        else:
                            install_cmd += f" {pip_name}"

                    error_msg += f"\n对于非tkinter包，请运行:\n{install_cmd}"

                    messagebox.showerror("依赖错误", error_msg)
                    return False

                return True

            def setup_exception_handling():
                """设置全局异常处理"""

                def handle_exception(exc_type, exc_value, exc_traceback):
                    if issubclass(exc_type, KeyboardInterrupt):
                        # 正常处理 Ctrl+C
                        sys.__excepthook__(exc_type, exc_value, exc_traceback)
                        return

                    logger.error("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))
                    error_msg = f"发生未捕获的错误:\n{exc_type.__name__}: {exc_value}"
                    messagebox.showerror("错误", error_msg)

                sys.excepthook = handle_exception

            def main():
                """主函数"""
                try:
                    logger.info("Application starting...")

                    # 设置异常处理
                    setup_exception_handling()

                    # 确保在正确的目录
                    ensure_correct_directory()

                    # 检查依赖
                    if not check_dependencies():
                        sys.exit(1)

                    # 运行GUI
                    gui = ServerGUI()
                    gui.run()

                except Exception as e:
                    logger.error(f"Application crashed: {str(e)}")
                    logger.error("Traceback:", exc_info=True)

                    # 如果GUI已经创建，使用messagebox
                    if 'gui' in locals() and hasattr(gui, 'root'):
                        messagebox.showerror("错误", f"程序崩溃: {str(e)}")
                    else:
                        print(f"Fatal error: {str(e)}")

                    sys.exit(1)

            if __name__ == "__main__":
                try:
                    main()
                except KeyboardInterrupt:
                    logger.info("Application terminated by user")
                    sys.exit(0)
                except Exception as e:
                    logger.critical(f"Fatal error: {str(e)}", exc_info=True)
                    sys.exit(1)