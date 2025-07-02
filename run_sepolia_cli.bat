@echo off
chcp 65001 >nul
echo 正在启动Sepolia测试网代币领取工具 - 命令行版本...
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.6或更高版本
    pause
    exit /b 1
)

REM 检查依赖是否安装
echo 检查依赖包...
pip show web3 >nul 2>&1
if errorlevel 1 (
    echo 正在安装依赖包...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖包安装失败
        pause
        exit /b 1
    )
)

echo.
echo ================================
echo Sepolia测试网代币领取工具 - CLI版本
echo 合约地址: 0x3edf60dd017ace33a0220f78741b5581c385a1ba
echo 网络: Sepolia测试网
echo ================================
echo.

echo 使用说明:
echo 1. 请先编辑 private_keys_example.txt 文件，添加您的私钥
echo 2. 重命名为 private_keys.txt
echo 3. 运行命令进行批量领取
echo.

echo 常用命令:
echo python sepolia_cli.py -k private_keys.txt              (使用默认配置)
echo python sepolia_cli.py -k private_keys.txt -t 10 -i 600 (10线程，600秒间隔)
echo python sepolia_cli.py -p YOUR_PRIVATE_KEY               (单个私钥)
echo python sepolia_cli.py --help                           (查看帮助)
echo.

REM 检查是否存在私钥文件
if exist private_keys.txt (
    echo 发现私钥文件 private_keys.txt
    echo.
    set /p choice="是否使用默认配置开始批量领取? (y/n): "
    if /i "%choice%"=="y" (
        echo.
        echo 启动批量领取...
        python sepolia_cli.py -k private_keys.txt
    ) else (
        echo.
        echo 请手动运行命令或查看帮助:
        echo python sepolia_cli.py --help
    )
) else (
    if exist private_keys_example.txt (
        echo 请先复制 private_keys_example.txt 为 private_keys.txt 并编辑添加您的私钥
    ) else (
        echo 未找到私钥文件，请创建 private_keys.txt 文件并添加您的私钥
    )
    echo.
    echo 或者使用单个私钥模式:
    echo python sepolia_cli.py -p YOUR_PRIVATE_KEY
)

echo.
echo 按任意键退出...
pause >nul 