import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── States ─────────────────────────────────────────────────────────────────────
S, I, R = 0, 1, 2
STATE_COLORS = ['#4CAF50', '#F44336', '#9E9E9E']
STATE_LABELS = ['Susceptible', 'Infected', 'Recovered']


# ══════════════════════════════════════════════════════════════════════════════
# Student class
# ══════════════════════════════════════════════════════════════════════════════

class Student:
    """
    A student moving freely around a continuous 2D room.

    Rules
    -----
    - Each round the student takes a random step (random walk) within
      the room bounds.
    - Interaction happens with any other student within `interaction_radius`.
      Up to `contacts` of those neighbors are randomly selected to play
      the finger-matching game with.
    - Finger-matching game: both players pick 1..fingers independently.
      Transmission occurs if they match. P(match) = 1/fingers = beta.
    - A Susceptible student who matches with an Infected neighbor
      becomes Infected next round.
    - An Infected student recovers (→ R) after `recovery_rounds` rounds.
    - Recovered students are immune.

    State changes are staged and applied simultaneously by Classroom.step().

    Attributes
    ----------
    x, y              : continuous position in [0, room_width] x [0, room_height]
    state             : SIR state (S=0, I=1, R=2)
    infected_for      : rounds spent in I state
    beta              : per-contact transmission prob = 1 / fingers
    contacts          : max neighbors to interact with per round
    recovery_rounds   : rounds in I before → R
    step_size         : max distance moved per round (random walk)
    interaction_radius: distance within which two students can interact
    room_width        : room x boundary
    room_height       : room y boundary
    """

    def __init__(self, x: float, y: float,
                 beta: float,
                 contacts: int = 2,
                 recovery_rounds: int = 3,
                 step_size: float = 1.0,
                 interaction_radius: float = 1.5,
                 room_width: float = 10.0,
                 room_height: float = 8.0):

        self.x = x
        self.y = y

        self.state = S
        self.infected_for = 0

        self.beta = beta
        self.contacts = contacts
        self.recovery_rounds = recovery_rounds
        self.step_size = step_size
        self.interaction_radius = interaction_radius
        self.room_width = room_width
        self.room_height = room_height

        # Staged next-round values
        self._next_state = S
        self._next_infected_for = 0
        self._next_x = x
        self._next_y = y

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

    @property
    def pos(self) -> tuple[float, float]:
        return (self.x, self.y)

    # ── Seeding ────────────────────────────────────────────────────────────────

    def infect(self):
        """Seed this student as Patient Zero before simulation starts."""
        self.state = I
        self.infected_for = 1
        self._next_state = I
        self._next_infected_for = 1

    # ── Movement ───────────────────────────────────────────────────────────────

    def stage_move(self):
        """
        Stage a random walk step. Direction is uniform in [0, 2π),
        step length is uniform in [0, step_size]. Position is clipped
        to room boundaries (reflecting wall behavior).
        """
        angle = random.uniform(0, 2 * np.pi)
        distance = random.uniform(0, self.step_size)
        new_x = self.x + distance * np.cos(angle)
        new_y = self.y + distance * np.sin(angle)

        # Reflect off walls
        self._next_x = float(np.clip(new_x, 0, self.room_width))
        self._next_y = float(np.clip(new_y, 0, self.room_height))

    # ── Interaction rules ──────────────────────────────────────────────────────

    def distance_to(self, other: 'Student') -> float:
        return np.sqrt((self.x - other.x) ** 2 + (self.y - other.y) ** 2)

    def is_near(self, other: 'Student') -> bool:
        return self.distance_to(other) <= self.interaction_radius

    def play_finger_game(self, other: 'Student') -> bool:
        """
        Both players independently pick a random integer in [1, 1/beta].
        Returns True (transmission) if numbers match.
        P(match) = beta = 1 / fingers.
        """
        fingers = round(1 / self.beta)
        my_fingers = random.randint(1, fingers)
        their_fingers = random.randint(1, fingers)
        return my_fingers == their_fingers

    def expose(self, susceptible: 'Student'):
        """
        Infected self plays the finger game with a susceptible neighbor.
        Stages the neighbor's infection if the game is won.
        """
        if self.is_infected and susceptible.is_susceptible:
            if self.play_finger_game(susceptible):
                susceptible._next_state = I
                susceptible._next_infected_for = 1

    def stage_next_state(self):
        """
        Stage own state transition based on current state.
        Exposure is staged separately via expose().
        """
        if self.state == S:
            pass  # stays S unless expose() marks us

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

    def interact(self, all_students: list['Student']):
        """
        If Infected, find all students within interaction_radius,
        randomly select up to `contacts` of them, and attempt to
        expose each susceptible one.
        """
        if self.is_infected:
            nearby = [s for s in all_students
                      if s is not self and self.is_near(s)]
            targets = random.sample(nearby, min(self.contacts, len(nearby)))
            for neighbor in targets:
                if neighbor.is_susceptible:
                    self.expose(neighbor)

    def advance(self):
        """Apply all staged changes. Called after all students have stepped."""
        self.state = self._next_state
        self.infected_for = self._next_infected_for
        self.x = self._next_x
        self.y = self._next_y

    def __repr__(self):
        return (f"Student(pos=({self.x:.1f},{self.y:.1f}), "
                f"state={STATE_LABELS[self.state]}, "
                f"infected_for={self.infected_for})")


