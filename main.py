import os.path
import sys
import time
from lupa.luajit21 import LuaRuntime

from compiler import Parser, lex, CodeGen

if len(sys.argv) > 0 and sys.argv[0].endswith(".py"):
    sys.argv.pop(0)

if len(sys.argv) < 1:
    print("Must be given 1 or more arguments to app")
    exit(1)

path = sys.argv[0]
if not os.path.exists(path):
    print("Unknown path to project: " + sys.argv[0])
    exit(1)

lua = LuaRuntime(unpack_returned_tuples=True)

lua.execute('jit.opt.start(3)')

with open(os.path.join(path, "main.lm"), encoding="utf-8", mode="r") as f:
    code = f.read()

print("=== ТОКЕНЫ ===")
tokens = lex(code)
for token in tokens:
    print(token)

print("\n=== AST ===")
parser = Parser(tokens)
ast = parser.parse()
print(ast)

lua_code = CodeGen(ast, path).generate()
print(lua_code)

def def_python_lib(name):
    return __import__(name)

def printlmerror(s):
    print(f"\033[31mLime Exception: {s}\033[0m")
    exit(1)

lua.globals()["args"] = sys.argv
lua.globals()["defpyt"] = def_python_lib
lua.globals()["exit"] = exit
lua.globals()["range"] = range
lua.globals()["error"] = printlmerror
lua.globals()["getattr"] = getattr
lua_code = "local ffi = require('ffi')\n" + lua_code
lua.execute(lua_code)