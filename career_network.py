import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter
import numpy as np

# Career milestones
career_data = [
    ('BS', 'BS\nUndergrad\n2010-2014'),
    ('MS', 'MS\nGrad School\n2014-2016'),
    ('PhD', 'PhD\nVandy\n2016-2021'),
    ('Postdoc', 'Postdoc\nUVA\n2021-2023'),
    ('Faculty', 'Faculty\nUVA\n2023-present')
]

# Topics added at each career stage
topic_data = {
    'BS': ['Cell Biology', 'Programming'],
    'MS': ['Microscopy', 'Image Analysis'],
    'PhD': ['Computational\nModeling', 'Systems Biology', 'Cancer Research'],
    'Postdoc': ['Machine Learning', 'Network Analysis'],
    'Faculty': ['Teaching', 'Mentoring']
}

# Topic connections (when topics connect to each other)
topic_connections = [
    ('Programming', 'Image Analysis'),
    ('Image Analysis', 'Computational\nModeling'),
    ('Computational\nModeling', 'Systems Biology'),
    ('Cell Biology', 'Cancer Research'),
    ('Computational\nModeling', 'Machine Learning'),
    ('Systems Biology', 'Network Analysis'),
    ('Machine Learning', 'Network Analysis'),
    ('Cancer Research', 'Teaching'),
    ('Machine Learning', 'Teaching')
]

# Initialize graph
G = nx.Graph()

# Fixed positions for timeline layout
def get_timeline_positions(G, career_nodes):
    pos = {}
    
    # Career nodes in a horizontal line
    for i, (node_id, _) in enumerate(career_nodes):
        pos[node_id] = (i * 2, 0)
    
    # Topic nodes staggered above
    topic_y = 1.5
    for i, (career_id, _) in enumerate(career_nodes):
        if career_id in topic_data:
            topics = topic_data[career_id]
            for j, topic in enumerate(topics):
                pos[topic] = (i * 2, topic_y + j * 0.8)
    
    return pos

# Animation function
def create_animation(save_path='career_network.gif'):
    fig, ax = plt.subplots(figsize=(14, 10))
    
    # Total stages: 5 career stages + connections reveal + force layout transition
    n_career_stages = len(career_data)
    n_total_frames = n_career_stages + 10 + 30  # career stages + pause + force animation
    
    # Keep track of what's been added
    current_nodes = []
    current_edges = []
    
    # Timeline positions
    timeline_pos = None
    
    # Force layout positions (will be computed later)
    force_pos = None
    
    def init():
        ax.clear()
        ax.set_xlim(-2, 10)
        ax.set_ylim(-2, 8)
        ax.axis('off')
        return []
    
    def update(frame):
        ax.clear()
        ax.set_xlim(-2, 10)
        ax.set_ylim(-2, 8)
        ax.axis('off')
        
        nonlocal timeline_pos, force_pos, current_nodes, current_edges
        
        # Phase 1: Add career stages sequentially (frames 0-4)
        if frame < n_career_stages:
            stage = frame
            
            # Add career node
            career_id, career_label = career_data[stage]
            if career_id not in current_nodes:
                current_nodes.append(career_id)
                G.add_node(career_id, label=career_label, type='career')
            
            # Add topics for this stage
            if career_id in topic_data:
                for topic in topic_data[career_id]:
                    if topic not in current_nodes:
                        current_nodes.append(topic)
                        G.add_node(topic, label=topic, type='topic')
                        current_edges.append((career_id, topic))
                        G.add_edge(career_id, topic)
            
            # Update timeline positions
            timeline_pos = get_timeline_positions(G, career_data[:stage+1])
            
            # Add topic connections that are now valid
            for source, target in topic_connections:
                if source in current_nodes and target in current_nodes:
                    if (source, target) not in current_edges and (target, source) not in current_edges:
                        current_edges.append((source, target))
                        G.add_edge(source, target)
            
            pos = timeline_pos
            
        # Phase 2: Hold on timeline (frames 5-14)
        elif frame < n_career_stages + 10:
            pos = timeline_pos
            
        # Phase 3: Animate to force layout (frames 15-44)
        else:
            # Compute force layout once
            if force_pos is None:
                force_pos = nx.spring_layout(G, k=1.5, iterations=50, seed=42)
            
            # Interpolate between timeline and force layout
            progress = (frame - n_career_stages - 10) / 30
            progress = min(1.0, progress)
            
            # Ease-out cubic for springy effect
            eased_progress = 1 - (1 - progress) ** 3
            
            pos = {}
            for node in G.nodes():
                if node in timeline_pos and node in force_pos:
                    x1, y1 = timeline_pos[node]
                    x2, y2 = force_pos[node]
                    pos[node] = (
                        x1 + (x2 * 5 - x1) * eased_progress,  # Scale force layout
                        y1 + (y2 * 5 - y1) * eased_progress
                    )
            
            # Adjust view for force layout
            ax.set_xlim(-3, 8)
            ax.set_ylim(-3, 8)
        
        # Draw network
        career_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'career']
        topic_nodes = [n for n in G.nodes() if G.nodes[n].get('type') == 'topic']
        
        # Draw edges
        nx.draw_networkx_edges(G, pos, alpha=0.4, width=2, ax=ax)
        
        # Draw career nodes (blue squares)
        nx.draw_networkx_nodes(G, pos, nodelist=career_nodes, 
                               node_color='#4A90E2', node_shape='s',
                               node_size=1200, ax=ax)
        
        # Draw topic nodes (red circles)
        nx.draw_networkx_nodes(G, pos, nodelist=topic_nodes,
                               node_color='#E94B3C', node_shape='o',
                               node_size=800, ax=ax)
        
        # Draw labels
        labels = {n: G.nodes[n]['label'] for n in G.nodes()}
        nx.draw_networkx_labels(G, pos, labels, font_size=7,
                               font_color='white', font_weight='bold', ax=ax)
        
        # Add title showing current phase
        if frame < n_career_stages:
            ax.set_title(f"Stage {frame + 1}/{n_career_stages}: {career_data[frame][1].split(chr(10))[0]}",
                        fontsize=14, fontweight='bold')
        elif frame < n_career_stages + 10:
            ax.set_title("Complete Career Timeline", fontsize=14, fontweight='bold')
        else:
            ax.set_title("Force-Directed Network View", fontsize=14, fontweight='bold')
        
        return []
    
    anim = FuncAnimation(fig, update, init_func=init, frames=n_total_frames,
                        interval=500, blit=False, repeat=True)
    
    # Save as GIF
    writer = PillowWriter(fps=2)
    anim.save(save_path, writer=writer)
    print(f"Animation saved to {save_path}")
    
    plt.close()
    return anim

