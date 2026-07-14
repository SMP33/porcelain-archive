import { test } from 'node:test';
import assert from 'node:assert/strict';
import { structuralDiff } from './structuralDiff.js';

test('пустые массивы', () => {
  assert.deepEqual(structuralDiff([], []), []);
});

test('один массив пустой — всё добавлено', () => {
  const newArr = [{ x: 'A', y: '1' }, { x: 'B', y: '2' }];
  assert.deepEqual(structuralDiff([], newArr), [
    { oldIndex: null, newIndex: 0, status: 'added' },
    { oldIndex: null, newIndex: 1, status: 'added' },
  ]);
});

test('один массив пустой — всё удалено', () => {
  const oldArr = [{ x: 'A', y: '1' }, { x: 'B', y: '2' }];
  assert.deepEqual(structuralDiff(oldArr, []), [
    { oldIndex: 0, newIndex: null, status: 'deleted' },
    { oldIndex: 1, newIndex: null, status: 'deleted' },
  ]);
});

test('полностью идентичные массивы — пустой результат', () => {
  const arr = [{ x: 'A', y: '1' }, { x: 'B', y: '2' }];
  assert.deepEqual(structuralDiff(arr, arr), []);
});

test('вставка не помечает соседей перемещёнными (1 2 3 3 3 4 -> 1 0 2 3 3 3 4)', () => {
  const mk = (x) => ({ x, y: 'same' });
  const oldArr = ['1', '2', '3', '3', '3', '4'].map(mk);
  const newArr = ['1', '0', '2', '3', '3', '3', '4'].map(mk);
  assert.deepEqual(structuralDiff(oldArr, newArr), [
    { oldIndex: null, newIndex: 1, status: 'added' },
  ]);
});

test('своп двух объектов даёт одну пару deleted+added, не две', () => {
  const oldArr = [{ x: 'A', y: '1' }, { x: 'B', y: '2' }];
  const newArr = [{ x: 'B', y: '2' }, { x: 'A', y: '1' }];
  const result = structuralDiff(oldArr, newArr);
  assert.equal(result.length, 2);
  assert.equal(result.filter((r) => r.status === 'deleted').length, 1);
  assert.equal(result.filter((r) => r.status === 'added').length, 1);
});

test('вставка + изменение текста: соседи с тем же x не считаются изменёнными', () => {
  const oldArr = [{ x: 'A', y: '1' }, { x: 'B', y: '2' }, { x: 'C', y: '3' }];
  const newArr = [
    { x: 'X', y: 'new' },
    { x: 'A', y: '1-changed' },
    { x: 'B', y: '2' },
    { x: 'C', y: '3' },
  ];
  assert.deepEqual(structuralDiff(oldArr, newArr), [
    { oldIndex: null, newIndex: 0, status: 'added' },
    { oldIndex: 0, newIndex: 1, status: 'modified' },
  ]);
});

test('ABCD -> ABDC: разрыв последовательности даёт ровно одну пару deleted+added', () => {
  const mk = (x) => ({ x, y: 'same' });
  const oldArr = ['A', 'B', 'C', 'D'].map(mk);
  const newArr = ['A', 'B', 'D', 'C'].map(mk);
  const result = structuralDiff(oldArr, newArr);
  assert.equal(result.length, 2);
  assert.equal(result.filter((r) => r.status === 'deleted').length, 1);
  assert.equal(result.filter((r) => r.status === 'added').length, 1);
});

test('x-дубли сопоставляются по FIFO, а не по совпадению y', () => {
  const oldArr = [{ x: 'A', y: '1' }, { x: 'A', y: '2' }];
  const newArr = [{ x: 'A', y: '2' }, { x: 'A', y: '1' }];
  assert.deepEqual(structuralDiff(oldArr, newArr), [
    { oldIndex: 0, newIndex: 0, status: 'modified' },
    { oldIndex: 1, newIndex: 1, status: 'modified' },
  ]);
});

test('сортировка вывода: modified(1/1), deleted(2/-), added(-/2), added(-/3)', () => {
  const oldArr = [
    { x: 'A', y: '1' },
    { x: 'B', y: '1' },
    { x: 'C', y: '1' },
  ];
  const newArr = [
    { x: 'A', y: '1' },
    { x: 'B', y: '2' },
    { x: 'D', y: '1' },
    { x: 'E', y: '1' },
  ];
  const result = structuralDiff(oldArr, newArr);
  assert.deepEqual(
    result.map((r) => r.status),
    ['modified', 'deleted', 'added', 'added']
  );
});

test('регистр x/y не влияет на сопоставление', () => {
  const oldArr = [{ x: 'AbCd', y: 'TeXt' }];
  const newArr = [{ x: 'ABCD', y: 'text' }];
  assert.deepEqual(structuralDiff(oldArr, newArr), []);
});