# ══════════════════════════════════════════════════════════════════════════════
# Classroom class
# ══════════════════════════════════════════════════════════════════════════════

class Classroom:
    """
    A continuous 2D room of freely moving Students.

    Unlike the grid version, neighbors are determined dynamically each
    round based on proximity rather than fixed seat adjacency.
    """

    def __init__(self,
                 n_students: int = 30,
                 room_width: float = 10.0,
                 room_height: float = 8.0,
                 fingers: int = 2,
                 contacts: int = 2,
                 recovery_rounds: int = 3,
                 step_size: float = 1.0,
                 interaction_radius: float = 1.5,
                 initial_infected: int = 1,
                 seed: int = 42):

        self.n_students = n_students
        self.room_width = room_width
        self.room_height = room_height
        self.beta = 1.0 / fingers
        self.round = 0

        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)

        # Scatter students randomly across the room
        self.students: list[Student] = [
            Student(
                x=random.uniform(0, room_width),
                y=random.uniform(0, room_height),
                beta=self.beta,
                contacts=contacts,
                recovery_rounds=recovery_rounds,
                step_size=step_size,
                interaction_radius=interaction_radius,
                room_width=room_width,
                room_height=room_height,
            )
            for _ in range(n_students)
        ]

        # Seed infections
        for s in random.sample(self.students, initial_infected):
            s.infect()

        self.history: list[dict] = [self._snapshot()]

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _snapshot(self) -> dict:
        s_count = sum(1 for s in self.students if s.is_susceptible)
        i_count = sum(1 for s in self.students if s.is_infected)
        r_count = sum(1 for s in self.students if s.is_recovered)
        positions = [(s.x, s.y, s.state) for s in self.students]
        return {
            'round':     self.round,
            'S':         s_count,
            'I':         i_count,
            'R':         r_count,
            'positions': positions,
        }

    # ── Simulation step ────────────────────────────────────────────────────────

    def step(self):
        """
        One round: 4-phase update.
          1. stage_next_state  — each student stages recovery/staying
          2. stage_move        — each student stages their random walk step
          3. interact          — infected students attempt to expose neighbors
          4. advance           — all staged changes applied simultaneously
        """
        for s in self.students:
            s.stage_next_state()
        for s in self.students:
            s.stage_move()
        for s in self.students:
            s.interact(self.students)
        for s in self.students:
            s.advance()

        self.round += 1
        self.history.append(self._snapshot())

    def run(self, rounds: int = 10):
        for _ in range(rounds):
            self.step()

    # ── Reporting ──────────────────────────────────────────────────────────────

    def print_summary(self):
        print(f"\n{'─'*50}")
        print(f"  Moving SIR  |  n={self.n_students}  "
              f"room={self.room_width}×{self.room_height}")
        print(f"  β={self.beta:.2f}  step={self.students[0].step_size}  "
              f"radius={self.students[0].interaction_radius}")
        print(f"{'─'*50}")
        for h in self.history:
            i_bar = '█' * min(h['I'], 30)
            print(f"  Round {h['round']:2d} | "
                  f"S:{h['S']:2d}  I:{h['I']:2d} {i_bar:<30}  R:{h['R']:2d}")
        peak = max(self.history, key=lambda h: h['I'])
        final = self.history[-1]
        print(f"{'─'*50}")
        print(f"  Peak infected : {peak['I']} at round {peak['round']}")
        print(f"  Final S/I/R   : {final['S']} / {final['I']} / {final['R']}")
        print(f"{'─'*50}\n")


