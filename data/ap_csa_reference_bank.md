# AP Computer Science A — Exam Reference & Strategy Guide

> **Purpose:** Authoritative reference for tutors and AI agents running this platform.
> Contains exam mechanics, scoring rules, strategy by section and FRQ type,
> topic-level tips and common mistakes, and agent guidance for question generation.
> Questions live in `data/ap_csa_question_bank.json` — not here.
>
> **Sources:** College Board AP Central (2021–2025 scoring guidelines, chief reader reports),
> APCSExamPrep.com, Runestone Academy CSAwesome, this platform's assessment JSON files.

---

## PART 1 — EXAM FORMAT & SCORING

### Section Breakdown

| Section | Questions | Time | Score Weight |
|---------|-----------|------|-------------|
| I: Multiple Choice | 42 questions | 90 minutes | 55% |
| II: Free Response | 4 questions | 90 minutes | 45% |

- No calculator permitted in either section
- Java Quick Reference Sheet is provided (see Part 6)
- No penalty for wrong MC answers — always guess

### Raw Score Formula

```
Composite = (MC correct / 42) × 55  +  (FRQ points / 36) × 45
```

FRQ raw score is out of 36 (4 questions × 9 points each).
Composite is out of 100.

### AP Grade Thresholds (estimated, based on historical data)

| AP Score | Composite Range | Approximate % |
|----------|----------------|--------------|
| 5 | 61–100 | ~78%+ |
| 4 | 50–60 | ~65–77% |
| 3 | 34–49 | ~46–64% |
| 2 | 20–33 | ~27–45% |
| 1 | 0–19 | below 27% |

2025 mean score: 3.18. 67.2% of students scored 3 or higher.

### FRQ Structure (consistent every year)

| Question | Type | Typical Difficulty | Avg Time |
|----------|------|--------------------|----------|
| Q1 | Methods & Control Structures | Medium | 17–20 min |
| Q2 | Class Design | Medium-Hard | 25–27 min |
| Q3 | Array / ArrayList | Medium | 20–23 min |
| Q4 | 2D Array | Hard | 23–25 min |

> **Q4 first strategy:** Many top scorers complete Q4 last — but Q1 (Methods & Control) is
> usually the most approachable. Attempt in order of your comfort, not exam order.
> Never spend more than 30 minutes on a single question.

---

## PART 2 — CURRICULUM STRUCTURE & EXAM WEIGHTS

### New 4-Unit Structure (2025–2026 Exam)

| Unit | Name | Exam Weight | MCQ Count (est.) |
|------|------|-------------|-----------------|
| 1 | Using Objects & Methods | 15–25% | ~10 questions |
| 2 | Selection & Iteration | 25–35% | ~12 questions |
| 3 | Class Creation | 10–18% | ~10 questions |
| 4 | Data Collections | 30–40% | ~8 questions |

**Data Collections is the most heavily tested unit** (30–40% of exam).
Arrays, ArrayList, 2D arrays, searching, and sorting together can account for
nearly half the exam. Iteration (Unit 2) is the second-largest weight.

### Legacy 10-Unit Mapping (used in this platform's test files)

| Legacy Unit | Name | Exam Weight | → New Unit |
|-------------|------|-------------|-----------|
| 1 | Primitive Types | 2.5–5% | → U1 |
| 2 | Using Objects | 5–7.5% | → U1 |
| 3 | Boolean & if Statements | 15–17.5% | → U2 |
| 4 | Iteration | 17.5–22.5% | → U2 |
| 5 | Writing Classes | 5–7.5% | → U3 |
| 6 | Array | 10–15% | → U4 |
| 7 | ArrayList | 2.5–7.5% | → U4 |
| 8 | 2D Array | 7.5–10% | → U4 |
| 9 | Inheritance | 5–10% | → U3/U4 |
| 10 | Recursion | 5–7.5% | → U2/U3 |

### 2025–2026 New Content

- **File I/O with Scanner** — reading text files, handling `FileNotFoundException`,
  `nextInt()` + `nextLine()` flush trap. New topic; may appear in 1–2 MCQ.
- **Wrapper classes expanded** — `Integer.MIN_VALUE`, autoboxing/unboxing,
  `Integer` comparison with `.equals()` vs `==` now more heavily tested.

---

## PART 3 — MULTIPLE CHOICE STRATEGY

### Time & Format

- 42 questions in 90 minutes → **~2.25 minutes per question**
- 37–53% of MC questions are **code traces** ("what is printed?")
- Remaining questions: algorithm analysis, concept identification, code analysis
- No penalty for guessing — fill in every bubble

### Question Type Breakdown

| Type | Frequency | Approach |
|------|-----------|----------|
| Code trace ("what is printed/returned?") | 37–53% | Trace line by line on scratch paper |
| Code analysis ("what does this code do?") | 20–30% | Identify the algorithm pattern |
| Concept/definition | 10–20% | Know the rule cold |
| Error identification | 5–15% | Look for the off-by-one, wrong operator, wrong method |

### Distractor Elimination Strategy

AP CSA distractors are not random — they represent specific student mistakes.
For each wrong answer, ask: "What mistake would produce this?" Then verify
you haven't made that mistake. The three distractors for a code trace question
typically represent:

