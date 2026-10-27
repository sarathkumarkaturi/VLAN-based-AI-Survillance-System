#!/bin/bash
echo "Validation Test Results"
test_ping() {
  ping -c 1 -W 1 $2 > /dev/null 2>&1
  if [ $? -eq 0 ] && [ "$3" == "ALLOW" ]; then echo "PASS: $1";
  elif [ $? -ne 0 ] && [ "$3" == "BLOCK" ]; then echo "PASS: $1";
  else echo "FAIL: $1"; fi
}
test_ping "1. Student -> Student" "192.168.10.100" "ALLOW"
test_ping "2. Student -> ERP" "192.168.30.100" "BLOCK"
test_ping "3. Student -> Exam" "192.168.40.100" "BLOCK"
test_ping "4. Faculty -> ERP" "192.168.30.100" "ALLOW"
test_ping "5. IoT -> Faculty" "192.168.20.100" "BLOCK"
test_ping "6. Student -> Gateway" "192.168.10.1" "ALLOW"
test_ping "7. Exam -> Gateway" "192.168.40.1" "ALLOW"
test_ping "8. CCTV -> Gateway" "192.168.60.1" "ALLOW"
