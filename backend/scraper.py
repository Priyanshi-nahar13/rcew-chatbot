import requests
from bs4 import BeautifulSoup
import json
import time
import os

BASE_URL = "https://www.rcew.ac.in"

URLS = [
    # ── Main pages ──
    "/college-information.php",
    "/admission.php",
    "/placement.php",
    "/contact-us.php",
    "/hostel.php",
    "/laboratories.php",
    "/campus.php",
    "/conveyance.php",
    "/notifications.php",
    "/events.php",
    "/career.php",
    "/message.php",
    "/it-infrastructure.php",
    "/association.php",
    "/committee-new.php",
    # ── Department home pages ──
    "/dept/cse",
    "/dept/ece",
    "/dept/ee",
    "/dept/civil",
    "/dept/cseai",
    "/dept/aids",
    "/dept/mca",
    "/dept/mba",
    "/dept/applied",
    "/dept/m-tech",
    # ── Department sub-pages ──
    "/dept/cse/about",
    "/dept/cse/faculty",
    "/dept/cse/syllabus",
    "/dept/cse/labs",
    "/dept/ece/about",
    "/dept/ece/faculty",
    "/dept/ece/syllabus",
    "/dept/ece/labs",
    "/dept/ee/about",
    "/dept/ee/faculty",
    "/dept/ee/syllabus",
    "/dept/civil/about",
    "/dept/civil/faculty",
    "/dept/civil/syllabus",
    "/dept/cseai/about",
    "/dept/cseai/faculty",
    "/dept/aids/about",
    "/dept/aids/faculty",
    "/dept/mca/about",
    "/dept/mca/faculty",
    "/dept/mba/about",
    "/dept/mba/faculty",
]


def scrape_page(path):
    url = BASE_URL + path
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
        }
        resp = requests.get(url, headers=headers, timeout=15)

        if resp.status_code == 404:
            print(f"  ✗ 404: {path}")
            return None

        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove only noise — keep body content intact
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()

        # Get ALL text from body (same as original working scraper)
        text = soup.get_text(separator="\n")

        # Clean blank lines
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines)

        char_count = len(clean_text)

        if char_count < 100:
            print(f"  ⚠  Only {char_count} chars (JS page?): {path}")
            return None

        print(f"  ✓  {char_count:,} chars  ←  {path}")
        return {
            "url": url,
            "page": path,
            "text": clean_text,
            "char_count": char_count
        }

    except requests.exceptions.ConnectionError:
        print(f"  ✗ Cannot connect: {path}")
        return None
    except Exception as e:
        print(f"  ✗ Error {path}: {e}")
        return None


def main():
    os.makedirs("data/raw", exist_ok=True)
    all_data = []
    skipped = 0

    print(f"Scraping {len(URLS)} URLs...\n")

    for path in URLS:
        result = scrape_page(path)
        if result:
            all_data.append(result)
        else:
            skipped += 1
        time.sleep(1)

    out_path = "data/raw/rcew_raw.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    total_chars = sum(d["char_count"] for d in all_data)

    print(f"\n{'─'*45}")
    print(f"  Pages scraped : {len(all_data)}")
    print(f"  Pages skipped : {skipped}")
    print(f"  Total text    : {total_chars:,} characters")
    print(f"  Saved to      : {out_path}")
    print(f"{'─'*45}")


if __name__ == "__main__":
    main()