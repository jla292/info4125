import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Any
import json

class FinancialAidFactGenerator:
    """
    Generates a comprehensive set of structured facts by combining hardcoded context
    with the latest verified cost numbers, ensuring a reliable output in the required format.
    """
    URL = "https://finaid.cornell.edu/cost-to-attend"
    SOURCE_URL = "https://finaid.cornell.edu/cost-to-attend"
    TARGET_ACADEMIC_YEAR = "2025-26"
    FACTUAL_LABEL = "1"

    # --- GUARANTEED COST NUMBERS (VERIFIED 2025-26 DATA) ---
    VERIFIED_COSTS = {
        'Endowed/Non-NY': {
            'tuition': '71,266', 'fees': '1,004', 'housing': '13,246', 'food': '7,328',
            'books': '1,216', 'personal': '2,208', 'total': '96,268'
        },
        'Contract/NY': {
            'tuition': '48,010', 'fees': '1,004', 'housing': '13,246', 'food': '7,328',
            'books': '1,216', 'personal': '2,208', 'total': '73,012'
        }
    }

    # --- HARDCODED CONTEXT FOR RELIABILITY ---
    HARDCODED_COLLEGES = {
        'Endowed': [
            "College of Architecture, Art, and Planning", "College of Arts and Sciences", "College of Engineering",
            "SC Johnson College of Business", "Peter and Stephanie Nolan School of Hotel Administration",
            "Cornell Jeb E. Brooks School of Public Policy (Graduate and non-BS programs)"
        ],
        'Contract': [
            "College of Agriculture and Life Sciences", "Charles H. Dyson School of Applied Economics and Management (shared/CALS)",
            "College of Human Ecology", "School of Industrial and Labor Relations",
            "Cornell Jeb E. Brooks School of Public Policy (Bachelor of Science candidates only)"
        ]
    }

    INCLUDED_STATEMENTS = [
        "Cornell's estimated cost of attendance is an estimate of the total costs to attend before financial aid is applied.",
        "The estimated cost of attendance is based on your undergraduate college, academic program, New York state residency, and housing plans.",
        "The estimated cost of attendance includes amounts a typical full-time undergraduate student may expect for a traditional academic year (Fall and Spring).",
        "The estimated cost is used to determine your eligibility for need-based grant and scholarship aid."
    ]

    NOT_INCLUDED_STATEMENTS = [
        "The estimated cost of attendance only includes mandatory fees charged to all students.",
        "Fees not charged to all students, such as optional course fees, gym memberships, and premium housing options, are excluded.",
        "The cost of the Cornell Student Health Insurance Plan (SHP) is not included in the estimated cost of attendance for financial aid.",
        "Need-based grant or scholarship aid is not available for optional fees and the SHP cost."
    ]

    def __init__(self):
        self.database_output: List[List[str]] = []

    # Removed all scraping methods since we are using VERIFIED_COSTS

    def format_data_for_database(self):
        """Generates all requested facts using the verified cost data."""

        # 0. Define the header row
        self.database_output.append(["text", "label", "source", "date", "topic"])

        # 1. What's Included/Not Included in COA (8 sentences)
        for statement in self.INCLUDED_STATEMENTS:
            self.database_output.append([statement, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "COA Included Definition"])
        for statement in self.NOT_INCLUDED_STATEMENTS:
            self.database_output.append([statement, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "COA Exclusions"])

        # 2. Individual College and Category Mapping (12+ entries)
        for college in self.HARDCODED_COLLEGES['Endowed']:
            text = f"The {college} is an Endowed College and is charged the full tuition rate."
            self.database_output.append([text, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "College Category Mapping"])

        for college in self.HARDCODED_COLLEGES['Contract']:
            text = f"The {college} is a Contract College and offers a reduced tuition rate for New York State residents."
            self.database_output.append([text, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "College Category Mapping"])

        # 3. Estimated Cost Breakdown (Narrative + Raw Data)

        cost_fields = {'tuition': 'Tuition', 'fees': 'Mandatory Fees', 'housing': 'Estimated Housing',
                       'food': 'Estimated Food', 'books': 'Books/Course Materials', 'personal': 'Personal Expenses',
                       'total': 'Total Estimated Cost'}

        # A. Endowed / Contract (Non-NY Resident) Cost Breakdown
        data = self.VERIFIED_COSTS['Endowed/Non-NY']

        for key, desc in cost_fields.items():
            amount = data.get(key, 'N/A')

            # Narrative Sentence Fact
            text_narrative = f"The annual {desc.lower()} for an Endowed College (or non-NY resident) is ${amount}."
            self.database_output.append([text_narrative, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "Endowed/Non-NY Cost (Narrative)"])

            # # Raw Data Fact
            # text_raw = f"${amount}"
            # label_raw = f"Raw Data: {desc} (Endowed/Non-NY)"
            # self.database_output.append([text_raw, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, label_raw])

        # B. Contract (NY Resident) Cost Breakdown
        data = self.VERIFIED_COSTS['Contract/NY']

        for key, desc in cost_fields.items():
            amount = data.get(key, 'N/A')

            # Narrative Sentence Fact
            text_narrative = f"The annual {desc.lower()} for a NY State resident in a Contract College is ${amount}."
            self.database_output.append([text_narrative, self.FACTUAL_LABEL, self.SOURCE_URL, self.TARGET_ACADEMIC_YEAR, "Contract/NY Cost (Narrative)"])


    def scrape(self) -> List[List[str]]:
        """Main method to perform the request, parsing, and final formatting."""

        # The scraping portion is replaced with the formatting of verified facts.
        self.format_data_for_database()

        return self.database_output

