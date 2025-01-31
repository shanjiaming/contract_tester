# contract_tester
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
--abi 和 --bin同时提供，或只提供--sol
启用--interactive更方便，不然还需要改代码。

example:
```bash
python contract_tester.py --sol sol/symuint.sol --interactive
```
