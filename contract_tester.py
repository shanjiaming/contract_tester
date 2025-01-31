import os
import json
import shutil
import argparse
from web3 import Web3
from eth_tester import EthereumTester
import subprocess
import atexit
import signal
import time

class ContractTester:
    def __init__(self):
        self.anvil_process = None
        self._start_anvil()  # 新增：自动启动Anvil
        self.w3 = Web3(Web3.HTTPProvider('http://localhost:8545'))
        self.accounts = self._get_anvil_accounts()
        self.contract_instance = None
        self.contract_address = None
        self.call_history = []

    def _start_anvil(self):
        """ 自动启动Anvil本地节点 """
        try:
            # 检查anvil是否安装
            subprocess.run(['anvil', '--version'], check=True, 
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            raise RuntimeError("Anvil未安装，请通过 'cargo install --git https://github.com/foundry-rs/foundry anvil' 安装")

        # 启动Anvil进程
        self.anvil_process = subprocess.Popen(
            ['anvil', '--silent', '--steps-tracing'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # 注册退出时的清理操作
        atexit.register(self._stop_anvil)
        
        # 等待节点启动
        timeout = 10
        start_time = time.time()
        while True:
            try:
                if Web3(Web3.HTTPProvider('http://localhost:8545')).is_connected():
                    break
            except:
                if time.time() - start_time > timeout:
                    raise RuntimeError("Anvil启动超时")
                time.sleep(0.5)

    def _stop_anvil(self):
        """ 停止Anvil进程 """
        if self.anvil_process:
            self.anvil_process.send_signal(signal.SIGTERM)
            try:
                self.anvil_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.anvil_process.kill()
            self.anvil_process = None

    def _get_anvil_accounts(self):
        """ 获取Anvil的默认测试账户 """
        return [
            '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
            '0x70997970C51812dc3A010C7d01b50e0d17dc79C8',
            '0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC'
        ]

    def load_from_solidity(self, sol_path):
        """ 模式1: 从Solidity源码编译 """
        if not os.path.exists(sol_path):
            raise FileNotFoundError(f"Solidity file not found: {sol_path}")

        # 创建结构化输出目录
        output_dir = os.path.join(
            "solc_output", 
            os.path.basename(sol_path).replace('.sol', '')
        )
        os.makedirs(output_dir, exist_ok=True)
        
        # 编译合约
        cmd = f'solc --abi --bin {sol_path} -o {output_dir} --overwrite'
        result = subprocess.run(cmd, shell=True, capture_output=True)
        if result.returncode != 0:
            raise RuntimeError(f"Compilation failed:\n{result.stderr.decode()}")

        # 复制源文件到输出目录
        shutil.copy(sol_path, output_dir)

        # 获取编译生成的合约列表
        contracts = self._get_compiled_contracts(output_dir)
        
        # 处理多合约选择
        if len(contracts) > 1:
            print("发现多个合约:")
            for i, c in enumerate(contracts, 1):
                print(f"{i}. {c}")
            choice = int(input("请选择合约编号: ")) - 1
            contract_name = contracts[choice]
        else:
            contract_name = contracts[0]
        
        return self._load_artifacts(output_dir, contract_name)

    def load_from_abi_bin(self, abi_path, bin_path):
        """ 模式2: 直接加载提供的ABI和BIN文件 """
        # 直接加载ABI文件
        try:
            with open(abi_path) as f:
                abi = json.load(f)
        except Exception as e:
            raise ValueError(f"加载ABI文件失败: {abi_path} - {str(e)}")
        
        # 直接加载字节码文件
        try:
            with open(bin_path) as f:
                bytecode = '0x' + f.read().strip()
        except Exception as e:
            raise ValueError(f"加载字节码文件失败: {bin_path} - {str(e)}")
        
        return abi, bytecode

    def load_from_bin(self, bin_path):
        """ 模式3: 仅从BIN文件加载 """
        # 直接加载字节码
        try:
            with open(bin_path) as f:
                bytecode = '0x' + f.read().strip()
        except Exception as e:
            raise ValueError(f"加载字节码文件失败: {bin_path} - {str(e)}")
        
        return [], bytecode  # 返回空ABI

    def _load_artifacts(self, artifacts_dir, contract_name):
        """ 加载编译产物 """
        # 处理可能包含路径的合约名
        base_name = contract_name.split(':')[-1]
        abi_path = os.path.join(artifacts_dir, f"{contract_name}.abi")
        
        # 加载ABI
        abi = []
        if os.path.exists(abi_path):
            try:
                with open(abi_path) as f:
                    abi = json.load(f)
            except Exception as e:
                print(f"⚠️ 加载ABI文件失败: {str(e)}")
        else:
            print(f"⚠️ 未找到ABI文件: {abi_path}")

        # 加载字节码
        bin_path = os.path.join(artifacts_dir, f"{contract_name}.bin")
        try:
            with open(bin_path) as f:
                bytecode = '0x' + f.read().strip()
        except FileNotFoundError:
            # 尝试其他可能的扩展名
            bin_path = os.path.join(artifacts_dir, f"{contract_name}.hex")
            if not os.path.exists(bin_path):
                raise FileNotFoundError(f"找不到字节码文件: {contract_name}.bin 或 {contract_name}.hex")
            with open(bin_path) as f:
                bytecode = '0x' + f.read().strip()
        except Exception as e:
            print(f"⚠️ 加载字节码失败: {str(e)}")
            raise

        return abi, bytecode

    def deploy(self, abi, bytecode):
        """ 部署合约 """
        # 添加部署参数验证
        # print(f"原始字节码长度: {len(bytecode)} 字符")
        if len(bytecode) < 100:
            raise ValueError("字节码异常，可能未包含构造函数")
        
        # 添加构造函数参数处理
        contract = self.w3.eth.contract(
            abi=abi,
            bytecode=bytecode
        )
        
        # 使用更明确的交易参数
        tx_hash = contract.constructor().transact({
            'from': self.accounts[0],
            'gas': 2_000_000,
            'gasPrice': self.w3.eth.gas_price
        })
        
        # 添加交易调试
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        # print(f"部署交易gas使用量: {receipt.gasUsed}")
        
        # 验证合约代码
        # code = self.w3.eth.get_code(receipt.contractAddress)
        # print(f"部署后合约代码长度: {len(code)} bytes")
        
        self.contract_address = receipt.contractAddress
        self.contract_instance = self.w3.eth.contract(
            address=self.contract_address, 
            abi=abi
        )
        print(f"✅ Contract deployed at: {self.contract_address}")

    def interactive_mode(self):
        choice = '1'
        while True:

            if choice == '1':
                self._quick_call()
            elif choice == '2':
                self._show_history()
            elif choice == '3':
                self._check_balance()
            elif choice == '0':
                break
            else:
                print("无效选择，请重新输入")

            print("\n===== 主菜单 =====")
            print("1. 🚀 快速调用模式")
            print("2. 📜 查看调用历史")
            print("3. 💰 查看账户余额")
            print("0. 退出")
            
            choice = input("请输入选项: ").strip()

    def _read_storage(self):
        """ 读取存储 """
        slot = input("输入存储槽位（十进制）: ").strip()
        try:
            value = self.w3.eth.get_storage_at(self.contract_address, int(slot))
            print(f"存储槽 {slot} 的值: {value.hex()}")
        except Exception as e:
            print(f"❌ 读取失败: {str(e)}")

    def _check_balance(self):
        """ 查看账户余额 """
        balance = self.w3.eth.get_balance(self.accounts[0])
        print(f"账户 {self.accounts[0]} 余额: {balance} wei")

    def example_usage(self):
        """ 示例用法 """
        print("\n===== 示例测试 =====")
        try:
            # 示例调用函数
            arg = 0xaaaaaaa
            print(f"调用 vulnerableFunction({arg})...")
            tx_hash = self.contract_instance.functions.vulnerableFunction(arg).transact({
                'from': self.accounts[0]
            })
            self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            # 读取存储示例
            print("读取存储槽 0...")
            storage_value = self.w3.eth.get_storage_at(self.contract_address, 0)
            print(f"存储槽 0 值: {storage_value.hex()} (十进制: {int.from_bytes(storage_value, 'big')})")
            
            # 更详细的ABI检查
            if self.contract_instance.abi:
                a_functions = [fn for fn in self.contract_instance.abi 
                              if fn.get('name') == 'a' and fn['type'] == 'function']
                if not a_functions:
                    print("⚠️ ABI中未找到a()函数")
                else:
                    print("找到a()函数签名:", a_functions[0])
            
            # 添加详细的ABI验证
            print("\n验证ABI内容:")
            if any(fn.get('name') == 'a' for fn in self.contract_instance.abi):
                print("✅ 找到a()函数定义")
                a_func = next(fn for fn in self.contract_instance.abi if fn.get('name') == 'a')
                print("函数签名:", json.dumps(a_func, indent=2))
            else:
                print("❌ 未找到a()函数定义")

            # 添加交易调试信息
            print("\n验证合约状态:")
            print(f"当前区块号: {self.w3.eth.block_number}")
            print(f"最新区块hash: {self.w3.eth.get_block('latest')['hash'].hex()}")
            
            # 使用静态call验证
            print("\n尝试静态call调用a()函数:")
            try:
                a_value = self.contract_instance.functions.a().call(
                    {'from': self.accounts[0], 'gas': 1_000_000}
                )
                print(f"✅ 变量 a 的值: {a_value}")
            except Exception as e:
                print(f"静态call失败: {repr(e)}")
                if hasattr(e, 'args') and 'message' in e.args[0]:
                    print(f"详细错误: {e.args[0]['message']}")
            
            # 添加交易回放调试
            print("\n调试交易回放:")
            latest_block = self.w3.eth.get_block('latest')
            print(f"最新区块交易数: {len(latest_block['transactions'])}")
            if len(latest_block['transactions']) > 0:
                last_tx = self.w3.eth.get_transaction(latest_block['transactions'][-1])
                print(f"最后交易输入数据: {last_tx.input}")

        except Exception as e:
            print(f"\n❌ 错误详情: {repr(e)}")
            if 'message' in str(e):
                print(f"错误信息: {e.args[0]['message']}")
            print("建议检查：")
            print("- 确保使用最新编译的ABI文件")
            print("- 确认Solidity版本为0.8.x")
            print("- 尝试清除并重新编译合约")

    def _get_compiled_contracts(self, output_dir):
        """ 获取编译生成的合约列表 """
        contracts = set()
        for filename in os.listdir(output_dir):
            if filename.endswith('.abi'):
                # 处理可能的路径格式（如"file.sol:Contract.abi"）
                contract_name = filename[:-4]
                if ':' in contract_name:
                    contract_name = contract_name.split(':')[-1]
                contracts.add(contract_name)
        return sorted(list(contracts))

    def _convert_arguments(self, params, inputs):
        """ 智能参数类型转换 """
        converted = []
        for raw, abi_type in zip(params, inputs):
            try:
                if abi_type['type'].startswith('uint'):
                    converted.append(int(raw))
                elif abi_type['type'].startswith('bytes'):
                    if raw.startswith('0x'):
                        converted.append(bytes.fromhex(raw[2:]))
                    else:
                        converted.append(raw.encode())
                # 添加其他类型处理...
            except ValueError as e:
                raise ValueError(f"参数 {abi_type['name']} 类型错误: {str(e)}")
        return converted

    def _quick_call(self):
        """ 快速调用模式（默认入口） """
        print("\n===== 快速调用模式 (输入exit退出) =====")
        print("\n输入格式: 函数名 参数1 参数2 ...")
        
        # 显示可用函数列表
        print("\n===== 可用函数 =====")
        funcs = [fn for fn in self.contract_instance.abi if fn['type'] == 'function']
        for i, fn in enumerate(funcs, 1):
            inputs = ','.join([i['type'] for i in fn.get('inputs', [])])
            print(f"{i}. {fn['name']}({inputs})")
        print("=====================")
            
        while True:

            cmd = input("> ").strip()
            if cmd.lower() in ('exit', 'quit', 'q'):
                break
            try:
                parts = cmd.split()
                if not parts:
                    continue
                    
                func_name = parts[0]
                params = parts[1:]
                
                # 查找函数
                func = next((f for f in self.contract_instance.abi 
                            if f['type'] == 'function' and f['name'] == func_name), None)
                if not func:
                    print(f"❌ 函数 {func_name} 不存在")
                    continue
                    
                # 判断调用类型
                is_view = func.get('stateMutability') in ('view', 'pure')
                
                # 参数转换
                converted = self._convert_arguments(params, func.get('inputs', []))
                
                # 视图调用
                result = getattr(self.contract_instance.functions, func_name)(*converted).call()
                print(f"✅ 返回值: {result}")
                self.call_history.append({
                    'function': func_name,
                    'params': params,
                    'result': result
                })
                if not is_view:
                    # 交易调用
                    tx_hash = getattr(self.contract_instance.functions, func_name)(*converted).transact({
                        'from': self.accounts[0],
                        'gas': 1_000_000
                    })
                    receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                    # print(f"✅ 成功！交易哈希: {tx_hash.hex()}")
                    # print(f"   Gas消耗: {receipt.gasUsed}")
                    # print(f"交易状态: {'成功' if receipt.status == 1 else '失败'}")
                    
                    # 添加Anvil调试支持
                    if self._is_anvil():
                        return_data = self._get_tx_return_data(tx_hash)
                        if return_data:
                            decoded = self._decode_return_data(
                                return_data,
                                [output['type'] for output in func.get('outputs', [])] 
                                if func.get('outputs') else []
                            )
                            print(f"🔍 调试返回值: {decoded}")
                    # self.call_history.append({
                        # 'function': func_name,
                        # 'params': params,
                        # 'result': tx_hash.hex()
                    # })
                
            except Exception as e:
                print(f"❌ 错误: {str(e)}")

    def _show_history(self):
        """ 查看调用历史 """
        if not self.call_history:
            print("没有调用历史记录")
            return
        
        print("\n===== 调用历史记录 =====")
        for i, record in enumerate(self.call_history, 1):
            print(f"{i}. 函数: {record['function']}")
            print(f"   参数: {', '.join(record['params'])}")
            print(f"   结果: {record['result']}")

    def _is_anvil(self):
        """ 检测是否使用Anvil节点 """
        try:
            return 'anvil' in self.w3.client_version.lower()
        except:
            return False

    def _get_tx_return_data(self, tx_hash):
        """ 通过Anvil调试接口获取返回值 """
        try:
            result = self.w3.provider.make_request(
                'anvil_getTransactionResult',
                [tx_hash.hex()]
            )
            return result.get('result', {}).get('returnValue')
        except Exception as e:
            print(f"⚠️ 获取返回值失败: {str(e)}")
            return None

    def _decode_return_data(self, hex_data, output_types):
        """ 解码ABI编码的返回值 """
        from eth_abi import decode_abi
        
        if not hex_data or hex_data == '0x':
            return "无返回值"
        
        if not output_types:
            return "（无返回值定义）"
        
        try:
            decoded = decode_abi(output_types, bytes.fromhex(hex_data[2:]))
            # 简化输出格式
            if len(decoded) == 1:
                return decoded[0]
            return decoded
        except Exception as e:
            print(f"⚠️ 解码失败: {str(e)}")
            return f"原始数据: {hex_data}"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="智能合约测试工具")
    
    # 参数组调整
    parser.add_argument('--solidity', help="Solidity源文件路径")
    parser.add_argument('--abi', help="ABI文件路径（需与--bin一起使用）")
    parser.add_argument('--bin', help="字节码文件路径")
    
    parser.add_argument('--interactive', action='store_true', help="进入交互模式")
    args = parser.parse_args()

    tester = ContractTester()
    
    try:
        if args.solidity and not (args.abi or args.bin):
            abi, bytecode = tester.load_from_solidity(args.solidity)
        elif args.abi and args.bin:
            if not os.path.exists(args.abi) or not os.path.exists(args.bin):
                raise FileNotFoundError("ABI或BIN文件不存在")
            abi, bytecode = tester.load_from_abi_bin(args.abi, args.bin)
        elif args.bin and not (args.abi or args.solidity):
            if not os.path.exists(args.bin):
                raise FileNotFoundError("BIN文件不存在")
            abi, bytecode = tester.load_from_bin(args.bin)
        else:
            raise ValueError("无效的参数组合，请使用以下组合之一：\n"
                             "1. --solidity [文件路径]\n"
                             "2. --abi [abi文件] --bin [bin文件]\n"
                             "3. --bin [bin文件]")

        tester.deploy(abi, bytecode)
        
        if args.interactive:
            tester.interactive_mode()
        else:
            tester.example_usage()

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        exit(1) 
