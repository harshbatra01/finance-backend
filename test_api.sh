#!/bin/bash
# Comprehensive API test script
# Tests all endpoints, RBAC, validation, and error handling

BASE="http://localhost:5000/api"
PASS=0
FAIL=0

check() {
    local desc="$1"
    local expected_code="$2"
    local actual_code="$3"
    local response="$4"
    if [ "$actual_code" = "$expected_code" ]; then
        echo "  ✅ $desc (HTTP $actual_code)"
        PASS=$((PASS + 1))
    else
        echo "  ❌ $desc — expected $expected_code, got $actual_code"
        echo "     Response: $response"
        FAIL=$((FAIL + 1))
    fi
}

echo "============================================"
echo "  FINANCE BACKEND API TEST SUITE"
echo "============================================"

# ---- AUTH TESTS ----
echo ""
echo "🔐 Authentication Tests"
echo "------------------------"

# Login as admin
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Admin login" "200" "$CODE" "$BODY"
ADMIN_TOKEN=$(echo "$BODY" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)

# Login as analyst
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"analyst@example.com","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Analyst login" "200" "$CODE" "$BODY"
ANALYST_TOKEN=$(echo "$BODY" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)

# Login as viewer
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"viewer@example.com","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Viewer login" "200" "$CODE" "$BODY"
VIEWER_TOKEN=$(echo "$BODY" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['data']['token'])" 2>/dev/null)

# Invalid login
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"wrongpassword"}')
CODE=$(echo "$RESP" | tail -1)
check "Invalid password rejected" "401" "$CODE"

# Get profile
RESP=$(curl -s -w "\n%{http_code}" "$BASE/auth/me" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Get admin profile" "200" "$CODE"

# No token
RESP=$(curl -s -w "\n%{http_code}" "$BASE/auth/me")
CODE=$(echo "$RESP" | tail -1)
check "Reject request without token" "401" "$CODE"

# ---- USER MANAGEMENT TESTS ----
echo ""
echo "👥 User Management Tests"
echo "------------------------"

# Admin lists users
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Admin lists all users" "200" "$CODE"

# Viewer cannot list users (RBAC)
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users" \
  -H "Authorization: Bearer $VIEWER_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Viewer denied user list (RBAC)" "403" "$CODE"

# Analyst cannot list users (RBAC)
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Analyst denied user list (RBAC)" "403" "$CODE"

# Register new user
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Test User","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Register new user" "201" "$CODE"
TEST_USER_ID=$(echo "$BODY" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)

# Duplicate email
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","name":"Another","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject duplicate email" "409" "$CODE"

# Update user role
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/users/$TEST_USER_ID/role" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"analyst"}')
CODE=$(echo "$RESP" | tail -1)
check "Admin updates user role" "200" "$CODE"

# Update user status
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/users/$TEST_USER_ID/status" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status":"inactive"}')
CODE=$(echo "$RESP" | tail -1)
check "Admin deactivates user" "200" "$CODE"

# Delete user
RESP=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE/users/$TEST_USER_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Admin deletes user" "204" "$CODE"

# Get non-existent user
RESP=$(curl -s -w "\n%{http_code}" "$BASE/users/non-existent-id" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "404 for non-existent user" "404" "$CODE"

# ---- FINANCIAL RECORDS TESTS ----
echo ""
echo "💰 Financial Records Tests"
echo "--------------------------"

# Admin creates record
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":1234.56,"type":"income","category":"Bonus","date":"2026-03-15","description":"Q1 bonus"}')
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Admin creates record" "201" "$CODE"
RECORD_ID=$(echo "$BODY" | /usr/bin/python3 -c "import sys,json; print(json.load(sys.stdin)['data']['id'])" 2>/dev/null)

# Viewer cannot create record
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"type":"income","category":"Test","date":"2026-03-01"}')
CODE=$(echo "$RESP" | tail -1)
check "Viewer denied record creation (RBAC)" "403" "$CODE"

# Analyst cannot create record
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ANALYST_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"type":"income","category":"Test","date":"2026-03-01"}')
CODE=$(echo "$RESP" | tail -1)
check "Analyst denied record creation (RBAC)" "403" "$CODE"

# All roles can view records
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records" \
  -H "Authorization: Bearer $VIEWER_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Viewer reads records" "200" "$CODE"

