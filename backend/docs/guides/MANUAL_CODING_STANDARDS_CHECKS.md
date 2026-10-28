## 🔍 **Manual Coding Standard Checks**

### **0. Setup Poetry Environment**

```bash
# Activate Poetry virtual environment
poetry shell

# Or run commands directly with Poetry
poetry run python --version
poetry run ruff --version
poetry run bandit --version
```

### **1. Check Variable Naming Conventions**

```bash
# Check for naming convention violations
poetry run ruff check --select=N --output-format=concise app/utils/constants.py

# Check for specific naming issues
poetry run ruff check --select=N802,N803,N804,N805,N806,N807,N808,N809,N810,N811,N812,N813,N814,N815,N816,N817,N818,N819,N820,N821,N822,N823,N824,N825,N826,N827,N828,N829,N830,N831,N832,N833,N834,N835,N836,N837,N838,N839,N840,N841,N842,N843,N844,N845,N846,N847,N848,N849,N850,N851,N852,N853,N854,N855,N856,N857,N858,N859,N860,N861,N862,N863,N864,N865,N866,N867,N868,N869,N870,N871,N872,N873,N874,N875,N876,N877,N878,N879,N880,N881,N882,N883,N884,N885,N886,N887,N888,N889,N890,N891,N892,N893,N894,N895,N896,N897,N898,N899,N900,N901,N902,N903,N904,N905,N906,N907,N908,N909,N910,N911,N912,N913,N914,N915,N916,N917,N918,N919,N920,N921,N922,N923,N924,N925,N926,N927,N928,N929,N930,N931,N932,N933,N934,N935,N936,N937,N938,N939,N940,N941,N942,N943,N944,N945,N946,N947,N948,N949,N950,N951,N952,N953,N954,N955,N956,N957,N958,N959,N960,N961,N962,N963,N964,N965,N966,N967,N968,N969,N970,N971,N972,N973,N974,N975,N976,N977,N978,N979,N980,N981,N982,N983,N984,N985,N986,N987,N988,N989,N990,N991,N992,N993,N994,N995,N996,N997,N998,N999 --output-format=concise app/utils/constants.py
```

**What it checks:**
- ✅ `snake_case` for variables
- ✅ `UPPER_SNAKE_CASE` for constants
- ✅ Descriptive names (no single letters except i, j, k)
- ✅ Boolean variables start with `is_`, `has_`, `can_`, `should_`

### **2. Check Function Naming and Parameters**

```bash
# Check function naming conventions
poetry run ruff check --select=ARG --output-format=concise app/utils/decorators.py

# Check for unused parameters
poetry run ruff check --select=ARG001,ARG002,ARG003,ARG004,ARG005 --output-format=concise app/utils/decorators.py

# Check function complexity
poetry run ruff check --select=C901 --output-format=concise app/utils/decorators.py
```

**What it checks:**
- ✅ `snake_case` for functions
- ✅ Verb-based names (`create_user`, `get_by_id`)
- ✅ Clear and descriptive names
- ✅ No abbreviations unless very common
- ✅ Maximum 7 parameters per function
- ✅ Proper parameter order

### **3. Check Type Hints**

```bash
# Check type hints for a specific file
poetry run mypy app/utils/constants.py

# Check type hints for entire project
poetry run mypy .

# Check with strict settings
poetry run mypy --strict app/utils/constants.py

# Check specific type issues
poetry run mypy --disallow-untyped-defs app/utils/constants.py
```

**What it checks:**
- ✅ All functions must have return type annotations
- ✅ All parameters must have type hints
- ✅ Variables should have type hints where appropriate
- ✅ Union types using `|` operator
- ✅ Optional types using `| None`

### **4. Check Code Formatting**

```bash
# Check if code is properly formatted
poetry run black --check app/utils/constants.py

# Check entire project
poetry run black --check .

# Show what would be changed
poetry run black --diff app/utils/constants.py
```

**What it checks:**
- ✅ Line length (88 characters)
- ✅ Indentation (4 spaces)
- ✅ Quote consistency (double quotes)
- ✅ Import organization
- ✅ Trailing whitespace

### **5. Check Security Issues**

```bash
# Check security issues in a specific directory
poetry run bandit -r app/utils/ -f json -o bandit-utils-report.json

# Check security issues in entire project
poetry run bandit -r . -f json -o bandit-report.json

# Check with specific confidence levels
poetry run bandit -r . -f json -o bandit-report.json -iii

# Check specific security issues
poetry run bandit -r . -f json -o bandit-report.json -s B101,B102,B103
```

**What it checks:**
- ✅ Hardcoded passwords
- ✅ SQL injection vulnerabilities
- ✅ Shell injection vulnerabilities
- ✅ Unsafe function calls
- ✅ Security best practices

### **6. Check Import Organization**

```bash
# Check import sorting
poetry run ruff check --select=I --output-format=concise app/utils/constants.py

# Check for unused imports
poetry run ruff check --select=F401 --output-format=concise app/utils/constants.py

# Check import formatting
poetry run ruff check --select=I001,I002,I003,I004,I005 --output-format=concise app/utils/constants.py
```

**What it checks:**
- ✅ Import sorting (standard library → third-party → local)
- ✅ Unused imports
- ✅ Import formatting
- ✅ Import organization

### **7. Check Documentation**