1. **Off-by-one error** (loop ran one too many or one too few times)
2. **Wrong operator/method** (used array.length as last valid index, or list.length instead of list.size())
3. **Conceptual confusion** (treating index as value, treating reference as copy)

### High-Value Topics for MCQ (appear on nearly every exam)

1. Integer division truncation: `7 / 2 = 3` (not 3.5)
2. `String.substring(a, b)` — index `b` is excluded
3. `&&` and `||` short-circuit evaluation
4. Off-by-one in loop bounds: `< arr.length` vs `<= arr.length`
5. Array index vs. array value confusion
6. Reference semantics: `c2 = c1` doesn't copy — both point to same object
7. `ArrayList.remove(int index)` vs `ArrayList.remove(Object o)` ambiguity
8. Dynamic dispatch: declared type vs. runtime type in polymorphism
9. Nested loop iteration count (sum, not multiply, when inner bound depends on outer)
10. Recursive call stack tracing

---

## PART 4 — FRQ STRATEGY BY TYPE

### Universal FRQ Rules

- **Method signature must match exactly** — return type, name, parameters in the right order
- **`private` instance variables, `public` methods** — losing this costs 1 point every time
- **All code paths must return a value** — if a method has conditional branches, every branch needs a return
- **Never check preconditions already stated** — if the problem says the array is non-empty, don't guard for it
- **Avoid non-curriculum features** — no `HashMap`, `try-catch`, lambdas, or generics beyond `ArrayList<Type>`
- **Spelling/case errors are forgiven** if unambiguously inferable — but don't rely on this
- **Partial credit is real** — a correct algorithm with syntax issues can still earn most points

### Scoring Rubric Structure (9 points per FRQ)

| Category | Points | What Earns Them |
|----------|--------|----------------|
| Algorithm correctness | 3–4 pts | Does the logic solve the problem for all inputs? |
| Language features | 2–3 pts | Correct use of loops, arrays, methods, operators |
| Completeness | 1–2 pts | All required components present (constructor, fields, return) |
| Syntax | 0–1 pt | Minor errors cost at most 1 point per question |

A penalty can only be deducted in a part where credit was already earned.
No part of a question can have a negative point total.
A given penalty is assessed at most once per question.

---

### Q1: Methods & Control Structures

**What it asks:** Write 1–2 methods using loops, conditionals, and calls to other methods.
Context class is always provided. You only write the method body.

**Key patterns to have memorized:**
```java
// Accumulator pattern
int sum = 0;
for (int i = 0; i < arr.length; i++) {
    sum += arr[i];
}

// String traversal
for (int i = 0; i < s.length(); i++) {
    char c = s.charAt(i);
}

// Count occurrences of substring
int count = 0;
int pos = secret.indexOf(guess);
while (pos != -1) {
    count++;
    pos = secret.indexOf(guess, pos + 1);
}
```

**What graders check:**
- Does the accumulator initialize correctly?
- Does the return statement exist in all branches?
- Are helper methods called on the right object with the right arguments?

**Common losses:** Missing `return`, off-by-one in loop bounds, using `=` instead of `==`, String comparison with `==`.

---

### Q2: Class Design

**What it asks:** Write a complete class — instance variables, constructor, methods.
Sometimes includes inheritance (extends another given class).

**Template:**
```java
public class ClassName {
    private Type field1;    // always private
    private Type field2;

    public ClassName(Type param1, Type param2) {
        this.field1 = param1;  // use this. when parameter name matches field
        this.field2 = param2;
    }

    public Type getField1() { return field1; }

    public void setField1(Type field1) { this.field1 = field1; }
}
```

**If it extends another class:**
```java
public class Child extends Parent {
    private Type extraField;

    public Child(Type p1, Type p2, Type extra) {
        super(p1, p2);          // must be first line
        this.extraField = extra;
    }

    @Override
    public String getInfo() {
        return super.getInfo() + " - " + extraField;  // reuse parent
    }
}
```

