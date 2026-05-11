# envdiff

> Tool to diff and sync `.env` files across environments safely.

---

## Installation

```bash
pip install envdiff
```

Or install from source:

```bash
pip install git+https://github.com/yourusername/envdiff.git
```

---

## Usage

Compare two `.env` files and highlight differences:

```bash
envdiff .env.local .env.production
```

Sync missing keys from one file to another (values are redacted by default):

```bash
envdiff sync .env.local .env.production --dry-run
```

Example output:

```
[+] DB_HOST        present in .env.production  |  missing in .env.local
[-] DEBUG          present in .env.local        |  missing in .env.production
[~] API_KEY        values differ
```

Use `--export` to write a merged result to a new file:

```bash
envdiff sync .env.local .env.production --export .env.merged
```

---

## Options

| Flag | Description |
|------|-------------|
| `--dry-run` | Preview changes without writing anything |
| `--export` | Write merged output to a specified file |
| `--show-values` | Display actual values (use with caution) |
| `--quiet` | Suppress output, exit code only |

---

## License

This project is licensed under the [MIT License](LICENSE).