# Wikipedia Game Improvement Proposal

I propose that, in order to improve the Wikipedia Game crawler, I will implement a heursitic search function to analyze link relevance, such as keyword extraction from the link context or employing machine learning models that can predict relevance more accurately.  To achieve this, I will make the program use techniques such as extracting key terms and phrases directly from the context surrounding the links. This will  provide insight into their relevance. Additionally, I will consider training a machine learning model on the data. 

## Additional Potential Improvements

1. Parallelization
The script fetches pages one at a time. Using concurrent requests to fetch multiple pages simultaneously could significantly reduce the total search time. Python's concurrent futures module or asynchronous programming with asyncio and aiohttp can be used for this purpose.
2. Caching
Pages that have already been fetched and processed could have their links cached to avoid re-fetching and re-parsing in future searches. This would be most useful for popular pages that are likely to be encountered often.
3. Graph-based Optimization
Instead of searching only from the start page towards the finish page, starting a simultaneous search from the finish page back to the start page could reduce the search space and time. The search completes when the two searches meet in the middle.
Heuristic Search (A or Greedy Best First Search):* If a heuristic can be defined (for example based on link popularity or text similarity between the current page and the finish page), these algorithms could prioritize paths that are more likely to lead to the finish page faster than BFS.
4. Data Structure Optimization
Using deque from the collections module for the queue can improve the efficiency of insertions and deletions compared to a list.
Set for Discovered Pages: The script already uses a set for discovered pages, which is good for ensuring that each page is only visited once. Ensuring that all lookups and insertions into this set are as efficient as possible is crucial.
5. Limit Search Depth
Introducing a maximum depth could prevent the search from going too deep into less relevant parts of Wikipedia. This could be a configurable parameter based on average path lengths observed in Wikipedia.