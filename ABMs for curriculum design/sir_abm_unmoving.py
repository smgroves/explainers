import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap

# ── States ─────────────────────────────────────────────────────────────────────
S, I, R = 0, 1, 2
STATE_COLORS = ['#4CAF50', '#F44336', '#9E9E9E']
STATE_LABELS = ['Susceptible', 'Infected', 'Recovered']


# ══════════════════════════════════════════════════════════════════════════════
# Student class
# ══════════════════════════════════════════════════════════════════════════════

class Student:
    """
    One student seated at (row, col) in a grid classroom.

    Rules
    -----
    - Each round, if Infected, the student randomly selects `contacts`
      neighbors to play the finger-matching game with.
    - Finger-matching game: both players independently pick 1..fingers.
      Transmission occurs if they match.  P(match) = 1/fingers = beta.
    - A Susceptible student who matches fingers with an Infected neighbor
      becomes Infected next round.
    - An Infected student recovers (→ R) after `recovery_rounds` rounds.
    - Recovered students are immune and cannot be re-infected.

    State changes are staged in _next_* attributes and applied
    simultaneously by Classroom.step() to avoid order-of-update artifacts.

    Attributes
    ----------
    row, col         : seat position in the grid
    state            : current SIR state (S=0, I=1, R=2)
    infected_for     : rounds spent in I state (resets on recovery)
    neighbors        : list of adjacent Student objects (set by Classroom)
    beta             : per-contact transmission probability = 1 / fingers
    contacts         : number of neighbors interacted with per round
    recovery_rounds  : rounds in I before transitioning to R
    """

    def __init__(self, row: int, col: int,
                 beta: float,
                 contacts: int = 2,
                 recovery_rounds: int = 3):
        self.row = row
        self.col = col
        self.state = S
        self.infected_for = 0
        self.neighbors: list['Student'] = []   # wired up by Classroom

        self.beta = beta
        self.contacts = contacts
        self.recovery_rounds = recovery_rounds

        # Staged next-round values
        self._next_state = S
        self._next_infected_for = 0

    # ── Convenience properties ─────────────────────────────────────────────────

    @property
    def is_susceptible(self) -> bool:
        return self.state == S

    @property
    def is_infected(self) -> bool:
        return self.state == I

    @property
    def is_recovered(self) -> bool:
        return self.state == R

    # ── Seeding ────────────────────────────────────────────────────────────────

    def infect(self):
        """Seed this student as Patient Zero before the simulation starts."""
        self.state = I
        self.infected_for = 1
        self._next_state = I
        self._next_infected_for = 1

    # ── Interaction rules ──────────────────────────────────────────────────────

    def play_finger_game(self, other: 'Student') -> bool:
        """
        Simulate one finger-matching interaction.

        Both players independently pick a random integer in [1, 1/beta].
        Returns True (transmission event) if both numbers match.
        P(match) = beta = 1 / fingers.
        """
        fingers = round(1 / self.beta)
        my_fingers = random.randint(1, fingers)
        their_fingers = random.randint(1, fingers)
        return my_fingers == their_fingers

    def expose(self, susceptible: 'Student'):
        """
        Infected self plays the finger game against a susceptible neighbor.
        If the game is won, stage the neighbor's infection.
        """
        if self.is_infected and susceptible.is_susceptible:
            if self.play_finger_game(susceptible):
                susceptible._next_state = I
                susceptible._next_infected_for = 1

    def stage_next_state(self):
        """
        Compute and stage this student's own next state based on current state.
        Exposure by neighbors is staged separately via expose().

        Called each round BEFORE interact() and advance().
        """
        if self.state == S:
            # No self-driven transition; stays S unless expose() marks us
            pass

        elif self.state == I:
            new_count = self.infected_for + 1
            if new_count > self.recovery_rounds:
                self._next_state = R
                self._next_infected_for = 0
            else:
                self._next_state = I
                self._next_infected_for = new_count

        elif self.state == R:
            self._next_state = R
            self._next_infected_for = 0

    def interact(self):
        """
        If Infected, randomly select up to `contacts` neighbors and
        attempt to expose each susceptible one via the finger-matching game.
        """
        if self.is_infected:
            targets = random.sample(
                self.neighbors,
                min(self.contacts, len(self.neighbors))
            )
            for neighbor in targets:
                if neighbor.is_susceptible:
                    self.expose(neighbor)

    def advance(self):
        """Apply staged next-round state. Called after all students have stepped."""
        self.state = self._next_state
        self.infected_for = self._next_infected_for

    def __repr__(self):
        return (f"Student(pos=({self.row},{self.col}), "
                f"state={STATE_LABELS[self.state]}, "
                f"infected_for={self.infected_for})")


