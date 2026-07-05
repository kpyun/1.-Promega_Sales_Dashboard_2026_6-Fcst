#!/usr/bin/env python3
"""
Update dashboard HTML with monthly sales data from Excel files.

This script reads sales data from Excel files and updates the embedded JS objects
in the HTML file (const D and const PYUN).

Usage:
    python3 update_dashboard.py [--target TARGET_XLSX] [--sales SALES_XLSX] [--output OUTPUT_HTML]
"""

import json
import re
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

try:
    import pandas as pd
except ImportError:
    print("Error: pandas is required. Install with: pip install pandas openpyxl")
    exit(1)


class DashboardUpdater:
    """Update Promega PK Sales Dashboard with monthly data."""

    def __init__(self, html_path: Path):
        self.html_path = Path(html_path)
        self.html_content = self.html_path.read_text(encoding='utf-8')

    def update_const_d(self, target_data: Dict[str, Any]) -> None:
        """Update const D (business division sales data) in HTML."""
        json_str = json.dumps(target_data, ensure_ascii=False, separators=(',', ':'))

        # Find and replace const D = {...}
        pattern = r'const D = \{[^}]*(?:\{[^}]*\}[^}]*)*\};'
        replacement = f'const D = {json_str};'

        # More robust approach: find the start and end markers
        match = re.search(r'const D = \{', self.html_content)
        if not match:
            print("Warning: Could not find 'const D' in HTML")
            return

        start_pos = match.start()
        # Find the matching closing brace (accounting for nested braces)
        brace_count = 0
        end_pos = start_pos
        in_string = False
        escape = False

        for i, char in enumerate(self.html_content[match.end()-1:], start=match.end()-1):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"' and not in_string:
                in_string = True
            elif char == '"' and in_string:
                in_string = False
            elif char == '{' and not in_string:
                brace_count += 1
            elif char == '}' and not in_string:
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break

        self.html_content = (
            self.html_content[:start_pos] +
            f'const D = {json_str};' +
            self.html_content[end_pos:]
        )
        print("✓ Updated const D (business division sales)")

    def update_const_pyun(self, pyun_data: Dict[str, Any]) -> None:
        """Update const PYUN (Kyung Hyun's customer data) in HTML."""
        json_str = json.dumps(pyun_data, ensure_ascii=False, separators=(',', ':'))

        match = re.search(r'const PYUN = \{', self.html_content)
        if not match:
            print("Warning: Could not find 'const PYUN' in HTML")
            return

        start_pos = match.start()
        brace_count = 0
        end_pos = start_pos
        in_string = False
        escape = False

        for i, char in enumerate(self.html_content[match.end()-1:], start=match.end()-1):
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"' and not in_string:
                in_string = True
            elif char == '"' and in_string:
                in_string = False
            elif char == '{' and not in_string:
                brace_count += 1
            elif char == '}' and not in_string:
                brace_count -= 1
                if brace_count == 0:
                    end_pos = i + 1
                    break

        self.html_content = (
            self.html_content[:start_pos] +
            f'const PYUN = {json_str};' +
            self.html_content[end_pos:]
        )
        print("✓ Updated const PYUN (customer sales)")

    def update_report_month(self, month: int, year: int = 2026) -> None:
        """Update report month in header."""
        month_str = f"{month}월 확정"

        # Update header span
        self.html_content = re.sub(
            r'<span id="updated">기준일: [\d\-]+</span>',
            f'<span id="updated">기준일: {year:04d}-{month:02d}-{datetime.now().day:02d}</span>',
            self.html_content
        )
        print(f"✓ Updated report month to {month_str}")

    def save(self, output_path: Path) -> None:
        """Save updated HTML to file."""
        output_path = Path(output_path)
        output_path.write_text(self.html_content, encoding='utf-8')
        print(f"✓ Saved to {output_path}")


