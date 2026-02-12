import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BarChart, Bar, XAxis, YAxis, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { useAuth } from '../contexts/AuthContext';
import api from '../api/client';
import { DailyStat } from '../types';

export default function MyStats() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);
  const [stats, setStats] = useState<DailyStat[]>([]);

  useEffect(() => {
    api.get(`/api/learning/stats?year=${year}&month=${month}`).then((res) => {
      setStats(res.data);
    });
  }, [year, month]);

  const prevMonth = () => {
    if (month === 1) { setYear(year - 1); setMonth(12); }
    else setMonth(month - 1);
  };
  const nextMonth = () => {
    if (month === 12) { setYear(year + 1); setMonth(1); }
    else setMonth(month + 1);
  };

  const totalCorrect = stats.reduce((s, d) => s + d.today_correct + d.review_correct + d.weak_correct, 0);
  const totalHint = stats.reduce((s, d) => s + d.today_hint + d.review_hint + d.weak_hint, 0);
  const totalIncorrect = stats.reduce((s, d) => s + d.today_incorrect + d.review_incorrect + d.weak_incorrect, 0);
  const total = totalCorrect + totalHint + totalIncorrect;
  const accuracyStr = total > 0 ? (totalCorrect / total * 100).toFixed(1) : '-';

  return (
    <div className="stats-page">
      <div className="header">
        <h1>{user?.username} さん 学習進捗</h1>
        <button className="btn-secondary" onClick={() => navigate('/child')}>戻る</button>
      </div>
      <h2>月間学習記録</h2>
      <div className="month-nav">
        <button onClick={prevMonth}>&lt;</button>
        <span>{year}年{month}月</span>
        <button onClick={nextMonth}>&gt;</button>
      </div>

      <div className="stats-summary">
        <div className="stat-card">
          <div className="stat-label">今日の学習 正解</div>
          <div className="stat-value" style={{ color: '#4caf50' }}>
            {stats.reduce((s, d) => s + d.today_correct, 0)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">復習 正解</div>
          <div className="stat-value" style={{ color: '#2e7d32' }}>
            {stats.reduce((s, d) => s + d.review_correct, 0)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">苦手 正解</div>
          <div className="stat-value" style={{ color: '#81c784' }}>
            {stats.reduce((s, d) => s + d.weak_correct, 0)}
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-label">ヒント正解</div>
          <div className="stat-value" style={{ color: '#ffb300' }}>{totalHint}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">不正解</div>
          <div className="stat-value incorrect" style={{ color: '#d32f2f' }}>{totalIncorrect}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">正解率</div>
          <div className="stat-value">{accuracyStr}{total > 0 ? '%' : ''}</div>
        </div>
      </div>

      <div className="chart-container">
        <div className="chart-box">
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={stats}>
              <XAxis dataKey="date" tickFormatter={(v: string) => v.slice(5).replace('-', '/')} />
              <YAxis />
              <Tooltip
                labelFormatter={(v) => String(v).slice(5).replace('-', '/')}
                wrapperStyle={{ zIndex: 20 }}
                itemSorter={(item: any) => {
                  const order = [
                    'today_correct', 'today_hint', 'today_incorrect',
                    'review_correct', 'review_hint', 'review_incorrect',
                    'weak_correct', 'weak_hint', 'weak_incorrect',
                  ];
                  return order.indexOf(item.dataKey as string);
                }}
              />
              <Legend content={() => (
                <div style={{ display: 'flex', flexWrap: 'wrap', justifyContent: 'center', gap: '8px 16px', fontSize: '14px', marginTop: '8px' }}>
                  {[
                    { label: '正解', color: '#4caf50' },
                    { label: 'ヒント正解', color: '#ffb300' },
                    { label: '不正解', color: '#d32f2f' },
                    { label: '復習 正解', color: '#2e7d32' },
                    { label: '復習 ヒント正解', color: '#ffb300' },
                    { label: '復習 不正解', color: '#c62828' },
                    { label: '苦手 正解', color: '#81c784' },
                    { label: '苦手 ヒント正解', color: '#ffb300' },
                    { label: '苦手 不正解', color: '#ef9a9a' },
                  ].map((item) => (
                    <span key={item.label} style={{ display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
                      <span style={{ width: 14, height: 14, background: item.color, borderRadius: 2, display: 'inline-block' }} />
                      {item.label}
                    </span>
                  ))}
                </div>
              )} />
              <Bar dataKey="today_correct" name="正解" stackId="today" fill="#4caf50" />
              <Bar dataKey="today_hint" name="ヒント正解" stackId="today" fill="#ffb300" />
              <Bar dataKey="today_incorrect" name="不正解" stackId="today" fill="#d32f2f" />
              <Bar dataKey="review_correct" name="復習 正解" stackId="review" fill="#2e7d32" />
              <Bar dataKey="review_hint" name="復習 ヒント正解" stackId="review" fill="#ffb300" />
              <Bar dataKey="review_incorrect" name="復習 不正解" stackId="review" fill="#c62828" />
              <Bar dataKey="weak_correct" name="苦手 正解" stackId="weak" fill="#81c784" />
              <Bar dataKey="weak_hint" name="苦手 ヒント正解" stackId="weak" fill="#ffb300" />
              <Bar dataKey="weak_incorrect" name="苦手 不正解" stackId="weak" fill="#ef9a9a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
