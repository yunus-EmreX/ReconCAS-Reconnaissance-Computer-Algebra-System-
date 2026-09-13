```markdown
# ReconCAS (OpticCAS-Terminal) // V10 Enterprise
**Vision-Based Computer Algebra System**

ReconCAS is a locally hosted desktop application that captures raw image data from the screen buffer, routes it through an Optical Character Recognition (OCR) pipeline, and translates it into symbolic mathematical expressions for advanced analysis. Unlike standard calculators, it eliminates manual input by allowing users to select screen regions (bounding boxes) to extract and evaluate equations instantly.

With the V10 release, the system has achieved a true production-grade standard, introducing context-aware OCR corrections, a secure password override infrastructure, and restored multi-variable 3D plotting in the laboratory module.

## ⚙️ Architecture and Technical Capabilities

The application operates on 3 decoupled layers (Core, Vision, GUI):

### 1. Vision Engine (Image Processing & OCR)
*   **Image Enhancement:** Selected screen regions are captured via Pillow, upscaled using bicubic/bilinear interpolation, converted to grayscale, and processed through high-contrast multipliers.
*   **Context-Aware Corrector:** Common Tesseract OCR errors (e.g., reading `l` as `1` or `O` as `0`) are rectified using specialized Regex patterns. These substitutions are context-aware (applied only to isolated characters), ensuring that legitimate mathematical functions like `sin`, `cos`, and `log` remain uncorrupted.
*   **Frame Differencing:** During Live Scanning mode, the system hashes (MD5) consecutive frames. If the visual data remains unchanged, the OCR engine is bypassed. This optimization drastically prevents CPU spiking.

### 2. Math Engine (Secure Symbolic Analysis)
*   **Lexical Validation (Whitelist Layer):** To prevent arbitrary code execution vulnerabilities from malicious or hallucinated OCR outputs, incoming text is subjected to strict lexical validation. Only whitelisted mathematical tokens `[0-9, x, y, +, -, *, /, sin, cos, exp...]` are permitted.
*   **Smart Implicit Multiplication:** The engine uses targeted Regex to safely map implied operations (like `5 x 3`) to exact syntax (`5 * 3`) strictly between numeric boundaries, preventing failures in explicit functions like `exp(2)`.
*   **SymPy Integration:** Sanitized strings are passed to the SymPy engine to compute analytical derivatives, indefinite integrals, polynomial factorization, and root solutions with a single click.

### 3. Core & Security
*   **Cryptography:** The application utilizes a local SQLite database (`recon_cas_secure.db`). User passwords and recovery hints are never stored in plaintext; they are securely salted and hashed using the `bcrypt` algorithm.
*   **Session Logging:** All successful authentications, blocked malicious inputs, and evaluated equations are logged into the database with corresponding user IDs and timestamps, creating a solid operational audit trail.

### 4. CAS Laboratory & Sandbox Studio
*   **Dynamic Rendering (2D/3D):** The CAS Laboratory dynamically scales its Matplotlib output based on variable counts. It plots standard 2D curves for single variables (x) and automatically shifts to 3D surface rendering for dual variables (x, y).
*   **Sandbox (Universe Simulator):** Users can define a base function and multiply it by a spatial modifier/warp function. The system computes the resulting Z matrix and renders a 3D Surface plot. Infinities (NaN/Inf) are filtered out via `np.errstate` to accurately display the absolute minimum/maximum (resistance) peaks.
*   **Memory Management:** To prevent Matplotlib memory leaks across consecutive renders, explicit garbage collection (`gc.collect()`) and `plt.close('all')` are aggressively invoked.

## 📂 Project Structure

```text
ReconCAS/
├── core/
│   ├── __init__.py
│   ├── auth_engine.py      # bcrypt, SQLite DB, Logging
│   └── math_engine.py      # SymPy Parser, Whitelist Validator
├── vision/
│   ├── __init__.py
│   └── ocr_engine.py       # Tesseract, Frame Differencing, Context-Aware Fix
├── gui/
│   ├── __init__.py
│   └── app_windows.py      # Tkinter UI (Login, Terminal, Lab, Sandbox)
├── requirements.txt        # Dependencies
└── main.py                 # Bootloader



