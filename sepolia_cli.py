#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import time
import threading
import concurrent.futures
import os
import sys
from datetime import datetime
from web3 import Web3
from eth_account import Account
import signal
import queue
import logging
from threading import Lock

class SepoliaClaimerCLI:
    def __init__(self, config_file="sepolia_config.json"):
        """初始化命令行版本的领取工具"""
        # 先设置日志
        self.setup_logging()
        
        # 然后加载配置
        self.config = self.load_config(config_file)
        self.web3 = None
        self.stop_event = threading.Event()
        self.stats_lock = Lock()
        self.stats = {
            'total_wallets': 0,
            'success_count': 0,
            'fail_count': 0,
            'running_count': 0
        }
        
    def setup_logging(self):
        """设置日志记录"""
        # 创建日志格式器
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        file_handler = logging.FileHandler('sepolia_claimer.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        self.logger = logging.getLogger('SepoliaClaimer')
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
    def load_config(self, config_file):
        """加载配置文件"""
        default_config = {
            "rpc_url": "https://rpc.sepolia.ethpandaops.io",
            "contract_address": "0x3edf60dd017ace33a0220f78741b5581c385a1ba",
            "gas_price": 20,
            "gas_limit": 100000,
            "interval": 3
        }
        
        try:
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    default_config.update(config)
                    self.logger.info(f"✅ 配置已从 {config_file} 加载")
            else:
                self.logger.warning(f"⚠️ 配置文件 {config_file} 不存在，使用默认配置")
        except Exception as e:
            self.logger.error(f"❌ 加载配置失败: {str(e)}")
        
        return default_config
        
    def connect_network(self):
        """连接到Sepolia网络"""
        try:
            self.logger.info("🔗 正在连接Sepolia测试网...")
            
            self.web3 = Web3(Web3.HTTPProvider(self.config['rpc_url']))
            
            if self.web3.is_connected():
                chain_id = self.web3.eth.chain_id
                if chain_id == 11155111:  # Sepolia chain ID
                    self.logger.info("✅ 成功连接到Sepolia测试网")
                    return True
                else:
                    raise Exception(f"错误的网络ID: {chain_id}, 应该是11155111 (Sepolia)")
            else:
                raise Exception("无法连接到网络")
                
        except Exception as e:
            self.logger.error(f"❌ 网络连接失败: {str(e)}")
            return False
    
    def validate_private_key(self, private_key):
        """验证私钥格式"""
        try:
            private_key = private_key.strip()
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            if len(private_key) != 64 or not all(c in '0123456789abcdefABCDEF' for c in private_key):
                return False, "私钥必须是64位十六进制字符串"
            
            account = Account.from_key('0x' + private_key)
            return True, account.address
            
        except Exception as e:
            return False, f"私钥验证失败: {str(e)}"
    
    def load_private_keys(self, keys_file):
        """从文件加载私钥列表"""
        try:
            private_keys = []
            
            if not os.path.exists(keys_file):
                self.logger.error(f"❌ 私钥文件 {keys_file} 不存在")
                return []
            
            with open(keys_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if not line or line.startswith('#'):  # 跳过空行和注释
                    continue
                
                is_valid, result = self.validate_private_key(line)
                if is_valid:
                    private_keys.append({
                        'private_key': line,
                        'address': result,
                        'line_num': i
                    })
                    self.logger.info(f"✅ 私钥 #{i} 验证成功: {result[:10]}...{result[-8:]}")
                else:
                    self.logger.warning(f"⚠️ 私钥 #{i} 验证失败: {result}")
            
            self.logger.info(f"📁 成功加载 {len(private_keys)} 个有效私钥")
            return private_keys
            
        except Exception as e:
            self.logger.error(f"❌ 加载私钥文件失败: {str(e)}")
            return []
    
    def check_balance(self, address):
        """检查ETH余额"""
        try:
            balance_wei = self.web3.eth.get_balance(Web3.to_checksum_address(address))
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            return balance_eth
        except Exception as e:
            self.logger.error(f"❌ 查询余额失败 {address}: {str(e)}")
            return 0
    
    def claim_token(self, private_key, address, wallet_id):
        """执行代币领取"""
        try:
            # 处理私钥（移除可能的0x前缀）
            if private_key.startswith('0x'):
                private_key = private_key[2:]
            
            account = Account.from_key('0x' + private_key)
            
            # 构建智能合约调用数据
            # 方法ID: 0x6a627842 + 钱包地址参数（32字节）
            wallet_address = account.address[2:].lower()  # 移除0x前缀
            wallet_param = wallet_address.zfill(64)  # 补足64位（32字节）
            call_data = '0x6a627842' + wallet_param
            
            # 构建交易
            transaction = {
                'to': Web3.to_checksum_address(self.config['contract_address']),
                'value': 0,
                'gas': self.config['gas_limit'],
                'gasPrice': self.web3.to_wei(self.config['gas_price'], 'gwei'),
                'nonce': self.web3.eth.get_transaction_count(account.address),
                'data': call_data,
                'chainId': 11155111  # Sepolia chain ID
            }
            
            self.logger.info(f"🚀 [{wallet_id}] 开始领取 {address[:10]}...{address[-8:]}")
            
            # 签名交易
            signed_txn = self.web3.eth.account.sign_transaction(transaction, '0x' + private_key)
            
            # 发送交易
            tx_hash = self.web3.eth.send_raw_transaction(signed_txn.rawTransaction)
            tx_hash_hex = tx_hash.hex()
            
            self.logger.info(f"📤 [{wallet_id}] 交易已发送: {tx_hash_hex}")
            
            # 等待交易确认
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash, timeout=300)
            
            with self.stats_lock:
                if receipt.status == 1:
                    self.stats['success_count'] += 1
                    self.logger.info(f"✅ [{wallet_id}] 代币领取成功! Gas使用: {receipt.gasUsed}")
                    self.logger.info(f"🔗 [{wallet_id}] 交易链接: https://sepolia.etherscan.io/tx/{tx_hash_hex}")
                    return True
                else:
                    self.stats['fail_count'] += 1
                    self.logger.error(f"❌ [{wallet_id}] 交易执行失败")
                    return False
                    
        except Exception as e:
            with self.stats_lock:
                self.stats['fail_count'] += 1
            
            error_msg = str(e)
            # 解析常见错误
            if "insufficient funds" in error_msg.lower():
                error_msg = "ETH余额不足，无法支付Gas费用"
            elif "nonce too low" in error_msg.lower():
                error_msg = "Nonce值过低，请稍后重试"
            elif "replacement transaction underpriced" in error_msg.lower():
                error_msg = "交易费用过低，请提高Gas价格"
            
            self.logger.error(f"❌ [{wallet_id}] 领取失败: {error_msg}")
            return False
    
    def wallet_worker(self, wallet_info, interval, max_attempts=None):
        """单个钱包的工作线程"""
        wallet_id = f"W{wallet_info['line_num']:03d}"
        private_key = wallet_info['private_key']
        address = wallet_info['address']
        attempts = 0
        
        with self.stats_lock:
            self.stats['running_count'] += 1
        
        try:
            self.logger.info(f"🎯 [{wallet_id}] 开始工作线程: {address[:10]}...{address[-8:]}")
            
            # 检查初始余额
            balance = self.check_balance(address)
            self.logger.info(f"💰 [{wallet_id}] ETH余额: {balance:.6f} ETH")
            
            if balance < 0.001:  # 最小Gas费用检查
                self.logger.warning(f"⚠️ [{wallet_id}] ETH余额过低，可能无法支付Gas费用")
            
            while not self.stop_event.is_set():
                if max_attempts and attempts >= max_attempts:
                    self.logger.info(f"🏁 [{wallet_id}] 达到最大尝试次数 {max_attempts}")
                    break
                
                attempts += 1
                self.logger.info(f"🔄 [{wallet_id}] 第 {attempts} 次尝试领取")
                
                success = self.claim_token(private_key, address, wallet_id)
                
                if success:
                    self.logger.info(f"🎉 [{wallet_id}] 领取成功！")
                else:
                    self.logger.info(f"😔 [{wallet_id}] 领取失败，将稍后重试")
                
                # 等待间隔时间（可中断）
                for _ in range(interval):
                    if self.stop_event.is_set():
                        break
                    time.sleep(1)
                
        except Exception as e:
            self.logger.error(f"❌ [{wallet_id}] 工作线程异常: {str(e)}")
        finally:
            with self.stats_lock:
                self.stats['running_count'] -= 1
            self.logger.info(f"🔚 [{wallet_id}] 工作线程结束")
    
    def print_stats(self):
        """打印统计信息"""
        with self.stats_lock:
            stats = self.stats.copy()
        
        success_rate = 0
        if stats['success_count'] + stats['fail_count'] > 0:
            success_rate = stats['success_count'] / (stats['success_count'] + stats['fail_count']) * 100
        
        print("\n" + "="*60)
        print("📊 领取统计信息")
        print("="*60)
        print(f"总钱包数量: {stats['total_wallets']}")
        print(f"运行中钱包: {stats['running_count']}")
        print(f"成功次数: {stats['success_count']}")
        print(f"失败次数: {stats['fail_count']}")
        print(f"成功率: {success_rate:.1f}%")
        print("="*60)
    
    def stats_monitor(self, interval=30):
        """统计信息监控线程"""
        while not self.stop_event.is_set():
            time.sleep(interval)
            if not self.stop_event.is_set():
                self.print_stats()
    
    def start_batch_claiming(self, private_keys, max_threads=5, interval=300, max_attempts=None):
        """开始批量领取"""
        if not private_keys:
            self.logger.error("❌ 没有有效的私钥")
            return
        
        with self.stats_lock:
            self.stats['total_wallets'] = len(private_keys)
        
        self.logger.info(f"🚀 开始批量领取，共 {len(private_keys)} 个钱包")
        self.logger.info(f"⚙️ 配置: 最大线程数={max_threads}, 间隔={interval}秒")
        
        if max_attempts:
            self.logger.info(f"⚙️ 每个钱包最多尝试 {max_attempts} 次")
        
        # 启动统计监控线程
        stats_thread = threading.Thread(target=self.stats_monitor, daemon=True)
        stats_thread.start()
        
        # 使用线程池执行
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_threads) as executor:
            # 提交所有任务
            futures = [
                executor.submit(self.wallet_worker, wallet_info, interval, max_attempts)
                for wallet_info in private_keys
            ]
            
            try:
                # 等待所有任务完成或被中断
                for future in concurrent.futures.as_completed(futures):
                    if self.stop_event.is_set():
                        break
                    try:
                        future.result()
                    except Exception as e:
                        self.logger.error(f"❌ 线程执行异常: {str(e)}")
                        
            except KeyboardInterrupt:
                self.logger.info("🛑 收到中断信号，正在停止...")
                self.stop_event.set()
        
        self.logger.info("🏁 批量领取结束")
        self.print_stats()