class ExcelDataExtractor:
    """Extract sales data from Excel files."""

    @staticmethod
    def extract_target_data(excel_path: Path) -> Dict[str, Any]:
        """
        Extract business division target data from Target Excel file.

        Expected sheet: "2026' Target(CUSD 1,300원)_v6"
        """
        print(f"\n📊 Reading Target data from: {excel_path.name}")

        # Try to find the correct sheet
        xl_file = pd.ExcelFile(excel_path)
        target_sheet = None

        for sheet in xl_file.sheet_names:
            if "Target" in sheet and "2026" in sheet:
                target_sheet = sheet
                break

        if not target_sheet:
            print(f"Available sheets: {xl_file.sheet_names}")
            raise ValueError("Could not find Target sheet in Excel file")

        print(f"  Using sheet: {target_sheet}")

        # Read the sheet
        df = pd.read_excel(excel_path, sheet_name=target_sheet)

        # For now, return a placeholder structure
        # You would need to customize this based on your actual Excel structure
        print(f"  Columns: {list(df.columns)}")
        print(f"  Rows: {len(df)}")

        # Placeholder - needs to be customized based on actual Excel layout
        D = {
            "div": {},
            "grand": {},
            "secs": [],
            "chs": []
        }

        print("  ⚠ Note: Extract logic needs customization for your Excel layout")
        return D

    @staticmethod
    def extract_pyun_data(excel_path: Path) -> Dict[str, Any]:
        """
        Extract Kyung Hyun's customer sales data from sales history Excel.

        Filters for:
        - Owner: 'Kyung-Hyun Pyun' (Capital) or 'Kyung-Hyun Pyun_CDx' (CDx)
        - Year: 'CY 2026'
        """
        print(f"\n👤 Reading Pyun customer data from: {excel_path.name}")

        try:
            # Try reading the main sheet
            df = pd.read_excel(excel_path, sheet_name=0)
        except Exception as e:
            print(f"Error reading Excel: {e}")
            return {"cap_clients": [], "cdx_clients": [], "cap_total": 0, "cdx_total": 0, "cap_count": 0, "cdx_count": 0, "grand_total": 0}

        print(f"  Columns: {list(df.columns)}")
        print(f"  Total rows: {len(df)}")

        # Filter for Kyung Hyun (Capital)
        cap_filter = (df.get('26_H2 ZEUC Onwer 변경', df.get('Owner', pd.Series())).fillna('') == 'Kyung-Hyun Pyun') & \
                     (df.get('Year Name', pd.Series()).fillna('') == 'CY 2026')

        # Filter for Kyung Hyun (CDx)
        cdx_filter = (df.get('26_H2 ZEUC Onwer 변경', df.get('Owner', pd.Series())).fillna('') == 'Kyung-Hyun Pyun_CDx') & \
                     (df.get('Year Name', pd.Series()).fillna('') == 'CY 2026')

        cap_df = df[cap_filter]
        cdx_df = df[cdx_filter]

        print(f"  Capital customers: {len(cap_df)}")
        print(f"  CDx customers: {len(cdx_df)}")

        # Aggregate by customer
        cap_clients = []
        cdx_clients = []

        # Placeholder structure - customize based on your actual column names
        PYUN = {
            "cap_total": 0,
            "cdx_total": 0,
            "grand_total": 0,
            "cap_count": 0,
            "cdx_count": 0,
            "cap_clients": cap_clients,
            "cdx_clients": cdx_clients
        }

        print("  ⚠ Note: Extract logic needs customization for your Excel layout")
        return PYUN


def main():
    parser = argparse.ArgumentParser(description='Update PK Sales Dashboard with monthly data')
    parser.add_argument('--target', type=Path, help='Path to Target Excel file')
    parser.add_argument('--sales', type=Path, help='Path to Sales history Excel file')
    parser.add_argument('--output', type=Path, help='Output HTML file path')
    parser.add_argument('--month', type=int, default=datetime.now().month, help='Report month (default: current)')
    parser.add_argument('--year', type=int, default=2026, help='Report year (default: 2026)')

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent

    target_path = args.target or (script_dir / "Target.xlsx")
    sales_path = args.sales or (script_dir / "Sales.xlsx")
    output_path = args.output or (script_dir / "index.html")

    html_path = script_dir / "dashboard-original.html"

    print("=" * 60)
    print("PK Sales Dashboard Auto-Updater")
    print("=" * 60)

    # Load HTML
    if not html_path.exists():
        print(f"Error: HTML file not found: {html_path}")
        return 1

    updater = DashboardUpdater(html_path)

    # Extract data
    if target_path.exists():
        try:
            target_data = ExcelDataExtractor.extract_target_data(target_path)
            updater.update_const_d(target_data)
        except Exception as e:
            print(f"Error extracting target data: {e}")
    else:
        print(f"⚠ Target file not found: {target_path}")

    if sales_path.exists():
        try:
            pyun_data = ExcelDataExtractor.extract_pyun_data(sales_path)
            updater.update_const_pyun(pyun_data)
        except Exception as e:
            print(f"Error extracting Pyun data: {e}")
    else:
        print(f"⚠ Sales file not found: {sales_path}")

    # Update report month
    updater.update_report_month(args.month, args.year)

    # Save
    updater.save(output_path)

    print("\n" + "=" * 60)
    print("✅ Dashboard update complete!")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    exit(main())
