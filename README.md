
# Wikipedia Search Crawler

## Project Overview
The Wikipedia Search Crawler is designed to find the shortest path between two Wikipedia articles using various graph search algorithms. This tool utilizes Python's asynchronous capabilities to fetch and parse web pages, constructing a graph that represents the links between Wikipedia pages, and then applies search algorithms to determine the path.

## Features
- **Graph Construction**: Dynamically builds a graph by fetching Wikipedia pages starting from the specified start and end pages, exploring up to a user-defined depth.
- **Progress Tracking**: Uses a progress bar to provide real-time feedback on the number of pages processed during graph construction.
- **Error Handling**: Robust error handling to ensure stability across network failures and data parsing issues.

### Algorithms Implemented
1. **Breadth-First Search (BFS)**: Used for unweighted graphs to find the shortest path in terms of the number of edges traversed.
2. **Depth-First Search (DFS)**: Used to explore as far as possible along each branch before backtracking, useful for finding all possible paths (with modifications to limit depth).
3. **Dijkstra’s Algorithm**: An algorithm for finding the shortest paths between nodes in a graph, which may be weighted.
4. **A-Star (A*) Search**: Utilizes heuristics to efficiently find the shortest path by estimating the cost to get from the current node to the end node.

### Test Cases
The project was tested using a variety of start and end pages on Wikipedia, along with different search algorithms to ensure reliability and accuracy. Tests focused on verifying the correct paths were found, the efficiency of the algorithms, and handling of non-existent or looped paths.

### Reproducing Test Results
To reproduce the test results, run the crawler with different start and end Wikipedia articles and experiment with the available search algorithms. Ensure that the crawler successfully constructs the graph and finds the appropriate paths.

## Installation

### Prerequisites
- Python 3.7 or higher
- Pip for Python package management

### Dependencies
Install the required Python packages using pip:
```bash
pip install -r requirements.txt
``

### Setting Up
1. **Clone the repository**:
   ```bash
   git clone https://github.com/memaxo/WikipediaGame.git
   cd wikipedia-search-crawler
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Environment Variables**:
   Create a `.env` file in the root directory and specify the following variables:
   ```plaintext
   RATE_LIMIT=5/minute  # Adjust rate limiting for API requests as needed
   ```

## Usage

### Command-Line Interface
To run the crawler directly from the command line and find paths between Wikipedia pages:
```bash
python crawler.py --start_page "Start_Article" --end_page "End_Article" --algorithm bfs
```
Replace `"Start_Article"` and `"End_Article"` with your chosen Wikipedia pages, and select an algorithm (`bfs`, `dfs`, `dijkstra`, `a_star`).