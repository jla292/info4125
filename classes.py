import requests
from bs4 import BeautifulSoup
import json
import re
from urllib.parse import urljoin
from typing import List, Dict, Optional

#Configuration
# Setting the semester, subject, and label for scraping Cornell class data
ROSTER = "FA25"
SUBJECT = "INFO"
BASE = "https://classes.cornell.edu"
SUBJECT_URL = f"{BASE}/browse/roster/{ROSTER}/subject/{SUBJECT}"
ACADEMIC_YEAR_TEXT = "Fall 2025"
LABEL = "1"

# Helpers
def fetch_html(url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
# sends get request and parses HTML into BeautifulSoup
    """Fetch and return a BeautifulSoup object for the given URL."""
    r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=timeout)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")


def select_text(soup: BeautifulSoup, selectors: List[str], min_len: int = 0) -> str:
# loops through selectors until finding non-empty text of minimum length
    """Try multiple CSS selectors to find meaningful text."""
    for sel in selectors:
        el = soup.select_one(sel)
        if not el:
            continue
        txt = el.get_text(" ", strip=True)
        if len(txt) >= min_len:
            return txt
    return ""


def parse_labeled_fields(soup: BeautifulSoup) -> Dict[str, str]:
# scans all text elements for key words, like "credit", "grading", and "prerequisites"
    """Extract credits, grading, and prerequisites heuristically."""
    fields = {"credits": "", "grading": "", "prereq": ""}
    for el in soup.find_all(["div", "li", "p", "tr"]):
        text = el.get_text(" ", strip=True)
        lower = text.lower()
        if not fields["credits"] and "credit" in lower:
            m = re.search(r"(\d+(?:\.\d+)?)\s*credit", lower)
            if m:
                fields["credits"] = m.group(1)
        if not fields["grading"] and ("grading" in lower or "grade option" in lower):
            mg = re.search(r"grading[:\s]+(.+)$", text, flags=re.I)
            if mg:
                fields["grading"] = mg.group(1).strip()
        if not fields["prereq"] and ("prereq" in lower or "prerequisite" in lower):
            mp = re.search(r"(?:Prereq(?:uisite)?s?:?\s*)(.+)$", text, flags=re.I)
            if mp:
                fields["prereq"] = mp.group(1).strip()
    return fields


def extract_classes(soup: BeautifulSoup) -> List[Dict[str, str]]:
# finds all <a> tags linking to individual course pages and extracts course code/title
# removes any duplicate results to avoid repeats from multiple listings
    """Get all course links from the subject page."""
    results = []
    for a in soup.select('a[href^="/browse/roster/"]'):
        href = a.get("href", "")
        if f"/browse/roster/{ROSTER}/class/{SUBJECT}/" in href:
            code_text = a.get_text(" ", strip=True)
            code, title = "", ""
            m = re.match(r"^([A-Z]{2,4}\s*\d{3,4})\s*[-–:]\s*(.+)$", code_text)
            if m:
                code, title = m.group(1).strip(), m.group(2).strip()
            else:
                cm = re.search(r"([A-Z]{2,4}\s*\d{3,4})", code_text)
                if cm:
                    code = cm.group(1).strip()
            detail_url = urljoin(BASE, href)
            if code:
                results.append({"code": code, "title": title, "url": detail_url})
    # Deduplicate
    seen, uniq = set(), []
    for r in results:
        if r["url"] not in seen:
            seen.add(r["url"])
            uniq.append(r)
    return uniq


def build_course_facts(course: Dict[str, str], label: str) -> List[Dict[str, str]]:
#scrapes course detail page for title, description, credits, grading, and prereqs
# returns a list of structured facts for later JSON export
    """Create all fact entries for a single course."""
    facts = []
    code = course["code"]
    url = course["url"]
    detail = fetch_html(url)
    if not detail:
        return facts

    title = course["title"] or select_text(detail, ["h1", ".title", ".class-title", ".course-title"], min_len=3)
    if title:
        facts.append({
            "text": f"{code} — {title}.",
            "label": label,
            "source": url,
            "date": ACADEMIC_YEAR_TEXT,
            "topic": f"{code} Title"
        })

    # Description
    description = select_text(detail, [
        ".catalog-descr", ".description", ".class-description", ".course-description",
        ".descr", "section.description p", ".content p"
    ], min_len=20)
    if description:
        facts.append({
            "text": f"{code} covers: {description}",
            "label": label,
            "source": url,
            "date": ACADEMIC_YEAR_TEXT,
            "topic": f"{code} Description"
        })

    # Getting details on classes, like credits, grading, prerequisites
    fields = parse_labeled_fields(detail)
    if fields["credits"]:
        facts.append({
            "text": f"{code} is {fields['credits']} credits.",
            "label": label,
            "source": url,
            "date": ACADEMIC_YEAR_TEXT,
            "topic": f"{code} Credits"
        })
    if fields["grading"]:
        facts.append({
            "text": f"{code} grading: {fields['grading']}.",
            "label": label,
            "source": url,
            "date": ACADEMIC_YEAR_TEXT,
            "topic": f"{code} Grading"
        })
    if fields["prereq"]:
        facts.append({
            "text": f"{code} prerequisites: {fields['prereq']}.",
            "label": label,
            "source": url,
            "date": ACADEMIC_YEAR_TEXT,
            "topic": f"{code} Prerequisites"
        })

    return facts


def main():
#fetches subject page, extracts list of courses, gathers structured info from each course, saves all extracted facts as JSON
    print(f"🔎 Fetching {SUBJECT} classes for {ROSTER}: {SUBJECT_URL}")
    subject_soup = fetch_html(SUBJECT_URL)
    if not subject_soup:
        print("❌ Could not load subject page.")
        return

    classes = extract_classes(subject_soup)
    if not classes:
        print("❌ No classes found — page structure may have changed.")
        return

    all_facts = []
    for c in classes:
        course_facts = build_course_facts(c, LABEL)
        all_facts.extend(course_facts)

    # ✅ Save results to JSON
    output_file = "cornell_classes_2025.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_facts, f, indent=4, ensure_ascii=False)

    print(f"✅ Saved {len(all_facts)} facts for {len(classes)} INFO classes to {output_file}")


if __name__ == "__main__":
    main()

