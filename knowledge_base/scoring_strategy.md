# Scoring Strategy

## Number Guesser Scoring
- Win bonus: `max(10, 100 - 10 * attempt_number)` — awarded on correct guess
- Too high on even attempt: +5 points
- Too high on odd attempt: -5 points
- Too low: always -5 points

### Implication
- Guess correctly on attempt 1 = 90 pts, attempt 5 = 50 pts, attempt 10 = 10 pts
- Wrong guesses can cost points — don't be reckless
- Prefer "too high" on even attempts (free +5 bonus)
- Binary search minimizes attempts, maximizing win bonus

## Code Breaker Scoring
- Win bonus: `max(10, 120 - 10 * attempt_number)` — awarded only on win
- No intermediate scoring — points only on a complete solve
- Attempt 1 solve = 110 pts, attempt 5 = 70 pts, attempt 10 = 20 pts

### Implication
- Every unnecessary guess costs 10 points
- Don't randomly guess — use constraint elimination to solve faster
- An optimized strategy targeting ≤ 5 guesses yields 70+ pts per win

## Combined Score Maximization
- Total = ng_score + cb_score
- Prioritize Code Breaker for higher raw ceiling (120 base vs 100)
- In Number Guesser, binary search on Hard difficulty (1–200) with 6 attempts needs 8 perfect bisections — requires optimal play
- Consistent wins on Normal difficulty outscores risky Hard attempts that fail

## Risk vs Reward
- Harder difficulty = same win bonus formula = no extra reward for hard mode
- Only advantage of Hard: challenge and bragging rights, not points
- For score maximization: Easy or Normal with fast binary search wins
