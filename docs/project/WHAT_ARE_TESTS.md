# What Are Tests? (Simple Explanation)

**Understanding automated testing in your Claims Management System**

---

## The Simple Answer

**Tests are automatic checks that verify your code works correctly.**

Think of them like a **quality control inspector** that checks your application automatically, 24/7.

---

## Real-World Analogy

### Without Tests (Manual Testing)

Imagine you're running a bakery:

1. You bake 100 loaves of bread
2. **You personally** taste each loaf to check quality
3. **You personally** check if they're the right size
4. **You personally** verify they're properly baked
5. Every time you change the recipe, you repeat ALL checks

⏱️ **Time**: Hours of manual work
😰 **Risk**: Might miss something, get tired, forget a check

### With Tests (Automated Testing)

Now imagine you have a robot helper:

1. You bake 100 loaves of bread
2. **Robot automatically** checks taste, size, temperature
3. **Robot runs** all checks in minutes
4. **Robot never gets tired** or forgets a check
5. Change recipe? Robot re-checks everything instantly

⏱️ **Time**: 2 minutes
😊 **Confidence**: Nothing gets missed

**Your tests are the robot helper for your code!**

---

## What Tests Do in Your Project

### Your Project Has 173 Tests

These tests automatically check:

1. **User Login Works**
   ```
   Test: Can user login with correct password?
   Test: Does login fail with wrong password?
   Test: Does admin have full access?
   ```

2. **Claims Work Correctly**
   ```
   Test: Can we create a claim?
   Test: Does claim amount calculate correctly?
   Test: Can we update claim status?
   Test: Does time-bar detection work?
   ```

3. **Voyages Work**
   ```
   Test: Can we assign voyage to analyst?
   Test: Does assignment history save?
   Test: Can team lead reassign voyages?
   ```

4. **Ships Work**
   ```
   Test: Does TC charter expiry calculate correctly?
   Test: Are IMO numbers unique?
   Test: Does charter status show correctly?
   ```

5. **Port Activities Work**
   ```
   Test: Does duration calculate correctly?
   Test: Can we detect overlapping activities?
   Test: Does RADAR sync work?
   ```

---

## When Do Tests Run?

### You Choose When to Run Them

Tests **don't run automatically in production**. You decide when to run them:

### 1. **During Development** (You, Right Now)

```bash
# Run all tests manually
pytest

# Output:
# ✅ 173 tests passed in 2.5 seconds
```

**When to run:**
- Before committing code
- After making changes
- When something breaks

**Purpose**: Make sure your changes didn't break anything

---

### 2. **Before Deploying** (You, Before Going Live)

```bash
# Run tests before deployment
pytest

# If all pass ✅ → Safe to deploy
# If any fail ❌ → Fix before deploying
```

**When to run:**
- Before pushing to enterprise GitHub
- Before stakeholder presentation
- Before production deployment

**Purpose**: Confidence that app works before showing it

---

### 3. **In CI/CD Pipeline** (Automatic, Optional)

Your project has GitHub Actions configured:

```yaml
# .github/workflows/django-tests.yml
# Runs tests automatically when you push to GitHub
```

**When it runs:**
- Automatically when you push code
- When you create a pull request
- When someone else contributes

**Purpose**: Automatic safety net - catches problems before they reach production

**Status**: ⚠️ Currently configured but optional to use

---

### 4. **Production** (NOT Recommended)

❌ **Tests do NOT run in production**
❌ **Tests do NOT run in background on live server**

**Why not?**
- Tests are for development only
- Production should only run the actual app
- Tests can be slow (not for live users)

---

## Example: How Tests Protect You

### Scenario: You Make a Change

**Without Tests:**
```
You: "Let me change how claim amounts are calculated"
      [Changes code]
You: "Looks good! Deploy to production"
      [Deploys]
Users: "Hey! Our claim amounts are wrong now!"
You: "Oh no! I broke something and didn't realize!"
      [Panic, rollback, fix, redeploy]
```

