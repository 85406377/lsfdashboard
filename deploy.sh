#!/bin/bash

# LSF Dashboard GitHub 部署脚本

echo "=== LSF Dashboard GitHub 部署脚本 ==="

# 1. 配置 Git 用户信息
echo "1. 配置 Git 用户信息..."
git config --global user.name "Jason Li"
git config --global user.email "jasonli-dr@example.com"

# 2. 检查当前分支
echo "2. 检查当前分支..."
current_branch=$(git branch --show-current)
echo "当前分支: $current_branch"

# 3. 重命名分支为 main（如果需要）
if [ "$current_branch" = "master" ]; then
    echo "重命名分支从 master 到 main..."
    git branch -M main
fi

# 4. 添加远程仓库（请替换为你的 GitHub 仓库 URL）
echo "4. 请手动创建 GitHub 仓库后，将下面的 URL 替换为你的仓库地址"
echo "例如：https://github.com/你的用户名/lsf-dashboard.git"
echo "或者：git@github.com:你的用户名/lsf-dashboard.git"
echo ""
echo "执行以下命令添加远程仓库："
echo "git remote add origin https://github.com/你的用户名/lsf-dashboard.git"
echo ""
echo "或者 SSH 方式："
echo "git remote add origin git@github.com:你的用户名/lsf-dashboard.git"
echo ""

# 5. 推送代码
echo "5. 推送代码到 GitHub..."
echo "执行以下命令："
echo "git push -u origin main"

echo ""
echo "=== 手动步骤 ==="
echo "1. 登录 GitHub (https://github.com)"
echo "2. 点击 '+' → 'New repository'"
echo "3. Repository name: lsf-dashboard"
echo "4. Description: IBM LSF 作业监控 Dashboard - Python + Vue + PyECharts"
echo "5. 选择 Public/Private"
echo "6. 不要勾选 'Add a README file'"
echo "7. 点击 'Create repository'"
echo "8. 复制上面的命令执行"

echo ""
echo "=== 当前 Git 状态 ==="
git status
echo ""
echo "=== 最近提交记录 ==="
git log --oneline -5