**What graders check:**
- Instance variables are `private`
- Constructor initializes ALL fields (including parent's via `super`)
- Methods return the correct type

**Common losses:** `public` instance variables, missing `super()` call, constructor with a return type (`void`).

---

### Q3: Array / ArrayList

**What it asks:** Traverse, filter, or transform a list. Often involves conditional checks
and building a new result list, or modifying in place.

**Standard traversal:**
```java
for (int i = 0; i < list.size(); i++) {
    Type element = list.get(i);
    // process element
}
```

**Backward removal (critical — forward removal skips elements):**
```java
for (int i = list.size() - 1; i >= 0; i--) {
    if (shouldRemove(list.get(i))) {
        list.remove(i);
    }
}
```

**In-place replacement — use `set()`, NOT `add()` + `remove()`:**
```java
list.set(i, newValue);  // replaces at index i — list size unchanged
// NOT: list.remove(i); list.add(i, newValue);  -- works but is wrong idiom
```

**What graders check:**
- `list.size()` not `list.length`
- `list.get(i)` not `list[i]`
- Correct traversal direction when removing
- `set()` for replacement, `add()` for insertion

**Common losses:** Forward removal causing index skip, `add()` when `set()` is correct (2025 Round trap), bracket notation `list[i]`.

---

### Q4: 2D Array

**What it asks:** Traverse a grid, compute values from neighbors, or mutate cells in place.

**Standard row-major traversal:**
```java
for (int r = 0; r < grid.length; r++) {
    for (int c = 0; c < grid[r].length; c++) {
        // process grid[r][c]
    }
}
```

**Neighbor access with bounds check:**
```java
// Check cell above
if (r > 0) {
    int above = grid[r - 1][c];
}
// Check cell to the right
if (c < grid[r].length - 1) {
    int right = grid[r][c + 1];
}
```

**Dimension reminders:**
- `grid.length` → number of rows
- `grid[0].length` → number of columns (not `grid.length`)
- `grid[row][col]` → row index first, column second

**What graders check:**
- Indices are in the right order (`grid[row][col]`)
- Bounds check before neighbor access
- `grid.length` vs `grid[0].length` used correctly

**Common losses:** Swapped indices, `grid.length` used for columns, missing bounds check before `grid[r-1][c]`.

---

## PART 5 — TOPIC TIPS & COMMON MISTAKES

### Unit 1 — Primitive Types

**Tricks:**
- `7 / 2 = 3` always. Division truncates toward zero. Never rounds.
- `double result = 7 / 2` → `3.0`, NOT `3.5`. Division happens first (both ints), then stored as double.
- `(double) 7 / 2` → `3.5`. Cast happens before the division.
- String concat trap: `"Sum: " + 1 + 2` → `"Sum: 12"`. Left-to-right, first `+` concatenates, second does too.
- Compound operators: `x += 3; x *= 2;` — apply in sequence, not simultaneously.

**Common mistakes:**
- Assuming `/` produces a decimal when at least one operand looks like a decimal in your head (both must be double)
- `int pi = 3.14` — compile error, not a warning
- `%` has same precedence as `*` and `/` — evaluate left to right in an expression

---

### Unit 2 — Using Objects (Strings, Math, Wrapper Classes)

**Tricks:**
- `substring(a, b)`: index `a` is included, index `b` is excluded. Length = `b - a`.
- `"hello".substring(1, 3)` → `"el"` (indices 1 and 2 only)
- `indexOf` returns -1 if not found, first occurrence index if found. Zero-based.
- Strings are immutable — `s.toUpperCase()` does NOT change `s`; it returns a new String.
- `Math.random()` range: `[0.0, 1.0)` — 1.0 is never returned.
- Random int in range `[min, max]`: `(int)(Math.random() * (max - min + 1)) + min`
- `==` on Strings compares references (object identity), not content. Always use `.equals()`.

**Common mistakes:**
- Off-by-one on `substring`: `"hello".substring(0, 5)` = `"hello"`, `substring(0, 4)` = `"hell"`
- `Integer.parseInt()` not needed on the exam (Scanner handles it) — but know autoboxing exists
- String `+` with numbers on the left: `1 + 2 + "x"` → `"3x"`, but `"x" + 1 + 2` → `"x12"`

---

### Unit 3 — Boolean Expressions & if Statements

**Tricks:**
- Short-circuit: `false && anything` → `false` immediately (right side not evaluated)
- Short-circuit: `true || anything` → `true` immediately
- De Morgan's: `!(a && b)` ≡ `(!a || !b)` · `!(a || b)` ≡ `(!a && !b)`
- `else if` chain stops at the first true branch — mutually exclusive execution
- Common equivalent form: `(x >= 1 && x <= 5)` is NOT the same as `(1 <= x <= 5)` — the latter won't compile

**Common mistakes:**
- `=` in a condition instead of `==` — Java allows `if (x = 5)` for booleans but it's almost always a bug
- Forgetting `!` applies to the whole parenthesized expression, not just the first operand
- Using `>` when `>=` is needed at a boundary condition

---

### Unit 4 — Iteration

**Tricks:**
- A `for` loop with `i = 0; i < n` runs exactly `n` times (indices 0 through n-1)
- A `for` loop with `i = 1; i <= n` also runs `n` times but starts at 1
- Nested triangular loops: `for (int j = 0; j < i; j++)` — total iterations = 0+1+2+…+(n-1) = n(n-1)/2
- Enhanced for loop: read-only access. You cannot modify array elements or remove ArrayList items inside it.
- `while` loop where condition is false at start → body never executes (zero iterations is valid)

**Common mistakes:**
- `i <= arr.length` → `ArrayIndexOutOfBoundsException` (last valid index is `arr.length - 1`)
- Thinking inner loop variable carries its value across outer iterations — it resets every time
- Forgetting to increment counter in `while` loop → infinite loop
- Counting nested loop iterations by multiplying instead of summing when inner bound changes

---

### Unit 5 — Writing Classes

**Tricks:**
- Constructor: same name as class, no return type (not even `void`), initializes all fields
- `this.name = name` — the `this.` refers to the instance variable; plain `name` is the parameter
- `static` methods belong to the class, not an object — they cannot use `this` or instance variables
- `toString()` override: return a meaningful String for `System.out.println(obj)` to work nicely
- Two variables can reference the same object: `c2 = c1` — all changes via either name affect the same object

**Common mistakes:**
- Instance variables declared `public` — costs FRQ points every time
- Constructor with `void` — turns it into a regular method, not a constructor
- Accessing `private` superclass fields directly from a subclass — must use `super.getField()`

---

### Unit 6 — Arrays

**Tricks:**
- `arr.length` is a field (no parentheses). `list.size()` is a method (parentheses). Know the difference.
- Last valid index: `arr.length - 1`. `arr[arr.length]` is always out of bounds.
- Initialize `max` to `arr[0]`, NEVER to `0`. A `0` initial max breaks for all-negative arrays.
- Arrays are passed by reference — a method that modifies the array changes the original.
- Default values after `new int[n]`: all zeros. `new boolean[n]`: all false. `new String[n]`: all null.

**Common mistakes:**
- `arr.length()` — compile error. It's a field, not a method.
- Starting the max-finding loop at `i = 0` and initializing max to `arr[0]` — double-counts index 0 (harmless but sloppy)
- Assuming step-increment loop `k = k + 2` visits every other element from position 0 — check whether n is even or odd

---

### Unit 7 — ArrayList

**Tricks:**
- `add(item)` appends to end. `add(index, item)` inserts at position. After insert, everything shifts right.
- `remove(int index)` removes by position. `remove(Object o)` removes by value. With `Integer` objects, `remove(1)` removes index 1; `remove(Integer.valueOf(1))` removes the value 1.
- `set(index, newValue)` replaces in place and returns the old value.
- Backward removal loop: `for (int i = list.size() - 1; i >= 0; i--)` — safe to remove inside
- Cannot hold primitives — must use `Integer`, `Double`, `Boolean`

**Common mistakes:**
- `list[i]` — ArrayList is not an array. Use `list.get(i)`.
- `list.length` — use `list.size()`.
- Forward removal during traversal skips the element that shifted into the removed index.
- `add()` instead of `set()` for in-place replacement — inserts a new element, doesn't replace (2025 Round FRQ trap).

---

### Unit 8 — 2D Arrays

**Tricks:**
- Declaration: `int[][] grid = new int[ROWS][COLS];`
- Row count: `grid.length`. Column count: `grid[0].length` (NOT `grid.length`).
- Access: `grid[row][col]` — row first, column second. This matches mathematical matrix notation.
- For neighbor access, always bounds-check before accessing: `if (r > 0) grid[r-1][c]`
- Column-major traversal: outer loop on columns, inner on rows — less common but appears in FRQ

**Common mistakes:**
- `grid[col][row]` — swapped. Write row first.
- Using `grid.length` for column count — only correct for square matrices.
- `grid.length()` — compile error. It's a field.
- No bounds check before accessing `grid[r-1][c]` when `r` could be 0.

---

### Unit 9 — Inheritance & Polymorphism

**Tricks:**
- `Animal a = new Dog()` is valid if Dog extends Animal. Dog IS-A Animal.
- Dynamic dispatch: at runtime, Java calls the method defined by the **runtime type** (Dog), not the declared type (Animal).
- `super.method()` calls the superclass version even from within an override.
- `super()` must be the first line in a subclass constructor. If omitted, Java inserts `super()` automatically — only works if the superclass has a no-arg constructor.
- `private` superclass methods are NOT inherited and cannot be overridden.
- Overriding = same signature. Overloading = same name, different parameters.

**Common mistakes:**
- Thinking declared type determines which method runs (it doesn't — runtime type does).
- Confusing `super.method()` (superclass version) with `this.method()` (most specific override).
- Trying to instantiate an abstract class: `Animal a = new Animal()` fails if Animal is abstract.
- Believing subclass constructors inherit automatically — they don't, must call `super(...)`.

---

### Unit 10 — Recursion

**Tricks:**
- Every recursive method must have a base case — the condition that returns without recursing.
- Each recursive call gets its own copy of local variables — they are not shared.
- Trace by expanding the call chain: `mystery(4)` = `4 + mystery(3)` = `4 + 3 + mystery(2)` = …
- Recursive String methods: the base case is usually `s.length() == 0`, and the recursive step is `s.substring(1)` (drop first character).
- Print-before-recurse → processes in order. Recurse-then-print → processes in reverse.

**Common mistakes:**
- No base case → infinite recursion → `StackOverflowError` at runtime.
- Off-by-one in base case: `n == 0` misses the case when `n` is negative.
- Forgetting to `return` the result of the recursive call: `mystery(n-1)` instead of `return mystery(n-1)`.
- Thinking shared state exists across calls — each call has its own frame.

---

## PART 6 — QUICK REFERENCE (Java Methods Provided on Exam)

The AP exam provides students with this exact reference. Agents generating FRQ questions
must not require methods outside this list without explicit provision in the problem context.

```java
// ── String ──────────────────────────────────────────────────
int    length()                  // number of characters
String substring(int from)       // from index to end
String substring(int from, int to) // from (inclusive) to to (exclusive)
int    indexOf(String str)       // first index of str, -1 if not found
boolean equals(Object other)     // content equality
int    compareTo(String other)   // negative/zero/positive
// Note: charAt(int index) is NOT on the quick reference sheet but IS tested

// ── Integer ─────────────────────────────────────────────────
Integer.MIN_VALUE                // -2147483648
Integer.MAX_VALUE                //  2147483647

// ── Math ────────────────────────────────────────────────────
static int    abs(int x)
static double abs(double x)
static double pow(double base, double exp)
static double sqrt(double x)
static double random()           // returns [0.0, 1.0)

// ── ArrayList<E> ────────────────────────────────────────────
int     size()
boolean add(E obj)               // append; always returns true
void    add(int index, E obj)    // insert at index
E       get(int index)
E       set(int index, E obj)    // replace; returns old value
E       remove(int index)        // remove by position; returns removed element
```

---

## PART 7 — AGENT GUIDE: WRITING EXCELLENT AP CSA QUESTIONS

> Read this section before generating any questions. It defines what makes AP CSA questions
> genuinely instructive, and sets the schema and conventions for this platform.

### Core Principles

**1. One concept per question.**
The best AP questions isolate a single misconception or skill. Don't combine integer division
AND casting AND string concatenation in one question. Pick one. Distractors should target the
specific misconception for that one concept.

**2. Every distractor must be meaningful.**
Wrong answers are not random — they represent the output a student would get
*if they made the most common mistake*. For integer division: offer `3.4` (treated as float),
`3.0` (assumed double return), `4` (rounded up). Each wrong answer tells the instructor
exactly which misconception the student has.

**3. Code traces are the exam backbone.**
37–53% of MC questions ask "what is printed/returned?" — not definitions.
Every question should have runnable code when possible. Abstract conceptual questions
are appropriate only for Unit 5 (Classes) and Unit 9 (Inheritance).

**4. Match the AP difficulty curve.**
- Easy: straightforward trace — student just follows the code
- Medium: requires knowing one specific rule (e.g., `remove(int)` vs `remove(Object)`)
- Hard: interaction of multiple concepts, subtle off-by-one, or a two-bug scenario

**5. Guiding questions are Socratic, not leading.**
BAD: "Remember that integer division truncates — what is 17/5?" (gives away answer)
GOOD: "What data type does dividing two int values produce in Java?" (makes student reason)
Each question needs 2–3 guiding questions. The last one should approach but not state the answer.

**6. Always-tested patterns to prioritize (highest ROI):**
- Integer division truncation — appears on >80% of released exams
- `substring(a, b)` exclusive upper bound — appears on >70%
- Short-circuit `&&` / `||` evaluation
- Off-by-one loop errors (`<` vs `<=`)
- Reference semantics vs. value semantics
- Array traversal + accumulator pattern
- ArrayList `remove(int)` vs `remove(Object)` ambiguity
- 2D array `[row][col]` indexing and `grid.length` vs `grid[0].length`
- Dynamic dispatch / polymorphism
- Recursive call stack trace

### JSON Schema for `ap_csa_question_bank.json`

All questions in this platform use this schema:

```json
{
  "id": "mc_u6_01",
  "question_type": "multiple_choice",
  "ap_unit": 6,
  "ap_unit_name": "Array",
  "source": "AP CSA style — Unit 6",
  "year": null,
  "topic_tags": ["arrays", "loops"],
  "concept_tested": "Find max element by initializing to arr[0] and scanning forward",
  "difficulty": "medium",
  "prompt": "What is printed when the following code executes?",
  "code_block": "int[] arr = {5, 3, 8, 1, 9};\nint max = arr[0];...",
  "options": { "A": "5", "B": "9", "C": "1", "D": "8", "E": "3" },
  "answer_key": "B",
  "explanation": "The loop finds the maximum element ...",
  "guiding_questions": [
    { "id": "mc_u6_01_g1", "text": "Why does the loop start at index 1 rather than index 0?" },
    { "id": "mc_u6_01_g2", "text": "After the loop processes arr[4]=9, what is the value of max?" }
  ]
}
```

**For FRQ questions**, substitute `"question_type": "free_response"` and replace `options`/`answer_key`
with `parts` (array of part objects) and `class_given`.

### Topic Tags Reference

Every question must include at least one `topic_tag` from this list:

```
variables_and_types   operators         conditionals
loops                 arrays            2d_arrays
methods               parameter_passing strings
classes_and_objects   inheritance       polymorphism
recursion             arraylist         searching_sorting
interfaces            casting
```

---

## PART 8 — HISTORICAL FRQ TOPIC INDEX (2004–2025)

Use this when generating FRQ-style questions to ensure coverage and avoid duplication.

### Type 1 — Methods & Control Structures
2025 DogWalker · 2024 Feeder · 2023 AppointmentBook · 2022 Game · 2021 WordMatch
· 2019 APCalendar · 2018 FrogSimulation · 2017 Phrase · 2012 Gray Bug · 2011 Sound
· 2010 CookieOrder · 2009 NumberCube · 2008 FlightList · 2007 SelfDivisor

### Type 2 — Class Design
2025 SignedText · 2024 Scoreboard · 2023 Sign · 2022 Textbook (+ Inheritance)
· 2021 CombinedTable · 2019 StepTracker · 2018 CodeWordChecker · 2015 HiddenWord
· 2013 TokenPass · 2012 Climbing · 2010 APLine

### Type 3 — Array / ArrayList
2025 Round · 2024 WordChecker · 2023 WeatherData · 2022 ReviewAnalysis
· 2021 ClubMembers · 2019 Delimiters · 2018 WordPair · 2017 Digits
· 2016 RandomStringChooser · 2015 SparseArray · 2014 StringFormatter
· 2012 HorseBarn · 2011 FuelDepot

### Type 4 — 2D Array
2025 SumOrSameGame · 2024 GridPath · 2023 BoxOfCandy · 2022 Data
· 2021 ArrayResizer · 2019 LightBoard · 2018 ArrayTester · 2017 Successors
· 2016 CrosswordPuzzle · 2015 DiverseArray · 2014 SeatingChart · 2013 SkyView
· 2012 GrayImage · 2011 BitMatrix

---

*Last updated: 2026-04-15. Sources: College Board AP Central (apcentral.collegeboard.org),
APCSExamPrep.com, Runestone Academy CSAwesome, CrackAP.com, APComputerScienceTutoring.com.*


---

## GENERATED QUESTIONS — Strings (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q1] What is printed by the following code?
**Type:** code_trace  **Unit:** 2

```java
String word = "COMPUTER";
System.out.println(word.substring(3, 6));
```

**Options:**
  - A) PUT
  - B) PUTE
  - C) MPU
  - D) MPUT

