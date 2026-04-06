"""
Example 1: Simple Quadratic Optimization

This example demonstrates basic MinOpt usage by optimizing a simple
quadratic function: f(x, y) = (x - 2)² + (y + 3)²

The global minimum is at x = 2, y = -3 with value 0.
"""

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig

# Define the objective function
def objective(params):
    """Objective function to minimize."""
    x = params["x"]
    y = params["y"]
    return (x - 2)**2 + (y + 3)**2

# Define the search space
search_space = SearchSpace()
search_space.add_continuous("x", -10, 10)
search_space.add_continuous("y", -10, 10)

# Create optimization configuration
config = ExperimentConfig(
    max_experiments=50,
    improvement_threshold=0.01,
    time_budget=1.0,  # 1 second per experiment (very fast function)
    direction="minimize"
)

# Create optimizer
optimizer = MinimalOptimizer(
    evaluate=objective,
    search_space=search_space,
    config=config,
    search_strategy="random",  # Try: random, bayesian, grid, annealing
    seed=42
)

# Run optimization
print("Starting optimization...")
print("Search strategy: random")
print(f"Max experiments: {config.max_experiments}")
print()

result = optimizer.run()

# Display results
print("\n" + "="*60)
print("Optimization Results")
print("="*60)
print(f"Best Score: {result.best_score:.6f}")
print(f"Best Parameters: {result.best_params}")
print("Expected: x ≈ 2.0, y ≈ -3.0")
print(f"\nTotal Experiments: {result.total_experiments}")
print(f"Total Time: {result.total_time:.2f}s")
print(f"Improvement: {result.improvement:.6f}")

# Save results
result.save("example1_results.json")
print("\nResults saved to: example1_results.json")

# Verify result
print("\n" + "="*60)
print("Verification")
print("="*60)
expected_x = 2.0
expected_y = -3.0
actual_x = result.best_params.get("x", 0)
actual_y = result.best_params.get("y", 0)

error_x = abs(actual_x - expected_x)
error_y = abs(actual_y - expected_y)

print(f"x: Expected {expected_x:.2f}, Got {actual_x:.2f}, Error {error_x:.2f}")
print(f"y: Expected {expected_y:.2f}, Got {actual_y:.2f}, Error {error_y:.2f}")

if error_x < 1.0 and error_y < 1.0:
    print("\n✓ Optimization successful! Found near-optimal solution.")
else:
    print("\n✗ Could not find optimal solution. Try increasing max_experiments.")
