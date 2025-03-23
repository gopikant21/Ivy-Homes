import aiohttp
import asyncio
import json
import logging
from collections import deque
import time
import string
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AutocompleteExplorer:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = None
        self.v1_names = set()
        self.v2_names = set()
        self.v3_names = set()
        self.requests_count = {'v1': 0, 'v2': 0, 'v3': 0}
        
    async def init_session(self):
        self.session = aiohttp.ClientSession()

    async def close_session(self):
        if self.session:
            await self.session.close()

    async def make_request(self, version: str, query: str) -> list:
        """Make a request to specific API version"""
        self.requests_count[version] += 1
        
        try:
            url = f"{self.base_url}/{version}/autocomplete"
            async with self.session.get(url, params={"query": query}) as response:
                if response.status == 429:
                    logger.warning(f"Rate limit hit for {version}, waiting...")
                    await asyncio.sleep(61)
                    return await self.make_request(version, query)
                    
                if response.status == 200:
                    data = await response.json()
                    return data.get("results", [])
                    
                logger.error(f"Error {response.status} for {version}: {await response.text()}")
                return []
                
        except Exception as e:
            logger.error(f"Request failed for {version}: {str(e)}")
            return []

    async def explore_v1(self):
        """Explore v1 with single and double letter combinations"""
        logger.info("Starting v1 exploration")
        
        # Try single letters
        for letter in string.ascii_lowercase:
            results = await self.make_request('v1', letter)
            self.v1_names.update(results)
            logger.info(f"V1 single letter '{letter}': found {len(results)} names")
            self.save_progress('v1')
            
        # Try two letter combinations
        for first in string.ascii_lowercase:
            for second in string.ascii_lowercase:
                query = first + second
                results = await self.make_request('v1', query)
                self.v1_names.update(results)
                logger.info(f"V1 two letters '{query}': found {len(results)} names")
                self.save_progress('v1')
        
        logger.info("=== V1 Final Statistics ===")
        logger.info(f"V1 total requests made: {self.requests_count['v1']}")
        logger.info(f"V1 total unique names found: {len(self.v1_names)}")

    async def explore_v2(self):
        """Explore v2 with single letters/numbers and two character combinations"""
        logger.info("Starting v2 exploration")
        
        # Characters to try (letters + numbers)
        chars = string.ascii_lowercase + string.digits
        
        # Try single characters
        for char in chars:
            results = await self.make_request('v2', char)
            self.v2_names.update(results)
            logger.info(f"V2 single char '{char}': found {len(results)} names")
            self.save_progress('v2')
            
        # Try two character combinations
        for first in chars:
            for second in chars:
                query = first + second
                results = await self.make_request('v2', query)
                self.v2_names.update(results)
                logger.info(f"V2 two chars '{query}': found {len(results)} names")
                self.save_progress('v2')
        
        logger.info("=== V2 Final Statistics ===")
        logger.info(f"V2 total requests made: {self.requests_count['v2']}")
        logger.info(f"V2 total unique names found: {len(self.v2_names)}")

    async def explore_v3(self):
        """Explore v3 with all characters including special chars"""
        logger.info("Starting v3 exploration")
        
        # All characters including special chars
        chars = string.ascii_lowercase + string.digits + '+- .'
        
        # Try single characters
        for char in chars:
            results = await self.make_request('v3', char)
            self.v3_names.update(results)
            logger.info(f"V3 single char '{char}': found {len(results)} names")
            self.save_progress('v3')
            
        # Try two character combinations
        for first in chars:
            for second in chars:
                # Skip invalid combinations of special chars
                if (first in '+- .' and second in '+- .'):
                    continue
                query = first + second
                results = await self.make_request('v3', query)
                self.v3_names.update(results)
                logger.info(f"V3 two chars '{query}': found {len(results)} names")
                self.save_progress('v3')

    def save_progress(self, version: str):
        """Save current progress to file"""
        with open(f'{version}_results.json', 'w') as f:
            names_set = getattr(self, f'{version}_names')
            json.dump({
                'requests_made': self.requests_count[version],
                'names_found': len(names_set),
                'names': sorted(list(names_set))
            }, f, indent=2)

    def write_all_names_to_file(self, filename="all_explored_names.txt"):
        """Write all explored names to a single file in a clean format"""
        all_names = sorted(self.v1_names.union(self.v2_names, self.v3_names))
        
        with open(filename, 'w') as f:
            # Write header with statistics
            f.write("=== Autocomplete API Exploration Results ===\n")
            f.write(f"Total unique names found: {len(all_names)}\n")
            f.write(f"Names from v1: {len(self.v1_names)}\n")
            f.write(f"Names from v2: {len(self.v2_names)}\n")
            f.write(f"Names from v3: {len(self.v3_names)}\n")
            f.write("\n=== All Unique Names ===\n\n")
            
            # Write all names, one per line
            for name in all_names:
                f.write(f"{name}\n")

    async def run_exploration(self):
        """Run the exploration for all versions"""
        await self.init_session()
        try:
            await self.explore_v1()
            await asyncio.sleep(5)
            await self.explore_v2()
            await asyncio.sleep(5)
            await self.explore_v3()
            
            # Save combined final results
            with open('combined_results.json', 'w') as f:
                json.dump({
                    'statistics': {
                        'v1_requests': self.requests_count['v1'],
                        'v2_requests': self.requests_count['v2'],
                        'v3_requests': self.requests_count['v3'],
                        'v1_names_found': len(self.v1_names),
                        'v2_names_found': len(self.v2_names),
                        'v3_names_found': len(self.v3_names),
                        'total_unique_names': len(self.v1_names.union(self.v2_names, self.v3_names))
                    },
                    'v1_names': sorted(list(self.v1_names)),
                    'v2_names': sorted(list(self.v2_names)),
                    'v3_names': sorted(list(self.v3_names)),
                    'all_unique_names': sorted(list(self.v1_names.union(self.v2_names, self.v3_names)))
                }, f, indent=2)
            
            # Write all names to a clean text file
            self.write_all_names_to_file()
                
        finally:
            await self.close_session()