# ══════════════════════════════════════════════════════════════════════════════
# Classroom class
# ══════════════════════════════════════════════════════════════════════════════

class Classroom:
    """
    A grid of Students. Manages neighbor wiring and SIR simulation steps.

    Neighborhood: Moore (8-connected) — each student can interact with
    immediate row, column, and diagonal neighbors.
    """

    def __init__(self,
                 rows: int = 5,
                 cols: int = 6,
                 fingers: int = 5,
                 contacts: int = 2,
                 recovery_rounds: int = 3,
                 initial_infected: int = 1,
                 seed: int = 42):

        self.rows = rows
        self.cols = cols
        self.beta = 1.0 / fingers
        self.round = 0

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Build grid
        self.grid: list[list[Student]] = [
            [Student(r, c, self.beta, contacts, recovery_rounds)
             for c in range(cols)]
            for r in range(rows)
        ]

        # Wire neighbors
        for r in range(rows):
            for c in range(cols):
                self.grid[r][c].neighbors = self._get_neighbors(r, c)

        # Seed infections
        all_cells = [(r, c) for r in range(rows) for c in range(cols)]
        for r, c in random.sample(all_cells, initial_infected):
            self.grid[r][c].infect()

        self.history: list[dict] = [self._snapshot()]

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _get_neighbors(self, row: int, col: int) -> list[Student]:
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = row + dr, col + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    neighbors.append(self.grid[nr][nc])
        return neighbors

    def _snapshot(self) -> dict:
        grid_state = np.array([[self.grid[r][c].state
                                for c in range(self.cols)]
                               for r in range(self.rows)])
        return {
            'round': self.round,
            'S':     int((grid_state == S).sum()),
            'I':     int((grid_state == I).sum()),
            'R':     int((grid_state == R).sum()),
            'grid':  grid_state,
        }

    @property
    def all_students(self) -> list[Student]:
        return [self.grid[r][c]
                for r in range(self.rows)
                for c in range(self.cols)]

    # ── Simulation step ────────────────────────────────────────────────────────

    def step(self):
        """Advance the simulation by one round (3-phase: stage → interact → advance)."""
        for student in self.all_students:
            student.stage_next_state()   # recovery / staying in state
        for student in self.all_students:
            student.interact()           # infected → expose susceptible neighbors
        for student in self.all_students:
            student.advance()            # apply all staged changes simultaneously

        self.round += 1
        self.history.append(self._snapshot())

    def run(self, rounds: int = 10):
        for _ in range(rounds):
            self.step()

    # ── Reporting ──────────────────────────────────────────────────────────────

    def print_summary(self):
        n = self.rows * self.cols
        print(f"\n{'─'*50}")
        print(f"  SIR Simulation  ({self.rows}×{self.cols} = {n} students)")
        print(f"  β={self.beta:.2f}  contacts/round={self.all_students[0].contacts}  "
              f"recovery={self.all_students[0].recovery_rounds} rounds")
        print(f"{'─'*50}")
        for h in self.history:
            s_bar = '█' * min(h['S'], 20)
            i_bar = '█' * min(h['I'], 20)
            r_bar = '█' * min(h['R'], 20)
            print(f"  Round {h['round']:2d} | "
                  f"S:{h['S']:2d} {s_bar:<20}  "
                  f"I:{h['I']:2d} {i_bar:<20}  "
                  f"R:{h['R']:2d}")
        peak = max(self.history, key=lambda h: h['I'])
        final = self.history[-1]
        print(f"{'─'*50}")
        print(f"  Peak infected : {peak['I']} at round {peak['round']}")
        print(f"  Final S/I/R   : {final['S']} / {final['I']} / {final['R']}")
        print(f"{'─'*50}\n")


# ══════════════════════════════════════════════════════════════════════════════
# Plotting helpers
# ══════════════════════════════════════════════════════════════════════════════

