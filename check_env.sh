#!/bin/bash

# ==========================
#  System & Tool Checker
#  Author: ChatGPT & Huynh Hiep
#  Purpose: Generate environment report
# ==========================

OUTPUT_FILE="check_env.txt"

echo "=== Checking system environment ==="
{
    echo "======================================="
    echo "🔍 SYSTEM ENVIRONMENT REPORT"
    echo "Generated on: $(date)"
    echo "======================================="
    echo ""

    echo "🖥️  Operating System:"
    lsb_release -d 2>/dev/null || cat /etc/os-release | grep PRETTY_NAME
    echo ""

    echo "⚙️  CPU Info:"
    lscpu | grep -E "Model name|CPU\(s\)"
    echo ""

    echo "💾 RAM Info:"
    free -h | grep Mem
    echo ""

    echo "🎮 GPU Info:"
    lspci | grep VGA || echo "No VGA device found"
    echo ""

    echo "🐳 Docker Version:"
    docker --version 2>/dev/null || echo "Docker not found"
    echo ""

    echo "☸️  Minikube Version:"
    minikube version 2>/dev/null | head -n 1 || echo "Minikube not found"
    echo ""

    echo "🏗️  Terraform Version:"
    terraform version 2>/dev/null | head -n 1 || echo "Terraform not found"
    echo ""

    echo "======================================="
    echo "✅ Check completed successfully."
    echo "File generated: $(realpath $OUTPUT_FILE)"
} > "$OUTPUT_FILE"

echo "✅ Environment information has been saved to: $OUTPUT_FILE"