**Answer:** A
**Explanation:** substring(3, 6) includes indices 3, 4, and 5. 'COMPUTER' has C(0) O(1) M(2) P(3) U(4) T(5) E(6) R(7). So indices 3-5 give 'PUT'. The length is 6 - 3 = 3 characters. Common mistake: thinking the end index is inclusive, which would give 'PUTE'.


### [quiz_q5] What is printed by the following code?
**Type:** code_trace  **Unit:** 5

```java
public class Box {
    private String label;
    private int width;
    private int height;

    public Box(String label, int width, int height) {
        this.label = label;
        this.width = width;
        this.height = height;
    }

    public int getArea() {
        return width * height;
    }

    public String toString() {
        return label.substring(0, 3) + "-" + getArea();
    }
}

// In main:
Box b = new Box("SHIPPING", 4, 5);
System.out.println(b);
```

**Options:**
  - A) SHI-20
  - B) SHIP-20
  - C) SHI-9
  - D) SHIPPING-20

**Answer:** A
**Explanation:** The constructor sets label="SHIPPING", width=4, height=5. toString() calls label.substring(0, 3) which gives "SHI" (indices 0, 1, 2). getArea() returns 4*5 = 20. So the result is "SHI-20". Common mistake: thinking substring(0,3) includes index 3 (giving "SHIP"), or miscalculating the area.


