# PyEncryptor

Python 项目源代码加密分发工具。它将项目中的 `.py` / `.pyw` 编译为字节码、混淆后与解密运行时一起打包分发，运行时自动解密执行，从而避免源码被直接阅读。

> ## ⚠️ 安全声明（使用前必读）
>
> Python 是解释型语言，程序在运行期必须包含可执行的字节码，因此**客户端无法实现真正意义上的加密**。
> 本工具的实现为「编译字节码 + XOR 混淆 + 密钥随产物分发」，密钥与解密算法都随产物一起交付：
>
> - 生成的"加密"文件本质是**明文 Python 源码**，其中以 `bytes` 字面量内嵌了密钥、偏移量与密文；
> - 任何人用十余行代码即可提取密钥并还原字节码（本项目 `runtime.py` 即解密算法源码）；
> - 还原出的标准 CPython 字节码可用 pycdc / decompyle3 / pylingual 等工具反编译到近源码级别。
>
> 因此本工具**只能阻挡"直接打开查看 / 全文搜索"级别的窥探，无法防御任何有意的逆向工程**。
> 对真正敏感的代码，建议采用 Nuitka 原生编译、PyArmor 运行时混淆，或将核心逻辑收敛到服务端。
> 请勿将其用于商业源码的保密交付场景。

## 功能特性

- 将 `.py` / `.pyw` 编译为字节码并用随机密钥混淆
- 保持原项目的目录结构与包导入关系
- 内置解密运行时，加密产物开箱即用
- 仅依赖 Python 标准库，零第三方依赖

## 工作原理

```
源码 .py ──compile()──▶ 字节码 ──marshal──▶ 序列化 ──XOR 加密──▶ 密文
                                                              │
                    +─────── 密钥插入随机偏移，偏移写入尾部 ──────+
                    ▼
  生成 stub：from __runtime__ import __run__
             __run__(<密文字节串>, globals())
  同时复制 runtime/ 目录为 __runtime__/
```

运行时执行时：

```
stub ──▶ __run__ ──▶ 读取尾部偏移 ──▶ 提取密钥 ──▶ XOR 解密
            ──▶ marshal.loads ──▶ exec(code, globals)
```

## 目录结构

```
PyEncryptor/
├── main.py                 # 加密器入口（Encryptor 类）
├── runtime.py              # 运行时源码（解密 + 执行）
├── runtime/                # 运行时发布目录
│   ├── __init__.py
│   └── runtime.cp312-win_amd64.pyd   # 由 runtime.py 编译得到的扩展模块
├── TestProject/            # 演示用示例项目
└── pyproject.toml
```

## 环境要求

- Python 3.12（CPython，Windows x64）
- 运行时扩展模块 `runtime.cp312-win_amd64.pyd` 与 CPython 版本、平台严格绑定

> 注意：加密产物同样只能在「Python 3.12 + Windows x64」环境下运行；
> `marshal` 字节码格式与运行时 .pyd 均不跨版本、不跨平台。

## 使用方法

### 1. 加密项目

编辑 [main.py](main.py) 底部的 `__main__` 入口，指定源项目与输出目录：

```python
if __name__ == "__main__":
    Encryptor("path/to/src", "path/to/dist").encryptProject()
```

然后运行：

```bash
python main.py
```

加密产物将输出到目标目录（保持源项目的目录结构），并自动带上解密运行时。

### 2. 运行加密产物

```bash
cd path/to/dist
python main.py
```

### API

```python
Encryptor(src: str | Path, dst: str | Path = None)
```

- `src`：源项目路径（必填）
- `dst`：输出路径（可选，默认 `src` 同级的 `<src>-dist`）
- 调用 `encryptProject()` 执行加密

## 已知限制（Roadmap）

1. **非 Python 文件不会随项目复制**：源项目中的配置、模板、静态资源等非 `.py/.pyw` 文件会被静默丢弃，包含资源的项目加密后无法正常运行。
2. **目标目录会无提示整体删除**：`dst` 已存在时将被 `shutil.rmtree` 直接删除，且未校验 `dst` 不能是 `src` 的父目录（如 `dst="."` 将清空整个工作区）。
3. **强平台绑定**：运行时 .pyd 仅提供 Windows x64 + CPython 3.12，仓库中无任何构建脚本可重新生成该模块。
4. **混淆强度极低**：密钥与算法随产物分发，详见上文「安全声明」。
5. **加密入口为硬编码**：`main.py` 的 `__main__` 写死了源路径，未提供命令行参数或包化入口。

## 示例

仓库自带演示项目 `TestProject/`：

```bash
# 加密（需先将 main.py 中 Encryptor 参数改为 "TestProject"）
python main.py

# 运行加密产物
cd testproject-dist
python main.py
# 输出：Hello from testproject! / testPrint
```
