# Zama测试网代币领取工具 - 命令行版本

这是一个基于命令行的Zama测试网代币自动领取工具，支持批量私钥处理和多线程并发领取。

## 🚀 功能特性

- ✅ **批量私钥处理**: 从文件读取多个私钥，同时处理多个钱包
- ✅ **多线程并发**: 支持多线程同时领取，提高效率
- ✅ **智能错误处理**: 自动识别常见错误并提供解决建议
- ✅ **实时状态监控**: 显示成功/失败统计和实时进度
- ✅ **安全信号处理**: 支持Ctrl+C安全退出
- ✅ **详细日志记录**: 同时输出到控制台和日志文件
- ✅ **余额检查**: 自动检查每个钱包的ETH余额
- ✅ **可配置参数**: 支持自定义Gas价格、线程数、间隔时间等

## 📦 安装依赖

```bash
pip install -r requirements.txt
```

## 📝 使用方法

### 1. 快速开始

```bash
# 运行启动脚本（Windows）
run_sepolia_cli.bat

# 或者直接运行Python脚本
python sepolia_cli.py --help
```

### 2. 批量领取模式

```bash
# 使用默认配置批量领取
python sepolia_cli.py -k private_keys.txt

# 自定义线程数和间隔时间
python sepolia_cli.py -k private_keys.txt -t 10 -i 600

# 限制每个钱包的最大尝试次数
python sepolia_cli.py -k private_keys.txt -t 5 -i 300 -a 3

# 使用自定义配置文件
python sepolia_cli.py -k private_keys.txt -c custom_config.json
```

### 3. 单钱包模式

```bash
# 使用单个私钥领取
python sepolia_cli.py -p YOUR_PRIVATE_KEY_HERE
```

### 4. 高级参数

```bash
# 自定义Gas参数
python sepolia_cli.py -k private_keys.txt --gas-price 25 --gas-limit 120000

# 完整参数示例
python sepolia_cli.py -k private_keys.txt -t 8 -i 300 -a 5 --gas-price 30
```

## 📄 私钥文件格式

创建一个文本文件（如`private_keys.txt`），每行一个私钥：

```
# 我的钱包1
1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef

# 我的钱包2
abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890

# 我的钱包3
fedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321
```

**注意事项：**
- 每行只能包含一个私钥
- 私钥必须是64位十六进制字符串
- 不要包含`0x`前缀
- 空行和以`#`开头的行会被忽略
- 请妥善保管此文件，不要泄露给他人

## ⚙️ 配置文件

默认配置文件`sepolia_config.json`：

```json
{
  "rpc_url": "https://rpc.sepolia.ethpandaops.io",
  "contract_address": "0x3edf60dd017ace33a0220f78741b5581c385a1ba",
  "gas_price": 20,
  "gas_limit": 100000,
  "interval": 300
}
```

## 📊 命令行参数

| 参数 | 简写 | 说明 | 默认值 |
|-----|-----|------|-------|
| `--keys-file` | `-k` | 私钥文件路径 | - |
| `--private-key` | `-p` | 单个私钥 | - |
| `--config` | `-c` | 配置文件路径 | `sepolia_config.json` |
| `--threads` | `-t` | 最大线程数 | `5` |
| `--interval` | `-i` | 领取间隔（秒） | `300` |
| `--attempts` | `-a` | 每个钱包最大尝试次数 | 无限制 |
| `--gas-price` | - | Gas价格（Gwei） | `20` |
| `--gas-limit` | - | Gas限制 | `100000` |
| `--help` | `-h` | 显示帮助信息 | - |

## 📋 使用示例

### 示例1：简单批量领取
```bash
python sepolia_cli.py -k private_keys.txt
```

### 示例2：高并发短间隔
```bash
python sepolia_cli.py -k private_keys.txt -t 20 -i 120
```

### 示例3：保守模式（每个钱包只尝试一次）
```bash
python sepolia_cli.py -k private_keys.txt -t 3 -i 600 -a 1
```

### 示例4：高Gas价格快速确认
```bash
python sepolia_cli.py -k private_keys.txt --gas-price 50 --gas-limit 150000
```

## 📈 监控和日志

- **实时监控**: 每30秒显示一次统计信息
- **控制台输出**: 实时显示每个钱包的领取进度
- **日志文件**: 所有记录自动保存到`sepolia_claimer.log`
- **交易链接**: 成功的交易会显示Etherscan链接

## 🔧 故障排除

### 常见错误及解决方案：

1. **ETH余额不足**
   - 确保每个钱包有足够的ETH支付Gas费用
   - 建议每个钱包至少有0.001 ETH

2. **网络连接问题**
   - 检查网络连接
   - 尝试更换RPC节点

3. **私钥格式错误**
   - 确保私钥是64位十六进制字符串
   - 不要包含0x前缀

4. **Gas价格太低**
   - 增加`--gas-price`参数值
   - 查看当前网络Gas价格

5. **并发限制**
   - 降低线程数量
   - 增加间隔时间

## 🚨 安全提醒

- **私钥安全**: 请妥善保管私钥文件，不要上传到公共平台
- **余额监控**: 定期检查钱包余额，防止意外损失

如果遇到问题，请检查：
1. Python版本是否为3.6+
2. 依赖包是否已正确安装
3. 网络连接是否正常
4. 私钥格式是否正确
5. 配置文件是否有效

## 🔄 版本对比

| 功能 | GUI版本 | CLI版本 |
|------|---------|---------|
| 界面 | 图形界面 | 命令行 |
| 批量处理 | ❌ | ✅ |
| 多线程 | ❌ | ✅ |
| 私钥文件 | ❌ | ✅ |
| 参数配置 | 界面设置 | 命令行参数 |
| 日志记录 | 界面显示 | 文件+控制台 |
| 自动化 | 手动操作 | 完全自动化 |