### [quiz_q7] A TagMaker class creates formatted tags from names. Each tag has a tag number and an abbreviated name. Study the partial class below and complete the methods as described.

The abbreviation of a name is formed by taking the first letter of the name concatenated with every character in the name that immediately follows a space. For example:
- "Ana Maria Lopez" → "AML"
- "Bo" → "B"
- "Kim Lee" → "KL"
**Type:** frq  **Unit:** 5

**Options:**


**Answer:** 
**Explanation:** Part (a) tests string traversal with substring and indexOf/charAt. The student must correctly handle substring boundaries. Part (b) tests using instance variables and method calls within a class, plus state mutation.


### [quiz_q8] A ContactList class manages a list of contacts. Each Contact has a name and a category (e.g., "friend", "work", "family"). Write the two methods described below.

The Contact class is provided and has the following methods:
- public String getName() — returns the contact's name
- public String getCategory() — returns the contact's category
**Type:** frq  **Unit:** 7

**Options:**


**Answer:** 
**Explanation:** Part (a) tests basic ArrayList traversal and building a new list with string comparison. Part (b) is a harder in-place removal problem requiring the student to track seen categories and handle index shifting during removal correctly — directly targeting their ArrayList removal weakness.



---

## GENERATED QUESTIONS — Operators (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q2] What is the value of result after the following code executes?
**Type:** code_trace  **Unit:** 1

