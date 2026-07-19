# Lime

> Язык программирования, который компилируется в код для **LuaJIT**.
> A programming language that compiles to **LuaJIT** code.

---

## 🇷🇺 Русская версия

### Суть языка

Lime — это язык с простым, лаконичным синтаксисом (`.lm`-файлы), который компилируется напрямую в Lua-код для **LuaJIT**. LuaJIT выбран целью не случайно: это один из самых быстрых JIT-рантаймов в мире для динамического языка, с крошечным весом (интерпретатор — единицы мегабайт) и зрелым, проверенным годами механизмом **FFI** — прямого вызова C-функций и работы с C-структурами без написания биндингов на C.

Lime забирает эту мощь и убирает её главную боль — многословность. Там, где на C/Python вам нужно вручную объявлять типы аргументов, структуры, следить за временем жизни строк, в Lime это делается декларативно, в одну конструкцию.

Компилятор построен как классический конвейер: лексер → парсер (строит AST) → генератор кода (AST → Lua). Никакой магии — предсказуемый, читаемый Lua на выходе, который можно открыть и проверить.

### Почему это интересно

- **Скорость исполнения** — весь сгенерированный код выполняется LuaJIT, а не интерпретируемым байткодом «средней» скорости.
- **Прямая работа с нативными библиотеками** без написания C-обвязки или отдельного модуля на C/C++.
- **Компактный синтаксис** — блоки `{ }`, минимум ключевых слов, никакого шаблонного кода.
- **Прозрачность** — выход компилятора — обычный Lua/LuaJIT-код, его можно встроить куда угодно, где уже есть LuaJIT (игровые движки, embedded-скрипты, high-perf сервисы).

### Пример: подключение DLL — Python vs Lime

Подключить функцию `add(int, int)` из `mylib.dll`:

**Python (ctypes):**
```python
import ctypes

lib = ctypes.CDLL("./mylib.dll")
lib.add.argtypes = [ctypes.c_int, ctypes.c_int]
lib.add.restype = ctypes.c_int

result = lib.add(2, 3)
```

**Lime:**
```
usec "mylib" {
    "int add(int a, int b);"
} as mylib

var result = mylib.add(2, 3)
```

Разница — не только в количестве строк. В Python нужно отдельно объявлять `argtypes`/`restype` для каждой функции через API `ctypes`. В Lime вы просто пишете C-сигнатуру как строку — так, как она выглядит в заголовочном файле — и получаете рабочий биндинг. Компилятор сам находит библиотеку (`.dll`/`.so`/`.dylib` — в зависимости от ОС) в папке проекта, рабочей директории, системных путях и `PATH`/`LD_LIBRARY_PATH`.

### Пример: структуры — Python vs Lime

**Python (ctypes):**
```python
import ctypes

class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]
```

**Lime:**
```
struct Point {
    x: i,
    y: i
}
```

В Lime структура сразу становится полноценным типом LuaJIT FFI (`ffi.metatype`) с собственной таблицей методов. Для строковых полей (тип `s`) компилятор сам генерирует геттеры через `ffi.string` и таблицу ссылок, чтобы сборщик мусора Lua не удалил C-строку раньше времени — в Python аналогичную логику пришлось бы писать руками.

### Методы у структур

```
Point:length(self) {
    ret 0
}
```

Вызов как в ООП: `Point:length(p)`. Компилятор превращает это в обычную Lua-функцию в таблице методов структуры — никакой отдельной среды выполнения, всё остаётся идиоматичным Lua.

### Базовый синтаксис

**Комментарии** — однострочные, `//`:
```
// комментарий
```

**Переменные:**
```
var x = 10 + 2
x = 20
a.b = 5
arr[0] = 1
```

**Условия:**
```
if x > 5 {
    ret 1
} elif x == 5 {
    ret 0
} else {
    ret -1
}
```

**Циклы:**
```
loop x < 10 {           // аналог while
    x = x + 1
}

for i = 0, 10, 1 {      // числовой цикл
    // тело
}

for k, v in myTable {   // цикл по коллекции (аналог pairs)
    // тело
}
```

**Функции:**
```
fn add(a, b) {
    ret a + b
}
```

**Массивы и словари:**
```
var arr = [1, 2, 3]
var dict = {name: "Lime", version: 1}
```

**Импорт кода:**
```
load "utils"      // подключает utils.lm из той же папки
use "mathx"        // подключает библиотеку libs/mathx/setup.lm
```

**Операторы:** `+ - * / // % ^`, `== != > < >= <=`, `& |` (логические И/ИЛИ), `#` (длина), `..` (конкатенация строк).

### Типы полей структур (для `usec`/`struct`)

| Код | Тип C          |
|-----|----------------|
| `i` | `int`          |
| `f` | `float`        |
| `d` | `double`       |
| `s` | `const char*`  |
| `b` | `bool`         |
| `p` | `void*`        |

