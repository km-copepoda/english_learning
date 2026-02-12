import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../api/client';
import { WeakWordOut } from '../types';

export default function MyWeakWords() {
  const navigate = useNavigate();
  const [words, setWords] = useState<WeakWordOut[]>([]);
  const [sort, setSort] = useState({ by: 'accuracy', order: 'asc' });
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get(`/api/learning/weak-words?sort_by=${sort.by}&order=${sort.order}`).then((res) => {
      setWords(res.data);
      setLoading(false);
    });
  }, [sort]);

  const toggleSort = (key: string) => {
    setSort((prev) =>
      prev.by === key
        ? { by: key, order: prev.order === 'asc' ? 'desc' : 'asc' }
        : { by: key, order: 'asc' }
    );
  };

  if (loading) return <div>読み込み中...</div>;

  return (
    <div className="weak-words-page">
      <div className="header">
        <h1>苦手単語一覧</h1>
        <button className="btn-secondary" onClick={() => navigate('/child')}>戻る</button>
      </div>
      {words.length === 0 ? (
        <p>苦手単語はありません</p>
      ) : (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th className="sortable" onClick={() => toggleSort('japanese')}>
                  日本語 {sort.by === 'japanese' ? (sort.order === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th className="sortable" onClick={() => toggleSort('english')}>
                  英語 {sort.by === 'english' ? (sort.order === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th>カタカナ読み</th>
                <th className="sortable" onClick={() => toggleSort('total_attempts')}>
                  全回答数 {sort.by === 'total_attempts' ? (sort.order === 'asc' ? '▲' : '▼') : ''}
                </th>
                <th>正解数</th>
                <th>ヒント使用</th>
                <th className="sortable" onClick={() => toggleSort('accuracy')}>
                  正解率 {sort.by === 'accuracy' ? (sort.order === 'asc' ? '▲' : '▼') : ''}
                </th>
              </tr>
            </thead>
            <tbody>
              {words.map((w) => (
                <tr key={w.id}>
                  <td>{w.japanese}</td>
                  <td>{w.english}</td>
                  <td>{w.english_katakana}</td>
                  <td>{w.total_attempts}</td>
                  <td>{w.correct_count}</td>
                  <td>{w.hint_count}</td>
                  <td>{(w.accuracy * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
