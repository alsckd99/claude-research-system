# Result Sanity Checks

이 문서는 result-analyzer가 매 실험 결과를 분석할 때 수행하는 범용 sanity check이다.
아래 숫자 threshold는 기본값이다. eval_policy.md에 프로젝트별 기준이 있으면 그걸 따른다.
프로젝트의 metric이나 task 특성에 따라 기준을 조정해서 적용한다.

---

## 1. Class Imbalance Exploitation

의미: 전체 metric은 높지만 minority class에서 실패하고 있다.

기본 체크:
```
for each class c:
  per_class_rate[c] = correctly classified in c / total in c
if worst class rate < 0.5 * best class rate:
  FLAG
```

조치: per-class metric의 harmonic mean 또는 worst-case로 재랭킹

---

## 2. Threshold Sensitivity

의미: 약간의 threshold 변경으로 metric이 크게 변한다.

기본 체크:
```
if threshold를 소폭 변경했을 때 metric 변화가 큰 경우:
  FLAG
```
(threshold-based metric이 아닌 프로젝트에서는 해당 없음)

조치: threshold-robust metric 사용 권장

---

## 3. Train-Test Metric Divergence

의미: train과 test 사이에 큰 gap이 있다.

기본 체크:
```
if significant gap between train and test metric:
  FLAG (overfitting or underfitting)
if test > train:
  FLAG (possible data leakage)
```

조치: cross-validation으로 재검증

---

## 4. Near-Random Subgroup

의미: 전체 metric은 좋지만 특정 subgroup에서 random 수준이다.

기본 체크:
```
for each subgroup g:
  if metric[g] ≈ random baseline:
    FLAG
```

조치: 해당 subgroup 분석

---

## 5. Metric Disagreement

의미: 서로 다른 metric들이 다른 이야기를 한다.

기본 체크:
```
if primary metric은 좋지만 secondary metric이 나쁨 (또는 반대):
  FLAG
```
(어떤 metric 쌍을 비교할지는 eval_policy.md에 정의된 metric들 기준)

조치: 어떤 metric이 프로젝트 목표에 더 부합하는지 판단

---

## 6. Degenerate Predictions

의미: 모델이 거의 같은 값만 출력한다.

기본 체크:
```
if prediction의 분산이 극단적으로 낮거나 distinct value가 매우 적으면:
  FLAG
```

조치: 모델/학습 과정 확인

---

## 7. Suspiciously Perfect Metrics

의미: metric이 완벽하다 — leakage 가능성.

기본 체크:
```
if any metric이 이론적 최대값 또는 최소값(loss)이면:
  FLAG
```

조치: data split, label, feature leakage 확인

---

## 8. Score Distribution Anomaly

의미: score 분포가 비정상적이다.

기본 체크:
```
if 대부분의 score가 극단값에 몰려있거나 class간 분리가 안 되면:
  FLAG
```

조치: calibration 확인

---

## 적용 방법

result-analyzer는 매 분석 시 위 check를 수행한다.
Flag가 발생하면:
1. 해당 flag를 분석 리포트에 포함
2. Flag된 method를 "best"로 선정하지 않음
3. 대안 제안
4. 동일 flag가 3회 연속 발생하면 eval_policy.md에 hard constraint로 승격
