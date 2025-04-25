import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
def calculate_critical_path(activities):

    G = nx.DiGraph()
    
    for activity, info in activities.items():
        G.add_node(activity, duration=info['duration'])
    
    for activity, info in activities.items():
        for dependency in info['depends_on']:
            G.add_edge(dependency, activity)
    
    ES = {}
    EF = {}
    
    for activity in nx.topological_sort(G):
        predecessors = list(G.predecessors(activity))
        if not predecessors:
            ES[activity] = 0
        else:
            ES[activity] = max(EF[pred] for pred in predecessors)
        
        EF[activity] = ES[activity] + activities[activity]['duration']
    
    LF = {}
    LS = {}
    
    project_completion = max(EF.values())
    
    for activity in reversed(list(nx.topological_sort(G))):
        successors = list(G.successors(activity))
        if not successors:
            LF[activity] = project_completion
        else:
            LF[activity] = min(LS[succ] for succ in successors)
        
        LS[activity] = LF[activity] - activities[activity]['duration']
    
    float_values = {}
    for activity in activities:
        float_values[activity] = LS[activity] - ES[activity]
    
    critical_path = [activity for activity, float_val in float_values.items() if float_val == 0]
    critical_path.sort() 
    
    return critical_path, ES, EF, LS, LF, float_values

activities = {
    'A': {'depends_on': [], 'duration': 3},
    'B': {'depends_on': ['A'], 'duration': 4},
    'C': {'depends_on': ['A'], 'duration': 6},
    'D': {'depends_on': ['B'], 'duration': 3},
    'E': {'depends_on': ['A'], 'duration': 2},
    'F': {'depends_on': ['C', 'D'], 'duration': 4},
    'G': {'depends_on': ['E'], 'duration': 7},
    'H': {'depends_on': ['B'], 'duration': 8},
    'I': {'depends_on': ['H'], 'duration': 2},
    'J': {'depends_on': ['F', 'H'], 'duration': 3},
    'K': {'depends_on': ['F', 'G'], 'duration': 10},
    'L': {'depends_on': ['I'], 'duration': 5},
    'M': {'depends_on': ['J'], 'duration': 7},
    'N': {'depends_on': ['L', 'M', 'K'], 'duration': 2}
}

critical_path, ES, EF, LS, LF, float_values = calculate_critical_path(activities)

critical_path_str = "-".join(critical_path)
print(f"Critical Path: {critical_path_str}")

print("\nActivity Details:")
print("Activity | ES | EF | LS | LF | Float | Critical")
print("-" * 55)
for activity in sorted(activities.keys()):
    is_critical = "Yes" if activity in critical_path else "No"
    print(f"{activity:8} | {ES[activity]:2} | {EF[activity]:2} | {LS[activity]:2} | {LF[activity]:2} | {float_values[activity]:5} | {is_critical}")

def draw_precedence_diagram():

    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 8))
    
    G = nx.DiGraph()
    
    for activity, info in activities.items():
        G.add_node(activity, duration=info['duration'])
        for dep in info['depends_on']:
            G.add_edge(dep, activity)
    
    pos = nx.spring_layout(G, seed=42)
    
    critical_nodes = set(critical_path)
    non_critical_nodes = set(activities.keys()) - critical_nodes
    
    nx.draw_networkx_nodes(G, pos, nodelist=list(non_critical_nodes), 
                          node_color='skyblue', node_size=700, ax=ax1)
    
    nx.draw_networkx_nodes(G, pos, nodelist=list(critical_nodes), 
                          node_color='lightcoral', node_size=700, ax=ax1)
    
    nx.draw_networkx_edges(G, pos, arrows=True, ax=ax1)
    
    labels = {activity: f"{activity}\n({info['duration']})" 
             for activity, info in activities.items()}
    nx.draw_networkx_labels(G, pos, labels=labels, ax=ax1)
    
    ax1.set_title("Complete Project Network\n(Red nodes are on the critical path)")
    ax1.axis('off')
    
    CP = nx.DiGraph()
    
    cp_sequence = []
    all_activities = list(nx.topological_sort(G))
    for activity in all_activities:
        if activity in critical_path:
            cp_sequence.append(activity)
    
    for activity in cp_sequence:
        CP.add_node(activity, duration=activities[activity]['duration'])
    
    for i in range(len(cp_sequence) - 1):
        CP.add_edge(cp_sequence[i], cp_sequence[i+1])
    
    pos_cp = {}
    for i, node in enumerate(cp_sequence):
        pos_cp[node] = np.array([i, 0])
    
    nx.draw_networkx_nodes(CP, pos_cp, node_size=700, node_color='lightcoral', ax=ax2)
    nx.draw_networkx_edges(CP, pos_cp, arrows=True, width=2, ax=ax2)
    nx.draw_networkx_labels(CP, pos_cp, labels={activity: f"{activity}\n({activities[activity]['duration']})" 
                                               for activity in cp_sequence}, ax=ax2)
    
    ax2.set_title(f"Critical Path Sequence: {'-'.join(cp_sequence)}")
    ax2.axis('off')
    
    plt.tight_layout()
    plt.show()

draw_precedence_diagram()
