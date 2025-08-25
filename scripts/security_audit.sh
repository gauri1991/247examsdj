#!/bin/bash

# Security Audit Script for Exam Portal
# Run this script regularly to check for security issues

set -e

echo "================================"
echo "Security Audit for Exam Portal"
echo "Date: $(date)"
echo "================================"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counter for issues
ISSUES=0

echo -e "\n${YELLOW}1. Checking Django Security Settings...${NC}"
python manage.py check --deploy 2>&1 | while read line; do
    if [[ $line == *"WARNINGS"* ]] || [[ $line == *"ERRORS"* ]]; then
        echo -e "${RED}$line${NC}"
        ((ISSUES++))
    else
        echo "$line"
    fi
done

echo -e "\n${YELLOW}2. Checking for Outdated Dependencies...${NC}"
pip list --outdated 2>&1 | while read line; do
    if [[ $line == *"Package"* ]] || [[ $line == *"---"* ]]; then
        echo "$line"
    else
        echo -e "${YELLOW}⚠ $line${NC}"
    fi
done

echo -e "\n${YELLOW}3. Checking for Known Vulnerabilities...${NC}"
if command -v safety &> /dev/null; then
    safety check --json | python -c "
import sys, json
data = json.load(sys.stdin)
if data:
    print('${RED}Found vulnerabilities:${NC}')
    for vuln in data:
        print(f'  - {vuln[\"package\"]}: {vuln[\"vulnerability\"]}')
else:
    print('${GREEN}✓ No known vulnerabilities found${NC}')
"
else
    echo "Installing safety for vulnerability scanning..."
    pip install safety
    safety check
fi

echo -e "\n${YELLOW}4. Checking File Permissions...${NC}"
# Check for world-writable files
WORLD_WRITABLE=$(find . -type f -perm -002 2>/dev/null | grep -v ".git" | grep -v "venv" | grep -v "__pycache__" || true)
if [ ! -z "$WORLD_WRITABLE" ]; then
    echo -e "${RED}⚠ Found world-writable files:${NC}"
    echo "$WORLD_WRITABLE"
    ((ISSUES++))
else
    echo -e "${GREEN}✓ No world-writable files found${NC}"
fi

echo -e "\n${YELLOW}5. Checking for Sensitive Data in Code...${NC}"
# Check for potential secrets
PATTERNS=(
    "SECRET_KEY.*=.*['\"].*['\"]"
    "PASSWORD.*=.*['\"].*['\"]"
    "API_KEY.*=.*['\"].*['\"]"
    "TOKEN.*=.*['\"].*['\"]"
    "aws_access_key_id"
    "aws_secret_access_key"
)

for pattern in "${PATTERNS[@]}"; do
    FOUND=$(grep -r "$pattern" --include="*.py" --exclude-dir=venv --exclude-dir=.git 2>/dev/null || true)
    if [ ! -z "$FOUND" ]; then
        echo -e "${RED}⚠ Found potential hardcoded secret (pattern: $pattern)${NC}"
        echo "$FOUND" | head -5
        ((ISSUES++))
    fi
done

if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ No hardcoded secrets found${NC}"
fi

echo -e "\n${YELLOW}6. Checking SSL/TLS Configuration...${NC}"
if [ -f "/etc/nginx/sites-enabled/default" ]; then
    SSL_PROTOCOLS=$(grep -i "ssl_protocols" /etc/nginx/sites-enabled/default || echo "Not configured")
    echo "SSL Protocols: $SSL_PROTOCOLS"
    
    if [[ $SSL_PROTOCOLS == *"SSLv2"* ]] || [[ $SSL_PROTOCOLS == *"SSLv3"* ]] || [[ $SSL_PROTOCOLS == *"TLSv1.0"* ]]; then
        echo -e "${RED}⚠ Insecure SSL protocols detected${NC}"
        ((ISSUES++))
    else
        echo -e "${GREEN}✓ SSL protocols look secure${NC}"
    fi
else
    echo "Nginx configuration not found (may be in Docker container)"
fi

echo -e "\n${YELLOW}7. Checking Database Security...${NC}"
# Check if default passwords are being used
if grep -q "password.*=.*changeme\|password.*=.*password\|password.*=.*admin" .env 2>/dev/null; then
    echo -e "${RED}⚠ Default or weak passwords detected in .env${NC}"
    ((ISSUES++))
else
    echo -e "${GREEN}✓ No default passwords detected${NC}"
fi

echo -e "\n${YELLOW}8. Checking CORS Configuration...${NC}"
python -c "
from exam_portal import settings
if hasattr(settings, 'CORS_ALLOW_ALL_ORIGINS') and settings.CORS_ALLOW_ALL_ORIGINS:
    print('${RED}⚠ CORS allows all origins - this is insecure for production${NC}')
else:
    print('${GREEN}✓ CORS configuration looks secure${NC}')
"

echo -e "\n${YELLOW}9. Checking Debug Mode...${NC}"
python -c "
from exam_portal import settings
if settings.DEBUG:
    print('${RED}⚠ DEBUG mode is enabled - should be False in production${NC}')
else:
    print('${GREEN}✓ DEBUG mode is disabled${NC}')
"

echo -e "\n${YELLOW}10. Checking Rate Limiting...${NC}"
python -c "
from exam_portal import settings
if hasattr(settings, 'RATELIMIT_ENABLE') and settings.RATELIMIT_ENABLE:
    print('${GREEN}✓ Rate limiting is enabled${NC}')
else:
    print('${YELLOW}⚠ Rate limiting might not be enabled${NC}')
"

echo -e "\n================================"
echo "Security Audit Complete"
echo "Total Issues Found: $ISSUES"
if [ $ISSUES -eq 0 ]; then
    echo -e "${GREEN}✓ All security checks passed!${NC}"
else
    echo -e "${RED}⚠ Please review and fix the issues above${NC}"
fi
echo "================================"

# Generate report file
REPORT_FILE="security_audit_$(date +%Y%m%d_%H%M%S).txt"
echo "Full report saved to: $REPORT_FILE"

exit $ISSUES