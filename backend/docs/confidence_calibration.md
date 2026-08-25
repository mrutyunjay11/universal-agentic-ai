# Universal Agentic AI — Confidence Calibration & Uncertainty Quantification

## 1. Uncertainty Quantification

Predicted model confidence is evaluated against empirical correctness:

- **Expected Calibration Error (ECE)**:
  $$ECE = \sum_{m=1}^{M} \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right|$$

- **Brier Score**:
  $$\text{Brier} = \frac{1}{N} \sum_{t=1}^{N} (f_t - o_t)^2$$

---

## 2. Overconfidence Penalty

When predicted confidence is high ($\ge 0.90$) but the execution fails quality or safety gates, the system flags the result for diagnostic recalibration.