```java
double result = 7 / 2 + 3.0;
```

**Options:**
  - A) 6.5
  - B) 6.0
  - C) 7.0
  - D) 7.5

**Answer:** A
**Explanation:** Java evaluates 7 / 2 first. Since both 7 and 2 are ints, integer division produces 3 (not 3.5). Then 3 + 3.0 is evaluated: the int 3 is widened to 3.0, giving 6.0... Wait — let me recalculate: 7/2 = 3 (int division), then 3 + 3.0 = 6.0. So the answer is 6.0, which is option B. Correction: The answer is B. Actually re-examining: 7/2 = 3 (integer division truncates), 3 + 3.0 = 6.0. The answer is B.


### [quiz_q6] What does the ArrayList contain after the following code executes?
**Type:** code_trace  **Unit:** 7

```java
ArrayList<Integer> vals = new ArrayList<Integer>();
vals.add(3);
vals.add(7);
vals.add(2);
vals.add(8);
vals.add(1);

for (int i = vals.size() - 1; i >= 0; i--) {
    if (vals.get(i) % 2 == 1) {
        vals.remove(i);
    }
}
```

**Options:**
  - A) [7, 2, 8]
  - B) [2, 8]
  - C) [3, 2, 1]
  - D) [3, 7, 2, 8]

