# Wikipedia Game Improvement Proposal Revision

In light of new findings during the development of the Wikipedia Game crawler, I propose a revision to the original improvement strategy. Initially, I suggested implementing a heuristic search function to analyze link relevance through keyword extraction or employing machine learning models. However, upon further development and testing, it has become clear that a simple bi-directional search algorithm significantly outperforms the heuristic approach in finding the shortest path between two Wikipedia links.

## Revised Improvement Strategy

1. Bi-Directional Search:
The core improvement will now focus on implementing a bi-directional search strategy. This approach initiates two simultaneous searches: one from the start page and another from the target page, meeting in the middle. This method effectively reduces the search space and time required to find the shortest path, proving more efficient than the previously proposed heuristic search. 
2. Parallelization
The script fetches pages one at a time. Using concurrent requests to fetch multiple pages simultaneously could significantly reduce the total search time. Python's concurrent futures module or asynchronous programming with asyncio and aiohttp can be used for this purpose.
3. Caching
Pages that have already been fetched and processed could have their links cached to avoid re-fetching and re-parsing in future searches. This would be most useful for popular pages that are likely to be encountered often.
4. Graph-based Optimization
Instead of searching only from the start page towards the finish page, starting a simultaneous search from the finish page back to the start page could reduce the search space and time. The search completes when the two searches meet in the middle.
Heuristic Search (A or Greedy Best First Search):* If a heuristic can be defined (for example based on link popularity or text similarity between the current page and the finish page), these algorithms could prioritize paths that are more likely to lead to the finish page faster than BFS.
5. Data Structure Optimization
Using deque from the collections module for the queue can improve the efficiency of insertions and deletions compared to a list.
Set for Discovered Pages: The script already uses a set for discovered pages, which is good for ensuring that each page is only visited once. Ensuring that all lookups and insertions into this set are as efficient as possible is crucial.
6. Limit Search Depth
Introducing a maximum depth could prevent the search from going too deep into less relevant parts of Wikipedia. This could be a configurable parameter based on average path lengths observed in Wikipedia.