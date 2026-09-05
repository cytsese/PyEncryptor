def __run__(en_code: bytes, globals_: dict):
    import struct
    import marshal

    def decrypt(en_code: bytes) -> bytes:
        en_code, offset_bytes = en_code[:-4], en_code[-4:]  # 去除偏移量
        insert_offset = struct.unpack("<I", offset_bytes)[0]
        key = en_code[insert_offset : insert_offset + 64]  # 提取key
        en_code = en_code[:insert_offset] + en_code[insert_offset + 64 :]  # 去除key
        # 解密
        de_code = bytes([en_code[i] ^ key[i % len(key)] for i in range(len(en_code))])
        return de_code

    code = marshal.loads(decrypt(en_code))
    exec(code, globals_, globals_)