def parse_args():
    parser = argparse.ArgumentParser(description='Explore autocomplete API versions')
    parser.add_argument('--version', type=str, choices=['v1', 'v2', 'v3', 'all'],
                      default='all', help='API version to explore (v1, v2, v3, or all)')
    return parser.parse_args()

async def main():
    args = parse_args()
    explorer = AutocompleteExplorer("http://35.200.185.69:8000")
    await explorer.init_session()
    
    try:
        if args.version == 'all':
            await explorer.explore_v1()
            await asyncio.sleep(5)
            await explorer.explore_v2()
            await asyncio.sleep(5)
            await explorer.explore_v3()
        elif args.version == 'v1':
            await explorer.explore_v1()
        elif args.version == 'v2':
            await explorer.explore_v2()
        elif args.version == 'v3':
            await explorer.explore_v3()
            
        # Save results for the version(s) explored
        with open('exploration_results.json', 'w') as f:
            results = {
                'statistics': {
                    'requests': explorer.requests_count,
                    'names_found': {
                        'v1': len(explorer.v1_names) if args.version in ['v1', 'all'] else 0,
                        'v2': len(explorer.v2_names) if args.version in ['v2', 'all'] else 0,
                        'v3': len(explorer.v3_names) if args.version in ['v3', 'all'] else 0
                    }
                },
                'names': {
                    'v1': sorted(list(explorer.v1_names)) if args.version in ['v1', 'all'] else [],
                    'v2': sorted(list(explorer.v2_names)) if args.version in ['v2', 'all'] else [],
                    'v3': sorted(list(explorer.v3_names)) if args.version in ['v3', 'all'] else []
                }
            }
            json.dump(results, f, indent=2)
        
        # Write all names to a clean text file
        explorer.write_all_names_to_file()
            
    finally:
        await explorer.close_session()

if __name__ == "__main__":
    asyncio.run(main()) 