import { useEffect, useRef, useState, FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { ChildOut } from '../types';

export default function ParentDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [children, setChildren] = useState<ChildOut[]>([]);
  const [childUsername, setChildUsername] = useState('');
  const [childPassword, setChildPassword] = useState('');
  const [error, setError] = useState('');
  const [info, setInfo] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchChildren = () => {
    api.get('/api/parent/children').then((res) => setChildren(res.data));
  };

  useEffect(() => { fetchChildren(); }, []);

  const handleCreateChild = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/parent/children', { username: childUsername, password: childPassword });
      setChildUsername('');
      setChildPassword('');
      fetchChildren();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'エラーが発生しました');
    }
  };

  const handleDeleteChild = async (id: number, username: string) => {
    if (!confirm(`${username} を削除しますか？`)) return;
    await api.delete(`/api/parent/children/${id}`);
    fetchChildren();
  };

  const handleImport = async () => {
    if (!selectedFile) return;
    setInfo('');
    setError('');
    const formData = new FormData();
    formData.append('file', selectedFile);
    try {
      const res = await api.post('/api/admin/import-words', formData);
      setInfo(res.data.detail);
      setSelectedFile(null);
      if (fileRef.current) fileRef.current.value = '';
    } catch {
      setError('インポートに失敗しました');
    }
  };

  return (
    <div className="dashboard">
      <div className="header">
        <h1>{user?.username} さん 管理メニュー</h1>
        <button className="btn-secondary" onClick={() => { logout(); navigate('/login'); }}>ログアウト</button>
      </div>

      <section className="section">
        <h2>子アカウント管理</h2>
        {children.length === 0 ? (
          <p>子アカウントがありません</p>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>ユーザー名</th>
                  <th>作成日</th>
                  <th>操作</th>
                </tr>
              </thead>
              <tbody>
                {children.map((c) => (
                  <tr key={c.id}>
                    <td>{c.username}</td>
                    <td>{new Date(c.created_at).toLocaleString()}</td>
                    <td>
                      <div className="actions">
                        <button className="btn-secondary" onClick={() => navigate(`/parent/child/${c.id}`)}>統計表示</button>
                        <button className="btn-secondary" onClick={() => navigate(`/parent/child/${c.id}/weak-words`)}>苦手単語</button>
                        <button className="btn-danger" onClick={() => handleDeleteChild(c.id, c.username)}>削除</button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>

      <section className="section">
        <h2>子アカウント作成</h2>
        {error && <p className="error">{error}</p>}
        <form className="inline-form" onSubmit={handleCreateChild}>
          <input placeholder="ユーザー名" value={childUsername} onChange={(e) => setChildUsername(e.target.value)} required />
          <input type="password" placeholder="パスワード" value={childPassword} onChange={(e) => setChildPassword(e.target.value)} required />
          <button type="submit" className="btn-primary">作成</button>
        </form>
      </section>

      <section className="section">
        <h3>単語CSVインポート</h3>
        {info && <p className="info">{info}</p>}
        <div className="inline-form">
          <input type="file" accept=".csv" ref={fileRef} onChange={(e) => setSelectedFile(e.target.files?.[0] || null)} />
          <button className="btn-primary" disabled={!selectedFile} onClick={handleImport}>インポート</button>
        </div>
      </section>
    </div>
  );
}
