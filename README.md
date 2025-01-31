# 智能合约测试工具

`contract_tester.py` - 交互式智能合约测试脚本

## 快速使用

```bash
# 基本命令格式
python contract_tester.py [--solidity SOLIDITY_FILE] 
                          [--abi ABI_FILE --bin BIN_FILE]
                          [--mainnet CONTRACT_ADDRESS]
                          [--interactive]
```

## 参数说明

| 参数            | 说明                          |
|-----------------|-------------------------------|
| `--solidity`    | Solidity合约文件路径          |
| `--abi` + `--bin`| ABI与BIN文件组合使用          |
| `--mainnet`     | 主网合约地址(需配置API密钥)   |
| `--interactive` | 启用交互模式（推荐）          |

## 配置要求

### 密钥环境（使用主网合约时需要）
```bash
# .env文件配置
ETHERSCAN_API_KEY="your_etherscan_key"  # 从etherscan.io获取
ALCHEMY_API_KEY="your_alchemy_key"     # 从alchemy.com获取
```

### 依赖安装
（不保证所有依赖都已安装，请酌情根据需求调整代码。）
```bash
# 安装Python依赖
pip install web3 python-dotenv requests eth-abi
# 安装系统依赖
sudo apt-get install solc  # Solidity编译器
cargo install anvil        # 本地测试节点
```

## 使用示例

### 示例合约
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract SymVars {
    uint public total = 0;
    function addTo(uint number) public returns (uint) {
        total += number;
        return total;
    }
}
```

### 执行流程
```bash
# 启动测试（使用示例合约）
python contract_tester.py --solidity sol/symuint.sol --interactive

# 控制台输出示例
1. 选择合约: SymVars
2. 调用函数:
   > total
   ✅ 返回值: 0
   > addTo 5
   ✅ 返回值: 5
```

## 功能菜单

### 主菜单界面
```
===== 主菜单 =====
1. 🚀 快速调用函数
2. 📜 查看调用历史
3. 💰 检查账户余额
4. 🗄️ 读取存储数据
0. ❌ 退出
```

### 存储读取示例
```
输入存储槽位: 0
存储槽 0x0 的值: 0x0000...002a
十进制: 42
```
