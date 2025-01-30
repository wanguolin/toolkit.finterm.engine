import os
import json
import re
from pathlib import Path
from typing import Optional, Tuple
import threading
from queue import Queue
import time
import argparse
from collections import defaultdict
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables and initialize client
load_dotenv()
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), base_url=os.getenv("DEEPSEEK_BASE_URL")
)

# Constants
NUM_THREADS = 2
TARGET_FILES = ["#"] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]
TEMPLATE = """You are a professional financial dictionary editor. Please explain the following financial term in both English and Chinese, following this format:

# <<<term>>>

## 中文解释 / English Explanation

* **定义 / Definition**  
  [Provide Chinese definition with originator and core concepts]  
  [Provide English definition strictly corresponding to Chinese]

* **应用 / Application**  
  [Describe Chinese application scenarios and risk notes]  
  [Describe English application scenarios matching Chinese content]

* **重要性 / Significance**  
  [Explain Chinese significance from regulatory/investment/industry perspectives]  
  [Explain English significance mirroring Chinese expression]

## 历史典故 / Historical Context

* **起源 / Origin**  
  [Detail Chinese historical background with timeline, figures, and discovery process]  
  [Detail English historical background with key timestamps]

* **影响 / Impact**  
  [Describe Chinese industry impact and current status]  
  [Describe English impact description with global applications]

## 要点总结 / Takeaway

* **中文**  
  - [Core value]
  - [Usage scenarios]
  - [Extended meaning]

* **English**  
  - [Key Point 1]
  - [Key Point 2]
  - [Key Point 3]

Please provide a comprehensive explanation for the term: <<<term>>>"""


def sanitize_filename(term: str) -> str:
    """Convert term to a valid filename"""
    return re.sub(r"[^\w\-_.]", "_", term.replace(" ", "_")).strip("_")


def get_directory_for_term(term: str) -> str:
    """Determine the appropriate directory for the term"""
    first_char = term[0].upper()
    return first_char if first_char.isalpha() and "A" <= first_char <= "Z" else "others"


def generate_term_explanation(term: str) -> Optional[Tuple[str, float]]:
    """Generate explanation for a term using DeepSeek"""
    thread_id = threading.current_thread().name
    start_time = time.time()

    for attempt in range(3):
        try:
            if attempt > 0:
                time.sleep(2**attempt)

            time.sleep(2)  # Base delay between requests
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": "You must explain the exact term provided",
                    },
                    {"role": "user", "content": TEMPLATE.replace("<<<term>>>", term)},
                ],
                temperature=0.0,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            if not content or content.count("\n") < 3:
                continue

            first_line = content.split("\n")[0].strip("# ").strip()
            if term.lower() not in first_line.lower():
                continue

            return content, time.time() - start_time

        except Exception as e:
            print(f"[{thread_id}] Error for '{term}' (attempt {attempt + 1}): {str(e)}")

    return None


def process_terms():
    """Process terms from queue"""
    gen_dir = Path("gen")
    file_lock = threading.Lock()

    while True:
        try:
            term = term_queue.get(timeout=200)
            directory = get_directory_for_term(term)
            output_dir = gen_dir / directory

            with file_lock:
                output_dir.mkdir(exist_ok=True)

            output_path = output_dir / f"{sanitize_filename(term)}.md"
            if output_path.exists():
                print(f"Skipping existing term: {term}")
                term_queue.task_done()
                continue

            result = generate_term_explanation(term)
            if result:
                content, elapsed_time = result
                with file_lock:
                    output_path.write_text(content, encoding="utf-8")
                print(f"Generated: {output_path} in {elapsed_time:.2f}s")

        except Queue.Empty:
            break
        finally:
            term_queue.task_done()


def load_terms() -> int:
    """Load terms from files into queue"""
    total_terms = 0
    meta_dir = Path("meta")

    for filename in TARGET_FILES:
        json_file = meta_dir / f"reviewed_{filename}.json"
        if not json_file.exists():
            continue

        try:
            terms = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(terms, list):
                for term in filter(None, terms):
                    term_queue.put(term)
                    total_terms += 1
        except Exception as e:
            print(f"Error loading {json_file}: {str(e)}")

    return total_terms


def create_index():
    """Create index page"""
    gen_dir = Path("gen")
    meta_dir = Path("meta")
    term_links = defaultdict(list)
    total_generated = 0
    total_source = sum(
        len(json.loads(f.read_text(encoding="utf-8")))
        for f in meta_dir.glob("reviewed_*.json")
        if f.is_file()
    )

    # Collect terms
    for category_dir in gen_dir.iterdir():
        if not category_dir.is_dir() or category_dir.name == "__pycache__":
            continue

        for md_file in category_dir.glob("*.md"):
            try:
                first_line = (
                    md_file.read_text(encoding="utf-8").split("\n")[0].strip("# \n")
                )
                if first_line:
                    relative_path = md_file.relative_to(gen_dir)
                    term_links[category_dir.name].append(
                        (first_line, str(relative_path))
                    )
                    total_generated += 1
            except Exception as e:
                print(f"Error reading {md_file}: {str(e)}")

    # Generate terms content
    terms_content = []

    # Add progress info
    progress_info = [
        f"> Last updated: {datetime.now().strftime('%Y-%m-%d')} | ",
        f"Progress: {total_generated}/{total_source} terms generated ",
        f"({total_generated/total_source*100:.1f}%)\n",
    ]

    # Add terms by category
    if "others" in term_links:
        terms_content.extend(
            [
                "### \\# ",
                *[
                    f"- [{term}]({path})"
                    for term, path in sorted(term_links.pop("others"))
                ],
                "\n---\n",
            ]
        )

    for category in sorted(term_links):
        terms_content.extend(
            [
                f"### {category}",
                *[f"- [{term}]({path})" for term, path in sorted(term_links[category])],
                "\n---\n",
            ]
        )

    try:
        template_path = Path("gen/README_template.md")
        if not template_path.exists():
            raise FileNotFoundError("README template not found")

        template_content = template_path.read_text(encoding="utf-8")

        # Generate content with section header
        section_header = ["## Index"]  # Add a header for the terms section

        final_content = template_content.replace(
            "## To be replaced",
            "\n".join(section_header + progress_info + terms_content),
        )

        # Write final README to gen directory
        readme_path = gen_dir / "README.md"  # Changed path to gen directory
        readme_path.write_text(final_content, encoding="utf-8")
        print(f"Index created with {total_generated} terms using template")

    except Exception as e:
        print(f"Error using template: {str(e)}")
        raise


def main():
    parser = argparse.ArgumentParser(description="Financial Dictionary Generator")
    parser.add_argument(
        "--dict", action="store_true", help="Generate dictionary entries"
    )
    parser.add_argument("--index", action="store_true", help="Generate index page")
    args = parser.parse_args()

    if not (args.dict or args.index):
        parser.error("At least one of --dict or --index must be specified")

    if args.dict:
        total_terms = load_terms()
        print(f"Starting dictionary generation: {total_terms} terms")

        threads = [
            threading.Thread(target=process_terms, name=f"Consumer-{i+1}")
            for i in range(NUM_THREADS)
        ]

        for thread in threads:
            thread.daemon = True
            thread.start()

        term_queue.join()
        print("Dictionary generation completed")

    if args.index:
        create_index()


if __name__ == "__main__":
    term_queue = Queue()
    main()
