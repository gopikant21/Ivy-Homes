import requests
import time
import string
from collections import deque
import concurrent.futures
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autocomplete_extraction.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "http://35.200.185.69:8000/v1/autocomplete"
RATE_LIMIT = 100  # 100 requests per minute
MAX_RETRIES = 5
MAX_WORKERS = 20  # Adjust based on API's concurrency tolerance

class RateLimiter:
    def __init__(self, limit, window):
        self.limit = limit  # Number of requests allowed
        self.window = window  # Time window in seconds
        self.timestamps = deque()
        
    def add_request(self):
        now = time.time()
        
        # Remove timestamps older than the window
        while self.timestamps and self.timestamps[0] < now - self.window:
            self.timestamps.popleft()
        
        # Add current timestamp
        self.timestamps.append(now)
    
    def wait_if_needed(self):
        if len(self.timestamps) < self.limit:
            return 0
        
        # If we've reached the limit, calculate how long to wait
        now = time.time()
        oldest = self.timestamps[0]
        wait_time = max(0, self.window - (now - oldest))
        
        if wait_time > 0:
            time.sleep(wait_time)
            return wait_time
        return 0

def make_api_request(query, rate_limiter):
    for attempt in range(MAX_RETRIES):
        # Wait if we're approaching rate limit
        rate_limiter.wait_if_needed()
        
        try:
            response = requests.get(f"{BASE_URL}?query={query}")
            rate_limiter.add_request()
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                wait_time = 60 * (attempt + 1)  # Wait longer with each retry
                logger.warning(f"Rate limit exceeded for query '{query}'. Waiting {wait_time}s")
                time.sleep(wait_time)
            else:
                logger.error(f"Error: Status code {response.status_code} for query '{query}'")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                
        except requests.RequestException as e:
            logger.error(f"Request failed for query '{query}': {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2 ** attempt)  # Exponential backoff
    
    logger.error(f"All retries failed for query '{query}'")
    return None

def bfs_explore():
    rate_limiter = RateLimiter(RATE_LIMIT, 60)  # 100 requests per 60 seconds
    queue = deque(string.ascii_lowercase)
    all_names = set()
    processed = set()
    request_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        while queue:
            # Take up to MAX_WORKERS prefixes from the queue
            current_batch = []
            for _ in range(min(MAX_WORKERS, len(queue))):
                if queue:
                    prefix = queue.popleft()
                    if prefix not in processed:
                        current_batch.append(prefix)
                        processed.add(prefix)
            
            if not current_batch:
                continue
            
            # Submit all prefixes in the batch to the executor
            future_to_prefix = {
                executor.submit(make_api_request, prefix, rate_limiter): prefix 
                for prefix in current_batch
            }
            request_count += len(current_batch)
            
            for future in concurrent.futures.as_completed(future_to_prefix):
                prefix = future_to_prefix[future]
                try:
                    response = future.result()
                    if response and "results" in response:
                        results = response["results"]
                        all_names.update(results)
                        
                        # If we got the maximum number of results, add deeper prefixes to the queue
                        if response.get("count", 0) == 10:
                            for char in string.ascii_lowercase:
                                new_prefix = prefix + char
                                if new_prefix not in processed:
                                    queue.append(new_prefix)
                        
                        # Log progress periodically
                        if len(all_names) % 100 == 0:
                            logger.info(f"Found {len(all_names)} unique names so far. Queue size: {len(queue)}")
                            
                except Exception as exc:
                    logger.error(f"Error processing '{prefix}': {exc}")
    
    return all_names, request_count

def save_checkpoint(names, filename="checkpoint.txt"):
    """Save current results to a checkpoint file"""
    with open(filename, "w") as f:
        for name in sorted(names):
            f.write(f"{name}\n")
    logger.info(f"Checkpoint saved with {len(names)} names")

if __name__ == "__main__":
    start_time = time.time()
    logger.info("Starting autocomplete extraction")
    
    try:
        all_names, request_count = bfs_explore()
        
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"Extraction completed in {duration:.2f} seconds")
        logger.info(f"Total names found: {len(all_names)}")
        logger.info(f"Total API requests made: {request_count}")
        
        # Save results to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"autocomplete_names_{timestamp}.txt"
        with open(result_file, "w") as f:
            for name in sorted(all_names):
                f.write(f"{name}\n")
        
        logger.info(f"All names saved to {result_file}")
        
        # Print sample of results
        sample = list(all_names)[:10] if all_names else []
        logger.info(f"Sample of names: {sample}")
        
    except KeyboardInterrupt:
        logger.warning("Extraction interrupted by user")
        if 'all_names' in locals():
            save_checkpoint(all_names)
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        if 'all_names' in locals():
            save_checkpoint(all_names)
