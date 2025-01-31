# contract_tester
run a solidity/ abi+bin.

dependency:python web3, py-evm, anvil, solc.
即使没有这些包，文件中可能也包含了其它的执行方法，请酌情根据需求调整代码。

```
python contract_tester.py -h
usage: contract_tester.py [-h] [--solidity SOLIDITY]
                          [--abi ABI] [--bin BIN]
                          [--interactive]
```
智能合约测试工具
```
options:
  -h, --help           show this help message and exit    
  --solidity SOLIDITY  Solidity源文件路径
  --abi ABI            ABI文件路径（需与--bin一起使用）   
  --bin BIN            字节码文件路径
  --interactive        进入交互模式
```

推荐使用方法：

--abi 和 --bin同时提供，或只提供--sol。

启用--interactive更方便，不然还需要改代码。



example:
File to run:
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

contract SymVars2 {
    uint public anothertotal = 0;
    function anotheraddTo(uint number) public returns (uint) {
        anothertotal += number;
        return anothertotal;
    }
}

```


```bash
python contract_tester.py --sol sol/symuint.sol --interactive
发现多个合约:
1. SymVars
2. SymVars2
请选择合约编号: 1
✅ Contract deployed at: 0x5FbDB2315678afecb367f032d93F642f64180aa3

===== 快速调用模式 (输入exit退出) =====

输入格式: 函数名 参数1 参数2 ...

===== 可用函数 =====
1. addTo(uint256)
2. total()
=====================
> total  
✅ 返回值: 0
> addTo 5
✅ 返回值: 5
> total
✅ 返回值: 5
> exit

===== 主菜单 =====
1. 🚀 快速调用模式
2. 📜 查看调用历史
3. 💰 查看账户余额
0. 退出
请输入选项: 3
账户 0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266 余额: 9999999633843042339907 wei

===== 主菜单 =====
1. 🚀 快速调用模式
2. 📜 查看调用历史
3. 💰 查看账户余额
0. 退出
请输入选项: 2

===== 调用历史记录 =====
1. 函数: total
   参数:
   结果: 0
2. 函数: addTo
   参数: 5
   结果: 5
3. 函数: total
   参数:
   结果: 5
```