def plot_results(classroom: Classroom, save_path: str = 'sir_abm.png'):
    history = classroom.history
    n = classroom.rows * classroom.cols
    rounds = classroom.round

    S_curve = [h['S'] for h in history]
    I_curve = [h['I'] for h in history]
    R_curve = [h['R'] for h in history]
    xs = list(range(rounds + 1))

    cmap = ListedColormap(STATE_COLORS)
    snap_rounds = sorted({0, rounds // 4, rounds // 2,
                          3 * rounds // 4, rounds})
    n_snaps = len(snap_rounds)

    fig = plt.figure(figsize=(14, 9))
    fig.patch.set_facecolor('#1a1a2e')

    # Epidemic curve
    ax = fig.add_subplot(2, 1, 1)
    ax.set_facecolor('#16213e')
    ax.plot(xs, S_curve, color='#4CAF50', lw=2.5, label='Susceptible')
    ax.plot(xs, I_curve, color='#F44336', lw=2.5, label='Infected')
    ax.plot(xs, R_curve, color='#9E9E9E', lw=2.5, label='Recovered')
    ax.fill_between(xs, I_curve, alpha=0.15, color='#F44336')
    ax.set_xlim(0, rounds)
    ax.set_ylim(0, n + 1)
    ax.set_xlabel('Round', color='white', fontsize=11)
    ax.set_ylabel('Number of Students', color='white', fontsize=11)
    ax.set_title(
        f'Classroom SIR ABM  |  n={n}  |  β={classroom.beta:.2f}',
        color='white', fontsize=13)
    ax.tick_params(colors='white')
    ax.spines[:].set_color('#444')
    ax.legend(facecolor='#16213e', labelcolor='white', fontsize=10)
    ax.set_xticks(xs)

    # Grid snapshots
    for idx, rnd in enumerate(snap_rounds):
        ax2 = fig.add_subplot(2, n_snaps, n_snaps + idx + 1)
        ax2.imshow(history[rnd]['grid'], cmap=cmap, vmin=0, vmax=2,
                   interpolation='nearest')
        ax2.set_title(f'Round {rnd}', color='white', fontsize=9)
        ax2.set_xticks([])
        ax2.set_yticks([])
        ax2.spines[:].set_color('#444')

    patches = [mpatches.Patch(color=STATE_COLORS[i], label=STATE_LABELS[i])
               for i in range(3)]
    fig.legend(handles=patches, loc='lower center', ncol=3,
               facecolor='#1a1a2e', labelcolor='white', fontsize=9,
               bbox_to_anchor=(0.5, 0.01))

    plt.tight_layout(rect=[0, 0.05, 1, 1])
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"Saved {save_path}")


def sweep_seeds(seeds=(1, 2, 3), replicates=20, rounds=10,
                rows=5, cols=6, fingers=5, contacts=2, recovery_rounds=3,
                save_path='sir_sweep.png'):
    """Parameter sweep: vary number of initial infected students."""
    fig, axes = plt.subplots(1, len(seeds), figsize=(14, 4), sharey=True)
    fig.patch.set_facecolor('#1a1a2e')
    n = rows * cols

    for ax, n_seeds in zip(axes, seeds):
        ax.set_facecolor('#16213e')
        all_I = []
        for rep in range(replicates):
            c = Classroom(rows=rows, cols=cols, fingers=fingers,
                          contacts=contacts, recovery_rounds=recovery_rounds,
                          initial_infected=n_seeds, seed=rep)
            c.run(rounds)
            all_I.append([h['I'] for h in c.history])

        all_I = np.array(all_I)
        xs = np.arange(all_I.shape[1])
        mean_I = all_I.mean(axis=0)
        lo_I = np.percentile(all_I, 10, axis=0)
        hi_I = np.percentile(all_I, 90, axis=0)

        ax.fill_between(xs, lo_I, hi_I, alpha=0.25, color='#F44336')
        ax.plot(xs, mean_I, color='#F44336', lw=2.5)
        ax.set_title(f'{n_seeds} initial seed(s)', color='white', fontsize=11)
        ax.set_xlabel('Round', color='white')
        if n_seeds == seeds[0]:
            ax.set_ylabel('Infected', color='white')
        ax.set_ylim(0, n)
        ax.tick_params(colors='white')
        ax.spines[:].set_color('#444')

    fig.suptitle('Sweep: Initial Infected  (shaded = 10–90th pct, 20 runs)',
                 color='white', fontsize=12)
    plt.tight_layout()
    plt.savefig(save_path, dpi=150, bbox_inches='tight', facecolor='#1a1a2e')
    plt.close()
    print(f"Saved {save_path}")


# ══════════════════════════════════════════════════════════════════════════════
# Entry point
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    classroom = Classroom(
        rows=5, cols=8,
        fingers=2,
        contacts=4,
        recovery_rounds=3,
        initial_infected=1,
        seed=42,
    )
    classroom.run(rounds=10)
    classroom.print_summary()
    plot_results(classroom)
    sweep_seeds()
