import argparse
import asyncio
from search_algorithms import bfs, dfs, dijkstra, a_star_search
from network import AsyncHTTPClient
from utils import parse_links, extract_title
from heuristic import compute_textual_similarity
from tqdm import tqdm

async def fetch_and_parse_links(page_url):
    try:
        async with AsyncHTTPClient() as client:
            content = await client.get(page_url)
        links = []
        for link in parse_links(content, base_url="https://en.wikipedia.org"):
            try:
                title = extract_title(link)
                links.append(title)
            except Exception as e:
                print(f"Failed to parse link {link} for {page_url}: {e}")
        return links
    except Exception as e:
        print(f"Failed to fetch content for {page_url}: {e}")
        return []

async def build_graph(start_page, end_page, max_depth=2, max_links_per_page=20, max_pages=1000):
    try:
        async with AsyncHTTPClient() as client:
            start_page_exists = await client.get(f"https://en.wikipedia.org/wiki/{start_page}")
            end_page_exists = await client.get(f"https://en.wikipedia.org/wiki/{end_page}")
            if start_page_exists.status_code != 200 or end_page_exists.status_code != 200:
                raise ValueError("Start or end page does not exist in Wikipedia")
    except Exception as e:
        print(f"An error occurred while checking start and end pages: {e}")
        return None

    queue = [(start_page, 0)]
    graph = {}
    visited = set()
    pbar = tqdm(desc="Building Graph", unit="pages", total=max_pages)

    while queue:
        current_page, current_depth = queue.pop(0)
        pbar.update(1)
        if current_page not in visited:
            visited.add(current_page)
            if current_depth < max_depth:
                links = await fetch_and_parse_links(f"https://en.wikipedia.org/wiki/{current_page}")
                if links:
                    sampled_links = links[:max_links_per_page] if len(links) > max_links_per_page else links
                    graph[current_page] = sampled_links
                    for link in sampled_links:
                        title = extract_title(link)
                        if title not in visited:
                            queue.insert(0, (title, current_depth + 1))  # Insert at the beginning for DFS order
                else:
                    graph[current_page] = []
            else:
                graph[current_page] = []
        if len(visited) >= max_pages:
            print(f"Stopping early due to reaching the maximum number of pages ({max_pages})")
            break
    pbar.close()
    return graph

def find_path(graph, start_page, end_page, algorithm):
    if not graph:
        print("Graph construction failed; cannot proceed with path finding.")
        return None
    if start_page not in graph or end_page not in graph:
        print("Start or end page not found in the graph; cannot proceed with path finding.")
        return None
    
    valid_algorithms = ['bfs', 'dfs', 'dijkstra', 'a_star']
    if algorithm not in valid_algorithms:
        raise ValueError(f"Invalid search algorithm specified. Valid choices are: {', '.join(valid_algorithms)}")
    
    try:
        if algorithm == 'bfs':
            path = bfs(graph, start_page, end_page)
        elif algorithm == 'dfs':
            path = dfs(graph, start_page, end_page)
        elif algorithm == 'dijkstra':
            path, _ = dijkstra(graph, start_page, end_page)
        elif algorithm == 'a_star':
            heuristic_func = lambda x, y: compute_textual_similarity(x, y)
            path, _ = a_star_search(graph, start_page, end_page, heuristic_func)
        
        if path is None:
            print(f"No path found between {start_page} and {end_page} using {algorithm} algorithm.")
        
        return path
    except (ValueError, TypeError) as e:
        print(f"An error occurred during path finding: {e}")
        return None

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', type=str, required=True, help='Start Wikipedia page title')
    parser.add_argument('--end_page', type=str, required=True, help='End Wikipedia page title')
    parser.add_argument('--algorithm', choices=['bfs', 'dfs', 'dijkstra', 'a_star'], required=True, help='Search algorithm to use')
    args = parser.parse_args()
    
    try:
        graph = asyncio.run(build_graph(args.start_page, args.end_page))
        if graph is None:
            print("Graph could not be constructed. Please check if the start and end pages are valid.")
            return
        
        path = find_path(graph, args.start_page, args.end_page, args.algorithm)
        if path:
            print("Path found:", " -> ".join(path))
        else:
            print(f"No path found between {args.start_page} and {args.end_page} using {args.algorithm} algorithm.")
    except (ValueError, TypeError) as e:
        print(f"An error occurred during the execution: {e}")

if __name__ == '__main__':
    main()
