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
            links = parse_links(content, base_url="https://en.wikipedia.org")
            return links
    except Exception as e:
        print(f"Failed to fetch or parse links for {page_url}: {e}")
        return []

async def build_graph(start_page, end_page, max_depth=2, max_links_per_page=20):
    queue = [(start_page, 0)]
    graph = {}
    visited = set()
    pbar = tqdm(desc="Building Graph", unit="pages", total=1)  # Initialize total with 1 or a more appropriate estimate

    while queue:
        current_page, current_depth = queue.pop(0)
        pbar.update(1)

        if current_page not in visited:
            visited.add(current_page)
            if current_depth < max_depth:
                links = await fetch_and_parse_links(f"https://en.wikipedia.org/wiki/{current_page}")
                if links:
                    # Randomly select a subset of links if there are too many
                    sampled_links = links[:max_links_per_page] if len(links) > max_links_per_page else links
                    graph[current_page] = sampled_links
                    for link in sampled_links:
                        title = extract_title(link)
                        if title not in visited:
                            queue.append((title, current_depth + 1))
                            pbar.total += 1  # Now this should work as pbar.total is initialized
            else:
                graph[current_page] = []

        if len(visited) > 1000:  # Or any other reasonable limit based on your specific requirements
            print("Stopping early due to large number of pages")
            break

    pbar.close()
    return graph

def find_path(graph, start_page, end_page, algorithm):
    if not graph:
        print("Graph construction failed; cannot proceed with path finding.")
        return None
    try:
        if algorithm == 'bfs':
            return bfs(graph, start_page, end_page)
        elif algorithm == 'dfs':
            return dfs(graph, start_page, end_page)
        elif algorithm == 'dijkstra':
            return dijkstra(graph, start_page, end_page)[0]
        elif algorithm == 'a_star':
            heuristic_func = lambda x, y: compute_textual_similarity(x, y)
            return a_star_search(graph, start_page, end_page, heuristic_func)[0]
        else:
            raise ValueError("Invalid search algorithm specified")
    except Exception as e:
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
        if graph:
            path = find_path(graph, args.start_page, args.end_page, args.algorithm)
            if path:
                print("Path found:", " -> ".join(path))
            else:
                print("No path found between the specified pages.")
        else:
            print("Graph could not be constructed due to an error.")
    except Exception as e:
        print(f"An error occurred during the execution: {e}")

if __name__ == '__main__':
    main()