**Answer:** B
**Explanation:** The loop goes backward removing odd numbers. Initial: [3, 7, 2, 8, 1]. i=4: vals.get(4)=1, 1%2==1 → remove → [3, 7, 2, 8]. i=3: vals.get(3)=8, 8%2==0 → keep. i=2: vals.get(2)=2, 2%2==0 → keep. i=1: vals.get(1)=7, 7%2==1 → remove → [3, 2, 8]. i=0: vals.get(0)=3, 3%2==1 → remove → [2, 8]. The backward loop avoids the skipping problem of forward removal.



---

## GENERATED QUESTIONS — Variables And Types (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q2] What is the value of result after the following code executes?
**Type:** code_trace  **Unit:** 1

```java
double result = 7 / 2 + 3.0;
```

**Options:**
  - A) 6.5
  - B) 6.0
  - C) 7.0
  - D) 7.5

**Answer:** A
**Explanation:** Java evaluates 7 / 2 first. Since both 7 and 2 are ints, integer division produces 3 (not 3.5). Then 3 + 3.0 is evaluated: the int 3 is widened to 3.0, giving 6.0... Wait — let me recalculate: 7/2 = 3 (int division), then 3 + 3.0 = 6.0. So the answer is 6.0, which is option B. Correction: The answer is B. Actually re-examining: 7/2 = 3 (integer division truncates), 3 + 3.0 = 6.0. The answer is B.


### [quiz_q7] A TagMaker class creates formatted tags from names. Each tag has a tag number and an abbreviated name. Study the partial class below and complete the methods as described.

The abbreviation of a name is formed by taking the first letter of the name concatenated with every character in the name that immediately follows a space. For example:
- "Ana Maria Lopez" → "AML"
- "Bo" → "B"
- "Kim Lee" → "KL"
**Type:** frq  **Unit:** 5

**Options:**


**Answer:** 
**Explanation:** Part (a) tests string traversal with substring and indexOf/charAt. The student must correctly handle substring boundaries. Part (b) tests using instance variables and method calls within a class, plus state mutation.



---

## GENERATED QUESTIONS — Loops (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q3] What is the value of count after this code executes?
**Type:** code_trace  **Unit:** 4

```java
int count = 0;
for (int i = 1; i <= 4; i++) {
    for (int j = i; j <= 4; j++) {
        count++;
    }
}
```

**Options:**
  - A) 10
  - B) 16
  - C) 8
  - D) 6

**Answer:** A
**Explanation:** Trace each iteration: i=1: j runs 1,2,3,4 → 4 increments. i=2: j runs 2,3,4 → 3 increments. i=3: j runs 3,4 → 2 increments. i=4: j runs 4 → 1 increment. Total = 4+3+2+1 = 10. Common mistake: assuming both loops always run 4 times (which gives 16) or not noticing j starts at i.


### [quiz_q6] What does the ArrayList contain after the following code executes?
**Type:** code_trace  **Unit:** 7

```java
ArrayList<Integer> vals = new ArrayList<Integer>();
vals.add(3);
vals.add(7);
vals.add(2);
vals.add(8);
vals.add(1);

for (int i = vals.size() - 1; i >= 0; i--) {
    if (vals.get(i) % 2 == 1) {
        vals.remove(i);
    }
}
```

**Options:**
  - A) [7, 2, 8]
  - B) [2, 8]
  - C) [3, 2, 1]
  - D) [3, 7, 2, 8]

**Answer:** B
**Explanation:** The loop goes backward removing odd numbers. Initial: [3, 7, 2, 8, 1]. i=4: vals.get(4)=1, 1%2==1 → remove → [3, 7, 2, 8]. i=3: vals.get(3)=8, 8%2==0 → keep. i=2: vals.get(2)=2, 2%2==0 → keep. i=1: vals.get(1)=7, 7%2==1 → remove → [3, 2, 8]. i=0: vals.get(0)=3, 3%2==1 → remove → [2, 8]. The backward loop avoids the skipping problem of forward removal.


### [quiz_q7] A TagMaker class creates formatted tags from names. Each tag has a tag number and an abbreviated name. Study the partial class below and complete the methods as described.

The abbreviation of a name is formed by taking the first letter of the name concatenated with every character in the name that immediately follows a space. For example:
- "Ana Maria Lopez" → "AML"
- "Bo" → "B"
- "Kim Lee" → "KL"
**Type:** frq  **Unit:** 5

**Options:**


**Answer:** 
**Explanation:** Part (a) tests string traversal with substring and indexOf/charAt. The student must correctly handle substring boundaries. Part (b) tests using instance variables and method calls within a class, plus state mutation.


### [quiz_q8] A ContactList class manages a list of contacts. Each Contact has a name and a category (e.g., "friend", "work", "family"). Write the two methods described below.

The Contact class is provided and has the following methods:
- public String getName() — returns the contact's name
- public String getCategory() — returns the contact's category
**Type:** frq  **Unit:** 7

**Options:**


