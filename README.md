# Convert-Chat: Google AI Studio JSON Parser

A Python utility script that converts raw, nested JSON conversation logs exported from **Google AI Studio** into clean, readable Markdown format.

## 🎯 Features

- **Parses Native Google AI Studio Exports**: Handles the complex, nested JSON structure exported natively from Google AI Studio.
- **Intelligent Formatting**: Merges fragmented conversation text, filters out internal LLM "Thought" blocks, and normalizes roles (User vs. Assistant).
- **Batch Processing**: Can process an entire directory of JSON logs simultaneously.
- **Markdown Output**: Generates clean `.md` files with clear structural separators (`---`) and escaped line breaks, saving them automatically into an `output_md` directory.
- **Graceful Fallbacks**: If the strict JSON parsing fails (e.g., due to malformed files), it falls back to a direct regex-based text extraction engine.

## 🛠️ Usage

### Prerequisites
- Python 3.6+
- No third-party dependencies required (uses only standard library).

### Command-Line Arguments

| Argument | Description |
|----------|-------------|
| `-o`, `--output` | Specify the output Markdown file path. |
| `-f`, `--force` | Force overwrite if the output file already exists. |
| `-t`, `--title` | Add a custom title to the generated Markdown document. |
| `-v`, `--verbose` | Enable debug-level logging. |
| `--batch` | Batch process all supported files in the current directory. |
| `input_file` | The path to the input JSON file (for single-file mode). |

### Examples

**1. Single File Processing**
```bash
python convert_chat.py conversation_log.json
```
*(This will generate `output_md/conversation_log.json.md`)*

**2. Custom Output & Title**
```bash
python convert_chat.py input.json -o custom_output.md -t "My AI Chat History"
```

**3. Batch Processing**
Convert all valid files in the current directory:
```bash
python convert_chat.py --batch
```

## 📁 Output Structure
By default, the script creates an `output_md` subdirectory and places all converted Markdown files there to keep your root workspace clean.

---
*Note: A Chinese version of the documentation is available in `README_zh.md`.*