**With Tests:**
```
You: "Let me change how claim amounts are calculated"
      [Changes code]
You: "Let me run tests first"
      [Runs: pytest]

Test Output:
  ❌ FAILED: test_claim_amount_calculation
  ❌ FAILED: test_outstanding_amount
  ✅ PASSED: test_claim_creation (171 other tests pass)

You: "Ah! My change broke the calculation. Let me fix it."
      [Fixes the bug]
      [Runs tests again]

Test Output:
  ✅ PASSED: All 173 tests passed

You: "Perfect! Now it's safe to deploy."
      [Deploys with confidence]
Users: "Everything works perfectly!"
```

**Tests caught the bug BEFORE it reached users!**

---

## What Tests Are Checking in Your Project

### 1. **User Model** (29 tests)

```python
# Example tests:
- Can create user ✅
- User roles work correctly ✅
- Passwords are encrypted ✅
- Admin has full permissions ✅
- READ user can't edit claims ✅
```

### 2. **Claims** (23 tests)

```python
# Example tests:
- Claim creation works ✅
- Claim amount calculation correct ✅
- Outstanding amount = Claim - Paid ✅
- Time-bar detection works ✅
- Status workflow works ✅
```

### 3. **Voyages** (17 tests)

```python
# Example tests:
- Voyage assignment works ✅
- Assignment history tracked ✅
- Can't assign to READ-only user ✅
- Reassignment with reason works ✅
```

### 4. **Ships** (38 tests)

```python
# Example tests:
- IMO numbers are unique ✅
- Charter days remaining calculated ✅
- TC expiry warnings work ✅
- Ship specifications valid ✅
```

### 5. **Port Activities** (44 tests)

```python
# Example tests:
- Activity duration calculated ✅
- Overlap detection works ✅
- RADAR sync ready ✅
- Activity types loaded ✅
```

---

## Are Tests Just For You?

### Yes AND No

**For You (Developer):**
✅ Catch bugs before deployment
✅ Safe to make changes (tests will catch breaks)
✅ Confidence when refactoring
✅ Documentation of how features should work

**For Your Team:**
✅ Other developers know what's expected
✅ New team members understand requirements
✅ Code quality stays high
✅ Prevents regressions (old bugs coming back)

**For Your Company:**
✅ Professional quality code
✅ Fewer bugs in production
✅ Faster development (less time fixing bugs)
✅ Reliable application

**For Your Stakeholders:**
✅ Confidence in code quality
✅ Fewer production issues
✅ Professional development practices
✅ Easy to add new features safely

---

## How to Use Tests (Practical Guide)

### Daily Development

```bash
# 1. Make changes to code
# ... edit files ...

# 2. Run tests to verify nothing broke
pytest

# 3. If tests pass, commit
git add .
git commit -m "Add new feature"

# 4. If tests fail, fix the issue first
# ... fix code ...
pytest  # Run again until all pass
```

### Before Important Milestones

```bash
# Before stakeholder presentation
pytest --verbose

# Before deploying to enterprise
pytest --cov  # With coverage report

# Before going to production
pytest && python manage.py check
```

### When Something Breaks

```bash
# Run specific test to debug
pytest claims/tests.py::TestClaimModel::test_claim_amount

# See detailed output
pytest -v -s

# Stop at first failure
pytest -x
```

---

## Test Results Explained

### When You Run Tests

```bash
pytest
```

### You'll See Output Like This

```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-7.4.0
collected 173 items

claims/tests.py::TestUserModel::test_user_creation ✅ PASSED
claims/tests.py::TestUserModel::test_user_permissions ✅ PASSED
claims/tests.py::TestClaimModel::test_claim_creation ✅ PASSED
claims/tests.py::TestClaimModel::test_claim_amount ✅ PASSED
... (169 more tests)

============================= 173 passed in 2.56s ==============================
```

**What This Means:**
- ✅ All 173 checks passed
- ⏱️ Took 2.56 seconds
- 🎉 Your code is working correctly!

---

## Test Coverage (Advanced Concept)

### What is Coverage?

**Coverage** = What percentage of your code is tested

```bash
pytest --cov
```

Output:
```
Name                    Stmts   Miss  Cover
-------------------------------------------
claims/models.py          450     50    89%
claims/views.py          1249    850    32%
ships/models.py           120      5    96%
-------------------------------------------
TOTAL                    3500   1050    70%
```