# ══════════════════════════════════════════════════════════════════════════════
# Plotting
# ══════════════════════════════════════════════════════════════════════════════

def plot_results(classroom: Classroom, save_path: str = 'sir_moving.png'):
    history = classroom.history
    n = classroom.n_students
    rounds = classroom.round

    S_curve = [h['S'] for h in history]
    I_curve = [h['I'] for h in history]
    R_curve = [h['R'] for h in history]
    xs = list(range(rounds + 1))

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
        f'Moving Student SIR ABM  |  n={n}  |  β={classroom.beta:.2f}  |  '
        f'radius={classroom.students[0].interaction_radius}',
        color='white', fontsize=13)
    ax.tick_params(colors='white')
    ax.spines[:].set_color('#444')
    ax.legend(facecolor='#16213e', labelcolor='white', fontsize=10)
    ax.set_xticks(xs)

    # Scatter snapshots
    for idx, rnd in enumerate(snap_rounds):
        ax2 = fig.add_subplot(2, n_snaps, n_snaps + idx + 1)
        ax2.set_facecolor('#16213e')
        ax2.set_xlim(0, classroom.room_width)
        ax2.set_ylim(0, classroom.room_height)

        positions = history[rnd]['positions']
        for x, y, state in positions:
            ax2.scatter(x, y, color=STATE_COLORS[state],
                        s=60, alpha=0.85, edgecolors='white', linewidths=0.3)

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


def sweep_step_size(step_sizes=(0.5, 1.0, 2.0), replicates=20, rounds=10,
                    save_path='sir_moving_sweep.png', **kwargs):
    """
    Parameter sweep over student step size.
    Small step_size ≈ clustered mixing; large ≈ well-mixed population.
    """
    fig, axes = plt.subplots(1, len(step_sizes), figsize=(14, 4), sharey=True)
    fig.patch.set_facecolor('#1a1a2e')
    n = kwargs.get('n_students', 30)

    for ax, step in zip(axes, step_sizes):
        ax.set_facecolor('#16213e')
        all_I = []
        for rep in range(replicates):
            c = Classroom(step_size=step, seed=rep, **kwargs)
            c.run(rounds)
            all_I.append([h['I'] for h in c.history])

        all_I = np.array(all_I)
        xs = np.arange(all_I.shape[1])
        mean_I = all_I.mean(axis=0)
        lo_I = np.percentile(all_I, 10, axis=0)
        hi_I = np.percentile(all_I, 90, axis=0)

        ax.fill_between(xs, lo_I, hi_I, alpha=0.25, color='#F44336')
        ax.plot(xs, mean_I, color='#F44336', lw=2.5)
        ax.set_title(f'step size = {step}', color='white', fontsize=11)
        ax.set_xlabel('Round', color='white')
        if step == step_sizes[0]:
            ax.set_ylabel('Infected', color='white')
        ax.set_ylim(0, n)
        ax.tick_params(colors='white')
        ax.spines[:].set_color('#444')

    fig.suptitle('Sweep: Step Size  (small=clustered, large=well-mixed)  '
                 '[shaded = 10–90th pct, 20 runs]',
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
        n_students=45,
        room_width=10.0,
        room_height=8.0,
        fingers=2,
        contacts=5,
        recovery_rounds=3,
        step_size=1.0,
        interaction_radius=1.5,
        initial_infected=1,
        seed=42,
    )
    classroom.run(rounds=10)
    classroom.print_summary()
    plot_results(classroom)

    sweep_step_size(
        step_sizes=(0.5, 1.5, 3.0),
        replicates=20,
        rounds=10,
        n_students=30,
        room_width=10.0,
        room_height=8.0,
        fingers=2,
        contacts=5,
        recovery_rounds=3,
        interaction_radius=1.5,
        initial_infected=1,
    )
