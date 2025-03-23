# Autocomplete API Name Extractor

This project implements a solution to systematically extract all possible names from an autocomplete API system.

## Approach & Implementation Details

2025-03-21 15:24:52,638 - INFO - Total requests made: 709
2025-03-21 15:24:52,638 - INFO - Total unique names found: 6720

### Key Features

1. **Asynchronous Processing**: Uses `aiohttp` for efficient concurrent requests
2. **Rate Limiting**: Implements a sliding window rate limiter
3. **Error Handling**: Robust error handling for various HTTP status codes
4. **Recursive Exploration**: Systematically explores the name space using prefix-based searching
5. **Result Deduplication**: Maintains a set of unique names
6. **Progress Logging**: Detailed logging of the extraction process

### Technical Implementation

- The solution uses a breadth-first approach to explore possible name combinations
- Starts with single letters (a-z) and recursively extends prefixes
- Implements intelligent backoff when rate limits are hit
- Saves results to a JSON file for persistence

### API Behavior Findings

1. **API Versions**:

   - Supports v1, v2, and v3 endpoints
   - v3 endpoint: `/v3/autocomplete`
   - v2 endpoint: `/v2/autocomplete`
   - v1 endpoint: `/v1/autocomplete` (fallback)

2. **Response Format**:

```json
{
    "version": "v3",
    "count": 15,
    "results": ["name1", "name2", ...]
}
```

3. **Name Patterns**:

   - Names can contain:
     - Letters (a-z)
     - Numbers (0-9)
     - Spaces
     - Special characters (+, -, .)
   - Examples: "j 1p3en", "j+2rs", "j-0elfe-9"
   - Names can have multiple special characters
   - Special characters can appear in various positions

4. **Character Rules**:
   - Spaces can appear in the middle of names
   - Multiple special characters can be present
   - Names can start or end with special characters

## Usage

1. Install dependencies:

```bash
pip install aiohttp
```

2. Run the script:

```bash
python autocomplete_extractor.py
```

3. Results will be saved to `discovered_names.json`

## Performance Considerations

- The script implements a sliding window rate limiter to stay within API limits
- Async processing allows for efficient concurrent requests
- Deduplication ensures we don't process the same names multiple times
- Recursive depth is limited to prevent excessive API calls

## Limitations & Future Improvements

1. The current implementation assumes English alphabet characters
2. Could be extended to handle international characters
3. Could implement more sophisticated retry mechanisms
4. Could add progress persistence to resume interrupted extractions

## Statistics

- Rate Limit: 10 requests/second
- Average response time: ~100ms
- Results are saved in `discovered_names.json`
