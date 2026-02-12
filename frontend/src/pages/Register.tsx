import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import api from '../api/client';

export default function Register() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.post('/api/auth/register', { email, username, password });
      navigate('/login');
    } catch (err: any) {
      setError(err.response?.data?.detail || '登録に失敗しました');
    }
  };

  return (
    <div className="auth-page">
      <h1>親アカウント登録</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>メールアドレス</label>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>ユーザー名</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>パスワード</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary" style={{ width: '100%' }}>登録</button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '16px' }}>
        <Link to="/login">アカウントをお持ちの方はこちら</Link>
      </p>
    </div>
  );
}
