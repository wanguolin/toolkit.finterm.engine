# Please install OpenAI SDK first: `pip3 install openai`

import os
import json
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()
api_key = os.getenv("DEEPSEEK_API_KEY")
base_url = os.getenv("DEEPSEEK_BASE_URL")

# Initialize DeepSeek client
client = OpenAI(api_key=api_key, base_url=base_url)

# Define the review prompt
REVIEW_PROMPT = """You are a professional financial media dictionary editor. Based on the following list of terms that start with a specific letter or symbol, complete these tasks and output as a JSON array:

1. Filter & Clean:
   - Ensure all terms are related to the financial field
   - Remove any irrelevant terms
   - Merge similar terms to avoid duplication

2. Optimize & Enhance:
   - Refine the terms to ensure they are clear, concise, and relevant to finance
   - Maintain alphabetical order of the terms

3. Fill Gaps:
   - Identify and add important missing financial terms that start with the same letter/symbol
   - Focus on commonly used terms in modern finance, including:
     * Traditional financial concepts
     * Market terminology
     * Investment vehicles
     * FinTech and cryptocurrency terms
     * Economic indicators
     * Regulatory terms

Note: Any added terms should follow the same alphabetical order as the input list."""

# Define target files to process
TARGET_FILES = ["#"] + [chr(i) for i in range(ord("A"), ord("Z") + 1)]


def review_json_file(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        # Convert content to string for the API
        content_str = json.dumps(content, ensure_ascii=False)

        # Send to DeepSeek for review
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {
                    "role": "user",
                    "content": f"{REVIEW_PROMPT}\n\nTerms:\n{content_str}",
                },
            ],
            stream=False,
        )

        # Get the reviewed content and clean it up
        reviewed_content = response.choices[0].message.content

        # Clean up the response: remove markdown code blocks and extra quotes
        reviewed_content = reviewed_content.strip()
        # Remove markdown code blocks if present
        if reviewed_content.startswith("```json"):
            reviewed_content = reviewed_content.replace("```json", "").replace(
                "```", ""
            )
        # Remove extra quotes at start/end if present
        reviewed_content = reviewed_content.strip('"')

        # Additional cleanup: ensure we only have the JSON array
        reviewed_content = reviewed_content.strip()
        # Find the first '[' and last ']' to extract just the JSON array
        start_idx = reviewed_content.find("[")
        end_idx = reviewed_content.rfind("]") + 1
        if start_idx != -1 and end_idx != 0:
            reviewed_content = reviewed_content[start_idx:end_idx]

        # Ensure it's valid JSON by parsing and re-serializing
        try:
            cleaned_json = json.loads(reviewed_content)
            # Save to new file with proper JSON formatting
            output_path = file_path.parent / f"reviewed_{file_path.name}"
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(cleaned_json, f, ensure_ascii=False, indent=4)

        except json.JSONDecodeError as e:
            print(f"Error parsing JSON for {file_path}: {str(e)}")
            print("Raw content:", reviewed_content)

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")


def main():
    current_dir = Path(".")

    # Process each target file
    for filename in TARGET_FILES:
        json_file = current_dir / f"{filename}.json"
        if json_file.exists():
            print(f"Processing {json_file}...")
            review_json_file(json_file)
            print(f"Completed review for {json_file}")


if __name__ == "__main__":
    main()
