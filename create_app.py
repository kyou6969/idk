"""
情感分析系统应用打包脚本
用于创建macOS应用程序包(.app)

功能：
1. 创建应用程序包结构
2. 复制必要的源代码文件
3. 创建启动脚本
4. 配置应用程序信息
5. 设置日志系统
6. 验证安装完整性

使用方法：
python create_app.py

要求：
- macOS操作系统
- Python 3.8+
- 必要的依赖包已安装
"""

import os
import sys
import shutil
import json
import logging
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 检查操作系统
if sys.platform != 'darwin':
    print("❌ 错误：此脚本只能在 macOS 系统上运行")
    sys.exit(1)

# 检查Python版本
if sys.version_info < (3, 8):
    print("❌ 错误：需要 Python 3.8 或更高版本")
    sys.exit(1)

# 配置日志系统
log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, f"app_creation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 定义必要的依赖包
REQUIRED_PACKAGES = [
    'tkinter',
    'fastapi',
    'uvicorn',
    'psutil',
    'aiohttp',
    'numpy'
]

# 定义源代码文件
SOURCE_FILES = [
    'run.py',
    'app.py',
    'requirements.txt'
]

# 定义默认配置
DEFAULT_CONFIG = {
    'host': '127.0.0.1',
    'port': 8000,
    'auto_open_browser': True,
    'environment': 'production',
    'max_batch_size': 100,
    'analysis_timeout': 30,
    'enable_real_time': True,
    'audio_formats': ['wav', 'pcm', 'amr'],
    'sample_rates': ['8000', '16000', '44100', '48000']
}


def check_dependencies() -> bool:
    """检查必要的依赖包是否已安装"""
    missing_packages = []
    for package in REQUIRED_PACKAGES:
        try:
            if package == 'tkinter':
                import tkinter
            else:
                __import__(package)
            logger.info(f"✓ 找到依赖包: {package}")
        except ImportError:
            missing_packages.append(package)
            logger.error(f"✗ 缺少依赖包: {package}")

    if missing_packages:
        print("\n❌ 缺少以下依赖包:")
        for package in missing_packages:
            print(f"  - {package}")
        print("\n请使用以下命令安装依赖:")
        print("pip install " + " ".join(pkg for pkg in missing_packages if pkg != 'tkinter'))
        if 'tkinter' in missing_packages:
            print("\n对于 tkinter，请安装 python3-tk:")
            print("brew install python-tk@3.9  # 根据你的Python版本选择")
        return False

    return True


def check_source_files() -> bool:
    """检查必要的源代码文件是否存在"""
    missing_files = []
    current_dir = os.path.dirname(os.path.abspath(__file__))

    for file in SOURCE_FILES:
        file_path = os.path.join(current_dir, file)
        if not os.path.exists(file_path):
            missing_files.append(file)
            logger.error(f"✗ 缺少源文件: {file}")
        else:
            logger.info(f"✓ 找到源文件: {file}")

    if missing_files:
        print("\n❌ 缺少以下源文件:")
        for file in missing_files:
            print(f"  - {file}")
        return False

    return True


