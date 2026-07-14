import { longestIncreasingSubsequenceIndices } from './lis.js';

/**
 * Сравнивает два массива объектов вида { x, y }:
 *   x — хеш СТРАНИЦЫ (идентичность объекта)
 *   y — хеш ТЕКСТА (контент объекта)
 *
 * Возвращает список изменений { oldIndex, newIndex, status },
 * status: 'added' | 'deleted' | 'modified'.
 * Объекты без изменений (тот же x и тот же y, без разрыва порядка)
 * в результат не попадают.
 */
export function structuralDiff(oldArr, newArr) {
  const norm = (s) => s.toLowerCase();

  // 1-2. группировка по x (в порядке появления) + FIFO-сопоставление внутри группы
  const oldGroups = new Map();
  const newGroups = new Map();

  oldArr.forEach((obj, i) => {
    const key = norm(obj.x);
    if (!oldGroups.has(key)) oldGroups.set(key, []);
    oldGroups.get(key).push(i);
  });

  newArr.forEach((obj, i) => {
    const key = norm(obj.x);
    if (!newGroups.has(key)) newGroups.set(key, []);
    newGroups.get(key).push(i);
  });

  const matchedPairs = [];
  const results = [];

  const allKeys = new Set([...oldGroups.keys(), ...newGroups.keys()]);

  for (const key of allKeys) {
    const oldQueue = oldGroups.get(key) ?? [];
    const newQueue = newGroups.get(key) ?? [];
    const pairCount = Math.min(oldQueue.length, newQueue.length);

    for (let i = 0; i < pairCount; i++) {
      matchedPairs.push({ oldIndex: oldQueue[i], newIndex: newQueue[i] });
    }
    // 3. непарный остаток
    for (let i = pairCount; i < oldQueue.length; i++) {
      results.push({ oldIndex: oldQueue[i], newIndex: null, status: 'deleted' });
    }
    for (let i = pairCount; i < newQueue.length; i++) {
      results.push({ oldIndex: null, newIndex: newQueue[i], status: 'added' });
    }
  }

  // 4. LIS по сопоставленным парам, упорядоченным по newIndex
  matchedPairs.sort((a, b) => a.newIndex - b.newIndex);
  const oldIndexSequence = matchedPairs.map((p) => p.oldIndex);
  const lisPositions = new Set(longestIncreasingSubsequenceIndices(oldIndexSequence));

  // 5-6. закреплённые (LIS) пары -> modified/опускаем; остальные -> deleted+added
  matchedPairs.forEach((pair, i) => {
    const oldObj = oldArr[pair.oldIndex];
    const newObj = newArr[pair.newIndex];
    const textChanged = norm(oldObj.y) !== norm(newObj.y);

    if (lisPositions.has(i)) {
      if (textChanged) {
        results.push({ oldIndex: pair.oldIndex, newIndex: pair.newIndex, status: 'modified' });
      }
      // иначе объект полностью не изменился — не включаем
    } else {
      results.push({ oldIndex: pair.oldIndex, newIndex: null, status: 'deleted' });
      results.push({ oldIndex: null, newIndex: pair.newIndex, status: 'added' });
    }
  });

  // 7. сортировка по newIndex ?? oldIndex; при равенстве deleted раньше
  results.sort((a, b) => {
    const keyA = a.newIndex ?? a.oldIndex;
    const keyB = b.newIndex ?? b.oldIndex;
    if (keyA !== keyB) return keyA - keyB;
    if (a.status === 'deleted' && b.status !== 'deleted') return -1;
    if (b.status === 'deleted' && a.status !== 'deleted') return 1;
    return 0;
  });

  return results;
}
