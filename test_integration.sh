#!/bin/bash

echo "===================================="
echo "Testing Full Stack Integration"
echo "===================================="
echo ""

# Test 1: Backend Health Check
echo "1. Testing Backend Health..."
curl -s http://localhost:8000/health | jq '.'
echo ""

# Test 2: Dashboard Stats
echo "2. Testing Dashboard Stats API..."
curl -s http://localhost:8000/api/dashboard/stats | jq '.'
echo ""

# Test 3: Check Frontend is Running
echo "3. Checking Frontend..."
if curl -s http://localhost:3001 > /dev/null; then
    echo "✅ Frontend is running on http://localhost:3001"
else
    echo "❌ Frontend is NOT running"
fi
echo ""

echo "===================================="
echo "Integration Points:"
echo "===================================="
echo "✅ Backend API: http://localhost:8000"
echo "✅ Frontend: http://localhost:3001"
echo "✅ Swagger Docs: http://localhost:8000/docs"
echo ""
echo "Test Flow:"
echo "1. Go to http://localhost:3001/upload"
echo "2. Upload a receipt image"
echo "3. Gemini Vision will extract data"
echo "4. Review extracted data"
echo "5. Generate health insights"
echo "6. View results with AI analysis"
echo ""