**Answer:** 
**Explanation:** Part (a) tests basic ArrayList traversal and building a new list with string comparison. Part (b) is a harder in-place removal problem requiring the student to track seen categories and handle index shifting during removal correctly — directly targeting their ArrayList removal weakness.



---

## GENERATED QUESTIONS — Arraylist (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q4] What does the ArrayList contain after the following code executes?
**Type:** code_trace  **Unit:** 7

```java
ArrayList<Integer> nums = new ArrayList<Integer>();
nums.add(5);
nums.add(10);
nums.add(15);
nums.add(20);
nums.remove(1);
nums.remove(Integer.valueOf(15));
```

**Options:**
  - A) [5, 20]
  - B) [5, 15]
  - C) [10, 20]
  - D) [5, 15, 20]

**Answer:** A
**Explanation:** Initial list: [5, 10, 15, 20]. nums.remove(1) removes the element at index 1, which is 10. List becomes [5, 15, 20]. Then nums.remove(Integer.valueOf(15)) removes the first occurrence of the value 15. List becomes [5, 20]. Common mistake: confusing remove(1) as removing the value 1 instead of the element at index 1.


### [quiz_q6] What does the ArrayList contain after the following code executes?
**Type:** code_trace  **Unit:** 7

```java
ArrayList<Integer> vals = new ArrayList<Integer>();
vals.add(3);
vals.add(7);
vals.add(2);
vals.add(8);
vals.add(1);

for (int i = vals.size() - 1; i >= 0; i--) {
    if (vals.get(i) % 2 == 1) {
        vals.remove(i);
    }
}
```

**Options:**
  - A) [7, 2, 8]
  - B) [2, 8]
  - C) [3, 2, 1]
  - D) [3, 7, 2, 8]

**Answer:** B
**Explanation:** The loop goes backward removing odd numbers. Initial: [3, 7, 2, 8, 1]. i=4: vals.get(4)=1, 1%2==1 → remove → [3, 7, 2, 8]. i=3: vals.get(3)=8, 8%2==0 → keep. i=2: vals.get(2)=2, 2%2==0 → keep. i=1: vals.get(1)=7, 7%2==1 → remove → [3, 2, 8]. i=0: vals.get(0)=3, 3%2==1 → remove → [2, 8]. The backward loop avoids the skipping problem of forward removal.


### [quiz_q8] A ContactList class manages a list of contacts. Each Contact has a name and a category (e.g., "friend", "work", "family"). Write the two methods described below.

The Contact class is provided and has the following methods:
- public String getName() — returns the contact's name
- public String getCategory() — returns the contact's category
**Type:** frq  **Unit:** 7

**Options:**


**Answer:** 
**Explanation:** Part (a) tests basic ArrayList traversal and building a new list with string comparison. Part (b) is a harder in-place removal problem requiring the student to track seen categories and handle index shifting during removal correctly — directly targeting their ArrayList removal weakness.



---

## GENERATED QUESTIONS — Classes And Objects (from Teststudent session session_1, 2026-04-15)

> Auto-generated by quiz_generator.py. Review before using in future sessions.

### [quiz_q5] What is printed by the following code?
**Type:** code_trace  **Unit:** 5

```java
public class Box {
    private String label;
    private int width;
    private int height;

    public Box(String label, int width, int height) {
        this.label = label;
        this.width = width;
        this.height = height;
    }

    public int getArea() {
        return width * height;
    }

    public String toString() {
        return label.substring(0, 3) + "-" + getArea();
    }
}

// In main:
Box b = new Box("SHIPPING", 4, 5);
System.out.println(b);
```

**Options:**
  - A) SHI-20
  - B) SHIP-20
  - C) SHI-9
  - D) SHIPPING-20

**Answer:** A
**Explanation:** The constructor sets label="SHIPPING", width=4, height=5. toString() calls label.substring(0, 3) which gives "SHI" (indices 0, 1, 2). getArea() returns 4*5 = 20. So the result is "SHI-20". Common mistake: thinking substring(0,3) includes index 3 (giving "SHIP"), or miscalculating the area.


### [quiz_q7] A TagMaker class creates formatted tags from names. Each tag has a tag number and an abbreviated name. Study the partial class below and complete the methods as described.

The abbreviation of a name is formed by taking the first letter of the name concatenated with every character in the name that immediately follows a space. For example:
- "Ana Maria Lopez" → "AML"
- "Bo" → "B"
- "Kim Lee" → "KL"
**Type:** frq  **Unit:** 5

**Options:**


**Answer:** 
**Explanation:** Part (a) tests string traversal with substring and indexOf/charAt. The student must correctly handle substring boundaries. Part (b) tests using instance variables and method calls within a class, plus state mutation.


### [quiz_q8] A ContactList class manages a list of contacts. Each Contact has a name and a category (e.g., "friend", "work", "family"). Write the two methods described below.

The Contact class is provided and has the following methods:
- public String getName() — returns the contact's name
- public String getCategory() — returns the contact's category
**Type:** frq  **Unit:** 7

**Options:**


**Answer:** 
**Explanation:** Part (a) tests basic ArrayList traversal and building a new list with string comparison. Part (b) is a harder in-place removal problem requiring the student to track seen categories and handle index shifting during removal correctly — directly targeting their ArrayList removal weakness.