# Create the animation
if __name__ == "__main__":
    create_animation('career_network_animation.gif')
    
    # Also create a static final frame
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Build complete graph
    G_full = nx.Graph()
    for career_id, career_label in career_data:
        G_full.add_node(career_id, label=career_label, type='career')
        if career_id in topic_data:
            for topic in topic_data[career_id]:
                G_full.add_node(topic, label=topic, type='topic')
                G_full.add_edge(career_id, topic)
    
    for source, target in topic_connections:
        G_full.add_edge(source, target)
    
    # Timeline layout
    timeline_pos = get_timeline_positions(G_full, career_data)
    
    career_nodes = [n for n in G_full.nodes() if G_full.nodes[n].get('type') == 'career']
    topic_nodes = [n for n in G_full.nodes() if G_full.nodes[n].get('type') == 'topic']
    
    # Plot timeline
    ax1.set_xlim(-2, 10)
    ax1.set_ylim(-2, 8)
    ax1.axis('off')
    ax1.set_title("Timeline Layout", fontsize=14, fontweight='bold')
    
    nx.draw_networkx_edges(G_full, timeline_pos, alpha=0.4, width=2, ax=ax1)
    nx.draw_networkx_nodes(G_full, timeline_pos, nodelist=career_nodes,
                          node_color='#4A90E2', node_shape='s', node_size=1200, ax=ax1)
    nx.draw_networkx_nodes(G_full, timeline_pos, nodelist=topic_nodes,
                          node_color='#E94B3C', node_shape='o', node_size=800, ax=ax1)
    labels = {n: G_full.nodes[n]['label'] for n in G_full.nodes()}
    nx.draw_networkx_labels(G_full, timeline_pos, labels, font_size=7,
                           font_color='white', font_weight='bold', ax=ax1)
    
    # Plot force layout
    force_pos = nx.spring_layout(G_full, k=1.5, iterations=50, seed=42)
    force_pos_scaled = {n: (x*5, y*5) for n, (x, y) in force_pos.items()}
    
    ax2.set_xlim(-3, 8)
    ax2.set_ylim(-3, 8)
    ax2.axis('off')
    ax2.set_title("Force-Directed Layout", fontsize=14, fontweight='bold')
    
    nx.draw_networkx_edges(G_full, force_pos_scaled, alpha=0.4, width=2, ax=ax2)
    nx.draw_networkx_nodes(G_full, force_pos_scaled, nodelist=career_nodes,
                          node_color='#4A90E2', node_shape='s', node_size=1200, ax=ax2)
    nx.draw_networkx_nodes(G_full, force_pos_scaled, nodelist=topic_nodes,
                          node_color='#E94B3C', node_shape='o', node_size=800, ax=ax2)
    nx.draw_networkx_labels(G_full, force_pos_scaled, labels, font_size=7,
                           font_color='white', font_weight='bold', ax=ax2)
    
    plt.tight_layout()
    plt.savefig('career_network_static.png', dpi=300, bbox_inches='tight')
    print("Static comparison saved to career_network_static.png")
    plt.show()