**What This Means:**
- **89% coverage** in models.py = Most code is tested ✅
- **32% coverage** in views.py = Needs more tests ⚠️
- **70% total** = Good overall coverage ✅

**Target**: 70%+ coverage is professional quality

---

## Should You Write More Tests?

### You Already Have Great Coverage!

**Current Status:**
- ✅ 173 tests passing
- ✅ 70%+ code coverage
- ✅ All models tested
- ✅ Business logic tested

**This is already professional quality!**

### When to Add More Tests

Only add tests when:
1. Adding new features (test the new feature)
2. Fixing bugs (add test to prevent regression)
3. Refactoring code (ensure nothing breaks)

**Don't need to:**
- Test everything to 100%
- Test simple getters/setters
- Test Django framework itself
- Over-test just for numbers

---

## Common Questions

### Q: Do tests slow down my app?

**A: No.** Tests only run when YOU run them. They don't affect production speed.

### Q: Can I delete tests?

**A: Not recommended.** Tests are insurance. Keep them!

### Q: Do I have to run tests?

**A: No, but highly recommended.** They catch bugs before users see them.

### Q: Are tests required for production?

**A: No, but professional teams always use them.**

### Q: What if a test fails?

**A: Fix the code or fix the test** (if test is wrong). Don't ignore it!

---

## Real Example from Your Project

### Test Code (What It Does)

```python
def test_claim_amount_cannot_be_negative():
    """Test that claims can't have negative amounts"""
    with pytest.raises(ValidationError):
        Claim.objects.create(
            claim_amount=-1000  # Negative amount
        )
```

**What This Tests:**
- ❌ System should reject negative claim amounts
- ✅ Prevents data corruption
- ✅ Protects database integrity

**Without This Test:**
- Someone might create claim with negative amount
- Database would accept it
- Reports would be wrong
- Financial data corrupted

**With This Test:**
- Test runs in 0.001 seconds
- Catches the bug immediately
- Prevents bad data
- Developers know the rule

---

## GitHub Actions (CI/CD)

### Your Project Has Automatic Testing Set Up

**File**: `.github/workflows/django-tests.yml`

**What It Does:**
1. When you push to GitHub
2. GitHub automatically runs all tests
3. You get email/notification if tests fail
4. Pull requests show test status

**Example:**
```
✅ All checks passed
   - Tests: 173 passed
   - Code quality: Passed
   - Security scan: Passed

→ Safe to merge!
```

**Benefits:**
- Automatic quality control
- Catches issues immediately
- No need to remember to run tests
- Team confidence in code quality

---

## Summary (TL;DR)

### What Are Tests?

**Tests = Automatic quality checks for your code**

### When Do They Run?

1. ✅ When YOU run them (manually during development)
2. ✅ Before deployment (your choice)
3. ✅ On GitHub automatically (optional, already configured)
4. ❌ NOT in production (tests are for development only)

### Why Are They Important?

1. **Catch bugs early** - Before users see them
2. **Confidence** - Know your code works
3. **Safety net** - Make changes without fear
4. **Professional** - Industry best practice
5. **Documentation** - Shows how features should work

### Should You Use Them?

**YES!** Especially:
- Before pushing to enterprise GitHub
- Before stakeholder presentations
- After making changes
- When debugging issues

### Your Status

✅ **173 tests** - Excellent coverage!
✅ **70%+ coverage** - Professional quality!
✅ **All passing** - Code works correctly!
✅ **CI/CD ready** - Automatic testing configured!

**You're already doing great!** Keep running tests before important deployments.

---

## Quick Command Reference

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov

# Run specific test file
pytest claims/tests.py

# Run specific test
pytest claims/tests.py::TestClaimModel

# Stop at first failure
pytest -x

# Show print statements
pytest -s
```

---

## Need More Help?

- **Full Testing Guide**: [docs/development/TESTING.md](../development/TESTING.md)
- **Run Tests**: `pytest`
- **Check Coverage**: `pytest --cov`

---

**Remember**: Tests are your friends! They help you catch bugs before your users do. 🛡️

---

*Last Updated: January 5, 2026*
