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
import requests
from datetime import datetime
import signal

# 配置日志
log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class ServerConfig:
    def __init__(self):
        self.config_file = 'server_config.json'
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        default_config = {
            'host': '127.0.0.1',
            'port': 8000,
            'auto_open_browser': True,
            'environment': 'development',
            'last_run': None
        }

        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    self.config = json.load(f)
            else:
                self.config = default_config
                self.save_config()
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config = default_config

    def save_config(self):
        """保存配置到文件"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving config: {e}")


class ServerGUI:
    def __init__(self):
        try:
            self.config = ServerConfig()
            self.server_thread = None
            self.should_stop = False

            # 创建主窗口
            self.root = tk.Tk()
            self.root.title("情感分析服务器控制面板")
            self.root.geometry("800x600")

            # 状态变量
            self.server_status = tk.StringVar(value="已停止")
            self.port = tk.StringVar(value=str(self.config.config['port']))

            # 设置UI
            self.setup_ui()

            # 绑定关闭事件
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            logger.info("GUI initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing GUI: {str(e)}")
            raise Exception(f"GUI initialization failed: {str(e)}")

    def setup_ui(self):
        """设置UI界面"""
        try:
            # 创建主框架
            main_frame = ttk.Frame(self.root, padding="10")
            main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 服务器控制区
            control_frame = ttk.LabelFrame(main_frame, text="服务器控制", padding="10")
            control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E))

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

            # 打开浏览器按钮
            self.browser_btn = ttk.Button(
                control_frame,
                text="打开浏览器",
                command=self.open_browser
            )
            self.browser_btn.grid(row=0, column=2, padx=5)

            # 配置区
            config_frame = ttk.LabelFrame(main_frame, text="配置", padding="10")
            config_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E))

            # 端口配置
            ttk.Label(config_frame, text="端口:").grid(row=0, column=0)
            port_entry = ttk.Entry(config_frame, textvariable=self.port)
            port_entry.grid(row=0, column=1)

            # 自动打开浏览器选项
            self.auto_open_var = tk.BooleanVar(
                value=self.config.config['auto_open_browser']
            )
            auto_open_check = ttk.Checkbutton(
                config_frame,
                text="自动打开浏览器",
                variable=self.auto_open_var,
                command=self.save_auto_open
            )
            auto_open_check.grid(row=0, column=2)

            # 状态区
            status_frame = ttk.LabelFrame(main_frame, text="状态", padding="10")
            status_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E))

            ttk.Label(
                status_frame,
                textvariable=self.server_status
            ).grid(row=0, column=0)

            # 语音分析区
            audio_frame = ttk.LabelFrame(main_frame, text="语音分析", padding="10")
            audio_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))

            # 选择文件按钮
            self.select_file_btn = ttk.Button(
                audio_frame,
                text="选择语音文件",
                command=self.select_audio_file
            )
            self.select_file_btn.grid(row=0, column=0, padx=5)

            # 显示选中的文件名
            self.file_label = ttk.Label(audio_frame, text="未选择文件")
            self.file_label.grid(row=0, column=1, padx=5)

            # 音频格式选择
            ttk.Label(audio_frame, text="格式:").grid(row=0, column=2)
            self.format_var = tk.StringVar(value="wav")
            format_combo = ttk.Combobox(
                audio_frame,
                textvariable=self.format_var,
                values=["wav", "pcm", "amr"],
                state="readonly",
                width=10
            )
            format_combo.grid(row=0, column=3, padx=5)

            # 采样率选择
            ttk.Label(audio_frame, text="采样率:").grid(row=0, column=4)
            self.rate_var = tk.StringVar(value="16000")
            rate_combo = ttk.Combobox(
                audio_frame,
                textvariable=self.rate_var,
                values=["8000", "16000", "44100", "48000"],
                state="readonly",
                width=10
            )
            rate_combo.grid(row=0, column=5, padx=5)

            # 分析按钮
            self.analyze_btn = ttk.Button(
                audio_frame,
                text="分析语音",
                command=self.analyze_audio,
                state=tk.DISABLED
            )
            self.analyze_btn.grid(row=0, column=6, padx=5)

            # 日志区
            log_frame = ttk.LabelFrame(main_frame, text="日志", padding="10")
            log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))

            self.log_text = tk.Text(log_frame, height=10, width=80)
            self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

            # 滚动条
            scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
            scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
            self.log_text['yscrollcommand'] = scrollbar.set

            # 设置网格权重
            main_frame.columnconfigure(0, weight=1)
            main_frame.rowconfigure(4, weight=1)
            log_frame.columnconfigure(0, weight=1)
            log_frame.rowconfigure(0, weight=1)

            logger.info("UI setup completed")

        except Exception as e:
            logger.error(f"Error in setup_ui: {str(e)}")
            raise

    def log_message(self, message):
        """添加日志消息"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.log_text.see(tk.END)
            logger.info(message)
        except Exception as e:
            logger.error(f"Error in log_message: {str(e)}")

    def save_auto_open(self):
        """保存自动打开浏览器设置"""
        try:
            self.config.config['auto_open_browser'] = self.auto_open_var.get()
            self.config.save_config()
            logger.info("Auto-open browser setting saved")
        except Exception as e:
            logger.error(f"Error saving auto-open setting: {str(e)}")

    def start_server(self):
        """启动服务器"""
        try:
            port = int(self.port.get())
            if not (1024 <= port <= 65535):
                raise ValueError("端口号必须在1024-65535之间")

            self.config.config['port'] = port
            self.config.save_config()

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
            error_msg = f"启动失败: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.log_message(error_msg)

    def stop_server(self):
        """停止服务器"""
        try:
            self.should_stop = True
            self.server_status.set("已停止")
            self.start_btn['state'] = tk.NORMAL
            self.stop_btn['state'] = tk.DISABLED
            self.log_message("服务器已停止")

            # 查找并关闭服务器进程
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'uvicorn' in cmdline[0].lower():
                        proc.send_signal(signal.SIGTERM)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            logger.info("Server stopped")

        except Exception as e:
            error_msg = f"停止服务器时出错: {str(e)}"
            logger.error(error_msg)
            self.log_message(error_msg)

    def run_server(self, host, port):
        """运行服务器"""
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
            error_msg = f"服务器运行错误: {str(e)}"
            logger.error(error_msg)
            self.log_message(error_msg)
            self.server_status.set("错误")
            self.start_btn['state'] = tk.NORMAL
            self.stop_btn['state'] = tk.DISABLED

    def open_browser(self):
        """打开浏览器"""
        try:
            port = int(self.port.get())
            url = f"http://{self.config.config['host']}:{port}/docs"
            webbrowser.open(url)
            self.log_message(f"已打开浏览器: {url}")
        except Exception as e:
            error_msg = f"无法打开浏览器: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.log_message(error_msg)

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
            error_msg = f"选择文件失败: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.log_message(error_msg)

    def analyze_audio(self):
        """分析音频文件"""
        if not hasattr(self, 'audio_file_path'):
            messagebox.showerror("错误", "请先选择音频文件")
            return

        try:
            self.analyze_btn['state'] = tk.DISABLED
            self.log_message("开始分析语音...")

            # 读取音频文件
            with open(self.audio_file_path, 'rb') as f:
                files = {
                    'file': (
                        os.path.basename(self.audio_file_path),
                        f,
                        f'audio/{self.format_var.get()}'
                    )
                }

                # 发送请求
                response = requests.post(
                    f"http://{self.config.config['host']}:{self.port.get()}/analyze/audio",
                    files=files,
                    data={
                        'format': self.format_var.get(),
                        'rate': self.rate_var.get()
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    # 显示结果
                    self.show_audio_analysis_result(result)
                else:
                    raise Exception(f"分析失败: {response.text}")

        except Exception as e:
            error_msg = f"分析错误: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.log_message(error_msg)
        finally:
            self.analyze_btn['state'] = tk.NORMAL

    def show_audio_analysis_result(self, result):
        """显示语音分析结果"""
        try:
            # 创建结果窗口
            result_window = tk.Toplevel(self.root)
            result_window.title("语音分析结果")
            result_window.geometry("500x400")

            # 创建结果显示区域
            result_text = tk.Text(result_window, wrap=tk.WORD, width=60, height=20)
            result_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

            # 格式化结果
            result_str = f"""语音分析结果：

情感极性: {"积极" if result['sentiment'] == 2 else "中性" if result['sentiment'] == 1 else "消极"}
置信度: {result['confidence']:.2%}
积极概率: {result['positive_prob']:.2%}
消极概率: {result['negative_prob']:.2%}

声学特征：
音高: {result['acoustic_features']['pitch']:.2f}
音量: {result['acoustic_features']['volume']:.2f}
语速: {result['acoustic_features']['speed']:.2f}
能量: {result['acoustic_features']['energy']:.2f}
"""

            if 'emotion_weights' in result:
                result_str += "\n情感权重："
                for emotion in result['emotion_weights']:
                    result_str += f"\n{emotion['emotion']}: {emotion['weight']:.2%}"
                    if emotion['keywords']:
                        result_str += f" (关键词: {', '.join(emotion['keywords'])})"

            result_text.insert(tk.END, result_str)
            result_text.config(state=tk.DISABLED)

            self.log_message("语音分析完成")
        except Exception as e:
            error_msg = f"显示结果失败: {str(e)}"
            logger.error(error_msg)
            messagebox.showerror("错误", error_msg)
            self.log_message(error_msg)

    def on_closing(self):
        """窗口关闭事件处理"""
        try:
            if messagebox.askokcancel("退出", "确定要退出吗？"):
                self.stop_server()
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
    except Exception as e:
        logger.error(f"Error in ensure_correct_directory: {str(e)}")
        raise


def main():
    """主函数"""
    try:
        logger.info("Application starting...")

        # 确保在正确的目录
        ensure_correct_directory()

        # 检查必要的包是否已安装
        required_packages = ['tkinter', 'uvicorn', 'fastapi', 'psutil']
        for package in required_packages:
            try:
                __import__(package)
            except ImportError:
                error_msg = f"缺少必要的包: {package}"
                logger.error(error_msg)
                if package == 'tkinter':
                    messagebox.showerror("错误", f"{error_msg}\n请安装 python3-tk")
                else:
                    messagebox.showerror("错误", f"{error_msg}\n请运行: pip install {package}")
                sys.exit(1)

        # 运行GUI
        gui = ServerGUI()
        gui.run()

    except Exception as e:
        logger.error(f"Application crashed: {str(e)}")
        logger.error("Traceback:", exc_info=True)
        messagebox.showerror("错误", f"程序崩溃: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()