import math

def games_needed(true_rate, alpha=0.01, power=0.5):
    """Paired games needed to separate `true_rate` from 0.5.

    power=0.5 is the point where the expected result lands exactly on the threshold;
    power=0.8 is where a single run clears it four times out of five.
    """
    z_a = 2.576 if alpha == 0.01 else 1.96
    z_b = {0.5: 0.0, 0.8: 0.842, 0.9: 1.282}[power]
    return math.ceil(((z_a + z_b) / (2 * (true_rate - 0.5))) ** 2)

print(f"{'true win rate':>14}  {'p<0.01, 50% power':>18}  {'p<0.01, 80% power':>18}")
for r in (0.55, 0.60, 0.65, 0.70, 0.80):
    print(f"{r:>14.2f}  {games_needed(r):>18,}  {games_needed(r, power=0.8):>18,}")

def z_score(wins, draws, n):
    """Draws count as half. Two-sided z against a fair coin."""
    points = wins + draws / 2
    return (points - n / 2) / math.sqrt(n / 4)

print()
print('192 games, 0 wins   :  z =', round(z_score(0, 0, 192), 1))
print('192 games, 118 wins :  z =', round(z_score(118, 0, 192), 1))
print('192 games, 105 wins :  z =', round(z_score(105, 0, 192), 1), ' <- not a finding')

# The comparison in the form worth reporting: half-point rate, sample size, z, and
# whether the change is even on the execution path.
def report(label, wins, losses, draws):
    n = wins + losses + draws
    half = (wins + draws / 2) / n
    z = z_score(wins, draws, n)
    reach = 'yes' if draws < n * 0.1 else 'NO - mostly identical games'
    print(f"{label:<24} {wins:>4}-{losses:<4}-{draws:<4}  half {half:6.1%}  z {z:6.2f}  on path: {reach}")

report('published agent', 0, 192, 0)
report('a knob variant', 33, 23, 328)
report('a real change', 118, 74, 0)