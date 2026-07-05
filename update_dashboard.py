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


class ContactMatcher:
    """Match CRM contacts with customer sales data."""

    @staticmethod
    def match_contacts(pyun_data: Dict[str, Any], contacts_excel: Path) -> Dict[str, Any]:
        """
        Enrich PYUN customer data with CRM contact information.

        Matches Company Name (CRM) with EndUser Customer Name (Sales).
        Adds contact info to each customer record.

        Args:
            pyun_data: PYUN sales data with customers
            contacts_excel: Path to CRM Excel file

        Returns:
            Enhanced PYUN data with contact information
        """
        print(f"\n📇 Matching contacts from: {contacts_excel.name}")

        if not contacts_excel.exists():
            print(f"  ⚠ Contacts file not found: {contacts_excel}")
            return pyun_data

        try:
            df = pd.read_excel(contacts_excel, sheet_name=0)
        except Exception as e:
            print(f"  ❌ Error reading contacts: {e}")
            return pyun_data

        print(f"  Loaded {len(df)} contacts")

        # Build contact map by Company Name
        contact_map = ContactMatcher._build_contact_map(df)
        print(f"  Indexed {len(contact_map)} unique companies")

        # Enrich capital clients
        if "cap_clients" in pyun_data:
            for client in pyun_data["cap_clients"]:
                contacts = ContactMatcher._find_contacts(
                    client.get("name", ""), contact_map, df
                )
                if contacts:
                    client["contacts"] = contacts
                    print(f"  ✓ {client['name']}: {len(contacts)} contacts")

        # Enrich CDx clients
        if "cdx_clients" in pyun_data:
            for client in pyun_data["cdx_clients"]:
                contacts = ContactMatcher._find_contacts(
                    client.get("name", ""), contact_map, df
                )
                if contacts:
                    client["contacts"] = contacts
                    print(f"  ✓ {client['name']}: {len(contacts)} contacts")

        print("  ✓ Contact matching complete")
        return pyun_data

    @staticmethod
    def _build_contact_map(df: pd.DataFrame) -> Dict[str, list]:
        """Build map of company names to contact records."""
        contact_map = {}

        # Find Company Name column
        company_col = None
        for col in df.columns:
            if "company" in col.lower() or "회사" in col:
                company_col = col
                break

        if not company_col:
            return contact_map

        for _, row in df.iterrows():
            company = row.get(company_col, "")
            if pd.isna(company):
                continue

            company = str(company).strip()
            if company not in contact_map:
                contact_map[company] = []

            contact_map[company].append(row.to_dict())

        return contact_map

    @staticmethod
    def _find_contacts(
        customer_name: str, contact_map: Dict[str, list], df: pd.DataFrame
    ) -> List[Dict[str, Any]]:
        """
        Find contacts for a customer using fuzzy matching.

        Tries:
        1. Exact match
        2. Partial match (either direction)
        3. Similar names (Levenshtein distance)
        """
        if not customer_name:
            return []

        # Try exact match first
        if customer_name in contact_map:
            return ContactMatcher._format_contacts(contact_map[customer_name])

        # Try partial matches
        for company_name, contacts in contact_map.items():
            if customer_name.lower() in company_name.lower() or \
               company_name.lower() in customer_name.lower():
                return ContactMatcher._format_contacts(contacts)

        # Try fuzzy matching (simple approach: common substrings)
        for company_name, contacts in contact_map.items():
            if ContactMatcher._similarity(customer_name, company_name) > 0.7:
                return ContactMatcher._format_contacts(contacts)

        return []

    @staticmethod
    def _format_contacts(contact_rows: List[dict]) -> List[Dict[str, Any]]:
        """Format contact rows into standardized structure."""
        formatted = []

        for row in contact_rows:
            contact = {}

            # Extract standard fields
            for col in row.keys():
                col_lower = col.lower()

                if "first" in col_lower or "name" in col_lower and len(contact.get("name", "")) < 5:
                    contact["name"] = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "last" in col_lower:
                    if "name" not in contact:
                        contact["name"] = ""
                    contact["name"] = str(row[col]).strip() + " " + contact.get("name", "")
                elif "email" in col_lower or "mail" in col_lower:
                    contact["email"] = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "phone" in col_lower or "mobile" in col_lower or "연락처" in col:
                    contact["phone"] = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "department" in col_lower or "부서" in col:
                    contact["department"] = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "tip" in col_lower or "메모" in col:
                    contact["notes"] = str(row[col]).strip() if pd.notna(row[col]) else ""
                elif "owner" in col_lower or "담당자" in col:
                    contact["owner"] = str(row[col]).strip() if pd.notna(row[col]) else ""

            if contact:
                formatted.append(contact)

        return formatted

    @staticmethod
    def _similarity(s1: str, s2: str) -> float:
        """Simple string similarity metric (0-1)."""
        s1, s2 = s1.lower(), s2.lower()

        # Check common substrings
        common = 0
        for i in range(min(len(s1), len(s2))):
            if s1[i] == s2[i]:
                common += 1

        return common / max(len(s1), len(s2)) if max(len(s1), len(s2)) > 0 else 0


