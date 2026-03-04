"""
Cell Transport Potential (CTrP) Visualization - Pedagogical Version

Shows step-by-step:
1. Markov chain with ~10 states
2. Random walk from each state
3. Expected steps before absorption (fundamental matrix N)
4. Distance matrix D
5. CTrP = N · D (inner product)
"""

from manim import *
import numpy as np
from itertools import combinations


class CTrPFullPipeline(Scene):
    """
    Complete CTrP calculation pipeline with visual demonstration
    """

    def construct(self):
        # Setup: Create a 10-state Markov chain
        n_states = 10
        self.states = [f"S{i}" for i in range(n_states)]

        # Create a realistic transition matrix (preferential transitions to nearby states)
        P = self.create_transition_matrix(n_states)

        # Euclidean distances (mock PCA distances)
        distances = self.create_distance_matrix(n_states)

        # === PART 1: Markov Chain Visualization ===
        self.show_introduction()

        # === PART 2: Fundamental Matrix Calculation ===
        self.demonstrate_fundamental_matrix(P, n_states)

        # === PART 3: Distance Matrix ===
        self.demonstrate_distance_matrix(distances, n_states)

        # === PART 4: CTrP Calculation ===
        self.demonstrate_ctrp_calculation(P, distances, n_states)

    def show_introduction(self):
        """Title and overview"""
        self.clear()

        title = Text("Cell Transport Potential (CTrP)",
                     font_size=44, color=BLUE, weight=BOLD)
        subtitle = Text("Expected distance traveled, weighted by time in each state",
                        font_size=24, color=GRAY_B)

        formula = MathTex(
            r"\text{CTrP}_i = \sum_j N_{ij} \cdot D_{ij}", font_size=36, color=YELLOW)

        vgroup = VGroup(title, subtitle, formula).arrange(DOWN, buff=0.5)

        self.play(FadeIn(vgroup))
        self.wait(2)
        self.clear()

    def create_transition_matrix(self, n_states):
        """Create a realistic transition matrix with absorbing state"""
        P = np.zeros((n_states, n_states))

        for i in range(n_states - 1):  # All but last state (absorbing)
            # Can transition to itself or nearby states
            for j in range(n_states):
                dist_to_j = abs(i - j)
                if j == n_states - 1:  # Higher prob to absorbing state
                    P[i, j] = 0.15
                elif dist_to_j == 0:
                    P[i, j] = 0.5
                elif dist_to_j == 1:
                    P[i, j] = 0.2
                elif dist_to_j == 2:
                    P[i, j] = 0.1
                else:
                    P[i, j] = 0.05 / (n_states - 4)

        # Last state is absorbing
        P[-1, -1] = 1.0

        # Normalize each row
        P = P / P.sum(axis=1, keepdims=True)

        return P

    def create_distance_matrix(self, n_states):
        """Create mock distance matrix (Euclidean in PCA space)"""
        # Simple: distance = |i - j| scaled + noise
        D = np.zeros((n_states, n_states))
        for i in range(n_states):
            for j in range(n_states):
                D[i, j] = abs(i - j) * 1.5 + np.random.uniform(0, 0.5)
        return D

    def create_markov_chain_visualization(self, n_states, highlighted_state=None):
        """Create visual representation of Markov chain graph"""
        # Arrange states in a circle or line
        radius = 3
        angles = np.linspace(0, 2*np.pi, n_states, endpoint=False)

        positions = {}
        nodes = {}

        for i, state in enumerate(self.states):
            x = radius * np.cos(angles[i])
            y = radius * np.sin(angles[i])
            positions[state] = np.array([x, y, 0])

            # Color: highlight specified state
            if i == highlighted_state:
                color = RED_E
                fill_opacity = 0.9
            elif i == n_states - 1:  # Absorbing state
                color = GREEN_E
                fill_opacity = 0.8
            else:
                color = BLUE_E
                fill_opacity = 0.6

            circle = Circle(radius=0.35, color=color,
                            fill_opacity=fill_opacity)
            circle.move_to(positions[state])
            label = Text(state, font_size=12, color=WHITE, weight=BOLD)
            label.move_to(positions[state])

            nodes[state] = VGroup(circle, label)

        # Create edges (show all transitions)
        edges = []
        for i, from_state in enumerate(self.states):
            for j, to_state in enumerate(self.states):
                if i != j:
                    edge = Arrow(positions[from_state], positions[to_state],
                                 stroke_width=1, color=GRAY_A, buff=0.4)
                    edges.append(edge)

        return nodes, positions, edges

    def simulate_random_walk(self, P, start_state, n_steps=50):
        """Simulate a random walk from starting state"""
        n_states = len(P)
        current = start_state
        path = [current]

        for step in range(n_steps):
            # Random transition based on P[current]
            next_state = np.random.choice(n_states, p=P[current])
            path.append(next_state)
            current = next_state

            if current == n_states - 1:  # Absorbed
                break

        return path

    def demonstrate_fundamental_matrix(self, P, n_states):
        """Demonstrate fundamental matrix calculation"""
        self.clear()

        # Title
        title = Text("Step 1: Fundamental Matrix N",
                     font_size=36, color=BLUE, weight=BOLD)
        subtitle = Text("N = (I - Q)⁻¹   →   Expected steps in each state before absorption",
                        font_size=20, color=GRAY_B)
        vgroup_title = VGroup(title, subtitle).arrange(
            DOWN, buff=0.3).to_edge(UP, buff=0.3)
        self.add(vgroup_title)

        # Create Markov chain on left
        nodes, positions, edges = self.create_markov_chain_visualization(
            n_states)

        graph = VGroup(*edges, *nodes.values()
                       ).scale(0.6).to_edge(LEFT, buff=1)
        self.add(graph)

        # Create fundamental matrix N
        Q = P[:-1, :-1]  # Transient submatrix
        I = np.eye(n_states - 1)
        N_transient = np.linalg.inv(I - Q)

        # Build full N (with absorbing state row/col as 0)
        N = np.zeros((n_states, n_states))
        N[:-1, :-1] = N_transient

        # Display and fill matrix row by row
        matrix_display = self.create_matrix_display(N, "N", position=RIGHT)
        self.add(matrix_display)

        # Animate: for each starting state, show random walk and update matrix
        # Show first 5 states to keep animation reasonable
        for i in range(min(5, n_states - 1)):
            # Highlight starting state
            state_label = Text(
                f"Starting from {self.states[i]}:", font_size=18, color=YELLOW)
            state_label.next_to(graph, DOWN, buff=0.5)
            self.add(state_label)

            # Simulate random walk
            path = self.simulate_random_walk(P, i, n_steps=30)
            self.animate_random_walk(path, nodes, positions, graph)

            # Show expected steps for this state
            expected_steps = N[i, :n_states-1]  # Steps to each transient state
            steps_text = Text(
                f"Expected steps to each state: {[f'{s:.2f}' for s in expected_steps[:3]]}...",
                font_size=14, color=ORANGE
            ).next_to(state_label, DOWN, buff=0.2)
            self.add(steps_text)

            self.wait(1)
            self.remove(state_label, steps_text)

        self.wait(1)

    def demonstrate_distance_matrix(self, distances, n_states):
        """Demonstrate distance matrix"""
        self.clear()

        # Title
        title = Text("Step 2: Distance Matrix D",
                     font_size=36, color=BLUE, weight=BOLD)
        subtitle = Text("D_ij = Euclidean distance between states i and j (in PCA space)",
                        font_size=20, color=GRAY_B)
        vgroup_title = VGroup(title, subtitle).arrange(
            DOWN, buff=0.3).to_edge(UP, buff=0.3)
        self.add(vgroup_title)

        # Create Markov chain on left
        nodes, positions, edges = self.create_markov_chain_visualization(
            n_states)
        graph = VGroup(*edges, *nodes.values()
                       ).scale(0.6).to_edge(LEFT, buff=1)
        self.add(graph)

        # Display distance matrix
        matrix_display = self.create_matrix_display(
            distances, "D", position=RIGHT)
        self.add(matrix_display)

        # Animate: show distance calculations between highlighted states
        for i in range(min(5, n_states)):
            # Highlight state i
            state_label = Text(
                f"State {self.states[i]}:", font_size=18, color=YELLOW)
            state_label.next_to(graph, DOWN, buff=0.5)
            self.add(state_label)

            # Show distances to first 3 other states
            dist_text = Text(
                f"Distances to other states: {[f'{d:.2f}' for d in distances[i, :3]]}...",
                font_size=14, color=ORANGE
            ).next_to(state_label, DOWN, buff=0.2)
            self.add(dist_text)

            # Draw distance lines on graph (to a few other states)
            for j in [0, 2, 4]:
                if i != j:
                    line = Line(positions[self.states[i]], positions[self.states[j]],
                                color=YELLOW, stroke_width=2)
                    self.play(Create(line), run_time=0.3)

            self.wait(0.8)
            self.remove(state_label, dist_text)

        self.wait(1)

    def demonstrate_ctrp_calculation(self, P, distances, n_states):
        """Demonstrate CTrP calculation via matrix inner product"""
        self.clear()

        # Compute N and CTrP
        Q = P[:-1, :-1]
        I = np.eye(n_states - 1)
        N_transient = np.linalg.inv(I - Q)
        N = np.zeros((n_states, n_states))
        N[:-1, :-1] = N_transient

        # CTrP = row-wise inner product
        ctrp = np.array([np.dot(N[i], distances[i]) for i in range(n_states)])

        # Title
        title = Text("Step 3: Cell Transport Potential (CTrP)",
                     font_size=36, color=BLUE, weight=BOLD)
        subtitle = Text("CTrP_i = Σ_j N_ij · D_ij   (inner product)",
                        font_size=20, color=GRAY_B)
        vgroup_title = VGroup(title, subtitle).arrange(
            DOWN, buff=0.3).to_edge(UP, buff=0.3)
        self.add(vgroup_title)

        # Left: N matrix
        n_matrix = self.create_matrix_display(
            N, "N", position=np.array([-5, 0, 0]), scale=0.5)
        self.add(n_matrix)

        # Center: D matrix
        d_matrix = self.create_matrix_display(
            distances, "D", position=np.array([0, 0, 0]), scale=0.5)
        self.add(d_matrix)

        # Right: CTrP result
        ctrp_label = Text("CTrP", font_size=28, color=ORANGE, weight=BOLD)
        ctrp_label.to_edge(RIGHT, buff=1).shift(UP * 2)

        ctrp_values = VGroup(
            *[Text(f"CTrP[{self.states[i]}] = {ctrp[i]:.2f}",
                   font_size=14, color=interpolate_color(BLUE_D, ORANGE, ctrp[i]/ctrp.max()))
              for i in range(min(8, n_states))]
        ).arrange(DOWN, buff=0.2, aligned_edge=LEFT).next_to(ctrp_label, DOWN, buff=0.3)

        # Animate inner product calculation
        self.add(ctrp_label)

        for i in range(min(5, n_states)):
            # Highlight row i in N and D
            row_text = Text(
                f"Row {i}: {self.states[i]}", font_size=16, color=YELLOW, weight=BOLD)
            row_text.to_edge(DOWN, buff=0.5)
            self.add(row_text)

            # Show calculation: N[i] · D[i]
            calc_text = Text(
                f"Inner product: {N[i, :3]} · {distances[i, :3]} = {ctrp[i]:.3f}",
                font_size=12, color=GREEN
            ).next_to(row_text, DOWN, buff=0.2)
            self.add(calc_text)

            self.wait(0.5)
            self.remove(row_text, calc_text)

        self.play(FadeIn(ctrp_values))
        self.wait(2)

        # Final interpretation
        self.clear()

        interpretation = VGroup(
            Text("CTrP Summary", font_size=36, color=BLUE, weight=BOLD),
            Text("", font_size=1),  # Spacer
            Text("High CTrP states:", font_size=20, color=ORANGE, weight=BOLD),
            Text("• Spend more time traversing phenotypic space", font_size=16),
            Text("• Travel greater distances before absorption", font_size=16),
            Text("• Exhibit higher plasticity & multipotency", font_size=16),
            Text("", font_size=1),  # Spacer
            Text("Low CTrP states:", font_size=20, color=BLUE, weight=BOLD),
            Text("• Quickly absorbed into terminal states", font_size=16),
            Text("• Limited phenotypic exploration", font_size=16),
            Text("• Committed to differentiation", font_size=16),
        ).arrange(DOWN, buff=0.3, aligned_edge=LEFT).shift(LEFT * 2)

        self.play(FadeIn(interpretation))
        self.wait(3)

    def create_matrix_display(self, matrix, label, position, scale=0.4):
        """Create a visual matrix display"""
        n = min(5, matrix.shape[0])  # Show only first 5x5 to keep readable

        matrix_elements = []
        for i in range(n):
            for j in range(n):
                val = matrix[i, j]
                # Color by magnitude
                color = interpolate_color(BLACK, YELLOW, val / matrix.max())
                text = Text(f"{val:.2f}", font_size=8, color=color)
                matrix_elements.append(text)

        # Arrange in grid
        grid = VGroup(*matrix_elements).arrange_in_grid(rows=n,
                                                        cols=n, buff=0.1)

        title = Text(label, font_size=20, color=WHITE, weight=BOLD)
        group = VGroup(title, grid).arrange(DOWN, buff=0.2)
        group.scale(scale).move_to(position)

        return group

    def animate_random_walk(self, path, nodes, positions, graph):
        """Animate a random walk path"""
        for i in range(len(path) - 1):
            from_state = self.states[path[i]]
            to_state = self.states[path[i+1]]

            # Draw arrow from current to next
            arrow = Arrow(
                positions[from_state],
                positions[to_state],
                stroke_width=2,
                color=RED,
                buff=0.4
            )
            self.play(Create(arrow), run_time=0.1)
            self.remove(arrow)

            if path[i+1] == len(self.states) - 1:  # Absorbed
                break


if __name__ == "__main__":
    # Run with: manim -pql cell_transport_potential.py CTrPFullPipeline
    pass
