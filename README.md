# 智能合约测试工具

## 项目概述
用于测试Solidity合约的交互式工具，支持本地部署和主网合约分析

## ⚙️ 依赖要求
- **必须组件**:
  - Python 3.8+
  - `web3`, `python-dotenv` 等Python包
  - solc编译器
  - Foundry Anvil本地节点

- **API密钥**:
  ```bash
  # .env文件配置
  ETHERSCAN_API_KEY="your_etherscan_key"
  ALCHEMY_API_KEY="your_alchemy_key"
  ```

## 🚀 使用方法
```bash
python contract_tester.py [-h] [--solidity SOLIDITY] [--abi ABI] [--bin BIN] [--mainnet MAINNET] [--interactive]
```

### 参数说明
| 参数 | 说明 |
|------|------|
| `--solidity` | Solidity源文件路径 |
| `--abi`      | ABI文件路径 (需配合--bin使用) |
| `--bin`      | 字节码文件路径 |
| `--mainnet`  | 主网合约地址 |
| `--interactive` | 进入交互模式 |

## 📖 使用示例

### 合约部署测试
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

```bash
# 部署并测试合约
python contract_tester.py --solidity sol/symuint.sol --interactive

===== 交互流程示例 =====
1. 选择合约: SymVars
2. 调用函数:
   > total
   ✅ 返回值: 0
   
   > addTo 5
   ✅ 返回值: 5
   
   > total
   ✅ 返回值: 5
```

## 🛠️ 功能特性
- 多合约选择支持
- 交易历史追踪
- 账户余额查询
- 存储数据读取

## 💡 使用技巧
```bash
# 推荐始终使用--interactive参数
python contract_tester.py --mainnet 0x... --interactive

# 主网合约需配置.env中的API密钥
# 本地测试需要运行anvil节点
```