```bash
# Check docstring formatting
poetry run ruff check --select=D --output-format=concise app/utils/decorators.py

# Check specific docstring issues
poetry run ruff check --select=D100,D101,D102,D103,D104,D105,D106,D107,D200,D201,D202,D203,D204,D205,D206,D207,D208,D209,D210,D211,D212,D213,D214,D215,D300,D301,D400,D401,D402,D403,D404,D405,D406,D407,D408,D409,D410,D411,D412,D413,D414,D415,D416,D417,D418,D419 --output-format=concise app/utils/decorators.py
```

**What it checks:**
- ✅ Missing docstrings
- ✅ Docstring formatting
- ✅ Docstring content
- ✅ Function documentation

---

## 📊 **Current Implementation Status**

### ✅ **Fully Enabled Standards:**
- **Type Annotations:** All ANN rules active
- **Docstrings:** All D100-D107 rules active
- **Naming Conventions:** All N and ARG rules active
- **Code Quality:** All essential rules active

### 🎯 **Current Coverage:**
- **Agent Files:** 100% compliant
- **Package Files:** 100% compliant
- **Remaining Files:** In progress

### 📈 **Next Steps:**
- Apply same standards to remaining files
- Maintain consistency across codebase
- Regular compliance monitoring

---

## 🛠️ **Complete Manual Check Script**

Create a script to run all checks manually:

```bash
#!/bin/bash
# manual_checks.sh

echo "🔍 Running Manual Coding Standards Checks..."

# 1. Check Variable Naming
echo "📝 Checking Variable Naming Conventions..."
poetry run ruff check --select=N --output-format=concise .

# 2. Check Function Naming and Parameters
echo "🔧 Checking Function Naming and Parameters..."
poetry run ruff check --select=ARG --output-format=concise .

# 3. Check Type Hints
echo "📋 Checking Type Hints..."
poetry run mypy .

# 4. Check Code Formatting
echo "🎨 Checking Code Formatting..."
poetry run black --check .

# 5. Check Security Issues
echo "🔒 Checking Security Issues..."
poetry run bandit -r . -f json -o bandit-report.json

# 6. Check Import Organization
echo "📦 Checking Import Organization..."
poetry run ruff check --select=I --output-format=concise .

# 7. Check Documentation
echo "📚 Checking Documentation..."
poetry run ruff check --select=D --output-format=concise .

echo "✅ Manual checks completed!"
```

**Usage:**
```bash
chmod +x manual_checks.sh
./manual_checks.sh
```

---

## 📊 **Check Results Interpretation**

### **Ruff Output Examples:**

```bash
# Good - No issues found
All checks passed!

# Issues found
app/utils/decorators.py:167:18: ARG001 Unused function argument: `ttl`
Found 1 error.
```

### **MyPy Output Examples:**

```bash
# Good - No issues found
Success: no issues found in 1 source file

# Issues found
app/utils/decorators.py:31: error: Function is missing a return type annotation
```

### **Black Output Examples:**

```bash
# Good - No formatting issues
All done! ✨ 🍰 ✨
1 file would be left unchanged.

# Issues found
would reformat app/utils/decorators.py
```

### **Bandit Output Examples:**

```bash
# Good - No security issues
No issues identified.

# Issues found
>> Issue: [B101:assert_used] Use of assert detected.
   Severity: Low   Confidence: High
   Location: app/tests/test_enums.py:23
```

---

## 🎯 **Quick Check Commands**

### **For a Single File:**
```bash
# Quick check for a specific file
poetry run ruff check app/utils/constants.py && \
poetry run mypy app/utils/constants.py && \
poetry run black --check app/utils/constants.py
```

### **For a Directory:**
```bash
# Quick check for a directory
poetry run ruff check app/utils/ && \
poetry run mypy app/utils/ && \
poetry run black --check app/utils/
```

### **For Entire Project:**
```bash
# Quick check for entire project
poetry run ruff check . && \
poetry run mypy . && \
poetry run black --check . && \
poetry run bandit -r . -f json -o bandit-report.json
```

---

## 🔧 **Auto-Fix Commands**

### **Fix Ruff Issues:**
```bash
# Auto-fix ruff issues
poetry run ruff check --fix .

# Auto-fix specific issues
poetry run ruff check --fix --select=N,ARG,I .
```

### **Fix Black Formatting:**
```bash
# Auto-format code
poetry run black .

# Format specific file
poetry run black app/utils/constants.py
```

### **Fix Import Issues:**
```bash
# Auto-fix import sorting
poetry run ruff check --fix --select=I .

# Auto-remove unused imports
poetry run ruff check --fix --select=F401 .
```

---

## 📝 **Summary**

### **Manual Check Process:**
1. **Variable Naming** → `poetry run ruff check --select=N`
2. **Function Naming** → `poetry run ruff check --select=ARG`
3. **Type Hints** → `poetry run mypy`
4. **Code Formatting** → `poetry run black --check`
5. **Security Issues** → `poetry run bandit -r`
6. **Import Organization** → `poetry run ruff check --select=I`
7. **Documentation** → `poetry run ruff check --select=D`

### **Key Points:**
- ✅ **bandit-report.json** should NOT be in Git (added to .gitignore)
- ✅ Use manual checks before committing
- ✅ Auto-fix when possible
- ✅ Run comprehensive checks regularly
- ✅ Interpret results correctly

### **Best Practices:**
- Run manual checks before committing
- Fix issues immediately when found
- Use auto-fix tools when safe
- Review security reports carefully
- Keep documentation up to date
