# Result Sanity Checks

이 문서는 result-analyzer가 매 실험 결과를 분석할 때 **자동으로** 수행해야 하는
범용 sanity check 목록이다. 데이터셋이나 task에 무관하게 적용한다.

---

## 1. Class Imbalance Exploitation

**감지 조건:**
- 전체 accuracy/AUC는 높지만, minority class의 recall/specificity가 낮음
- Majority class 비율이 70% 이상인데 overall metric만으로 "best" 판단함

**체크 방법:**
```
for each class c:
  per_class_rate[c] = correctly classified in c / total in c
min_class_rate = min(per_class_rate.values())
if min_class_rate < 0.5 * max(per_class_rate.values()):
  FLAG: "imbalance exploitation — worst class rate ({min_class_rate}) is
         less than half of best class rate ({max_class_rate})"
```

**조치:** per-class metric의 harmonic mean 또는 worst-case로 재랭킹

---

## 2. Threshold Sensitivity

**감지 조건:**
- Accuracy가 높지만 threshold를 0.01만 바꿔도 크게 변함
- AUC는 높지만 실제 operating point (EER 근처)에서 성능이 나쁨

**체크 방법:**
```
acc_at_optimal = accuracy(best_threshold)
acc_at_nearby = accuracy(best_threshold ± 0.05)
if abs(acc_at_optimal - acc_at_nearby) > 0.05:
  FLAG: "threshold-sensitive — ±0.05 shift causes {diff:.1%} accuracy drop"
```

**조치:** AUC 대신 EER 또는 threshold-robust metric 사용 권장

---

## 3. Train-Test Metric Divergence

**감지 조건:**
- Train metric >> test metric (overfitting)
- Train metric << test metric (data leakage or lucky split)

**체크 방법:**
```
gap = abs(train_metric - test_metric)
if gap > 0.05:
  FLAG: "train-test gap = {gap:.3f}"
if test_metric > train_metric + 0.02:
  FLAG: "test > train — possible data leakage or lucky split"
```

**조치:** k-fold cross-validation으로 재검증

---

## 4. Near-Random Subgroup

**감지 조건:**
- 전체 metric은 좋지만, 특정 subgroup/category에서 random 수준 (AUC ≈ 0.5)

**체크 방법:**
```
for each subgroup g:
  if metric[g] < random_baseline + 0.1:
    FLAG: "near-random on subgroup {g} — metric={metric[g]:.3f}"
```

**조치:** 해당 subgroup 분석, 데이터 부족 또는 모델 한계 확인

---

## 5. Metric Disagreement

**감지 조건:**
- AUC는 높지만 F1이 낮음 (또는 반대)
- Precision과 Recall이 극단적으로 다름

**체크 방법:**
```
if auc > 0.95 and f1 < 0.85:
  FLAG: "AUC-F1 disagreement — likely threshold/calibration issue"
if abs(precision - recall) > 0.3:
  FLAG: "precision-recall gap = {gap:.3f} — model is biased toward one class"
```

**조치:** calibration 확인, threshold 최적화 방법 변경

---

## 6. Degenerate Predictions

**감지 조건:**
- 모든 sample에 대해 같은 class를 예측 (모든 것을 fake/real로 예측)
- 예측 분산이 극단적으로 낮음

**체크 방법:**
```
pred_var = variance(predictions)
if pred_var < 0.01:
  FLAG: "near-constant predictions — model may have collapsed"
unique_preds = unique(round(predictions, 2))
if len(unique_preds) < 5:
  FLAG: "only {len(unique_preds)} distinct prediction values"
```

**조치:** 모델 학습 과정 확인, loss가 정상적으로 감소했는지 확인

---

## 7. Suspiciously Perfect Metrics

**감지 조건:**
- AUC = 1.0, ACC = 1.0 등 완벽한 점수

**체크 방법:**
```
if any(metric == 1.0 for metric in [auc, accuracy, f1]):
  FLAG: "perfect metric detected — likely data leakage, label error, or trivial task"
```

**조치:** train/test split 확인, label 정확성 검증, feature leakage 확인

---

## 8. Score Distribution Anomaly

**감지 조건:**
- 대부분의 score가 0 또는 1 근처에 몰려있음 (overconfident)
- Score 분포가 bimodal이 아님 (discrimination 없음)

**체크 방법:**
```
scores_near_boundary = sum((s < 0.1) | (s > 0.9) for s in scores) / len(scores)
if scores_near_boundary > 0.95:
  FLAG: "overconfident — {scores_near_boundary:.0%} of scores near 0 or 1"

# Check if scores separate classes
mean_pos = mean(scores[labels == 1])
mean_neg = mean(scores[labels == 0])
if abs(mean_pos - mean_neg) < 0.1:
  FLAG: "weak separation — mean(pos)={mean_pos:.3f}, mean(neg)={mean_neg:.3f}"
```

**조치:** calibration 필요, ECE 확인

---

## 적용 방법

result-analyzer skill은 매 분석 시 위 8개 check를 자동으로 수행한다.
Flag가 발생하면:
1. 해당 flag를 분석 리포트에 포함
2. Flag된 method를 "best"로 선정하지 않음
3. Flag 사유와 함께 대안 metric/method를 제안
4. 동일 flag가 3회 연속 발생하면 eval_policy.md에 hard constraint로 승격
