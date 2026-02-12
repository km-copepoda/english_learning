import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { MenuStatus } from '../types';

export default function ChildDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [menu, setMenu] = useState<MenuStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [openGroup, setOpenGroup] = useState<string | null>(null);

  useEffect(() => {
    api.get('/api/learning/menu-status').then((res) => {
      setMenu(res.data);
      setLoading(false);
    });
  }, []);

  if (loading) return <div>読み込み中...</div>;

  const toggleGroup = (group: string) => {
    setOpenGroup(openGroup === group ? null : group);
  };

  const goQuiz = (mode: string, period?: string) => {
    const params = new URLSearchParams({ mode });
    if (period) params.set('period', period);
    navigate(`/child/quiz?${params.toString()}`);
  };

  return (
    <div className="dashboard">
      <div className="header">
        <h1>{user?.username} さん</h1>
        <button className="btn-secondary" onClick={() => { logout(); navigate('/login'); }}>ログアウト</button>
      </div>
      <div className="today-status">
        {menu!.studied_today
          ? <span className="today-done">今日の学習 OK!</span>
          : <span className="todo-not-yet">今日はまだ学習していません</span>
        }
      </div>
      <h2>学習メニュー</h2>
      <div className="menu-list">
        {/* 今日の単語学習 */}
        <div
          className={`menu-item ${menu!.today === 0 ? 'disabled' : ''}`}
          onClick={() => menu!.today > 0 && goQuiz('today')}
        >
          <div className="menu-item-header">
            <span>今日の単語学習</span>
            <span className="badge">{menu!.today}問</span>
          </div>
        </div>

        {/* これまでに学習した単語 */}
        <div className="menu-item" onClick={() => toggleGroup('review')}>
          <div className="accordion-header">
            <span>これまでに学習した単語</span>
            <span className={`arrow ${openGroup === 'review' ? 'open' : ''}`}>▶</span>
          </div>
        </div>
        {openGroup === 'review' && (
          <div className="accordion-body">
            {[
              { label: '1週間以内', period: 'week', count: menu!.review_week },
              { label: '1ヶ月以内', period: 'month', count: menu!.review_month },
              { label: '1ヶ月以上', period: 'over_month', count: menu!.review_over_month },
              { label: '全範囲', period: 'all', count: menu!.review_all },
            ].map((item) => (
              <div
                key={item.period}
                className={`menu-item menu-item-sub ${item.count === 0 ? 'disabled' : ''}`}
                onClick={() => item.count > 0 && goQuiz('review', item.period)}
              >
                <div className="menu-item-header">
                  <span>{item.label}</span>
                  <span className="badge">{item.count}問</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 苦手単語学習 */}
        <div className="menu-item" onClick={() => toggleGroup('weak')}>
          <div className="accordion-header">
            <span>苦手単語学習</span>
            <span className={`arrow ${openGroup === 'weak' ? 'open' : ''}`}>▶</span>
          </div>
        </div>
        {openGroup === 'weak' && (
          <div className="accordion-body">
            {[
              { label: '1ヶ月以内', period: 'month', count: menu!.weak_month },
              { label: '1ヶ月以上', period: 'over_month', count: menu!.weak_over_month },
              { label: '全範囲', period: 'all', count: menu!.weak_all },
            ].map((item) => (
              <div
                key={item.period}
                className={`menu-item menu-item-sub ${item.count === 0 ? 'disabled' : ''}`}
                onClick={() => item.count > 0 && goQuiz('weak', item.period)}
              >
                <div className="menu-item-header">
                  <span>{item.label}</span>
                  <span className="badge">{item.count}問</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* My Stats & Weak Words */}
        <div className="menu-item" onClick={() => navigate('/child/stats')}>
          <div className="menu-item-header">
            <span>学習進捗</span>
          </div>
        </div>
        <div className="menu-item" onClick={() => navigate('/child/weak-words')}>
          <div className="menu-item-header">
            <span>苦手単語一覧</span>
          </div>
        </div>
      </div>
    </div>
  );
}
