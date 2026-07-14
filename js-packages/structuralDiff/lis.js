// Стандартный O(n log n) поиск наибольшей строго возрастающей подпоследовательности.
// Возвращает индексы (в исходном массиве) одного из валидных LIS.
// Изолирован специально, чтобы при желании заменить на npm-пакет
// (например, longest-increasing-subsequence) с тем же контрактом:
// (number[]) => number[] индексов.
export function longestIncreasingSubsequenceIndices(arr) {
  const n = arr.length;
  if (n === 0) return [];

  const tails = [];               // tails[k] = индекс в arr с наименьшим "хвостом" для подпоследовательности длины k+1
  const prev = new Array(n).fill(-1); // предок для восстановления пути

  for (let i = 0; i < n; i++) {
    const val = arr[i];

    let lo = 0;
    let hi = tails.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (arr[tails[mid]] < val) {
        lo = mid + 1;
      } else {
        hi = mid;
      }
    }

    if (lo > 0) {
      prev[i] = tails[lo - 1];
    }

    if (lo === tails.length) {
      tails.push(i);
    } else {
      tails[lo] = i;
    }
  }

  const result = [];
  let k = tails[tails.length - 1];
  while (k !== -1) {
    result.push(k);
    k = prev[k];
  }

  return result.reverse();
}
