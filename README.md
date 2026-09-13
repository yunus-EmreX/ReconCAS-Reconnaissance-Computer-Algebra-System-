```markdown
# OpticCAS-Terminal: Vision-Based Computer Algebra System

A locally hosted desktop application that captures raw image data from the screen buffer, routes it through an Optical Character Recognition (OCR) pipeline, and parses it into symbolic mathematical expressions. The system features multi-threaded execution, local data persistence, and a dedicated laboratory module capable of 2D/3D topological analysis.

## Architecture and Stack

*   **GUI:** `Tkinter` (Custom CLI-style Dark Interface, High-DPI awareness, Topmost window management)
*   **Vision/OCR Engine:** `pytesseract`, `Pillow` (Bicubic up-scaling, Contrast/Sharpness filters)
*   **Symbolic Computation:** `SymPy` (Equation parsing, Derivatives, Integrals, Factorization, Root analysis)
*   **Graphics/Rendering:** `Matplotlib`, `NumPy` (2D plotting, 3D surface rendering, Garbage Collection integration)
*   **Data Management:** `SQLite3`, `hashlib` (SHA-256 encryption, Session logging)

## Core Modules and Capabilities

### 1. Authentication and History Logging
The application bypasses in-memory volatility by initializing a local `sqlite3` database upon startup.
*   **Cryptography:** User passwords are encrypted using the SHA-256 hashing algorithm rather than plaintext storage.
*   **Session Tracking:** During an authenticated session, every successful OCR read and symbolic execution is recorded in the `history` table with a timestamp.
*   **Override Protocol:** Password reset routines are managed via a localized secret hint established during registration.

### 2. Vision Engine and Live Scanning
Data captured from screen coordinates (Bounding Box) is processed via `Pillow`.
*   **Image Enhancements:** To minimize character loss, frames are up-scaled by 2x, converted to grayscale, and processed through contrast multipliers.
*   **Daemon Threads:** Continuous area scanning (Live Area) and global scanning (Live Full) execute on isolated background threads to prevent main thread blocking. Scanning operations are throttled with 1.0 - 2.0 second sleep cycles to prevent CPU spiking.
*   **Smart Routing:** Extracted text is filtered via regex. Pure arithmetic inputs (e.g., `587-325`) are routed to a sanitized evaluation engine for immediate output. Expressions containing variables (x, y) or inequalities are automatically forwarded to the CAS laboratory.

### 3. Computer Algebra System (CAS Laboratory)
The system utilizes a SymPy-backed symbolic engine, autonomously correcting implicit multiplications (e.g., mapping `2x` to `2*x`).
*   **Calculus Operations:** Computes analytical derivatives and indefinite integrals relative to identified variables.
*   **Algebraic Analysis:** Executes polynomial factorization and solves for roots by equating expressions to zero (Eq(f, 0)).
*   **Console Logging:** Execution states and outputs are piped directly into an isolated CLI text widget within the GUI.

### 4. Sandbox Simulation Studio (Custom Universe)
The most advanced module of the system. It permits the combination of separate functions to construct custom topological fields.
*   **Equation Fusion:** Combines a base function and a spatial modifier via $Z = f(x,y) \cdot U(x,y)$.
*   **3D Rendering and Meshgrid:** Utilizes `NumPy` to generate spatial matrices. The system dynamically invokes Matplotlib's 3D axis engine when bi-variable (x, y) expressions are detected.
*   **Resistance (Min/Max) Analysis:** Filters out infinities and undefined regions (NaN, Inf) using `np.errstate`. Computes the absolute minimum and maximum Z-values within the matrix, logging them as "Critical Peaks/Troughs" to the terminal.
*   **Memory Management:** To prevent standard Matplotlib memory leaks during consecutive renders, `plt.close('all')` and explicit garbage collection (`gc.collect()`) are forcefully invoked upon window termination or graph updates.

## Installation and Dependencies
Tesseract OCR binary must be installed on the host machine (`C:\Program Files\Tesseract-OCR\tesseract.exe`).

```bash
pip install pytesseract pillow sympy numpy matplotlib