ReconCAS V10 // Quality Assurance & Test Suite Documentation (tests/)
This document covers the technical architecture and user guide of the automated test suite (tests/) developed to verify the stability, cryptographic integrity, and security filters of the ReconCAS V10 project.

🧪 Test Architecture and Scope
The test suite is built upon Python's native unittest framework, auditing critical system components through isolated test scenarios. The directory structure consists of the following modules:

Plaintext
tests/
├── __init__.py
├── test_math.py        # Math engine and lexical whitelist security tests
├── test_auth.py        # Bcrypt cryptography and session management tests
└── test_ocr.py         # OCR text cleaning and smart corrector tests
1. test_math.py (Symbolic Math and Security Tests)
Tests the arithmetic accuracy of the math engine and its resistance against external injection attacks.

Basic Arithmetic & Factorials: Verification of fundamental operations like 587 - 325, sqrt(9), and 12!.

exp() Conflict Fix: A regression test ensuring that exp(0) calls are not corrupted into e*p(0).

Lexical Whitelist Injection Tests: Verifies that the following malicious payloads sent to system parameters are blocked by UnsafeExpressionException before reaching the SymPy parser:

__import__('os').system('dir')

x; print('hacked')

eval('1+1')

foo(x)

Polynomial Root Analysis: Validation of the root set (-4, 1) for the equation x^2 + 3x - 4 = 0.

2. test_auth.py (Cryptography and Session Security Tests)
Creates a temporary test database (test_recon_cas.db) for each test class to isolate database operations and destroys it upon completion.

Bcrypt Salt & Hashing: Verification that user passwords and recovery hints in user registrations are salted (gensalt) and hashed rather than stored in plaintext.

Authentication Cycle: Successful login scenarios returning a unique user_id, while incorrect passwords deny access.

Password Override (Reset): Ensuring the hash value in the database is securely updated after verifying the secret hint, allowing login with the new password.

3. test_ocr.py (Optical Character Recognition and Smart Corrector Tests)
Simulates the process of translating Tesseract OCR outputs from raw data into symbolic mathematical expressions.

Context-Aware Corrections: Ensuring substitutions like l -> 1 or O -> 0 are applied only to isolated characters, protecting function names such as log(x) or cos(y) from corruption.

Math Filtering (is_actual_math): Filtering out plain texts ("Hello World") or standalone numbers ("15") read by OCR to avoid unnecessary routing to the CAS engine, while passing valid equations (x + 5 = 10).

🚀 Running the Tests
To execute the test suite, run the following command from the project's root directory (ReconCAS/):

Bash
python -m unittest discover -s tests
Upon successful completion, an OK message indicating that all scenarios have passed will be displayed in the console.










🛠️ Installation Guide
Python 3.8+ and Tesseract-OCR must be installed on your system.

Step 1: Install Tesseract-OCR

For Windows, download and install the Tesseract installer.

Ensure the installation path matches the default: C:\Program Files\Tesseract-OCR\tesseract.exe (The engine explicitly targets this path).

Step 2: Clone the Repository

Bash
git clone https://github.com/yunus-EmreX/ReconCAS-Reconnaissance-Computer-Algebra-System-.git
cd ReconCAS
Step 3: Install Dependencies
Install all required Python packages automatically via the requirements file:

Bash
pip install -r requirements.txt
Step 4: Boot the Application
Execute the main script from the root directory:

Bash
python main.py
(Note: The SQLite database will be generated automatically upon the first launch. Use CREATE_ACCOUNT to register your first operator credential before logging in.)

📜 License
This project is licensed under the Apache License 2.0. See the LICENSE file for details.
