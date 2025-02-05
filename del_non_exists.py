import json
from pathlib import Path
import re


def sanitize_filename(term: str) -> str:
    """Convert term to a valid filename"""
    return re.sub(r"[^\w\-_.]", "_", term.replace(" ", "_")).strip("_")


def find_mismatched_files():
    # 1. Collect all terms from meta/*.json
    meta_terms = set()
    meta_dir = Path("meta")
    for json_file in meta_dir.glob("reviewed_*.json"):
        try:
            terms = json.loads(json_file.read_text(encoding="utf-8"))
            if isinstance(terms, list):
                # Convert each term to its sanitized filename form
                meta_terms.update(
                    sanitize_filename(term) + ".md" for term in terms if term
                )
        except Exception as e:
            print(f"Error reading {json_file}: {str(e)}")

    print(f"Total terms in meta files: {len(meta_terms)}")

    # 2. Collect all .md files in gen directory
    gen_dir = Path("gen")
    existing_files = []
    for md_file in gen_dir.rglob("*.md"):
        # Skip README files
        if md_file.name.lower() in ("readme.md", "readme_template.md"):
            continue
        existing_files.append(md_file)

    print(f"Total .md files in gen directory: {len(existing_files)}")

    # 3. Find mismatches
    mismatched_files = []
    for file_path in existing_files:
        if file_path.name not in meta_terms:
            mismatched_files.append(file_path)

    # Print results
    if mismatched_files:
        print("\nFiles not matching any term in meta:")
        for file in sorted(mismatched_files):
            print(f"- {file}")
    else:
        print("\nNo mismatched files found.")

    return mismatched_files


def find_and_delete_mismatched_files():
    mismatched_files = find_mismatched_files()

    if not mismatched_files:
        return

    print("\nPreparing to delete the above files...")
    confirmation = input("Are you sure you want to delete these files? (yes/no): ")

    if confirmation.lower() == "yes":
        deleted_count = 0
        for file_path in mismatched_files:
            try:
                file_path.unlink()
                print(f"Deleted: {file_path}")
                deleted_count += 1
            except Exception as e:
                print(f"Error deleting {file_path}: {str(e)}")

        print(f"\nSuccessfully deleted {deleted_count} files")
    else:
        print("Operation cancelled")


if __name__ == "__main__":
    find_and_delete_mismatched_files()
