# TaggedZ's Binary JSON Converter - CLI Reference

Convert binary files to signed JSON and back.

## 📘 Command Line Interface (`tzbjc-cli`)

### Usage

```bash
tzbjc-cli <command> [options]
```

---

### Commands

#### 🔹 `encode` — Compress a binary file into JSON

```bash
tzbjc-cli encode --input <file> [--output <json-file>] [--force]
```

**Options:**

* `--input, -i` (required): Path to the input binary file
* `--output, -o`: Path to output JSON file (default: stdout)
* `--force, -f`: Overwrite output file if it already exists

**Example:**

```bash
tzbjc-cli encode -i data.bin -o encoded.json
tzbjc-cli encode -i data.bin > encoded.json
```

---

#### 🔹 `decode` — Extract a binary file from a JSON archive

```bash
tzbjc-cli decode --input <json-file> [--output <file>] [--force]
```

**Options:**

* `--input, -i` (required): Path to the input JSON file
* `--output, -o`: Output binary file (default: uses embedded filename from JSON)
* `--force, -f`: Overwrite output file if it already exists

**Example:**

```bash
tzbjc-cli decode -i encoded.json
tzbjc-cli decode -i encoded.json -o new_data.bin --force
```

---

### Exit Codes

| Code | Meaning                   |
| ---- | ------------------------- |
| 0    | Success                   |
| 1    | Error (e.g., file exists) |