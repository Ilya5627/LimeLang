# Lime

> Язык программирования, который компилируется в код для **LuaJIT**.
> A programming language that compiles to **LuaJIT** code.

---

## 🇷🇺 Русская версия

### Суть языка

Lime — это язык с простым, лаконичным синтаксисом (`.lm`-файлы), который компилируется напрямую в Lua-код для **LuaJIT**. Так как LuaJIT - это один из самых быстрых JIT-рантаймов в мире для динамического языка, который при выполнении занимает единицы мегабайт. Также он имеет мощный механизм - FFI - прямое выполнение кода C.

Lime создан с целью убрать её главную боль — многословность.

Компилятор работает следующим образом: лексер → парсер (строит AST) → генератор кода (AST → LuaJIT код). Компилятор написан на Python с целью использовать его библиотеку - lupa 2.8 - которая предоставляет возможность встраивать в Lua-code python функции. В Lime это делается с целью получить возможность импорта любой питон библиотеки без особой потери скорости.

### Почему это интересно

- **Скорость исполнения** — весь сгенерированный код выполняется LuaJIT, который является легковесным и быстрым.
- **Прямая работа с нативными библиотеками** без написания C-обвязки или отдельного модуля на C/C++.
- **Компактный синтаксис** — блоки `{ }`, минимум ключевых слов, никакого шаблонного кода.
- **Прозрачность** — выход компилятора — обычный Lua/LuaJIT-код, его можно встроить куда угодно, где уже есть LuaJIT (игровые движки, embedded-скрипты, high-perf сервисы).

### Пример: подключение DLL в Lime

Подключить функцию `add(int, int)` из `mylib.dll`:

**Lime:**
```
usec "mylib" {
    "int add(int a, int b);"
} as mylib

var result = mylib.add(2, 3)
```

Разница с Python — не только в количестве строк. В Python нужно отдельно объявлять `argtypes`/`restype` для каждой функции через API `ctypes`. В Lime вы просто пишете C-сигнатуру как строку — так, как она выглядит в заголовочном файле — и получаете рабочий биндинг. Компилятор сам находит библиотеку (`.dll`/`.so`/`.dylib` — в зависимости от ОС) в папке проекта, рабочей директории, системных путях и `PATH`/`LD_LIBRARY_PATH`.

### Пример: структуры в Lime

**Lime:**
```
struct Point {
    x: i,
    y: i
}
```

В Lime структура сразу становится полноценным типом FFI - C-структурой, что по сравнению с другими языками программирования, например Python или Java, обеспечивает максимальную C-производительность. Такие типы будут работать в минимум 50 раз быстрее Python классов.

Также ключевой особенностью структур является то что они имеют методы. При помощи FFI данные структуры связываются с методами.

Пример:

### Методы у структур

```
Point:length() {
    ret self.x * self.y
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
var dict = {name: "Lime", [1]: 1}
```

**Импорт кода:**
```
load "utils"      // подключает utils.lm из той же папки
use "mathx"        // подключает библиотеку libs/mathx/setup.lm
```

**Операторы:** `+ - * / // % ^`, `== != > < >= <=`, `& |` (логические И/ИЛИ), `#` (длина), `..` (конкатенация строк).


**Match/Case:**
```
op = "+"

match op:
    case "+" print("right")
    case _ {
        print("It is not +")
        op = "+"
    }

//ИЛИ

res = match op:
    case "+" -> "right"
    case _ -> "wrong"
```


### Типы полей структур (для `struct`)

| Код | Тип C          |
|-----|----------------|
| `i` | `int`          |
| `f` | `float`        |
| `d` | `double`       |
| `s` | `const char*`  |
| `b` | `bool`         |
| `p` | `void*`        |

### Текущее состояние

- Строки без экранирования спецсимволов (пока без `\"`, `\n` и т.п.).
- Числа без экспоненциальной записи (`1e10`).
- Планируется добавить enum и interface с FFI.

---

## en English version

WARNING: This text was AUTOMATICLY TRANSLATED TO ENGLISH

### The essence of language

