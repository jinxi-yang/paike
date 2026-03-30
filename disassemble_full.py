import dis
import marshal
import os

pyc_path = r"backend\routes\__pycache__\schedule.cpython-312.pyc"

if not os.path.exists(pyc_path):
    print(f"Error: {pyc_path} not found")
else:
    with open(pyc_path, "rb") as f:
        f.read(16)  # Skip magic and timestamp
        code_obj = marshal.load(f)

    with open("schedule_full_disassembled.txt", "w", encoding="utf-8") as out:
        def dump_code(c, level=0):
            indent = "  " * level
            out.write(f"{indent}--- Function/Code: {c.co_name} ---\n")
            dis.dis(c, file=out)
            out.write("\n")
            for const in c.co_consts:
                if hasattr(const, 'co_code'):
                    dump_code(const, level + 1)
                    
        dump_code(code_obj)
        print("Successfully fully disassembled into schedule_full_disassembled.txt")
