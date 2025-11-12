#!/usr/bin/env powershell

# CodeArtifact Configuration Script (Windows PowerShell Version)
# Used to configure Poetry to use AWS CodeArtifact private repository
# Packages are deployed to AWS CodeArtifact private repository, requires AWS credentials configuration
#  1. Install AWS CLI
#  2. Ask admin to provision AWS account
#  3. Run `aws configure sso --profile oxsci-dev` to configure AWS credentials, enter the following configuration:
#     - SSO session name (Recommended): oxsci-dev
#     - SSO start URL: https://oxsci-ai.awsapps.com/start
#     - SSO region: ap-southeast-1
#     - SSO registration scopes: sso:account:access
#  4. A login page will pop up for authentication
#  5. After successful login, select default region as ap-southeast-1, and default output as json
#  6. Copy this script to the project root directory
#  7. Run `./entrypoint-dev.ps1` in the project root directory (needs to be executed every 12 hours)

$ErrorActionPreference = "Stop"

$PROFILE_NAME = "oxsci-dev"
$DOMAIN = "oxsci-domain"
$DOMAIN_OWNER = "000373574646"
$REPOSITORY = "oxsci-pypi"
$REGION = "ap-southeast-1"

Write-Host "🔧 开始配置 AWS CodeArtifact 用于 Poetry..." -ForegroundColor Cyan

# 检查 AWS CLI 是否安装
if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "❌ AWS CLI 未安装，请先安装 AWS CLI" -ForegroundColor Red
    exit 1
}

# 检查 Poetry 是否安装
if (-not (Get-Command poetry -ErrorAction SilentlyContinue)) {
    Write-Host "❌ Poetry 未安装，请先安装 Poetry" -ForegroundColor Red
    exit 1
}

# 检查 AWS Profile 是否存在
Write-Host "🔍 检查 AWS Profile: $PROFILE_NAME" -ForegroundColor Yellow
$profiles = aws configure list-profiles
if ($profiles -notcontains $PROFILE_NAME) {
    Write-Host "❌ AWS Profile '$PROFILE_NAME' 不存在" -ForegroundColor Red
    Write-Host ""
    Write-Host "请配置 AWS Profile，推荐使用 SSO："
    Write-Host "  aws configure sso --profile $PROFILE_NAME"
    Write-Host ""
    Write-Host "或使用传统方式配置："
    Write-Host "  aws configure --profile $PROFILE_NAME"
    Write-Host ""
    Write-Host "确保 Profile 拥有 CodeArtifact 相关权限："
    Write-Host "  - codeartifact:GetRepositoryEndpoint"
    Write-Host "  - codeartifact:GetAuthorizationToken"
    exit 1
}

# 测试 Profile 是否有效，如果无效则尝试自动登录
Write-Host "🔐 验证 AWS Profile 权限..." -ForegroundColor Yellow
$identityCheck = aws sts get-caller-identity --profile $PROFILE_NAME 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  AWS Profile '$PROFILE_NAME' 无法验证身份，尝试自动登录..." -ForegroundColor Yellow
    aws sso login --profile $PROFILE_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ SSO 登录失败，请手动执行：" -ForegroundColor Red
        Write-Host "  aws sso login --profile $PROFILE_NAME"
        exit 1
    }
    Write-Host "✅ SSO 登录成功" -ForegroundColor Green
} else {
    Write-Host "✅ AWS Profile 验证成功" -ForegroundColor Green
}

# 获取 CodeArtifact 仓库 URL
Write-Host "🌐 获取 CodeArtifact 仓库端点..." -ForegroundColor Yellow
$REPO_URL = aws codeartifact get-repository-endpoint `
    --profile $PROFILE_NAME `
    --domain $DOMAIN `
    --domain-owner $DOMAIN_OWNER `
    --repository $REPOSITORY `
    --format pypi `
    --region $REGION `
    --query repositoryEndpoint `
    --output text 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($REPO_URL)) {
    Write-Host "❌ 获取仓库端点失败，请检查权限和参数" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 仓库端点获取成功: $REPO_URL" -ForegroundColor Green

# 配置 Poetry 仓库
Write-Host "📦 配置 Poetry 仓库..." -ForegroundColor Yellow
poetry config repositories.oxsci-ca $REPO_URL

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Poetry 仓库配置失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Poetry 仓库配置成功" -ForegroundColor Green

# 获取认证令牌
Write-Host "🔑 获取认证令牌..." -ForegroundColor Yellow
$AUTH_TOKEN = aws codeartifact get-authorization-token `
    --profile $PROFILE_NAME `
    --domain $DOMAIN `
    --domain-owner $DOMAIN_OWNER `
    --region $REGION `
    --query authorizationToken `
    --output text 2>&1

if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrEmpty($AUTH_TOKEN)) {
    Write-Host "❌ 获取认证令牌失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ 认证令牌获取成功" -ForegroundColor Green

# 配置 Poetry 认证
Write-Host "🔐 配置 Poetry 认证..." -ForegroundColor Yellow
poetry config http-basic.oxsci-ca aws $AUTH_TOKEN

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Poetry 认证配置失败" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Poetry 认证配置成功" -ForegroundColor Green

Write-Host ""
Write-Host "🎉 CodeArtifact 配置完成！" -ForegroundColor Green
Write-Host "📋 配置信息：" -ForegroundColor Cyan
Write-Host "  - 仓库名称: oxsci-ca"
Write-Host "  - 仓库地址: $REPO_URL"
Write-Host "  - Profile: $PROFILE_NAME"
Write-Host "  - 令牌有效期: 12 小时"
Write-Host ""
Write-Host "现在可以安装依赖了：" -ForegroundColor Yellow
Write-Host "  poetry install"
Write-Host ""
Write-Host "💡 提示: Token 有效期为 12 小时，过期后请重新运行此脚本" -ForegroundColor Yellow
