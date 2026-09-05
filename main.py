from pathlib import Path
from random import randint, choice
import hashlib
import struct
import marshal
import shutil


class Encryptor:
    def __init__(self, src: str | Path, dst: str | Path = None) -> None:
        self.src = Path(src)
        self.dst = Path(dst) if dst else (self.src.parent / f"{self.src.name}-dist")
        if self.dst == self.src:
            raise ValueError("dst cannot be the same as src")
        if self.dst.exists():
            shutil.rmtree(self.dst)
        self.dst.mkdir(parents=True)

    def __generateKey(self) -> bytes:
        """
        生成64位密钥
        """
        key = "".join([chr(randint(33, 126)) for _ in range(64)])
        key = key.encode("utf-8") if isinstance(key, str) else key
        return hashlib.sha3_512(key).digest()

    def __encrypt(self, pyFile: Path) -> bytes:
        code = compile(Path(pyFile).read_bytes(), pyFile.__str__(), "exec")
        bytecode = marshal.dumps(code)
        bytecode_length = len(bytecode)
        key = self.__generateKey()
        # 异或加密
        en_code = bytes(
            [bytecode[i] ^ key[i % len(key)] for i in range(bytecode_length)]
        )
        # 随机偏移量，偏移量位置插入key
        insert_offset = randint(0, len(en_code) - 1)
        en_code = en_code[:insert_offset] + key + en_code[insert_offset:]
        offset_bytes = struct.pack("<I", insert_offset)
        # 在尾部记录偏移量
        en_code += offset_bytes
        return en_code

    def encryptProject(self):
        """
        生成加密项目
        """
        runtimeDir = Path(__file__).parent / "runtime"
        if not runtimeDir.exists():
            raise FileNotFoundError("runtime.py not found")

        newRuntimeName = "__runtime__"
        runtimePlace = self.dst / newRuntimeName

        def __encryptFile(file):
            print(f"Encrypting {file}...")
            en_code = self.__encrypt(file)
            dst_file = self.dst / file.relative_to(self.src)
            if not dst_file.parent.exists():
                dst_file.parent.mkdir(parents=True)
            with open(dst_file, "w") as f:
                f.write(
                    f"from {newRuntimeName} import __run__\n__run__({en_code}, globals())"
                )

        for file in self.src.rglob("*.py"):
            __encryptFile(file)
        for file in self.src.rglob("*.pyw"):
            __encryptFile(file)

        # 复制runtime文件夹
        shutil.copytree(runtimeDir, runtimePlace, dirs_exist_ok=True)
        print(f'dist to "{self.dst}"')
        print("Compiled successfully.")


if __name__ == "__main__":
    encryptor = Encryptor("testproject")
    encryptor.encryptProject()
