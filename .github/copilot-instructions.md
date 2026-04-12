# Copilot Instructions for APCompSci

- This repository is a tiny Java learning workspace. The main source file is `src/Main.java` and the `out/` directory is used for compiled output.
- There is no Maven/Gradle build file. Do not assume an existing Java build system; keep fixes compatible with plain `javac` and `java`.
- The current `src/Main.java` is not valid Java yet. Key issues to fix first:
  - add a `public class Main` wrapper
  - use a standard entry point: `public static void main(String[] args)`
  - replace invalid statements like `whatsItDo;`
  - resolve undefined helpers such as `IO.println`
- Keep the code simple and idiomatic for AP Computer Science level: `System.out.println`, `static` methods when appropriate, and minimal use of packages.
- Prefer modifying `src/Main.java` directly rather than introducing complex project structure.

## Build / Run
- Compile with: `javac -d out src/Main.java`
- Run with: `java -cp out Main`
- If you add new source files, keep them under `src/` and update the `javac` command accordingly.

## What to preserve
- The goal is educational Java examples, not production infrastructure.
- `BuildGuide` appears unused and empty; do not rely on it for build logic.
- There are no external dependencies visible; use only the JDK standard library.

## Notes for editing
- `src/Main.java` currently shows a method `trial()` demonstrating parameter passing by value. Preserve the intended teaching example while making it compile.
- Avoid inventing unrelated architecture: this repo is a single-class example project, not a multi-module application.
- Prefer clear, short Java code over advanced Java idioms.

## When in doubt
- Ask whether the user wants a real runnable AP-style Java program or just a corrected version of the current demonstration code.
