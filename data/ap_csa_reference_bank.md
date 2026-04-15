# AP Computer Science A — Question Bank & Reference Guide

> **Purpose:** Reference document for tutors and AI agents generating AP CSA practice material.
> Contains topic summaries, exam-focus analysis, agent guidance, and organized sample questions.
> Compiled from College Board official materials (2021–2025 FRQs), CrackAP, Runestone Academy,
> APCSExamPrep.com, APComputerScienceTutoring.com, and platform test JSON files.

---

## PART 1 — AP CSA TOPIC ORDER & EXAM WEIGHTS

### Curriculum Structure

The AP CSA curriculum was reorganized in 2025–2026 from 10 units to 4 larger units.
Both structures are listed here since older materials (including this platform's test files) use the 10-unit structure.

#### New 4-Unit Structure (2025–2026 Exam)

| Unit | Name | Exam Weight |
|------|------|-------------|
| 1 | Using Objects & Methods | 15–25% |
| 2 | Selection & Iteration | 25–35% |
| 3 | Class Creation | 10–18% |
| 4 | Data Collections | 30–40% |

#### Legacy 10-Unit Structure (used in this platform's test files)

| Unit | Name | Exam Weight | New Unit Mapping |
|------|------|-------------|------------------|
| 1 | Primitive Types | 2.5–5% | → New U1 |
| 2 | Using Objects | 5–7.5% | → New U1 |
| 3 | Boolean Expressions & if Statements | 15–17.5% | → New U2 |
| 4 | Iteration | 17.5–22.5% | → New U2 |
| 5 | Writing Classes | 5–7.5% | → New U3 |
| 6 | Array | 10–15% | → New U4 |
| 7 | ArrayList | 2.5–7.5% | → New U4 |
| 8 | 2D Array | 7.5–10% | → New U4 |
| 9 | Inheritance | 5–10% | → New U3/U4 |
| 10 | Recursion | 5–7.5% | → New U2/U3 |

### FRQ Format (4 Questions, 45% of score)

Every year, the four FRQs test one of four consistent types:

| FRQ | Type | Typical Focus | 2025 Example |
|-----|------|---------------|--------------|
| Q1 | Methods & Control Structures | Write 2 methods using loops, conditionals, method calls | DogWalker |
| Q2 | Class Design | Full class: constructor + instance vars + methods | SignedText |
| Q3 | Array/ArrayList | Traverse, filter, or modify a list in-place | Round |
| Q4 | 2D Array | Nested loops, grid traversal, in-place mutation | SumOrSameGame |

**Historical FRQ Topics by Type (2004–2025) — Type 1: Methods & Control Structures:**
2025 DogWalker · 2024 Feeder · 2023 AppointmentBook · 2022 Game Scoring · 2019 APCalendar · 2018 FrogSimulation · 2017 Phrase · 2012 Gray Bug

**Historical — Type 2: Class Design:**
2025 SignedText · 2024 Scoreboard · 2023 Sign · 2022 Textbook · 2019 StepTracker · 2018 CodeWordChecker · 2015 Hidden Word

**Historical — Type 3: Array/ArrayList:**
2025 Round · 2024 WordChecker · 2023 WeatherData · 2022 ReviewAnalysis · 2019 Delimiters · 2018 WordPair · 2017 Digits

**Historical — Type 4: 2D Array:**
2025 SumOrSameGame · 2024 GridPath · 2023 BoxOfCandy · 2022 Data · 2019 LightBoard · 2018 ArrayTester · 2017 Successors

---

## PART 2 — AGENT GUIDE: WRITING EXCELLENT AP CSA QUESTIONS

> Read this section before generating any questions. It distills the patterns that make
> AP CSA questions genuinely instructive vs. trivially easy or unfairly tricky.

### Core Principles

**1. One concept per question.**
The best AP questions isolate a single misconception or skill. Don't combine integer division
AND casting AND string concatenation in one question. Pick one. The trap answers should
target the specific misconception for that concept.

**2. Make every distractor meaningful.**
AP CSA wrong answers are not random. They represent the output a student would get
*if they made the most common mistake*. For integer division: offer 3.4 (wrong: treated
as float), 3.0 (wrong: assumed double return), and 4 (wrong: rounded up). Each wrong
answer tells the instructor exactly which misconception the student has.

**3. Code traces are the exam's backbone.**
The majority of MC questions ask "what is printed/returned?" — not definitions.
Every question should have runnable code when possible. Abstract conceptual questions
("what is encapsulation?") are appropriate only for Unit 5 (Classes) and Unit 9 (Inheritance).

**4. Match the AP difficulty curve.**
- Easy: straightforward syntax/output — student just needs to trace the code
- Medium: requires knowing a rule (e.g., how `remove(int)` vs `remove(Object)` works in ArrayList)
- Hard: interaction of multiple concepts, or a subtle off-by-one / null pointer trap

**5. Guiding questions are Socratic, not leading.**
A guiding question should make the student arrive at the answer themselves.
BAD: "Remember that integer division truncates — what is 17/5?" (gives away answer)
GOOD: "What data type does dividing two int values produce in Java?" (makes student reason)
Each question needs 2–3 guiding questions. The last one should get very close to the answer
but not state it.

**6. FRQ-style questions must have complete method context.**
Always provide the class name, method signature, parameter names and types, return type,
and a description of what the method should do. Students should not have to guess context.
Model after actual College Board FRQ structure: describe the class first, then the specific method.

**7. Topic tags drive adaptive targeting.**
Always include at least one topic_tag. Common tags used in this platform:
`variables_and_types`, `operators`, `conditionals`, `loops`, `arrays`, `2d_arrays`,
`methods`, `parameter_passing`, `strings`, `classes_and_objects`, `inheritance`,
`polymorphism`, `recursion`, `arraylist`, `searching_sorting`, `interfaces`

**8. Always-tested patterns to prioritize:**
- Integer division truncation (Unit 1) — appears in >80% of released exams
- String methods: substring, indexOf, length (Unit 2)
- Short-circuit evaluation: && and || (Unit 3)
- Off-by-one loop errors (Unit 4)
- Reference semantics vs value semantics (Unit 5)
- Array traversal + accumulator pattern (Unit 6)
- ArrayList remove(int index) vs remove(Object) ambiguity (Unit 7)
- 2D array row/col indexing: arr[row][col], arr.length, arr[0].length (Unit 8)
- Dynamic dispatch / polymorphism (Unit 9)
- Recursive base case + trace (Unit 10)

### JSON Schema Reminder

Questions in this platform use this structure:

```json
{
  "id": "unique_id",
  "type": "multiple_choice | free_response | code_trace",
  "topic_tags": ["arrays", "loops"],
  "difficulty": "easy | medium | hard",
  "prompt": "Question text",
  "code_block": "Java code (null if none)",
  "options": { "A": "...", "B": "...", "C": "...", "D": "..." },
  "answer_key": "B",
  "explanation": "Why the answer is correct + why the distractors are wrong",
  "guiding_questions": [
    { "id": "q_g1", "text": "Socratic probe 1" },
    { "id": "q_g2", "text": "Socratic probe 2" }
  ]
}
```

**For free_response / FRQ questions** (instructor reference, not yet platform-supported):
Include `prompt` (full problem statement), `code_block` (any provided class skeletons),
and `answer_key` (sample solution code). No `options` field.

---

## PART 3 — TOPIC SECTIONS WITH EXAM FOCUS AND SAMPLE QUESTIONS

---

### UNIT 1 — Primitive Types
*(New curriculum: Unit 1 — Using Objects & Methods)*

**What the AP exam always tests:**
- Integer division truncates toward zero: `7/2 = 3`, never `3.5`
- The modulo operator `%` for remainder: `7 % 2 = 1`
- Type promotion and casting: `(double) x / y` vs `x / y`
- Integer overflow is NOT tested (out of scope for AP CSA)
- Order of compound assignment operators: `+=`, `-=`, `*=`, `/=`, `%=`

**What the exam increasingly tests (2022–2025):**
- Distinguishing `int` truncation from `double` arithmetic in the same expression
- Mixing `int` and `double` operands without explicit casts
- The string concatenation trap: `"Sum: " + 1 + 2` → `"Sum: 12"` not `"Sum: 3"`

**Common student errors:**
- Assuming `/` performs floating-point division when both operands are `int`
- Forgetting that `%` has the same precedence as `*` and `/`
- Believing that `double result = 7 / 2` gives `3.5` (it gives `3.0` — division happens first)

---

#### Sample Question U1-1 (Easy)

**Prompt:** What is the value of the expression `17 / 5` in Java?

| Option | Value |
|--------|-------|
| A | 3.4 |
| **B** | **3** ✓ |
| C | 3.0 |
| D | 2 |
| E | Compile error: integer division is not allowed |

**Answer: B**
Java integer division truncates the decimal portion. 17 / 5 = 3 remainder 2, result is 3.

**Guiding questions:**
1. What data type is the result of dividing two `int` values in Java?
2. How is integer division different from floating-point division?

---

#### Sample Question U1-2 (Medium)

**Prompt:** What is printed when the following code executes?

```java
int x = 7;
int y = 2;
double result = (double) x / y;
System.out.println(result);
```

| Option | Value |
|--------|-------|
| A | 3 |
| B | 3.0 |
| **C** | **3.5** ✓ |
| D | 3.4 |
| E | Compile error |

**Answer: C**
The cast `(double) x` converts x to `7.0` before division. `7.0 / 2 = 3.5`.

**Guiding questions:**
1. What does `(double)` do to the value of x before the division?
2. If you removed the cast, what would `result` be?

---

#### Sample Question U1-3 (Medium)

**Prompt:** What is the value of `x` after these statements?

```java
int x = 5;
x += 3;
x *= 2;
x -= 4;
```

| Option | Value |
|--------|-------|
| **A** | **12** ✓ |
| B | 8 |
| C | 16 |
| D | 6 |
| E | 14 |

**Answer: A**
`x=5` → `+= 3` → `x=8` → `*= 2` → `x=16` → `-= 4` → `x=12`

---

### UNIT 2 — Using Objects (String, Math, Wrapper Classes)
*(New curriculum: Unit 1 — Using Objects & Methods)*

**What the AP exam always tests:**
- `String` methods: `substring(a, b)`, `indexOf(str)`, `length()`, `equals()`, `compareTo()`
- `substring(a, b)` is inclusive of index `a`, exclusive of index `b`
- `Math.random()` returns `[0.0, 1.0)` — the formula for a range is `(int)(Math.random() * n) + min`
- `Math.abs()`, `Math.pow()`, `Math.sqrt()` syntax
- Strings are **immutable** — methods return new Strings, never modify in place

**What the exam increasingly tests (2022–2025):**
- Chaining String methods: `s.substring(1).indexOf("x")`
- `charAt(i)` for character-level traversal (bridging Unit 2 → Unit 4)
- Integer vs. Double wrapper classes, autoboxing with ArrayList<Integer>

**Common student errors:**
- Off-by-one on `substring`: `"hello".substring(1, 3)` → `"el"` (not `"ell"`)
- Thinking `indexOf` is 1-based (it's 0-based)
- Using `==` to compare Strings (must use `.equals()`)

---

#### Sample Question U2-1 (Easy)

**Prompt:** What is printed when the following code executes?

```java
String s = "computer";
System.out.println(s.substring(3, 6));
```

| Option | Value |
|--------|-------|
| **A** | **put** ✓ |
| B | pute |
| C | com |
| D | ter |
| E | omp |

**Answer: A**
`substring(3, 6)` returns characters at indices 3, 4, 5 → `'p'`, `'u'`, `'t'` → `"put"`. Index 6 is excluded.

**Guiding questions:**
1. What index does `'c'` have in `"computer"`? Count from 0.
2. In `substring(a, b)`, is the character at index `b` included in the result?

---

#### Sample Question U2-2 (Medium)

**Prompt:** Which correctly generates a random integer in the range 1–6 (inclusive), simulating a die roll?

| Option | Value |
|--------|-------|
| A | `(int)(Math.random() * 6)` |
| **B** | **`(int)(Math.random() * 6) + 1`** ✓ |
| C | `(int)(Math.random() * 7)` |
| D | `(int)(Math.random() * 5) + 1` |
| E | `Math.random() * 6 + 1` |

**Answer: B**
`Math.random()` gives `[0.0, 1.0)`. × 6 gives `[0.0, 6.0)`. Cast to int: 0–5. +1: 1–6.

**Guiding questions:**
1. What is the largest value `Math.random()` can ever return?
2. If `Math.random()` returns 0.99, what is `(int)(0.99 * 6) + 1`?

---

### UNIT 3 — Boolean Expressions & if Statements
*(New curriculum: Unit 2 — Selection & Iteration)*

**What the AP exam always tests:**
- Evaluating complex boolean expressions with `&&`, `||`, `!`
- Short-circuit evaluation: `&&` stops if left is false; `||` stops if left is true
- De Morgan's Laws: `!(a && b)` is equivalent to `(!a || !b)`
- if/else-if/else chains — tracing which branch executes
- Nested conditionals — order of evaluation matters

**What the exam increasingly tests (2022–2025):**
- Compound conditions that combine relational operators: `x > 0 && x < 10`
- Recognizing logically equivalent boolean expressions (multiple correct answer forms)
- Off-by-one in boundary conditions: `<` vs `<=`

**Common student errors:**
- Confusing `=` (assignment) with `==` (comparison)
- Forgetting `!` flips the entire condition, not just part of it
- Misreading De Morgan's Law direction

---

#### Sample Question U3-1 (Medium)

**Prompt:** What is the value of `!(true && false) || (false || true)`?

| Option | Value |
|--------|-------|
| **A** | **true** ✓ |
| B | false |
| C | Compile error |
| D | Cannot be determined |
| E | null |

**Answer: A**
`!(true && false)` = `!(false)` = `true`. `(false || true)` = `true`. `true || true` = `true`.

---

#### Sample Question U3-2 (Medium)

**Prompt:** What is printed when the following code executes?

```java
int x = 7;
int y = 3;
if ((x < 10) && (y < 0))
    System.out.println("Value is: " + x * y);
else
    System.out.println("Value is: " + x / y);
```

| Option | Value |
|--------|-------|
| A | Value is: 21 |
| B | Value is: 2.3333333 |
| **C** | **Value is: 2** ✓ |
| D | Value is: 0 |
| E | Value is: 1 |

**Answer: C**
`(x < 10)` is true, but `(y < 0)` is false. `true && false = false`, so the `else` runs: `7 / 3 = 2` (integer division).

**Guiding questions:**
1. Is `(y < 0)` true or false when `y = 3`?
2. For `&&` to be true, what must be true about both sides?

---

#### Sample Question U3-3 (Hard)

**Prompt:** What does `classify(15)` return?

```java
public static String classify(int n) {
    if (n % 3 == 0 && n % 5 == 0)
        return "FizzBuzz";
    else if (n % 3 == 0)
        return "Fizz";
    else if (n % 5 == 0)
        return "Buzz";
    else
        return "" + n;
}
```

| Option | Value |
|--------|-------|
| A | Fizz |
| B | Buzz |
| **C** | **FizzBuzz** ✓ |
| D | 15 |
| E | FizzBuzz15 |

**Answer: C**
`15 % 3 == 0` (true) AND `15 % 5 == 0` (true) → first condition met → `"FizzBuzz"` returned.

---

### UNIT 4 — Iteration (Loops)
*(New curriculum: Unit 2 — Selection & Iteration)*

**What the AP exam always tests:**
- `for` loop trace: counting iterations, knowing the final value of the loop variable
- `while` loop trace: identifying when the condition becomes false
- Accumulator patterns: sum, count, max, min
- Nested loops: inner loop runs completely for each outer iteration
- Enhanced for loop (`for (Type x : collection)`) — read-only traversal

**What the exam increasingly tests (2022–2025):**
- Off-by-one errors: `i < arr.length` vs `i <= arr.length`
- Nested loop complexity analysis: how many total inner iterations?
- String traversal using `charAt()` inside a for loop
- While loops that may not execute (condition false initially)

**Common student errors:**
- Believing the loop variable is accessible after the loop (it's block-scoped)
- `i = i + 2` step counting — miscounting which indices are visited
- Infinite loop: forgetting to update the loop variable in a while loop

---

#### Sample Question U4-1 (Medium)

**Prompt:** What value is printed when the following code runs?

```java
int count = 0;
for (int i = 1; i <= 5; i++) {
    if (i % 2 == 0) count++;
}
System.out.println(count);
```

| Option | Value |
|--------|-------|
| A | 5 |
| B | 3 |
| **C** | **2** ✓ |
| D | 1 |
| E | 0 |

**Answer: C**
`i = 1, 2, 3, 4, 5`. Only `i=2` and `i=4` satisfy `i % 2 == 0` → count increments twice.

---

#### Sample Question U4-2 (Hard)

**Prompt:** What value is printed when the following code runs?

```java
int sum = 0;
for (int i = 0; i < 3; i++) {
    for (int j = 0; j < i; j++) {
        sum++;
    }
}
System.out.println(sum);
```

| Option | Value |
|--------|-------|
| A | 6 |
| B | 9 |
| **C** | **3** ✓ |
| D | 0 |
| E | 4 |

**Answer: C**
When `i=0`: inner loop runs 0 times. When `i=1`: inner runs 1 time. When `i=2`: inner runs 2 times. Total: 0+1+2 = 3.

**Guiding questions:**
1. When `i=0`, the condition is `j < 0` — how many times does that loop execute?
2. Make a table: for each value of `i` (0, 1, 2), how many times does the inner loop run?

---

#### Sample Question U4-3 (Medium) — While Loop

**Prompt:** What is printed when the following code executes?

```java
int n = 1;
while (n < 100) {
    n *= 2;
}
System.out.println(n);
```

| Option | Value |
|--------|-------|
| A | 64 |
| B | 100 |
| **C** | **128** ✓ |
| D | 256 |
| E | Infinite loop |

**Answer: C**
`n` doubles: 1→2→4→8→16→32→64→128. At `n=128`, condition `128 < 100` is false.

---

### UNIT 5 — Writing Classes
*(New curriculum: Unit 3 — Class Creation)*

**What the AP exam always tests:**
- Instance variables declared `private`
- Constructors: initialize all instance variables; same name as class, no return type
- Accessor (getter) methods: `public ReturnType getName() { return name; }`
- Mutator (setter) methods: `public void setName(String name) { this.name = name; }`
- The `this` keyword for disambiguation
- `toString()` override returning a meaningful String
- `equals()` comparing instance variable values (not references)

**What the exam increasingly tests (2022–2025):**
- Static vs. instance method distinction (FRQ Class Writing type)
- Reference semantics: two variables can point to the same object
- Accumulated state across multiple method calls on the same object
- FRQ Q2 is always a complete class-writing exercise

**Common student errors:**
- Using `public` for instance variables (breaks encapsulation — costs FRQ points)
- Missing `this.` when parameter name matches instance variable name
- Forgetting constructor has no return type (not even `void`)
- Using `==` for object comparison instead of `.equals()`

---

#### Sample Question U5-1 (Medium)

**Prompt:** Why are instance variables typically declared `private` in Java?

| Option | Value |
|--------|-------|
| A | Private variables execute faster |
| B | To prevent the variable from ever being changed |
| **C** | **To enforce encapsulation — controlling access through getter/setter methods** ✓ |
| D | Java requires all instance variables to be private |
| E | Private variables cannot be inherited |

**Answer: C**
`private` enforces encapsulation. External classes must go through accessor/mutator methods.

---

#### Sample Question U5-2 (Hard) — Reference Semantics

**Prompt:** What is printed when the following code executes?

```java
public class Counter {
    private int count;
    public Counter() { count = 0; }
    public void increment() { count++; }
    public int getCount() { return count; }
}

// In main:
Counter c1 = new Counter();
Counter c2 = c1;
c1.increment();
c1.increment();
c2.increment();
System.out.println(c1.getCount());
```

| Option | Value |
|--------|-------|
| A | 0 |
| B | 1 |
| C | 2 |
| **D** | **3** ✓ |
| E | Compile error |

**Answer: D**
`c2 = c1` makes both variables reference the **same** Counter object. All three `increment()` calls operate on that single object → `count = 3`.

**Guiding questions:**
1. Does `c2 = c1` create a new Counter object, or make `c2` point to the same one `c1` already points to?
2. How many Counter objects exist in memory after the assignments?

---

### UNIT 6 — Arrays
*(New curriculum: Unit 4 — Data Collections)*

**What the AP exam always tests:**
- Array declaration and initialization: `int[] arr = new int[5];` or `int[] arr = {1,2,3};`
- Zero-based indexing: `arr[0]` through `arr[arr.length - 1]`
- `ArrayIndexOutOfBoundsException` from off-by-one errors
- Standard traversal patterns: accumulator (sum/count), find max/min, copy
- Passing arrays to methods (pass by reference — method can modify the original array)
- `arr.length` (no parentheses) to get size

**What the exam increasingly tests (2022–2025):**
- Methods that return a new array (not void)
- Partial array filling with a sentinel or condition
- Step-increment traversal: `i += 2` to skip elements
- FRQ questions that mix array traversal with boolean conditions

**Common student errors:**
- `arr.length()` with parentheses (compile error — length is a field, not a method)
- Using `arr.length` as the last valid index (`arr[arr.length]` is out of bounds)
- Treating arrays as pass-by-value (they're pass-by-reference)

---

#### Sample Question U6-1 (Medium) — Max Finding

**Prompt:** What is printed when the following code executes?

```java
int[] arr = {5, 3, 8, 1, 9};
int max = arr[0];
for (int i = 1; i < arr.length; i++) {
    if (arr[i] > max) max = arr[i];
}
System.out.println(max);
```

| Option | Value |
|--------|-------|
| A | 5 |
| **B** | **9** ✓ |
| C | 1 |
| D | 8 |
| E | 3 |

**Answer: B**
Starting from `arr[0]=5`: `8 > 5` (max=8), `9 > 8` (max=9). Final max = 9.

**Guiding questions:**
1. Why does the loop start at index 1 rather than index 0?
2. After the loop processes `arr[4]=9`, what is `max`?

---

#### Sample Question U6-2 (Medium) — Step Traversal

**Prompt:** What does `mystery({3, 6, 1, 0, 1, 4, 2})` return?

```java
public static int mystery(int[] arr) {
    int x = 0;
    for (int k = 0; k < arr.length; k = k + 2)
        x = x + arr[k];
    return x;
}
```

| Option | Value |
|--------|-------|
| A | 5 |
| B | 6 |
| **C** | **7** ✓ |
| D | 10 |
| E | 17 |

**Answer: C**
`k` takes values 0, 2, 4, 6: `arr[0]=3`, `arr[2]=1`, `arr[4]=1`, `arr[6]=2`. Sum = 3+1+1+2 = 7.

**Guiding questions:**
1. What indices does `k` take on? List them.
2. Are you summing even-indexed or odd-indexed elements?

---

### UNIT 7 — ArrayList
*(New curriculum: Unit 4 — Data Collections)*

**What the AP exam always tests:**
- `ArrayList<Type>` syntax, declaration, and initialization
- Methods: `add(item)`, `add(index, item)`, `get(index)`, `set(index, item)`, `remove(index)`, `size()`
- The `remove(int index)` vs `remove(Object o)` disambiguation with Integer
- Forward traversal while removing causes index-shifting bugs — must traverse backwards or use iterator
- `ArrayList` is dynamic (unlike arrays, it resizes automatically)
- `ArrayList` cannot hold primitives — must use `Integer`, `Double`, `Boolean`

**What the exam increasingly tests (2022–2025):**
- In-place modification with `set()` — FRQ 2025 Round was entirely about `set()` vs `add()` trap
- Filtering: building a new list or removing from an existing one based on condition
- Autoboxing/unboxing implications when comparing Integer objects with `==` vs `.equals()`

**Common student errors:**
- `list[i]` instead of `list.get(i)` (compile error — ArrayList is not an array)
- `list.length` instead of `list.size()` (compile error)
- Using `add()` when `set()` is needed (inserts a new element vs replacing existing)
- Removing during forward iteration without decrementing index

---

#### Sample Question U7-1 (Medium)

**Prompt:** What is printed when the following code executes?

```java
ArrayList<Integer> list = new ArrayList<>();
list.add(10);
list.add(20);
list.add(30);
list.remove(1);
System.out.println(list);
```

| Option | Value |
|--------|-------|
| **A** | **[10, 30]** ✓ |
| B | [20, 30] |
| C | [10, 20] |
| D | [10, 20, 30] |
| E | [30] |

**Answer: A**
`remove(1)` removes the element at **index** 1, which is 20. Remaining: [10, 30].

**Guiding questions:**
1. ArrayList has two `remove` methods. This call uses an `int` argument — does that remove by index or by value?
2. After the three `add()` calls, what are the indices of 10, 20, and 30?

---

#### Sample Question U7-2 (Hard) — In-Place Modification Trap

**Prompt:** A student writes a method to double every element in an ArrayList:

```java
// Version A — using set()
for (int i = 0; i < list.size(); i++) {
    list.set(i, list.get(i) * 2);
}

// Version B — using add() and remove()
for (int i = 0; i < list.size(); i++) {
    int val = list.get(i);
    list.remove(i);
    list.add(i, val * 2);
}
```

If `list = [1, 2, 3]`, which version correctly produces `[2, 4, 6]`?

| Option | Value |
|--------|-------|
| **A** | **Version A only** ✓ |
| B | Version B only |
| C | Both produce [2, 4, 6] |
| D | Neither produces [2, 4, 6] |
| E | Version A, but only for even-length lists |

**Answer: A**
`set()` replaces in place — correct. Version B works too (remove then insert at same index), but is unnecessarily complex and fragile. In FRQ grading, `set()` is the expected approach.

---

### UNIT 8 — 2D Arrays
*(New curriculum: Unit 4 — Data Collections)*

**What the AP exam always tests:**
- Declaration: `int[][] grid = new int[rows][cols];`
- Indexing: `grid[row][col]` — row index FIRST, column index SECOND
- Row count: `grid.length`
- Column count: `grid[0].length` (not `grid.length`)
- Standard nested loop traversal (row-major order)
- Summing rows, columns, or diagonals

**What the exam increasingly tests (2022–2025):**
- Accessing neighbor cells: `grid[row-1][col]`, `grid[row][col+1]` — always requires bounds check
- Column-major traversal (outer loop on column)
- In-place mutation of cells based on neighboring values (2025 SumOrSameGame, 2024 GridPath)
- Passing 2D arrays to methods

**Common student errors:**
- `grid[col][row]` — swapped indices
- `grid.length` used as column count (it's row count)
- Missing bounds check before accessing neighbors
- Using `grid.length()` with parentheses (compile error)

---

#### Sample Question U8-1 (Easy)

**Prompt:** What is printed when the following code executes?

```java
int[][] grid = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
System.out.println(grid[1][2]);
```

| Option | Value |
|--------|-------|
| **A** | **6** ✓ |
| B | 8 |
| C | 5 |
| D | 2 |
| E | 7 |

**Answer: A**
`grid[1][2]` → row 1 is `{4, 5, 6}` → column 2 is `6`.

**Guiding questions:**
1. In `grid[r][c]`, what does the first index represent?
2. List all three rows. What values are in row 1?

---

#### Sample Question U8-2 (Hard) — Nested Loop + Condition

**Prompt:** What is printed when the following code executes?

```java
int[][] mat = {{1, 2}, {3, 4}, {5, 6}};
int total = 0;
for (int r = 0; r < mat.length; r++) {
    for (int c = 0; c < mat[r].length; c++) {
        if ((r + c) % 2 == 0)
            total += mat[r][c];
    }
}
System.out.println(total);
```

| Option | Value |
|--------|-------|
| A | 9 |
| B | 21 |
| C | 10 |
| D | 6 |
| E | 15 |

**Answer: C (10)**
Cells where `(r+c) % 2 == 0`: (0,0)→1, (1,1)→4, (2,0)→5. Sum = 1+4+5 = 10.

**Guiding questions:**
1. List all valid (r,c) pairs. For which ones is `(r+c)` even?
2. What are `mat.length` and `mat[0].length` for a 3-row, 2-column array?

---

### UNIT 9 — Inheritance & Polymorphism
*(New curriculum: Unit 3 — Class Creation)*

**What the AP exam always tests:**
- A superclass variable can hold a subclass object: `Animal a = new Dog();`
- Dynamic dispatch (late binding): the **runtime type** determines which overridden method executes
- `super` keyword: calling superclass constructor (`super(args)`) and superclass methods (`super.method()`)
- Method overriding vs. method overloading distinction
- `instanceof` operator (occasionally, less tested)
- Abstract classes: cannot be instantiated; subclasses must implement abstract methods

**What the exam increasingly tests (2022–2025):**
- Compile-time type vs. runtime type — what compiles vs. what actually runs
- FRQ class hierarchy with `super` calls in overridden methods (2022 Textbook FRQ)
- Recognizing that private superclass methods are NOT inherited (not overridable)

**Common student errors:**
- Thinking `Animal a = new Dog()` causes a compile error (it doesn't — Dog IS-A Animal)
- Thinking the declared type (Animal) determines which `speak()` runs (it doesn't — runtime type does)
- Confusing overriding (same signature) with overloading (different parameters)
- Forgetting `super()` must be the first line in a subclass constructor

---

#### Sample Question U9-1 (Medium) — Polymorphism

**Prompt:** Class `Animal` has a method `speak()` that returns `"..."`. Subclass `Dog` overrides `speak()` to return `"Woof"`. What is printed?

```java
Animal a = new Dog();
System.out.println(a.speak());
```

| Option | Value |
|--------|-------|
| A | ... |
| **B** | **Woof** ✓ |
| C | Compile error: Animal variable cannot hold a Dog object |
| D | Runtime error: wrong method called |
| E | null |

**Answer: B**
Dynamic dispatch: declared type is `Animal`, runtime type is `Dog`. Java calls `Dog`'s `speak()` → `"Woof"`.

**Guiding questions:**
1. Can a superclass variable hold a reference to a subclass object in Java?
2. At runtime, which `speak()` is called — `Animal`'s or `Dog`'s?

---

#### Sample Question U9-2 (Hard) — Compile vs. Runtime Type

**Prompt:** Which statement about subclass methods is **false**?

| Option | Value |
|--------|-------|
| **A** | **Writing two subclass methods with the same name but different parameters is method overriding** ✓ (FALSE) |
| B | A public method in a subclass not in its superclass is not accessible by the superclass |
| C | A private method in a superclass is not inherited by its subclass |
| D | Two different subclasses of the same superclass inherit the same public methods of the superclass |
| E | If Class1 is superclass of Class2, which is superclass of Class3, and Class2 has no overrides, Class3 inherits all public methods of Class1 |

**Answer: A**
Same name with **different parameters** is method **overloading** (not overriding). Overriding requires the same signature.

---

#### Sample Question U9-3 (Medium) — super Keyword

**Prompt:** A `Textbook` subclass extends `Book`. `Book`'s `getBookInfo()` returns `title + " - $" + price`. `Textbook` overrides it to include the edition. What is printed?

```java
Textbook t = new Textbook("Biology", 49.75, 2);
System.out.println(t.getBookInfo());
```

| Option | Value |
|--------|-------|
| A | Biology - $49.75 |
| **B** | **Biology - $49.75 - Edition 2** ✓ |
| C | Compile error: Textbook does not inherit getBookInfo() |
| D | Biology |
| E | $49.75 - Edition 2 |

**Answer: B**
`Textbook.getBookInfo()` calls `super.getBookInfo()` (→ `"Biology - $49.75"`) and appends `" - Edition 2"`.

---

### UNIT 10 — Recursion
*(New curriculum: Unit 2 — Selection & Iteration)*

**What the AP exam always tests:**
- Identifying the base case (the condition that stops recursion)
- Tracing a recursive method: building the call stack and unwinding it
- Recursive methods that return a value (not just print)
- Simple patterns: countdown, sum of integers, factorial, fibonacci
- Understanding that each call has its own local variable copies

**What the exam increasingly tests (2022–2025):**
- Recursive methods on Strings: `mystery("abc")` → processes one character and recurses on `s.substring(1)`
- Recognizing when a method has no base case (infinite recursion — stack overflow)
- Comparing iterative vs. recursive solutions for the same problem

**Common student errors:**
- Thinking variables are shared across recursive calls (they're not — each call is independent)
- Confusing the base case with the recursive case
- Off-by-one in base case: `if (n == 0)` vs `if (n <= 0)`
- Not returning the result of the recursive call

---

#### Sample Question U10-1 (Medium) — Trace

**Prompt:** What does `mystery(4)` return?

```java
public static int mystery(int n) {
    if (n <= 0)
        return 0;
    return n + mystery(n - 1);
}
```

| Option | Value |
|--------|-------|
| A | 4 |
| B | 0 |
| C | 6 |
| **D** | **10** ✓ |
| E | Infinite recursion |

**Answer: D**
`mystery(4)` = 4 + `mystery(3)` = 4 + 3 + `mystery(2)` = 4+3+2 + `mystery(1)` = 4+3+2+1 + `mystery(0)` = 4+3+2+1+0 = 10.

**Guiding questions:**
1. What is the base case? What does the method return when `n <= 0`?
2. Write out the call chain: `mystery(4)` → `mystery(3)` → ... What is each return value?

---

#### Sample Question U10-2 (Medium) — String Recursion

**Prompt:** What does `mystery("abcd")` return?

```java
public static String mystery(String s) {
    if (s.length() == 0)
        return "";
    return mystery(s.substring(1)) + s.charAt(0);
}
```

| Option | Value |
|--------|-------|
| A | abcd |
| **B** | **dcba** ✓ |
| C | "" |
| D | a |
| E | bcd |

**Answer: B**
The recursive call processes the rest of the string first (building up from the end), then appends the first character. This reverses the string.

**Guiding questions:**
1. What is the base case? What is returned when `s` is empty?
2. Trace: `mystery("abcd")` calls `mystery("bcd")` + `'a'`. What does `mystery("bcd")` produce?

---

#### Sample Question U10-3 (Hard) — Identify Base Case Error

**Prompt:** A student writes a method to count how many times a digit appears in a number:

```java
public static int countDigit(int n, int digit) {
    if (n == 0) return 0;
    int last = n % 10;
    if (last == digit)
        return 1 + countDigit(n / 10, digit);
    else
        return countDigit(n / 10, digit);
}
```

What is the result of `countDigit(300, 0)`?

| Option | Value |
|--------|-------|
| A | 3 |
| **B** | **2** ✓ |
| C | 0 |
| D | 1 |
| E | Infinite recursion |

**Answer: B**
`300 / 10 = 30 / 10 = 3`. At `n=3`: `3 % 10 = 3 ≠ 0`, recurse → `n=0` → base case returns 0. Count from `30` (last digit = 0 → +1) and `300` (last digit = 0 → +1). Total = 2. *Note: the base case `n==0` will miss a zero in that position — known edge case for negative numbers and zero itself, but standard for this exam context.*

---

## PART 4 — FRQ REFERENCE: 2021–2025 OFFICIAL QUESTIONS

These are the actual College Board FRQ topics. Use as models for generating FRQ-style questions.

### 2025 FRQs
| # | Name | Type | Key Concepts |
|---|------|------|--------------|
| 1 | DogWalker | Methods & Control | `Math.min()`, loop accumulation, method decomposition |
| 2 | SignedText | Class Design | Constructor, String field, class anatomy |
| 3 | Round | ArrayList | `set()` vs `add()`, in-place modification, integer rounding |
| 4 | SumOrSameGame | 2D Array | Nested loops, conditional merge, in-place mutation |

### 2024 FRQs
| # | Name | Type | Key Concepts |
|---|------|------|--------------|
| 1 | Feeder | Methods & Control | Bird feeder simulation, `Math.min()`, loop with accumulator |
| 2 | Scoreboard | Class Design | Constructor, tracking wins/losses, computed output |
| 3 | WordChecker | ArrayList | String comparison, filtering, list traversal |
| 4 | GridPath | 2D Array | Path traversal, row/column bounds, neighbor access |

### 2023 FRQs
| # | Name | Type | Key Concepts |
|---|------|------|--------------|
| 1 | AppointmentBook | Methods & Control | Nested conditionals, time slots, method calls |
| 2 | Sign | Class Design | String fields, constructor, computed display |
| 3 | WeatherData | ArrayList | Double list, accumulator, filtering |
| 4 | BoxOfCandy | 2D Array | Grid rotation, column traversal, null handling |

### 2022 FRQs
| # | Name | Type | Key Concepts |
|---|------|------|--------------|
| 1 | Game | Methods & Control | Score accumulation, bonus calculation |
| 2 | Textbook | Class Design + Inheritance | `super` call, method override, `extends` |
| 3 | ReviewAnalysis | ArrayList | String ArrayList, filtering by rating |
| 4 | Data | 2D Array | Random grid, row/column statistics |

### 2021 FRQs
| # | Name | Type | Key Concepts |
|---|------|------|--------------|
| 1 | WordMatch | Methods & Control | String comparison, loops, method calls |
| 2 | CombinedTable | Class Design | Multi-object composition |
| 3 | ClubMembers | ArrayList | Membership list, removal, traversal |
| 4 | ArrayResizer | 2D Array | Jagged array, resize algorithm |

---

## PART 5 — FRQ SCORING PATTERNS & COMMON POINT-LOSS

> Use this to calibrate difficulty and help students understand what earns partial credit.

### Universal Point Distribution (9 points per FRQ)
- **Algorithm correctness:** 3–4 points (biggest bucket — logic must be right)
- **Language features used correctly:** 2–3 points (proper `set()`, correct loop syntax, etc.)
- **Method signatures / class header:** 1–2 points (quick points — don't lose these)
- **Edge case handling:** 0–1 point (sometimes included; often not penalized)

### Top Reasons Students Lose Points (FRQ)

**Class Design (Q2):**
- Instance variables declared `public` instead of `private` — lose 1 point
- Constructor doesn't initialize all instance variables
- Missing class header or closing brace

**ArrayList (Q3):**
- Using `add()` instead of `set()` for in-place replacement (2025 Round — this was the trap)
- Forward iteration while removing elements (index shift bug)
- Using `list.length` instead of `list.size()`
- Bracket notation `list[i]` instead of `list.get(i)`

**2D Array (Q4):**
- Swapped indices: `arr[col][row]` instead of `arr[row][col]`
- `arr.length` used as column count (must be `arr[0].length`)
- Missing bounds check for neighbor access

**Methods & Control (Q1):**
- Missing return statements in all code paths
- Using `=` instead of `==` in conditions
- String comparison with `==` instead of `.equals()`

### Time Management (90 min for 4 FRQs)
| FRQ | Recommended Time |
|-----|-----------------|
| Q1 Methods & Control | 17–20 min (usually easiest) |
| Q2 Class Design | 25–27 min (most complete writing) |
| Q3 ArrayList | 20–23 min |
| Q4 2D Array | 23–25 min (usually hardest) |

---

## PART 6 — QUICK REFERENCE: JAVA SYNTAX TESTED ON AP CSA

```java
// String methods
s.length()          // number of characters
s.substring(a, b)   // chars at indices a to b-1 (b excluded)
s.indexOf("x")      // first index of substring, -1 if not found
s.equals("abc")     // true/false — use instead of ==
s.charAt(i)         // char at index i

// Math class
Math.random()       // [0.0, 1.0) double
Math.abs(x)         // absolute value
Math.pow(base, exp) // base^exp (returns double)
Math.sqrt(x)        // square root (returns double)
Math.min(a, b)      // minimum of two values

// Array
int[] arr = new int[n];    // creates array of size n (all zeros)
arr.length                 // size (NOT a method — no parentheses)
arr[i]                     // access element at index i (0-based)

// ArrayList
ArrayList<Integer> list = new ArrayList<>();
list.add(item)             // append to end
list.add(index, item)      // insert at index
list.get(index)            // retrieve element
list.set(index, item)      // replace element — returns old value
list.remove(index)         // remove by index
list.size()                // number of elements (IS a method — parentheses!)

// 2D Array
int[][] grid = new int[rows][cols];
grid.length                // number of rows
grid[0].length             // number of columns
grid[row][col]             // access element (row FIRST)

// Inheritance
class Dog extends Animal { ... }
super.method()             // call superclass method
super(args)                // call superclass constructor (first line only)

// Casting
(double) x / y             // cast x to double before division
(int) 3.7                  // truncates to 3 (NOT rounds)
```

---

*Sources: College Board AP Central (apcentral.collegeboard.org), APCSExamPrep.com, CrackAP.com, APComputerScienceTutoring.com, Runestone Academy CSAwesome, Wiingy AP CSA Guide, this platform's ap_csa_assessment_2021_2024.json.*
