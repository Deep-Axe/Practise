from collections import defaultdict
import math

def binomial_coefficient(n, k):
    if k > n:
        return 0
    return math.comb(n, k)

def expected_minimum(n, i):
    expected_value = 0
    total_combinations = binomial_coefficient(n, i)
    for k in range(1, n + 1):
        favorable_combinations = binomial_coefficient(n - k, i - 1)
        probability_k_is_min = favorable_combinations / total_combinations
        expected_value += k * probability_k_is_min
    return expected_value

def calculate_weight(n):
    weights = [0] + [expected_minimum(n, i) for i in range(1, n + 1)]
    return weights

def is_valid_edge(graph, u, v):
    if len(graph[u]) == 1:
        return True

    def dfs_count(node, visited):
        visited.add(node)
        count = 1
        for neighbor in graph[node]:
            if neighbor not in visited:
                count += dfs_count(neighbor, visited)
        return count

    visited_before = set()
    count_before = dfs_count(u, visited_before)
    
    graph[u].remove(v)
    graph[v].remove(u)
    
    visited_after = set()
    count_after = dfs_count(u, visited_after)
    
    graph[u].append(v)
    graph[v].append(u)
    
    return count_before == count_after

def print_eulerian_path_and_calculate_c1(graph, weights, u):
    total_cost = 0
    path = []
    visited_edges = set()

    def dfs(current_node):
        nonlocal total_cost
        for v in graph[current_node]:
            if is_valid_edge(graph, current_node, v):
                edge_weight = math.ceil(weights[current_node]) + math.ceil(weights[v])
                total_cost += edge_weight
                visited_edges.add((current_node, v))
                visited_edges.add((v, current_node))
                graph[current_node].remove(v)
                graph[v].remove(current_node)
                path.append(v)
                dfs(v)

    path.append(u)
    dfs(u)

    # Backtrack logic based on the last node and the starting node
    if len(path) > 1:
        last_node = path[-1]
        start_node = path[0]
        i = len(graph)  # Since we added edges from 1 to n, i is n

        # Condition 1: If ending at a node other than 1 or i
        if last_node != 1 and last_node != i:
            edge_weight = math.ceil(weights[last_node]) + math.ceil(weights[start_node])
            total_cost += edge_weight

        # Condition 2: If ending at node i
        elif last_node == i:
            if start_node == 1:
                # Go to (i-1) first
                edge_weight = math.ceil(weights[last_node]) + math.ceil(weights[i-1])
                total_cost += edge_weight
                # Then go back to 1
                edge_weight = math.ceil(weights[i-1]) + math.ceil(weights[start_node])
                total_cost += edge_weight
            else:
                edge_weight = math.ceil(weights[last_node]) + math.ceil(weights[start_node])
                total_cost += edge_weight

        # Condition 3: If ending at node 1
        elif last_node == 1:
            if start_node == i:
                # Go to (i-1) first
                edge_weight = math.ceil(weights[last_node]) + math.ceil(weights[i-1])
                total_cost += edge_weight
                # Then go to i
                edge_weight = math.ceil(weights[i-1]) + math.ceil(weights[start_node])
                total_cost += edge_weight
            else:
                edge_weight = math.ceil(weights[last_node]) + math.ceil(weights[start_node])
                total_cost += edge_weight

    return total_cost

def find_starting_node(graph, n):
    odd_degree_nodes = [i for i in range(1, n + 1) if len(graph[i]) % 2 == 1]
    if len(odd_degree_nodes) == 2:
        return odd_degree_nodes[0]
    return 1

def eulerian_path(C0):
    n = (C0 % 17) + 3
    graph = defaultdict(list)
    for i in range(1, n + 1):
        for j in range(i + 1, n + 1):
            if not (i == 1 and j == n):
                graph[i].append(j)
                graph[j].append(i)
    weights = calculate_weight(n)
    start_node = find_starting_node(graph, n)
    C1 = print_eulerian_path_and_calculate_c1(graph, weights, start_node)
    return C1

def c0_cost(k):
    """
    The minimum cost for the C0 path graph is the number of edges,
    which equals the input value C0.
    """
    C0 = k
    return C0

def c1_cost(c0):
    """
    Calculate C1 based on the C0 input.
    """
    return eulerian_path(c0)

MOD = 10007

def binomial_coefficient(n, k):
    if k > n or k < 0:
        return 0
    return math.comb(n, k)

def non_crossing_partitions(N, k):
    if k == 0:
        return 1  
    return (pow(k + 1, -1, MOD) * binomial_coefficient(N - 3, k) * binomial_coefficient(N + k - 1, k)) 

def total_non_crossing_diagonals(N):

    total = 0
    for k in range(0, N - 2): 
        total = (total + non_crossing_partitions(N, k))
    return total

def c3_cost(c1):
    c2 = (c1 % 107) + 3
    c3 = (total_non_crossing_diagonals(c2))
    c3 = (c3 % 10007) + 3
    return c3

def main(k):
    cost_c0 = c0_cost(k)
    cost_c1 = c1_cost(cost_c0)
    cost_c3 = c3_cost(cost_c1)
    print(f"{cost_c0} {cost_c1} {cost_c3}")

if __name__ == "__main__":
    k = eval(input().strip())
    main(k)