class ExcelDataExtractor:
    """Extract sales data from Excel files."""

    @staticmethod
    def extract_target_data(excel_path: Path, current_month: int = None) -> Dict[str, Any]:
        """
        Extract business division target data from Target Excel file.

        Reads all sheets and aggregates data by division and product category.
        Returns const D structure for HTML embedding.
        """
        print(f"\n📊 Reading Target data from: {excel_path.name}")

        try:
            xl_file = pd.ExcelFile(excel_path)
        except Exception as e:
            print(f"  ❌ Error reading file: {e}")
            return ExcelDataExtractor._create_empty_d()

        print(f"  Available sheets: {xl_file.sheet_names[:5]}..." if len(xl_file.sheet_names) > 5 else f"  Available sheets: {xl_file.sheet_names}")

        # Initialize structure
        D = {
            "div": {},
            "grand": {
                "시약": {},
                "장비": {},
                "합계": {}
            },
            "secs": [],
            "chs": []
        }

        # Map sheet names to divisions
        division_map = {
            "Capital": ["Capital", "Capital 영역"],
            "Strategic CDx": ["CDx", "Strategic CDx"],
            "Local": ["Local", "로컬"],
            "Strategic Forensic": ["Forensic", "법의학"]
        }

        # Process each sheet
        for div_name, sheet_patterns in division_map.items():
            sheet = None
            for pattern in sheet_patterns:
                if pattern in xl_file.sheet_names:
                    sheet = pattern
                    break

            if not sheet:
                print(f"  ⚠ Skipping {div_name} - sheet not found")
                continue

            try:
                df = pd.read_excel(excel_path, sheet_name=sheet, header=0)
                print(f"  ✓ {div_name}: {len(df)} rows, {len(df.columns)} cols")

                # Extract data for this division
                # This is a generic extraction - customize based on your actual Excel structure
                div_data = ExcelDataExtractor._extract_division_data(
                    df, div_name, current_month
                )
                D["div"][div_name] = div_data

            except Exception as e:
                print(f"  ❌ Error processing {div_name}: {e}")
                continue

        print("  ⚠ Note: Review extracted data structure and customize column mapping")
        return D

    @staticmethod
    def _extract_division_data(df: pd.DataFrame, division: str, current_month: int = None) -> Dict[str, Any]:
        """
        Extract data for a specific division from its sheet.

        Expects columns like:
        - Annual Target, Growth Rate
        - Monthly Target, Actual, Achievement
        - YTD metrics
        """
        # Default structure
        div_data = {
            "gr_ann": 0.0,
            "시약": {},
            "장비": {},
            "합계": {}
        }

        # Try to infer column names
        col_lower = [c.lower() for c in df.columns]

        # Find annual target column
        annual_target_col = None
        for col in df.columns:
            if "annual" in col.lower() or "연간" in col:
                annual_target_col = col
                break

        if annual_target_col and len(df) > 0:
            div_data["gr_ann"] = df[annual_target_col].iloc[0] if pd.notna(df[annual_target_col].iloc[0]) else 0

        return div_data

    @staticmethod
    def _create_empty_d() -> Dict[str, Any]:
        """Return empty D structure."""
        return {
            "div": {},
            "grand": {"시약": {}, "장비": {}, "합계": {}},
            "secs": [],
            "chs": []
        }

    @staticmethod
    def extract_pyun_data(excel_path: Path, current_month: int = None) -> Dict[str, Any]:
        """
        Extract Kyung Hyun's customer sales data from sales history Excel.

        Filters for:
        - Owner: 'Kyung-Hyun Pyun' (Capital) or 'Kyung-Hyun Pyun_CDx' (CDx)
        - Year: 'CY 2026'

        Expected columns:
        - 26_H2 ZEUC Onwer 변경 or similar: Owner/Salesperson
        - Year Name: Year identifier
        - EndUser Address 1: Customer address
        - EndUser Customer Name 2: Customer name
        - Product Number: Product identifier
        - Product Name: Product name
        - Net Sales: Sales amount
        """
        print(f"\n👤 Reading Kyung Hyun's customer data from: {excel_path.name}")

        try:
            # Try reading sheets - sales data might be in specific sheet
            xl_file = pd.ExcelFile(excel_path)
            print(f"  Available sheets: {xl_file.sheet_names[:5]}...")

            # Common sheet names for sales data
            target_sheet = None
            for sheet in xl_file.sheet_names:
                if "sales" in sheet.lower() or "매출" in sheet or "판매" in sheet:
                    target_sheet = sheet
                    break

            if not target_sheet:
                target_sheet = xl_file.sheet_names[0]

            df = pd.read_excel(excel_path, sheet_name=target_sheet, header=0)

        except Exception as e:
            print(f"  ❌ Error reading Excel: {e}")
            return ExcelDataExtractor._create_empty_pyun()

        print(f"  Sheet: {target_sheet} | Rows: {len(df)} | Cols: {len(df.columns)}")
        print(f"  Columns: {list(df.columns)[:10]}..." if len(df.columns) > 10 else f"  Columns: {list(df.columns)}")

        # Find owner column
        owner_col = None
        for col in df.columns:
            if 'owner' in col.lower() or '담당자' in col:
                owner_col = col
                break

        if not owner_col:
            print("  ⚠ Could not find owner column")
            return ExcelDataExtractor._create_empty_pyun()

        # Find year column
        year_col = None
        for col in df.columns:
            if 'year' in col.lower() or '년' in col:
                year_col = col
                break

        # Filter for Kyung Hyun (Capital & CDx)
        cap_filter = (df[owner_col].fillna('').astype(str) == 'Kyung-Hyun Pyun')
        cdx_filter = (df[owner_col].fillna('').astype(str) == 'Kyung-Hyun Pyun_CDx')

        if year_col:
            cap_filter = cap_filter & (df[year_col].fillna('').astype(str) == 'CY 2026')
            cdx_filter = cdx_filter & (df[year_col].fillna('').astype(str) == 'CY 2026')

        cap_df = df[cap_filter]
        cdx_df = df[cdx_filter]

        print(f"  Capital records: {len(cap_df)} | CDx records: {len(cdx_df)}")

        # Aggregate by customer and product
        cap_clients = ExcelDataExtractor._aggregate_customers(
            cap_df, "Capital"
        )
        cdx_clients = ExcelDataExtractor._aggregate_customers(
            cdx_df, "CDx"
        )

        # Calculate totals
        cap_total = sum(c.get("total_sales", 0) for c in cap_clients)
        cdx_total = sum(c.get("total_sales", 0) for c in cdx_clients)

        PYUN = {
            "cap_clients": sorted(cap_clients, key=lambda x: x.get("total_sales", 0), reverse=True),
            "cdx_clients": sorted(cdx_clients, key=lambda x: x.get("total_sales", 0), reverse=True),
            "cap_total": int(cap_total),
            "cdx_total": int(cdx_total),
            "grand_total": int(cap_total + cdx_total),
            "cap_count": len(set(cap_df.get("EndUser Customer Name 2", cap_df.get("Customer", [])).dropna())),
            "cdx_count": len(set(cdx_df.get("EndUser Customer Name 2", cdx_df.get("Customer", [])).dropna()))
        }

        print(f"  ✓ Aggregated: {PYUN['cap_count']} Capital, {PYUN['cdx_count']} CDx customers")
        return PYUN

    @staticmethod
    def _aggregate_customers(df: pd.DataFrame, category: str) -> List[Dict[str, Any]]:
        """
        Aggregate sales data by customer.

        Groups by customer name and sums by product.
        """
        # Find relevant columns
        customer_col = None
        product_col = None
        product_name_col = None
        sales_col = None

        for col in df.columns:
            if 'customer' in col.lower() or '고객' in col or 'enduser' in col.lower():
                customer_col = col
            elif 'product' in col.lower() and 'number' in col.lower():
                product_col = col
            elif 'product' in col.lower() and 'name' in col.lower():
                product_name_col = col
            elif 'sales' in col.lower() or 'amount' in col.lower():
                sales_col = col

        if not customer_col or not sales_col:
            return []

        # Group by customer
        customers = {}
        for _, row in df.iterrows():
            customer = row.get(customer_col, "Unknown")
            if pd.isna(customer):
                continue

            customer = str(customer).strip()
            if customer not in customers:
                customers[customer] = {
                    "addr": customer,
                    "name": customer,
                    "category": category,
                    "total_sales": 0,
                    "products": {}
                }

            sales = row.get(sales_col, 0)
            if pd.notna(sales):
                try:
                    sales = float(sales)
                    customers[customer]["total_sales"] += sales

                    # Group by product
                    if product_col and product_name_col:
                        pn = str(row.get(product_col, "Unknown")).strip()
                        pname = str(row.get(product_name_col, "Unknown")).strip()
                        if pn not in customers[customer]["products"]:
                            customers[customer]["products"][pn] = {
                                "pn": pn,
                                "pname": pname,
                                "sales": 0
                            }
                        customers[customer]["products"][pn]["sales"] += sales
                except (ValueError, TypeError):
                    pass

        # Convert to list format with top 10 products
        result = []
        for customer_name, data in customers.items():
            products = sorted(
                data["products"].values(),
                key=lambda x: x.get("sales", 0),
                reverse=True
            )[:10]

            result.append({
                "addr": data["addr"],
                "name": data["name"],
                "category": data["category"],
                "total_sales": int(data["total_sales"]),
                "product_count": len(data["products"]),
                "products": products
            })

        return result

    @staticmethod
    def _create_empty_pyun() -> Dict[str, Any]:
        """Return empty PYUN structure."""
        return {
            "cap_clients": [],
            "cdx_clients": [],
            "cap_total": 0,
            "cdx_total": 0,
            "grand_total": 0,
            "cap_count": 0,
            "cdx_count": 0
        }


