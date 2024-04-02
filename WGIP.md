# Wikipedia Graph Crawler Improvement Proposal (WGIP)
## Overview
The Wikipedia Graph Crawler algorithm, as implemented in crawler.py, employs a bidirectional search strategy to find the shortest path between two Wikipedia pages by navigating through the links contained within the pages. This document provides a comprehensive description of the algorithm, mathematical formalization, and suggestions for enhancements.

## Algorithm Description
Input
- Parameters: start_page (URL of the starting Wikipedia page) and finish_page (URL of the target Wikipedia page).
Initialization
- Priority Queues: start_queue and finish_queue, initialized with the starting and target pages, respectively.
- Dictionaries: discovered_from_start and discovered_from_finish track discovered pages.
- Sets: visited_from_start and visited_from_finish prevent revisiting pages.
Concurrency Control: An asyncio.Semaphore limits the number of concurrent requests.
Search Step
- Alternates between start and finish sides, fetching links from current pages, calculating priorities, and updating queues until a path is found or queues are empty.
- The search concludes by reconstructing and returning the shortest path or None if unreachable within the depth limit.

---

# Wikipedia Link Graph:
Let `G = (V, E)` be a directed graph representing the Wikipedia link structure, where:
- `V` is the set of vertices (Wikipedia pages).
- `E` is the set of edges (links between pages), where each edge `e = (u, v)` represents a link from page `u` to page `v`.

## Bidirectional Search Algorithm:
Let `s ∈ V` be the starting page and `t ∈ V` be the target page.
Let `d(u, v)` be the shortest path distance between pages `u` and `v`.
Let `p(u, t)` be a priority function that estimates the similarity between page `u` and the target page `t`.
Let `Q_s` and `Q_t` be priority queues for the start and finish sides, respectively.
Let `D_s` and `D_t` be dictionaries to store the discovered pages and their corresponding paths for the start and finish sides, respectively.
Let `V_s` and `V_t` be sets to store the visited pages for the start and finish sides, respectively.

### Initialization:
- `Q_s = [(0, s, [s], 0)]`, where `0` is the initial priority, `s` is the starting page, `[s]` is the initial path, and `0` is the initial depth.
- `Q_t = [(0, t, [t], 0)]`, where `0` is the initial priority, `t` is the target page, `[t]` is the initial path, and `0` is the initial depth.
- `D_s = {s: [s]}`, where `s` is the starting page and `[s]` is the initial path.
- `D_t = {t: [t]}`, where `t` is the target page and `[t]` is the initial path.
- `V_s = ∅`, an empty set to store visited pages from the start side.
- `V_t = ∅`, an empty set to store visited pages from the finish side.

### Search Step:
While `Q_s ≠ ∅` and `Q_t ≠ ∅`:
- If `Q_s ≠ ∅`:
  - `(priority, u, path, depth) = Q_s.pop()`
  - If `depth > MAX_DEPTH` or `u ∈ V_s`, continue to the next iteration.
  - If `u ∈ D_t`, return `path + D_t[u][::-1][1:]` as the shortest path.
  - `V_s = V_s ∪ {u}`
  - For each unvisited neighbor `v` of `u`:
    - `priority = p(v, t)`
    - `D_s[v] = path + [v]`
    - `Q_s.push((priority, v, path + [v], depth + 1))`
- If `Q_t ≠ ∅`:
  - `(priority, u, path, depth) = Q_t.pop()`
  - If `depth > MAX_DEPTH` or `u ∈ V_t`, continue to the next iteration.
  - If `u ∈ D_s`, return `D_s[u] + path[::-1][1:]` as the shortest path.
  - `V_t = V_t ∪ {u}`
  - For each unvisited neighbor `v` of `u`:
    - `priority = p(v, s)`
    - `D_t[v] = path + [v]`
    - `Q_t.push((priority, v, path + [v], depth + 1))`

### Termination:
- If a shortest path is found, the algorithm terminates and returns the path.
- If both queues become empty and no path is found, the algorithm terminates and returns `None`, indicating no path within the depth limit.

The priority function `p(u, t)` can be defined based on the similarity between page `u` and the target page `t`. One possible definition is:
- `p(u, t) = -|words(u) ∩ words(t)|`, where `words(u)` and `words(t)` are the sets of words in the titles of pages `u` and `t`, respectively. The negative sign is used to prioritize pages with higher similarity.

---

# Further Improvements

## Adaptive Depth Limit:
Instead of using a fixed depth limit (`MAX_DEPTH`), consider implementing an adaptive depth limit based on the characteristics of the start and target pages. Analyze the link structure and connectivity of the Wikipedia graph to determine an appropriate depth limit dynamically. This can help optimize the search by avoiding unnecessary exploration of deep paths when a shorter path is likely to exist.

## Intelligent Pruning:
Implement intelligent pruning techniques to reduce the search space and improve efficiency. Use domain knowledge or heuristics to identify and prune irrelevant or unlikely paths early in the search process. For example, prune pages that belong to drastically different categories or have a low semantic similarity to the target page.

## Bidirectional Heuristic:
Develop a bidirectional heuristic that estimates the distance between two pages based on their content and link structure. Use this heuristic to guide the search and prioritize the exploration of pages that are more likely to lead to the target page. The heuristic can consider factors such as the number of common categories, the overlap of key phrases, or the co-occurrence of links.

## Parallel Processing:
Leverage parallel processing to speed up the search process, especially for large-scale crawls. Distribute the workload across multiple machines or processes to explore different parts of the graph concurrently. Implement efficient synchronization mechanisms to share discovered paths and avoid redundant work.

## Caching and Incremental Updates:
Enhance the caching mechanism to store and reuse previously discovered paths between pages. Implement incremental updates to the cache when the Wikipedia graph evolves over time. Use techniques like cache invalidation or time-to-live (TTL) to ensure the freshness and validity of cached data.

## Machine Learning-based Prioritization:
Incorporate machine learning techniques to learn patterns and features that indicate the likelihood of a page leading to the target page. Train a model on a large dataset of successful paths and use it to prioritize the exploration of pages during the search. Features can include textual similarity, link structure, category information, and user navigation patterns.

## Graph Embedding and Representation Learning:
Apply graph embedding techniques to learn low-dimensional representations of Wikipedia pages and their relationships. Use these embeddings to measure the similarity between pages and guide the search towards the target page. Embedding methods like Node2Vec, DeepWalk, or Graph Convolutional Networks (GCNs) can be explored.

## Integration with External Knowledge Bases:
Leverage external knowledge bases, such as Wikidata or DBpedia, to enrich the search process. Use structured data and semantic relationships from these knowledge bases to infer connections between pages and improve the prioritization of paths.