class AppCreator:
    """macOS应用程序包创建器"""

    def __init__(self):
        """初始化应用创建器"""
        self.current_dir = os.path.abspath(os.path.dirname(__file__))
        self.app_name = "SentimentAnalysis.app"
        self.app_path = os.path.expanduser(f'~/Applications/{self.app_name}')
        self.contents_path = os.path.join(self.app_path, 'Contents')
        self.macos_path = os.path.join(self.contents_path, 'MacOS')
        self.resources_path = os.path.join(self.contents_path, 'Resources')
        self.python_path = os.path.join(self.resources_path, 'python')

        # 记录开始时间
        self.start_time = datetime.now()
        logger.info(f"Initializing AppCreator for {self.app_name}")

    def create_directory_structure(self) -> bool:
        """创建应用程序包目录结构"""
        try:
            # 如果已存在，先删除
            if os.path.exists(self.app_path):
                logger.info(f"Removing existing application at {self.app_path}")
                shutil.rmtree(self.app_path)

            # 创建必要的目录
            os.makedirs(self.macos_path, exist_ok=True)
            os.makedirs(self.resources_path, exist_ok=True)
            os.makedirs(self.python_path, exist_ok=True)

            # 创建日志目录
            app_log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
            os.makedirs(app_log_dir, exist_ok=True)

            logger.info("Created directory structure successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory structure: {str(e)}")
            return False

    def copy_source_files(self) -> bool:
        """复制源代码文件到应用程序包"""
        try:
            for file in SOURCE_FILES:
                src = os.path.join(self.current_dir, file)
                dst = os.path.join(self.python_path, file)
                if os.path.exists(src):
                    shutil.copy2(src, dst)
                    logger.info(f"Copied {file} to {dst}")
                else:
                    logger.error(f"Source file not found: {src}")
                    return False

            # 创建默认配置文件
            config_path = os.path.join(self.python_path, 'server_config.json')
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
            logger.info(f"Created default config at {config_path}")

            return True
        except Exception as e:
            logger.error(f"Failed to copy source files: {str(e)}")
            return False

    def create_launcher_script(self) -> bool:
        """创建启动脚本"""
        try:
            launcher_path = os.path.join(self.macos_path, 'launcher')
            with open(launcher_path, 'w') as f:
                f.write(f'''#!/bin/bash

# 设置环境变量
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# 设置工作目录
APP_DIR="{self.python_path}"
cd "$APP_DIR"

# 设置日志路径
LOG_DIR="$HOME/Library/Logs/SentimentAnalysis"
LOG_FILE="$LOG_DIR/app_$(date +%Y%m%d_%H%M%S).log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录启动时间和环境信息
echo "----------------------------------------" >> "$LOG_FILE"
echo "Starting application at $(date)" >> "$LOG_FILE"
echo "Python: {sys.executable}" >> "$LOG_FILE"
echo "Working directory: $APP_DIR" >> "$LOG_FILE"
echo "PATH: $PATH" >> "$LOG_FILE"

# 检查Python环境
if ! command -v "{sys.executable}" &> /dev/null; then
    osascript -e 'display alert "Python Not Found" message "Please install Python 3.8 or later."'
    exit 1
fi

# 检查依赖包
REQUIRED_PACKAGES="tkinter fastapi uvicorn psutil aiohttp numpy"
for package in $REQUIRED_PACKAGES; do
    {sys.executable} -c "import $package" 2>> "$LOG_FILE"
    if [ $? -ne 0 ]; then
        osascript -e 'display alert "Missing Package" message "Please install required package: '$package'"'
        exit 1
    fi
done

# 运行应用
"{sys.executable}" "run.py" 2>> "$LOG_FILE" 1>> "$LOG_FILE"

# 检查退出状态
EXIT_CODE=$?
if [ $EXIT_CODE -ne 0 ]; then
    echo "Application crashed with exit code $EXIT_CODE" >> "$LOG_FILE"
    osascript -e 'display alert "Application Error" message "The application has crashed. Please check the logs for details."'
fi
''')
            # 设置执行权限
            os.chmod(launcher_path, 0o755)
            logger.info(f"Created launcher script at {launcher_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create launcher script: {str(e)}")
            return False

    def create_info_plist(self) -> bool:
        """创建Info.plist文件"""
        try:
            plist_path = os.path.join(self.contents_path, 'Info.plist')
            with open(plist_path, 'w') as f:
                f.write(f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>launcher</string>
    <key>CFBundleIdentifier</key>
    <string>com.example.sentimentanalysis</string>
    <key>CFBundleName</key>
    <string>SentimentAnalysis</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
    <key>NSAppTransportSecurity</key>
    <dict>
        <key>NSAllowsArbitraryLoads</key>
        <true/>
    </dict>
</dict>
</plist>''')
            logger.info(f"Created Info.plist at {plist_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Info.plist: {str(e)}")
            return False

    def copy_icon(self) -> bool:
        """复制应用图标"""
        try:
            icon_source = os.path.join(self.current_dir, 'app/statics/images/AppIcon.icns')
            if os.path.exists(icon_source):
                icon_dest = os.path.join(self.resources_path, 'AppIcon.icns')
                shutil.copy2(icon_source, icon_dest)
                logger.info(f"Copied app icon to {icon_dest}")
                return True
            else:
                logger.warning(f"Icon file not found at {icon_source}")
                return False
        except Exception as e:
            logger.error(f"Failed to copy icon: {str(e)}")
            return False

    def verify_installation(self) -> bool:
        """验证安装的完整性"""
        try:
            required_paths = [
                self.app_path,
                self.macos_path,
                self.resources_path,
                self.python_path,
                os.path.join(self.macos_path, 'launcher'),
                os.path.join(self.contents_path, 'Info.plist'),
                os.path.join(self.python_path, 'run.py'),
                os.path.join(self.python_path, 'app.py'),
                os.path.join(self.python_path, 'server_config.json')
            ]

            for path in required_paths:
                if not os.path.exists(path):
                    logger.error(f"Missing required path: {path}")
                    return False
                logger.info(f"Verified path: {path}")

            # 检查启动脚本权限
            launcher_path = os.path.join(self.macos_path, 'launcher')
            if not os.access(launcher_path, os.X_OK):
                logger.error(f"Launcher script is not executable: {launcher_path}")
                return False

            logger.info("Installation verification completed successfully")
            return True
        except Exception as e:
            logger.error(f"Installation verification failed: {str(e)}")
            return False

    def create_app(self) -> bool:
        """创建应用程序包的主函数"""
        try:
            logger.info("Starting application creation process...")

            # 检查依赖
            if not check_dependencies():
                raise Exception("Missing required dependencies")

            # 检查源文件
            if not check_source_files():
                raise Exception("Missing required source files")

            # 创建目录结构
            if not self.create_directory_structure():
                raise Exception("Failed to create directory structure")

            # 复制源代码文件
            if not self.copy_source_files():
                raise Exception("Failed to copy source files")

            # 创建启动脚本
            if not self.create_launcher_script():
                raise Exception("Failed to create launcher script")

            # 创建 Info.plist
            if not self.create_info_plist():
                raise Exception("Failed to create Info.plist")

            # 复制图标（可选）
            self.copy_icon()

            # 验证安装
            if not self.verify_installation():
                raise Exception("Installation verification failed")

            # 计算执行时间
            duration = datetime.now() - self.start_time
            logger.info(f"Application creation completed in {duration.total_seconds():.2f} seconds")

            print("\n✅ 应用创建成功！")
            print(f"\n应用位置：{self.app_path}")
            print(f"\n配置文件：{os.path.join(self.python_path, 'server_config.json')}")
            print("\n使用方法：")
            print("1. 在 Finder 中打开 Applications 文件夹")
            print("2. 找到 SentimentAnalysis 应用")
            print("3. 双击启动，或拖到 Dock 栏以便日后快速启动")
            print("\n如果应用崩溃或出现问题：")
            print(f"请查看日志文件：~/Library/Logs/SentimentAnalysis/")

            return True

        except Exception as e:
            logger.error(f"Application creation failed: {str(e)}")
            print(f"\n❌ 创建应用失败：{str(e)}")
            print(f"详细错误信息请查看：{log_file}")
            return False


def main():
    """主函数"""
    print("\n📦 开始创建情感分析系统应用...")

    try:
        creator = AppCreator()
        success = creator.create_app()
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n⚠️ 用户中断了应用创建过程")
        logger.info("Application creation interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误：{str(e)}")
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()