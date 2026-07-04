#!/usr/bin/env python3
"""
YouTube 自動發布技能 — 環境檢查工具

檢查所有先決條件是否就緒：
- pip 套件：google-api-python-client, google-auth-oauthlib
- 憑證檔案：client_secrets.json, token.json
- Python 版本

用法：
    python env_check.py
    python env_check.py --json

作者：阿亮老師・3A科技研究社
"""

import argparse
import json
import sys
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_DIR = SKILL_DIR / "credentials"
CLIENT_SECRETS_FILE = CREDENTIALS_DIR / "client_secrets.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.json"


def check_pip_package(package_name: str, import_name: str = "") -> dict:
    """檢查 pip 套件是否安裝。"""
    try:
        import importlib.metadata
        version = importlib.metadata.version(package_name)
        return {
            "name": f"pip: {package_name}",
            "required": "已安裝",
            "found": version,
            "passed": True,
        }
    except Exception:
        return {
            "name": f"pip: {package_name}",
            "required": "已安裝",
            "found": "未安裝",
            "passed": False,
        }


def check_file(filepath: Path, label: str) -> dict:
    """檢查檔案是否存在。"""
    if filepath.exists():
        size = filepath.stat().st_size
        size_str = f"{size} bytes"
        return {
            "name": label,
            "required": "已存在",
            "found": f"存在 ({size_str})",
            "passed": True,
        }
    return {
        "name": label,
        "required": "已存在",
        "found": "不存在",
        "passed": False,
    }


def check_python() -> dict:
    """檢查 Python 版本。"""
    version = sys.version.split()[0]
    return {
        "name": "Python",
        "required": "≥ 3.8",
        "found": version,
        "passed": True,
    }


def check_token_valid() -> dict:
    """檢查 token.json 是否有效。"""
    if not TOKEN_FILE.exists():
        return {
            "name": "OAuth2 權杖狀態",
            "required": "有效",
            "found": "尚未授權",
            "passed": False,
        }
    try:
        from google.oauth2.credentials import Credentials
        SCOPES = [
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/youtube",
        ]
        creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)
        if creds.valid:
            return {
                "name": "OAuth2 權杖狀態",
                "required": "有效",
                "found": "有效",
                "passed": True,
            }
        elif creds.expired and creds.refresh_token:
            return {
                "name": "OAuth2 權杖狀態",
                "required": "有效",
                "found": "已過期（可自動重新整理）",
                "passed": True,
            }
        else:
            return {
                "name": "OAuth2 權杖狀態",
                "required": "有效",
                "found": "無效，需重新授權",
                "passed": False,
            }
    except Exception as e:
        return {
            "name": "OAuth2 權杖狀態",
            "required": "有效",
            "found": f"無法驗證：{e}",
            "passed": False,
        }


def run_all_checks() -> list[dict]:
    """執行所有檢查。"""
    checks = [
        check_python(),
        check_pip_package("google-api-python-client"),
        check_pip_package("google-auth-oauthlib"),
        check_file(CLIENT_SECRETS_FILE, "client_secrets.json"),
        check_file(TOKEN_FILE, "token.json"),
    ]
    # 僅在 token.json 存在時檢查有效性
    if TOKEN_FILE.exists():
        checks.append(check_token_valid())
    return checks


def print_table(checks: list[dict]) -> None:
    """以表格格式印出檢查結果。"""
    print()
    print("=" * 68)
    print("  YouTube 自動發布技能 — 環境檢查")
    print("  阿亮老師・3A科技研究社")
    print("=" * 68)
    print()

    print(f"  {'檢查項目':<30} {'需求':<10} {'結果':<22} {'狀態'}")
    print("  " + "-" * 64)

    pass_count = 0
    fail_count = 0
    for c in checks:
        status = "PASS" if c["passed"] else "FAIL"
        marker = "[v]" if c["passed"] else "[X]"
        print(f"  {c['name']:<30} {c['required']:<10} {c['found']:<22} {marker} {status}")
        if c["passed"]:
            pass_count += 1
        else:
            fail_count += 1

    print()
    print("  " + "-" * 64)
    total = pass_count + fail_count
    print(f"  總計：{pass_count}/{total} 通過，{fail_count}/{total} 未通過")

    if fail_count == 0:
        print("\n  所有檢查皆通過！可以開始上傳影片。")
    else:
        print(f"\n  有 {fail_count} 個項目未通過：")
        for c in checks:
            if not c["passed"]:
                name = c["name"]
                if "google-api-python-client" in name:
                    print(f"    - {name}：pip install google-api-python-client")
                elif "google-auth-oauthlib" in name:
                    print(f"    - {name}：pip install google-auth-oauthlib google-auth-httplib2")
                elif "client_secrets" in name:
                    print(f"    - {name}：請先執行 python setup_credentials.py 完成設定")
                elif "token" in name:
                    print(f"    - {name}：請執行 python setup_credentials.py --auth 進行授權")

    print(f"\n  憑證目錄：{CREDENTIALS_DIR}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="YouTube 自動發布技能 — 環境檢查工具"
    )
    parser.add_argument(
        "--json", action="store_true",
        help="以 JSON 格式輸出結果",
    )
    args = parser.parse_args()

    checks = run_all_checks()

    if args.json:
        output = {
            "checks": checks,
            "passed": sum(1 for c in checks if c["passed"]),
            "failed": sum(1 for c in checks if not c["passed"]),
            "total": len(checks),
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        print_table(checks)

    if any(not c["passed"] for c in checks):
        sys.exit(1)


if __name__ == "__main__":
    main()