def main():
    parser = argparse.ArgumentParser(description='Update PK Sales Dashboard with monthly data')
    parser.add_argument('--target', type=Path, help='Path to Target Excel file')
    parser.add_argument('--sales', type=Path, help='Path to Sales history Excel file')
    parser.add_argument('--contacts', type=Path, help='Path to CRM Contacts Excel file (optional)')
    parser.add_argument('--output', type=Path, help='Output HTML file path')
    parser.add_argument('--month', type=int, default=datetime.now().month, help='Report month (default: current)')
    parser.add_argument('--year', type=int, default=2026, help='Report year (default: 2026)')

    args = parser.parse_args()

    # Determine paths
    script_dir = Path(__file__).parent

    target_path = args.target or (script_dir / "Target.xlsx")
    sales_path = args.sales or (script_dir / "Sales.xlsx")
    contacts_path = args.contacts or (script_dir / "Contacts.xlsx")
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

    # Extract business division data (const D)
    if target_path.exists():
        try:
            target_data = ExcelDataExtractor.extract_target_data(target_path)
            updater.update_const_d(target_data)
        except Exception as e:
            print(f"Error extracting target data: {e}")
    else:
        print(f"⚠ Target file not found: {target_path}")

    # Extract customer sales data (const PYUN)
    pyun_data = None
    if sales_path.exists():
        try:
            pyun_data = ExcelDataExtractor.extract_pyun_data(sales_path)

            # Enrich with CRM contacts if available
            if contacts_path.exists():
                pyun_data = ContactMatcher.match_contacts(pyun_data, contacts_path)
            else:
                print(f"ℹ Contacts file not found (optional): {contacts_path}")

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
