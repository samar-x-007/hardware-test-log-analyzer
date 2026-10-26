"""Metrics for labeled diagnosis evaluations."""


def score_categories(expected: list[str], predicted: list[str], labels: list[str]) -> dict:
    if len(expected) != len(predicted):
        raise ValueError("Expected and predicted label counts must match")
    matrix = {label: {guess: 0 for guess in labels} for label in labels}
    for actual, guess in zip(expected, predicted):
        if actual not in matrix or guess not in matrix:
            raise ValueError("Every label must be included in the labels list")
        matrix[actual][guess] += 1
    per_class = {}
    for label in labels:
        tp = matrix[label][label]
        fp = sum(matrix[other][label] for other in labels if other != label)
        fn = sum(matrix[label][other] for other in labels if other != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        per_class[label] = {"precision": precision, "recall": recall,
                            "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                            "support": sum(matrix[label].values())}
    accuracy = sum(matrix[label][label] for label in labels) / len(expected) if expected else 0.0
    macro_f1 = sum(v["f1"] for v in per_class.values()) / len(labels) if labels else 0.0
    return {"accuracy": accuracy, "macro_f1": macro_f1,
            "per_class": per_class, "confusion_matrix": matrix}
