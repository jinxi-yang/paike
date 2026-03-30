import dis
import marshal
import struct

pyc_path = r"backend\routes\__pycache__\schedule.cpython-312.pyc"
out_path = "schedule_disassembled.txt"

with open(pyc_path, "rb") as f:
    magic = f.read(4)
    bit_field = f.read(4)
    moddate = f.read(4)
    file_size = f.read(4)
    code = marshal.load(f)

# The loaded `code` is a code object for the entire module.
# Let's find the specific functions we care about in its constants.
funcs_to_dump = ["_score_candidate", "evaluate_preview", "update_schedule"]

def dump_code_object(co, out_file):
    out_file.write(f"\n--- Function: {co.co_name} ---\n")
    dis.dis(co, file=out_file)
    for const in co.co_consts:
        if hasattr(const, "co_code"):
            dump_code_object(const, out_file)

with open(out_path, "w", encoding="utf-8") as out:
    for const in code.co_consts:
        if hasattr(const, "co_name") and const.co_name in funcs_to_dump:
            dump_code_object(const, out)

print(f"Disassembled {funcs_to_dump} into {out_path}")
