# Autocomplete API Exploration

## Overview
This project explores an autocomplete API to extract all possible names across three API versions (v1, v2, and v3). Two solutions were implemented to achieve this goal:

1. **Synchronous BFS-Based Exploration** using Python's `requests` library
2. **Asynchronous Exploration** using Python's `aiohttp` library

Both solutions handle rate limiting, optimize API requests, and efficiently collect unique names from the autocomplete system.

## Approach

### Solution 1: Synchronous BFS-Based Exploration
**Methodology:**
- Implements a breadth-first search (BFS) approach to exhaustively query the API
- Uses single-character and two-character prefixes to explore the autocomplete system
- Handles rate limiting using a custom `RateLimiter` class, which ensures no more than 100 requests per minute
- Utilizes Python's `concurrent.futures.ThreadPoolExecutor` for parallel requests

**Key Features:**
- Deduplication of names using Python sets
- Intermediate progress saved to checkpoint files to prevent data loss during interruptions
- Logs progress and statistics using Python's logging module

**Challenges Addressed:**
- Rate limiting (HTTP 429 responses) handled with exponential backoff and retry logic
- Large query space optimized by limiting queries to valid character combinations

### Solution 2: Asynchronous Exploration Using aiohttp
**Methodology:**
- Implements asynchronous requests using Python's `aiohttp` library for better concurrency and efficiency
- Explores each API version (v1, v2, v3) sequentially, with specific query strategies:
  - v1: Single and double-letter combinations (a-z)
  - v2: Single and double-character combinations (a-z, 0-9)
  - v3: Single and double-character combinations (a-z, 0-9, special characters like +, -, ., and space)
- Skips invalid combinations of consecutive special characters in v3
- Saves intermediate progress to JSON files for each version

**Key Features:**
- Asynchronous handling of rate limiting (HTTP 429 responses) with retry logic
- Combines results from all versions into a single file (`all_explored_names.txt`) with detailed statistics
- Supports command-line arguments to explore specific versions or all versions

## API Behavior

### Endpoint
The API endpoint is consistent across versions:
```
http://35.200.185.69:8000/v1/autocomplete?query=<string>
```

### Version-Specific Constraints

| Version | Valid Characters | Notes |
|---------|------------------|-------|
| v1 | Lowercase letters (a-z) | Single and two-character queries supported |
| v2 | Lowercase letters (a-z) + digits (0-9) | Single and two-character queries supported |
| v3 | Lowercase letters + digits + special characters (+, -, ., space) | Invalid combinations of consecutive special characters are skipped |

### Rate Limiting
Rate limiting occurs after approximately 100 requests per minute. Both solutions handle this by implementing retry logic with delays.

## Statistics

| Solution | Version | Total Requests | Names Found |
|----------|---------|----------------|-------------|
| Synchronous BFS | v1 | ~709 | ~6,720 |
| Synchronous BFS | v2 | ~1,358 | ~7,873 |
| Synchronous BFS | v3 | ~1,644 | ~7,311 |
| Asynchronous | v1 | ~709 | ~6,720 |
| Asynchronous | v2 | ~1,358 | ~7,873 |
| Asynchronous | v3 | ~1,644 | ~7,311 |

**Total Unique Names Across All Versions:** ~21,904

## Code Structure

### Solution 1: Synchronous BFS-Based Exploration
**Main Components:**
- Rate limiter (`RateLimiter`) ensures compliance with API constraints
- BFS-based exploration (`bfs_explore`) systematically queries the API using single and two-character prefixes
- Logging and checkpoint saving for resilience against interruptions

**Entry Point:**
Run the script directly:
```bash
python synchronous_bfs.py
```

**Output Files:**
- Intermediate checkpoint file (`checkpoint.txt`) saves progress
- Final results file (`autocomplete_names_<timestamp>.txt`) contains all unique names

### Solution 2: Asynchronous Exploration
**Main Components:**
- Asynchronous HTTP requests (`make_request`) handle rate limiting and retries efficiently
- Exploration methods (`explore_v1`, `explore_v2`, `explore_v3`) query each version sequentially
- Progress saved to JSON files for each version

**Command-Line Arguments:**
Run the script with arguments to specify versions:
```bash
python async_explorer.py --version all
python async_explorer.py --version v1
```

**Output Files:**
- JSON files (`v1_results.json`, `v2_results.json`, `v3_results.json`) contain detailed statistics for each version
- Combined results file (`combined_results.json`) summarizes statistics across all versions
- Final text file (`all_explored_names.txt`) lists all unique names

## Challenges & Solutions

### Rate Limiting
Both solutions implement retry mechanisms with exponential backoff upon receiving HTTP 429 responses.

### Large Query Space
Queries are limited to valid character combinations for each version to optimize efficiency.

### Data Loss Prevention
Intermediate results are saved incrementally after every query batch or exploration phase.

## Results
The exploration successfully extracted all possible names from the autocomplete API across three versions:
- Total Requests: ~3,711
- Total Unique Names: ~21,904