RESP=$(curl -s -w "\n%{http_code}" "$BASE/records" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Analyst reads records" "200" "$CODE"

# Get specific record
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records/$RECORD_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Get specific record" "200" "$CODE"

# Filter by type
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?type=income" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Filter records by type" "200" "$CODE"

# Filter by category
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?category=Salary" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Filter records by category" "200" "$CODE"

# Filter by date range
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?date_from=2026-01-01&date_to=2026-12-31" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Filter records by date range" "200" "$CODE"

# Filter by amount range
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?min_amount=1000&max_amount=5000" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Filter records by amount range" "200" "$CODE"

# Sorting
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?sort_by=amount&sort_order=asc" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Sort records by amount asc" "200" "$CODE"

# Update record
RESP=$(curl -s -w "\n%{http_code}" -X PUT "$BASE/records/$RECORD_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":2000.00,"description":"Updated bonus"}')
CODE=$(echo "$RESP" | tail -1)
check "Admin updates record" "200" "$CODE"

# Viewer cannot update
RESP=$(curl -s -w "\n%{http_code}" -X PUT "$BASE/records/$RECORD_ID" \
  -H "Authorization: Bearer $VIEWER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":999.00}')
CODE=$(echo "$RESP" | tail -1)
check "Viewer denied record update (RBAC)" "403" "$CODE"

# Viewer cannot delete
RESP=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE/records/$RECORD_ID" \
  -H "Authorization: Bearer $VIEWER_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Viewer denied record delete (RBAC)" "403" "$CODE"

# Delete record
RESP=$(curl -s -w "\n%{http_code}" -X DELETE "$BASE/records/$RECORD_ID" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Admin deletes record" "204" "$CODE"

# ---- DASHBOARD TESTS ----
echo ""
echo "📊 Dashboard Tests"
echo "-------------------"

# Summary
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/summary" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
BODY=$(echo "$RESP" | sed '$d')
check "Admin gets dashboard summary" "200" "$CODE"
echo "     Summary: $(echo "$BODY" | /usr/bin/python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(f\"Income: {d['total_income']}, Expenses: {d['total_expenses']}, Net: {d['net_balance']}, Records: {d['total_records']}\")" 2>/dev/null)"

# Analyst can view dashboard
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/summary" \
  -H "Authorization: Bearer $ANALYST_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Analyst gets dashboard summary" "200" "$CODE"

# Viewer cannot view dashboard
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/summary" \
  -H "Authorization: Bearer $VIEWER_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Viewer denied dashboard (RBAC)" "403" "$CODE"

# Category breakdown
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/category-breakdown" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Category breakdown" "200" "$CODE"

# Monthly trends
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/trends" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Monthly trends" "200" "$CODE"

# Trends with custom months
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/trends?months=6" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Monthly trends (6 months)" "200" "$CODE"

# Recent activity
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/recent-activity" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Recent activity" "200" "$CODE"

# Recent activity with limit
RESP=$(curl -s -w "\n%{http_code}" "$BASE/dashboard/recent-activity?limit=5" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Recent activity (limit 5)" "200" "$CODE"

# ---- VALIDATION TESTS ----
echo ""
echo "🛡️  Validation & Error Handling Tests"
echo "--------------------------------------"

# Missing required fields
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}')
CODE=$(echo "$RESP" | tail -1)
check "Reject empty record body" "400" "$CODE"

# Negative amount
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":-100,"type":"income","category":"Test","date":"2026-03-01"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject negative amount" "400" "$CODE"

# Invalid type
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"type":"invalid","category":"Test","date":"2026-03-01"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject invalid record type" "400" "$CODE"

# Invalid date format
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/records" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"amount":100,"type":"income","category":"Test","date":"not-a-date"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject invalid date format" "400" "$CODE"

# Invalid email on registration
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"not-an-email","name":"Test","password":"password123"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject invalid email" "400" "$CODE"

# Short password
RESP=$(curl -s -w "\n%{http_code}" -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"new@example.com","name":"Test","password":"short"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject short password" "400" "$CODE"

# Invalid role
RESP=$(curl -s -w "\n%{http_code}" -X PATCH "$BASE/users/some-id/role" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"superadmin"}')
CODE=$(echo "$RESP" | tail -1)
check "Reject invalid role value" "400" "$CODE"

# Invalid filter type
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records?type=invalid" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "Reject invalid type filter" "400" "$CODE"

# 404 for missing record
RESP=$(curl -s -w "\n%{http_code}" "$BASE/records/non-existent-id" \
  -H "Authorization: Bearer $ADMIN_TOKEN")
CODE=$(echo "$RESP" | tail -1)
check "404 for non-existent record" "404" "$CODE"

# ---- SUMMARY ----
echo ""
echo "============================================"
echo "  TEST RESULTS: $PASS passed, $FAIL failed"
echo "============================================"
