# Binary Search Strategy for Number Guessing

## Core Principle
Always guess the midpoint of the remaining valid range. This is optimal information theory — each guess eliminates exactly half the remaining candidates regardless of the outcome.

## Algorithm
1. Track `lo` (minimum possible) and `hi` (maximum possible)
2. Guess `mid = (lo + hi) // 2`
3. If "too high": set `hi = mid - 1`
4. If "too low": set `lo = mid + 1`
5. Repeat until correct

## Example (range 1–100)
- Guess 50 → too high → range becomes 1–49
- Guess 25 → too low → range becomes 26–49
- Guess 37 → too low → range becomes 38–49
- Guess 43 → correct in 4 attempts

## Why Midpoint Wins
Any other strategy leaves more candidates alive after a bad outcome. Guessing 70 in a 1–100 range means a "too low" leaves 30 candidates; a "too high" leaves 69. Midpoint (50) caps the worst case at 49 either way.

## Attempt Budget per Difficulty
- Easy (1–20, 10 tries): Binary search guarantees solution in ≤ 5 guesses — 5 spare attempts
- Normal (1–100, 8 tries): Binary search needs ≤ 7 guesses — comfortable margin
- Hard (1–200, 6 tries): Binary search needs ≤ 8 guesses — requires near-perfect play; start exactly at midpoint 100

## Score Optimization
Score formula: `max(10, 100 - 10 * attempt_number)`. Earlier wins score more.
- Win attempt 1 = 90 pts, attempt 2 = 80 pts, attempt 3 = 70 pts
- Binary search maximizes expected score by minimizing expected attempts
- Avoid guessing near boundaries (1 or 200) early — they yield little information

## Common Mistakes
- Guessing sequentially (1, 2, 3…) — O(n) instead of O(log n)
- Not updating bounds after each guess
- Guessing outside the remaining valid range (wastes information)