### Текущее состояние

- Ключевые слова `match`/`case` зарезервированы под будущий pattern-matching, но пока не реализованы в парсере.
- Строки без экранирования спецсимволов (пока без `\"`, `\n` и т.п.).
- Числа без экспоненциальной записи (`1e10`).
- Сообщения об ошибках парсера — на русском.

---

## 🇬🇧 English version

### What Lime is about

Lime is a language with a small, clean syntax (`.lm` files) that compiles directly to Lua code for **LuaJIT**. LuaJIT isn't an incidental choice: it's one of the fastest JIT runtimes for a dynamic language, extremely lightweight (a few megabytes), and comes with a mature, battle-tested **FFI** — calling C functions and working with C structs directly, without hand-written C bindings.

Lime takes that power and removes its biggest pain point: verbosity. Where C or Python make you manually declare argument types, structs, and manage string lifetimes, Lime lets you do it declaratively, in a single construct.

The compiler is a classic pipeline: lexer → parser (builds an AST) → code generator (AST → Lua). No magic — the output is plain, readable Lua/LuaJIT code you can open and inspect.

### Why it's worth a look

- **Runtime speed** — everything you write runs as LuaJIT-compiled code, not "average" interpreted bytecode.
- **Direct native interop** — call into C libraries without writing a C wrapper or a separate module.
- **Compact syntax** — `{ }` blocks, minimal keywords, no boilerplate.
- **Transparent output** — the compiler emits plain Lua/LuaJIT, so it drops straight into anything that already embeds LuaJIT (game engines, embedded scripting, high-performance services).

### Example: loading a DLL — Python vs Lime

Calling `add(int, int)` from `mylib.dll`:

**Python (ctypes):**
```python
import ctypes

lib = ctypes.CDLL("./mylib.dll")
lib.add.argtypes = [ctypes.c_int, ctypes.c_int]
lib.add.restype = ctypes.c_int

result = lib.add(2, 3)
```

**Lime:**
```
usec "mylib" {
    "int add(int a, int b);"
} as mylib

var result = mylib.add(2, 3)
```

The difference isn't just line count. Python's `ctypes` requires declaring `argtypes`/`restype` separately for every function through its API. In Lime, you write the C signature as a plain string — exactly as it appears in a header file — and get a working binding immediately. The compiler locates the library itself (`.dll`/`.so`/`.dylib`, depending on the OS) by searching the project's `libs` folder, the working directory, system paths, and `PATH`/`LD_LIBRARY_PATH`.

### Example: structs — Python vs Lime

**Python (ctypes):**
```python
import ctypes

class Point(ctypes.Structure):
    _fields_ = [("x", ctypes.c_int), ("y", ctypes.c_int)]
```

**Lime:**
```
struct Point {
    x: i,
    y: i
}
```

In Lime, a struct immediately becomes a first-class LuaJIT FFI type (`ffi.metatype`) with its own method table. For string fields (type `s`), the compiler auto-generates getters through `ffi.string` plus a reference table so Lua's garbage collector doesn't free the underlying C string too early — logic you'd otherwise have to write by hand in Python.

### Struct methods

```
Point:length(self) {
    ret 0
}
```

Called like a method: `Point:length(p)`. The compiler turns this into a plain Lua function on the struct's method table — no separate runtime, just idiomatic Lua underneath.

### Core syntax

**Comments** — single-line, `//`:
```
// a comment
```

**Variables:**
```
var x = 10 + 2
x = 20
a.b = 5
arr[0] = 1
```

**Conditionals:**
```
if x > 5 {
    ret 1
} elif x == 5 {
    ret 0
} else {
    ret -1
}
```

**Loops:**
```
loop x < 10 {           // like while
    x = x + 1
}

for i = 0, 10, 1 {      // numeric loop
    // body
}

for k, v in myTable {   // collection loop (like pairs)
    // body
}
```

**Functions:**
```
fn add(a, b) {
    ret a + b
}
```

**Arrays and dicts:**
```
var arr = [1, 2, 3]
var dict = {name: "Lime", version: 1}
```

**Importing code:**
```
load "utils"       // includes utils.lm from the same folder
use "mathx"         // includes the libs/mathx/setup.lm library
```

**Operators:** `+ - * / // % ^`, `== != > < >= <=`, `& |` (logical AND/OR), `#` (length), `..` (string concatenation).

### Struct field type codes (for `usec`/`struct`)

| Code | C type         |
|------|----------------|
| `i`  | `int`          |
| `f`  | `float`        |
| `d`  | `double`       |
| `s`  | `const char*`  |
| `b`  | `bool`         |
| `p`  | `void*`        |

### Current state

- `match`/`case` are reserved keywords for future pattern matching, not yet implemented in the parser.
- Strings don't support escape sequences yet (no `\"`, `\n`, etc.).
- No exponential number notation (`1e10`).
- Parser error messages are currently in Russian.
