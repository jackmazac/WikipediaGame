from collections import deque, defaultdict
import heapq
import math
from heuristic import WikipediaTextFetcher, TextPreprocessor, TextSimilarity

fetcher = WikipediaTextFetcher()
preprocessor = TextPreprocessor()
similarity_calculator = TextSimilarity()

def bfs(graph, start_page, target_page, max_depth=10):
    if start_page not in graph or target_page not in graph:
        raise ValueError("Start or target page not found in the graph")
    if start_page == target_page:
        return [start_page]
    queue = deque([(start_page, [start_page], 0)])
    visited = set([start_page])
    while queue:
        current_page, path, depth = queue.popleft()
        if depth > max_depth:
            continue
        for neighbor in graph.get(current_page, []):
            if neighbor == target_page:
                return path + [neighbor]
            if neighbor not in visited:
                if depth + 1 <= max_depth:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor], depth + 1))
    return []

def dfs(graph, start_page, target_page, max_depth=10):
    if start_page not in graph or target_page not in graph:
        raise ValueError("Start or target page not found in the graph")

    def dfs_util(current_page, path, depth, visited):
        if current_page == target_page:
            return path
        if depth >= max_depth:
            return None
        visited.add(current_page)
        for neighbor in graph.get(current_page, []):
            if neighbor not in visited:
                result = dfs_util(neighbor, path + [neighbor], depth + 1, visited)
                if result is not None:
                    return result
        return None

    visited = set()
    result = dfs_util(start_page, [start_page], 0, visited)
    return result if result is not None else []

def dijkstra(graph, start_page, target_page):
    if start_page not in graph or target_page not in graph:
        raise ValueError("Start or target page not found in the graph")
    priority_queue = []
    heapq.heappush(priority_queue, (0, start_page, [start_page]))
    distances = defaultdict(lambda: float('inf'))
    distances[start_page] = 0
    while priority_queue:
        current_distance, current_node, path = heapq.heappop(priority_queue)
        if current_node == target_page:
            return path, current_distance
        if current_distance > distances[current_node]:
            continue
        for neighbor in graph[current_node]:
            distance = current_distance + 1  # Assuming unweighted graph
            if distance < distances[neighbor]:
                distances[neighbor] = distance
                heapq.heappush(priority_queue, (distance, neighbor, path + [neighbor]))
    return [], float('inf')

def textual_similarity_heuristic(page_url1, page_url2):
    try:
        page_title1 = page_url1.split('/')[-1].replace('_', ' ')
        page_title2 = page_url2.split('/')[-1].replace('_', ' ')
        text1 = fetcher.fetch_text(page_title1)
        text2 = fetcher.fetch_text(page_title2)
        
        if text1 is None or text2 is None or not text1.strip() or not text2.strip():
            raise ValueError("One or both pages have no text content")
        
        text1 = preprocessor.preprocess_text(text1)
        text2 = preprocessor.preprocess_text(text2)
        
        if not text1 or not text2:
            raise ValueError("One or both pages have no text content after preprocessing")
        
        return similarity_calculator.compute_similarity(text1, text2)
    except (requests.exceptions.RequestException, ValueError) as e:
        print(f"Error calculating textual similarity between {page_url1} and {page_url2}: {e}")
        return float('inf')

def a_star_search(graph, start_page, target_page):
    if start_page not in graph or target_page not in graph:
        raise ValueError("Start or target page not found in the graph")
    open_set = []
    heapq.heappush(open_set, (0 + textual_similarity_heuristic(start_page, target_page), start_page, [start_page]))
    g_scores = {node: float('inf') for node in graph}
    g_scores[start_page] = 0
    f_scores = {node: float('inf') for node in graph}
    f_scores[start_page] = textual_similarity_heuristic(start_page, target_page)
    heuristic_cache = {}
    while open_set:
        current_f_score, current_node, current_path = heapq.heappop(open_set)
        if current_node == target_page:
            return current_path, current_f_score
        for neighbor in graph[current_node]:
            tentative_g_score = g_scores[current_node] + 1  # Assuming unweighted graph
            if tentative_g_score < g_scores[neighbor]:
                g_scores[neighbor] = tentative_g_score
                if (neighbor, target_page) not in heuristic_cache:
                    heuristic_cache[(neighbor, target_page)] = textual_similarity_heuristic(neighbor, target_page)
                f_score = tentative_g_score + heuristic_cache[(neighbor, target_page)]
                if f_score < f_scores[neighbor]:
                    f_scores[neighbor] = f_score
                    heapq.heappush(open_set, (f_score, neighbor, current_path + [neighbor]))
    return [], float('inf')
