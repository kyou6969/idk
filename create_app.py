import os
import sys
import shutil
import logging
from pathlib import Path
from datetime import datetime

# 配置日志
log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "app_creation.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class AppCreator:
    def __init__(self):
        self.current_dir = os.path.abspath(os.path.dirname(__file__))
        self.app_name = "SentimentAnalysis.app"
        self.app_path = os.path.expanduser(f'~/Applications/{self.app_name}')
        self.contents_path = os.path.join(self.app_path, 'Contents')
        self.macos_path = os.path.join(self.contents_path, 'MacOS')
        self.resources_path = os.path.join(self.contents_path, 'Resources')

    def create_directory_structure(self):
        """创建应用目录结构"""
        try:
            # 如果已存在，先删除
            if os.path.exists(self.app_path):
                logger.info(f"Removing existing application at {self.app_path}")
                shutil.rmtree(self.app_path)

            # 创建必要的目录
            os.makedirs(self.macos_path, exist_ok=True)
            os.makedirs(self.resources_path, exist_ok=True)
            logger.info(f"Created directory structure at {self.app_path}")

            # 创建日志目录
            log_dir = os.path.expanduser("~/Library/Logs/SentimentAnalysis")
            os.makedirs(log_dir, exist_ok=True)
            logger.info(f"Created log directory at {log_dir}")

            return True
        except Exception as e:
            logger.error(f"Failed to create directory structure: {str(e)}")
            return False

    def create_launcher_script(self):
        """创建启动脚本"""
        try:
            launcher_path = os.path.join(self.macos_path, 'launcher')
            with open(launcher_path, 'w') as f:
                f.write(f'''#!/bin/bash

# 设置环境变量
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8

# 设置日志路径
LOG_DIR="$HOME/Library/Logs/SentimentAnalysis"
LOG_FILE="$LOG_DIR/app.log"

# 创建日志目录
mkdir -p "$LOG_DIR"

# 记录启动时间和环境信息
echo "----------------------------------------" >> "$LOG_FILE"
echo "Starting application at $(date)" >> "$LOG_FILE"
echo "Python: {sys.executable}" >> "$LOG_FILE"
echo "Working directory: {self.current_dir}" >> "$LOG_FILE"
echo "PATH: $PATH" >> "$LOG_FILE"

# 确保在正确的目录中
cd "{self.current_dir}"

# 设置 Python 路径
export PYTHONPATH="{self.current_dir}"

# 检查 Python 环境
if ! command -v "{sys.executable}" &> /dev/null; then
    echo "ERROR: Python not found at {sys.executable}" >> "$LOG_FILE"
    osascript -e 'display alert "Python Not Found" message "Please install Python 3.8 or later."'
    exit 1
fi

# 检查必要的包是否安装
{sys.executable} -c "import tkinter; import fastapi; import uvicorn" 2>> "$LOG_FILE"
if [ $? -ne 0 ]; then
    echo "ERROR: Missing required packages" >> "$LOG_FILE"
    osascript -e 'display alert "Missing Dependencies" message "Please run: pip install fastapi uvicorn"'
    exit 1
fi

# 运行应用并记录输出
"{sys.executable}" "{os.path.join(self.current_dir, 'run.py')}" 2>> "$LOG_FILE" 1>> "$LOG_FILE"

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

    def create_info_plist(self):
        """创建 Info.plist 文件"""
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
    <string>1.0</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.10</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>CFBundleIconFile</key>
    <string>AppIcon</string>
    <key>CFBundleSupportedPlatforms</key>
    <array>
        <string>MacOSX</string>
    </array>
    <key>LSApplicationCategoryType</key>
    <string>public.app-category.developer-tools</string>
</dict>
</plist>''')
            logger.info(f"Created Info.plist at {plist_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create Info.plist: {str(e)}")
            return False

    def copy_icon(self):
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

    def verify_installation(self):
        """验证安装"""
        try:
            # 检查必要的文件和目录
            required_paths = [
                self.app_path,
                self.macos_path,
                self.resources_path,
                os.path.join(self.macos_path, 'launcher'),
                os.path.join(self.contents_path, 'Info.plist')
            ]

            for path in required_paths:
                if not os.path.exists(path):
                    logger.error(f"Missing required path: {path}")
                    return False

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

    def create_app(self):
        """创建应用"""
        try:
            logger.info("Starting application creation process...")

            # 创建目录结构
            if not self.create_directory_structure():
                raise Exception("Failed to create directory structure")

            # 创建启动脚本
            if not self.create_launcher_script():
                raise Exception("Failed to create launcher script")

            # 创建 Info.plist
            if not self.create_info_plist():
                raise Exception("Failed to create Info.plist")

            # 复制图标
            self.copy_icon()  # 图标是可选的，所以不检查返回值

            # 验证安装
            if not self.verify_installation():
                raise Exception("Installation verification failed")

            logger.info(f"Successfully created application at {self.app_path}")

            print("\n✅ 应用创建成功！")
            print(f"\n应用位置：{self.app_path}")
            print("\n使用方法：")
            print("1. 在 Finder 中打开 Applications 文件夹")
            print("2. 找到 SentimentAnalysis 应用")
            print("3. 双击启动，或拖到 Dock 栏以便日后快速启动")
            print("\n如果应用崩溃或出现问题：")
            print(f"请查看日志文件：{log_file}")

            return True

        except Exception as e:
            logger.error(f"Application creation failed: {str(e)}")
            print(f"\n❌ 创建应用失败：{str(e)}")
            print(f"详细错误信息请查看：{log_file}")
            return False


def main():
    """主函数"""
    try:
        # 检查操作系统
        if sys.platform != 'darwin':
            raise Exception("This script only works on macOS")

        # 检查 Python 版本
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8 or higher is required")

        # 创建应用
        creator = AppCreator()
        success = creator.create_app()

        sys.exit(0 if success else 1)

    except Exception as e:
        logger.error(f"Main function failed: {str(e)}")
        print(f"\n❌ 错误：{str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()