import time
import json
from typing import Callable, List, Dict, Any
from dataclasses import dataclass
from lingminopt.core.searcher import SearchSpace

@dataclass
class ExperimentConfig:
    max_experiments: int = 50
    improvement_threshold: float = 0.01
    time_budget: float = 300
    early_stopping_patience: int = 10
    direction: str = "minimize"
    random_seed: int = 42

class OptimizationResult:
    def __init__(self):
        self.best_score = float('inf') if ExperimentConfig().direction == "minimize" else float('-inf')
        self.best_params = {}
        self.history = []
        self.total_experiments = 0
        self.total_time = 0
        self.improvement = 0

    def to_dict(self):
        return {
            "best_score": self.best_score,
            "best_params": self.best_params,
            "total_experiments": self.total_experiments,
            "total_time": self.total_time,
            "improvement": self.improvement
        }

class MinimalOptimizer:
    def __init__(self, evaluate: Callable, search_space: SearchSpace, config: ExperimentConfig = None):
        self.evaluate = evaluate
        self.search_space = search_space
        self.config = config or ExperimentConfig()
        self.result = OptimizationResult()
        
        if self.config.direction == "minimize":
            self.result.best_score = float('inf')
        else:
            self.result.best_score = float('-inf')

    def run(self):
        """Run optimization"""
        import random
        random.seed(self.config.random_seed)
        
        start_time = time.time()
        patience_counter = 0
        last_best = self.result.best_score
        
        for i in range(self.config.max_experiments):
            # Check time budget
            if time.time() - start_time > self.config.time_budget:
                break
            
            # Sample parameters
            params = self.search_space.sample()
            
            # Evaluate
            try:
                score = self.evaluate(params)
            except Exception as e:
                continue
            
            # Update best
            improved = False
            if self.config.direction == "minimize":
                if score < self.result.best_score:
                    self.result.best_score = score
                    self.result.best_params = params
                    improved = True
            else:
                if score > self.result.best_score:
                    self.result.best_score = score
                    self.result.best_params = params
                    improved = True
            
            # Record history
            self.result.history.append({
                "experiment_id": i,
                "params": params,
                "score": score,
                "timestamp": time.time()
            })
            
            # Check improvement
            if improved:
                self.result.improvement = abs(score - last_best)
                last_best = score
                patience_counter = 0
            else:
                patience_counter += 1
                if patience_counter >= self.config.early_stopping_patience:
                    break
        
        self.result.total_experiments = len(self.result.history)
        self.result.total_time = time.time() - start_time
        
        return self.result
