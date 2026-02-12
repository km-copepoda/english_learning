import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await login(username, password);
      navigate('/');
    } catch {
      setError('ユーザー名またはパスワードが正しくありません');
    }
  };

  return (
    <div className="auth-page">
      <h1>ログイン</h1>
      {error && <p className="error">{error}</p>}
      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>ユーザー名</label>
          <input value={username} onChange={(e) => setUsername(e.target.value)} required />
        </div>
        <div className="form-group">
          <label>パスワード</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
        </div>
        <button type="submit" className="btn-primary" style={{ width: '100%' }}>ログイン</button>
      </form>
      <p style={{ textAlign: 'center', marginTop: '16px' }}>
        <Link to="/register">アカウントをお持ちでない方はこちら</Link>
      </p>
    </div>
  );
}
