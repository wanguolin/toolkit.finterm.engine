# FinTerms :moneybag: [![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

**An Open-Source FinTerms Engine Powered by DeepSeek-V3**

## What's Inside?

FinTerms is an auto-generated financial dictionary that combines **prompts engineering** with **AI-native design**, delivering: 

✨ **Structured Terminology**  
`Markdown-native` formatting with strict bilingual alignment (CN/EN).

🤖 **DeepSeek-V3 Powered**  
Leveraging the cost-efficient architecture of DeepSeek's latest LLM for sustainable content generation at industry-leading rates:
- Input: $0.014-0.14 per 1M tokens
- Output: $0.28 per 1M tokens
- 64K context window

📚 **Structured Knowledge Architecture**  
- Dual-language synchronized definitions and explanations
- Historical context and origin tracking
- Practical application scenarios and risk notes
- Regulatory and market significance analysis
- Structured key takeaways for quick reference
- LLM-reviewed entries based on [Investopedia](https://www.investopedia.com/)'s Daily FinTerms¹

¹ *The original word list is from [Investopedia](https://www.investopedia.com/)'s Daily FinTerms. It was filtered and expanded by Gemini Advanced Experimental 2.0, then reviewed by DeepSeek-V3 using this code: [meta/dict_review.py](meta/dict_review.py)*

## API Pricing

*Cost estimate based on a 500-word bilingual entry (~2000 tokens): input cost $0.00028 + output cost $0.00056 ≈ $0.00084 per entry*
Reference: [DeepSeek-V3 API Pricing](https://www.deepseek.com/docs/api/pricing)

## Quick Start

Update/Create your `.env` file with your OpenAI API key and endpoint:

```bash
OPENAI_API_KEY=<your_openai_api_key>
OPENAI_ENDPOINT=<your_deepseek_endpoint>
```

Run the script:

```bash
python3.10 -m venv .venv
source .venv/bin/activate
pip install python-dotenv openai
python gen.py --dict # generate all entries
python gen.py --index # generate all entries
```

## Features

🚀 **High Performance**
- Multi-threaded term generation
- Smart retry mechanism with exponential backoff
- Efficient file handling with thread-safe operations

🎯 **Smart Organization**
- Automatic A-Z category sorting
- Special handling for numeric/symbol terms
- Sanitized filename generation for cross-platform compatibility

📊 **Progress Tracking**
- Real-time generation progress monitoring
- Detailed completion statistics
- Timestamp-based update tracking

🛠 **Developer Friendly**
- CLI interface with --dict and --index options
- Template-based content generation
- Configurable via environment variables
- Automatic index generation with Markdown linking

🔄 **Robust Processing**
- Comprehensive error handling
- Duplicate entry detection
- Content validation for generated terms
- Auto-creation of category directories

## Todo

- Currently DeepSeek-V3 is experiencing high traffic limitations, making multi-threading ineffective
- Looking for cost-effective hosting solutions to:
  - Deploy self-hosted inference
  - Support multiple API endpoints
  - Enable full multi-threading capabilities with several API endpoints
