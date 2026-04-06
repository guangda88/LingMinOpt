"""
Example 2: Hyperparameter Tuning for Simple Neural Network

This example demonstrates using MinOpt to tune hyperparameters for a
simple neural network on the Iris dataset.

We'll optimize:
- Learning rate (continuous)
- Dropout rate (continuous)
- Number of hidden units (discrete)
- Activation function (discrete)
"""

from lingminopt import MinimalOptimizer, SearchSpace, ExperimentConfig
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np

# Load and prepare data
iris = load_iris()
X, y = iris.data, iris.target

# Standardize features
scaler = StandardScaler()
X = scaler.fit_transform(X)

# Split data
X_train, X_val, y_train, y_val = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print("Dataset loaded:")
print(f"  Features: {X.shape[1]}")
print(f"  Classes: {len(np.unique(y))}")
print(f"  Training samples: {X_train.shape[0]}")
print(f"  Validation samples: {X_val.shape[0]}")
print()

# Define neural network (simple implementation)
def create_and_train_nn(params):
    """Create and train a simple neural network."""
    import numpy as np

    # Extract parameters
    hidden_units = int(params["hidden_units"])
    learning_rate = params["learning_rate"]
    dropout = params["dropout"]
    activation = params["activation"]

    # Network architecture
    input_size = X_train.shape[1]
    hidden_size = hidden_units
    output_size = len(np.unique(y))

    # Initialize weights (Xavier initialization)
    np.random.seed(42)
    W1 = np.random.randn(input_size, hidden_size) * np.sqrt(2.0 / input_size)
    b1 = np.zeros(hidden_size)
    W2 = np.random.randn(hidden_size, output_size) * np.sqrt(2.0 / hidden_size)
    b2 = np.zeros(output_size)

    # Training loop (simplified)
    epochs = 100
    batch_size = 16

    for epoch in range(epochs):
        # Shuffle training data
        indices = np.random.permutation(len(X_train))

        for i in range(0, len(X_train), batch_size):
            batch_indices = indices[i:i+batch_size]
            X_batch = X_train[batch_indices]
            y_batch = y_train[batch_indices]

            # Forward pass
            z1 = np.dot(X_batch, W1) + b1

            # Activation function
            if activation == "relu":
                a1 = np.maximum(0, z1)
            elif activation == "sigmoid":
                a1 = 1.0 / (1.0 + np.exp(-z1))
            elif activation == "tanh":
                a1 = np.tanh(z1)
            else:
                raise ValueError(f"Unknown activation: {activation}")

            # Dropout
            dropout_mask = (np.random.rand(*a1.shape) > dropout).astype(float) / (1.0 - dropout)
            a1_dropout = a1 * dropout_mask

            # Output layer
            z2 = np.dot(a1_dropout, W2) + b2

            # Softmax
            exp_z2 = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
            a2 = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)

            # One-hot encoding
            y_one_hot = np.zeros((len(y_batch), output_size))
            y_one_hot[np.arange(len(y_batch)), y_batch] = 1

            # Backward pass (simplified)
            dz2 = (a2 - y_one_hot) / len(y_batch)
            dW2 = np.dot(a1_dropout.T, dz2)
            db2 = np.sum(dz2, axis=0)

            da1 = np.dot(dz2, W2.T) * dropout_mask

            if activation == "relu":
                dz1 = da1 * (z1 > 0)
            elif activation == "sigmoid":
                sig = 1.0 / (1.0 + np.exp(-z1))
                dz1 = da1 * sig * (1 - sig)
            elif activation == "tanh":
                tanh_h = np.tanh(z1)
                dz1 = da1 * (1 - tanh_h**2)

            dW1 = np.dot(X_batch.T, dz1)
            db1 = np.sum(dz1, axis=0)

            # Update weights (gradient descent)
            W1 -= learning_rate * dW1
            b1 -= learning_rate * db1
            W2 -= learning_rate * dW2
            b2 -= learning_rate * db2

    # Evaluate on validation set
    z1 = np.dot(X_val, W1) + b1
    if activation == "relu":
        a1 = np.maximum(0, z1)
    elif activation == "sigmoid":
        a1 = 1.0 / (1.0 + np.exp(-z1))
    elif activation == "tanh":
        a1 = np.tanh(z1)

    z2 = np.dot(a1, W2) + b2
    exp_z2 = np.exp(z2 - np.max(z2, axis=1, keepdims=True))
    predictions = exp_z2 / np.sum(exp_z2, axis=1, keepdims=True)

    # Calculate accuracy (higher is better, so we return negative error)
    predicted_classes = np.argmax(predictions, axis=1)
    accuracy = np.mean(predicted_classes == y_val)

    # Return negative accuracy (MinOpt minimizes by default)
    return -accuracy

# Define search space
search_space = SearchSpace()

# Hyperparameters
search_space.add_continuous("learning_rate", 1e-4, 1e-1)
search_space.add_continuous("dropout", 0.0, 0.5)
search_space.add_discrete("hidden_units", [16, 32, 64, 128])
search_space.add_discrete("activation", ["relu", "sigmoid", "tanh"])

# Create configuration
config = ExperimentConfig(
    max_experiments=30,  # Limited for demo
    improvement_threshold=0.001,
    time_budget=10.0,  # 10 seconds per experiment
    direction="minimize",  # Minimize negative accuracy = maximize accuracy
    random_seed=42
)

# Create optimizer
print("Starting hyperparameter optimization...")
print(f"Max experiments: {config.max_experiments}")
print(f"Search space: {len(search_space)} parameters")
print()

optimizer = MinimalOptimizer(
    evaluate=create_and_train_nn,
    search_space=search_space,
    config=config,
    search_strategy="random",
    seed=42
)

# Run optimization
result = optimizer.run()

# Display results
print("\n" + "="*60)
print("Optimization Results")
print("="*60)
print(f"Best Accuracy: {-result.best_score:.4f} ({-result.best_score*100:.2f}%)")
print("Best Parameters:")
for key, value in result.best_params.items():
    print(f"  {key}: {value}")

print(f"\nTotal Experiments: {result.total_experiments}")
print(f"Total Time: {result.total_time:.2f}s")
print(f"Improvement: {-result.improvement:.4f}")

# Save results
result.save("example2_results.json")
print("\nResults saved to: example2_results.json")

# Analysis
print("\n" + "="*60)
print("Analysis")
print("="*60)

# Find best validation accuracy
best_accuracy = -result.best_score
print(f"\nBest validation accuracy: {best_accuracy:.4f} ({best_accuracy*100:.2f}%)")

if best_accuracy > 0.9:
    print("✓ Excellent! Found a good configuration.")
elif best_accuracy > 0.8:
    print("✓ Good! Reasonable configuration found.")
else:
    print("✗ Poor accuracy. Try increasing max_experiments or adjusting search space.")

# Show some experiments
print("\nTop 5 experiments:")
sorted_experiments = sorted(result.history, key=lambda e: e.score)[:5]
for i, exp in enumerate(sorted_experiments, 1):
    print(f"{i}. Accuracy: {-exp.score:.4f}, Params: {exp.params}")