def signal_handler(signum, frame, claimer):
    """信号处理器"""
    print("\n🛑 收到停止信号，正在安全退出...")
    claimer.stop_event.set()
    claimer.print_stats()
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(
        description="Zama测试网代币领取工具 - 命令行版本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  %(prog)s -k private_keys.txt                    # 使用默认配置批量领取
  %(prog)s -k keys.txt -t 10 -i 600              # 10线程，600秒间隔
  %(prog)s -k keys.txt -t 5 -i 300 -a 3          # 每个钱包最多尝试3次
  %(prog)s -p YOUR_PRIVATE_KEY                    # 单个私钥领取
  %(prog)s -k keys.txt -c custom_config.json     # 使用自定义配置文件

私钥文件格式 (每行一个私钥，支持注释):
  # 我的钱包1
  1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef  
  # 我的钱包2
  abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890
        """
    )
    
    # 私钥参数组
    key_group = parser.add_mutually_exclusive_group(required=True)
    key_group.add_argument('-k', '--keys-file', 
                          help='私钥文件路径 (每行一个私钥)')
    key_group.add_argument('-p', '--private-key',
                          help='单个私钥 (64位十六进制字符串)')
    
    # 其他参数
    parser.add_argument('-c', '--config', default='sepolia_config.json',
                       help='配置文件路径 (默认: sepolia_config.json)')
    parser.add_argument('-t', '--threads', type=int, default=5,
                       help='最大线程数 (默认: 5)')
    parser.add_argument('-i', '--interval', type=int, default=3,
                       help='领取间隔秒数 (默认: 3)')
    parser.add_argument('-a', '--attempts', type=int,
                       help='每个钱包最大尝试次数 (默认: 无限制)')
    parser.add_argument('--gas-price', type=int,
                       help='Gas价格 (Gwei)')
    parser.add_argument('--gas-limit', type=int,
                       help='Gas限制')
    
    args = parser.parse_args()
    
    # 创建领取器实例
    claimer = SepoliaClaimerCLI(args.config)
    
    # 设置信号处理器
    signal.signal(signal.SIGINT, lambda s, f: signal_handler(s, f, claimer))
    signal.signal(signal.SIGTERM, lambda s, f: signal_handler(s, f, claimer))
    
    # 覆盖配置参数
    if args.gas_price:
        claimer.config['gas_price'] = args.gas_price
    if args.gas_limit:
        claimer.config['gas_limit'] = args.gas_limit
    
    # 连接网络
    if not claimer.connect_network():
        sys.exit(1)
    
    # 准备私钥列表
    private_keys = []
    
    if args.keys_file:
        # 从文件加载私钥
        private_keys = claimer.load_private_keys(args.keys_file)
        if not private_keys:
            claimer.logger.error("❌ 没有找到有效的私钥")
            sys.exit(1)
    else:
        # 单个私钥
        is_valid, result = claimer.validate_private_key(args.private_key)
        if is_valid:
            private_keys = [{
                'private_key': args.private_key,
                'address': result,
                'line_num': 1
            }]
            claimer.logger.info(f"✅ 私钥验证成功: {result[:10]}...{result[-8:]}")
        else:
            claimer.logger.error(f"❌ 私钥验证失败: {result}")
            sys.exit(1)
    
    # 显示配置信息
    print("\n" + "="*60)
    print("⚙️ 配置信息")
    print("="*60)
    print(f"RPC节点: {claimer.config['rpc_url']}")
    print(f"合约地址: {claimer.config['contract_address']}")
    print(f"Gas价格: {claimer.config['gas_price']} Gwei")
    print(f"Gas限制: {claimer.config['gas_limit']}")
    print(f"钱包数量: {len(private_keys)}")
    print(f"最大线程: {args.threads}")
    print(f"领取间隔: {args.interval} 秒")
    if args.attempts:
        print(f"最大尝试: {args.attempts} 次/钱包")
    print("="*60)
    
    # 确认开始
    try:
        input("\n按 Enter 键开始领取，Ctrl+C 停止...")
    except KeyboardInterrupt:
        print("\n👋 已取消")
        sys.exit(0)
    
    # 开始批量领取
    claimer.start_batch_claiming(
        private_keys, 
        max_threads=args.threads,
        interval=args.interval,
        max_attempts=args.attempts
    )

if __name__ == "__main__":
    main() 