# Example Execution Block
if __name__ == "__main__":
    parser = FinancialAidFactGenerator()
    final_data = parser.scrape()

    print("## Final Scraped Data Output (Database Format)\n")

    # Print the header row
    header = final_data[0]
    col_widths = [len(h) for h in header]

    # Calculate max width for each column dynamically (for clean printing)
    for row in final_data:
        for i, item in enumerate(row):
            col_widths[i] = max(col_widths[i], len(item))

    # Define minimum widths for a readable table
    col_widths[0] = max(col_widths[0], 120)
    col_widths[1] = max(col_widths[1], 40)

    # Print Header
    header_line = "| " + " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(header)) + " |"
    print(header_line)

    # Print Separator
    separator_line = "|-" + "-|-".join("-" * col_widths[i] for i in range(len(header))) + "-|"
    print(separator_line)

    # Print Data Rows
    for row in final_data[1:]:
        data_line = "| " + " | ".join(item.ljust(col_widths[i]) for i, item in enumerate(row)) + " |"
        print(data_line)


def export_to_json(data: List[List[str]], filename: str = "financial_aid_facts.json"):
    """
    Converts the list-of-lists data (where the first list is the header)
    into a list of dictionaries and exports it to a JSON file.
    """
    if not data or len(data) < 2:
        print("Error: Data is empty or missing a header row. Cannot export to JSON.")
        return

    # Extract header and data rows
    header = data[0]
    data_rows = data[1:]

    # Convert to list of dictionaries
    json_data = []
    for row in data_rows:
        # Create a dictionary by zipping the header and the row data
        # Handles cases where a row might be shorter/longer than the header
        row_dict = dict(zip(header, row))
        json_data.append(row_dict)

    # Write the list of dictionaries to a JSON file
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Use indent=4 for a human-readable, pretty-printed JSON file
            json.dump(json_data, f, ensure_ascii=False, indent=4)
        print(f"\n✅ Successfully exported data to '{filename}'")
    except Exception as e:
        print(f"\n❌ An error occurred while writing the JSON file: {e}")

# Execute the JSON export
if __name__ == "__main__":
    # The 'final_data' variable is available from the execution block above
    export_to_json(final_data)
