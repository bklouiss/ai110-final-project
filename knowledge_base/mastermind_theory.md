# Mastermind / Code Breaker Strategy

## Game Rules
- Secret: 4 digits, each from 1–6, repeats allowed (1296 total possible codes)
- Feedback per guess:
  - `●` (exact): correct digit in correct position
  - `○` (close): correct digit in wrong position

## Optimal Opening Guess
Start with **1122**. This guess tests two pairs and covers all 6 digits in exactly 2 guesses maximum for elimination. Alternative: **1234** (tests 4 distinct digits, no repeats).

Why 1122 is strong: it partitions the 1296 possibilities into the fewest worst-case remaining candidates after feedback.

## Constraint Elimination Strategy
After each guess, eliminate all codes that would not produce the same exact/close feedback.

Example: guess `1234` gets `●○··` (1 exact, 1 close)
- One digit is in the right place (could be 1, 2, 3, or 4)
- One digit exists but is misplaced
- The other two digits from {1,2,3,4} are NOT in the code

## Reading Feedback
- `●●●●` = solved
- `0 exact, 0 close` = none of the guessed digits appear in the secret
- `0 exact, 4 close` = all digits present but all misplaced — try a permutation
- High close count + low exact count = right digits, wrong order

## Position Testing
If you suspect a digit is correct but unsure of position:
- Fix confirmed digits in their known positions
- Move the suspected digit through remaining slots

## Score Optimization
Score formula: `max(10, 120 - 10 * attempt_number)`. Solving in 1 attempt = 110 pts, 5 attempts = 70 pts.
- Knuth's algorithm guarantees a solution in ≤ 5 guesses
- Practical strategy: aim for ≤ 6 guesses with constraint tracking

## Recommended Sequence
1. Guess `1122` (or `1234`)
2. Use feedback to partition remaining possibilities
3. Next guess: pick a code that distinguishes the largest partitions
4. Continue until solved