Lime is a language with a simple, concise syntax (`.lm` files) that compiles directly into Lua code for **LuaJIT**. Because LuaJIT is one of the fastest JIT runtimes in the world for a dynamic language, which takes up units of megabytes when executed. It also has a powerful mechanism - FFI - direct C code execution.

Lime was created to remove its main pain — verbosity.

The compiler works as follows: lexer → parser (builds AST) → code generator (AST → LuaJIT code). The compiler is written in Python in order to use its library, lupa 2.8, which provides the ability to embed python functions in Lua code. In Lime, this is done in order to be able to import any python library without much loss of speed.

### Why is it interesting

- **Execution speed** — All generated code is executed by LuaJIT, which is lightweight and fast.
- **Direct work with native libraries** without writing a C-binding or a separate module in C/C++.
- **Compact syntax** — `{ }` blocks, minimum keywords, no template code.
- **Transparency** — the output of the compiler is ordinary Lua/LuaJIT code, it can be embedded anywhere where LuaJIT already exists (game engines, embedded scripts, high-perf services).

### Example: connecting a DLL in Lime

Connect the `add(int, int)` function from `mylib.dll `:

**Lime:**
```
usec "mylib" {
    "int add(int a, int b);"
} as mylib

var result = mylib.add(2, 3)
```

The difference with Python is not only in the number of lines. In Python, you need to declare `argtypes`/`restype` separately for each function via the `ctypes` API. In Lime, you simply write the C-signature as a string — the way it looks in the header file — and get a working binding. The compiler finds the library itself ('.dll`/`.so`/`.dylib' — depending on the OS) in the project folder, working directory, system paths and `PATH`/`LD_LIBRARY_PATH'.

### Example: structures in Lime

**Lime:**
```
struct Point {
    x: i,
    y: i
}
```

In Lime, the structure immediately becomes a full-fledged type of FFI -C structure, which, compared to other programming languages, such as Python or Java, provides maximum C performance. These types will run at least 50 times faster than Python classes.

Also, a key feature of the structures is that they have methods. Using FFI, these structures are linked to methods.

Example:

### Methods for structures

```
Point:length() {
    ret self.x * self.y
}
```

The call is like in OOP: `Point:length(p)`. The compiler turns this into a regular Lua function in the structure's method table — no separate runtime environment, everything remains idiomatic Lua.

### Basic syntax

**Comments** — single-line, `//`:
``
// comment
```

**Variables:**
``
var x = 10 + 2
x = 20
a.b = 5
arr[0] = 1
```

**Conditions:**
``
if x > 5 {
ret 1
} elif x == 5 {
    ret 0
} else {
    ret -1
}
```

**Cycles:**
``
loop x < 10 { // analog while
    x = x + 1
}

for i = 0, 10, 1 { // numeric loop
    // body
}

for k, v in myTable { // a loop through the collection (analogous to pairs)
    // body
}
```

**Functions:**
```
fn add(a, b) {
    ret a + b
}
```

**Arrays and dictionaries:**
``
var arr = [1, 2, 3]
var dict = {name: "Lime", [1]: 1}
```

**Code import:**
``
load "utils" // connects utils.lm from the same folder
use "mathx" // connects the libs/mathx/setup.lm
library ``

**Operators:** `+ - * / // % ^`, `== != > < >= <=`, `& |` ( logical AND/OR), `#` (length), `..` (string concatenation).


**Match/Case:**
```
op = "+"

match op:
    case "+" print("right")
    case _ {
        print("It is not +")
        op = "+"
    }

//OR

res = match op:
    case "+" -> "right"
    case _ -> "wrong"
```


### Types of structure fields (for `struct')

| Code | Type C |
|-----|----------------|
| `i` | `int`          |
| `f` | `float`        |
| `d` | `double`       |
| `s` | `const char*`  |
| `b` | `bool`         |
| `p` | `void*`        |

### Current status

- Strings without escaping special characters (so far without `\"`, `\n`, etc.).
- Numbers without exponential notation (`1e10`).
- It is planned to add an enum and interface with FFI.