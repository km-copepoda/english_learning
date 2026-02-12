import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import api from '../api/client';
import { QuizWord, AnswerResult } from '../types';

export default function Quiz() {
  const [searchParams] = useSearchParams();
  const mode = searchParams.get('mode') || 'today';
  const period = searchParams.get('period') || '';
  const navigate = useNavigate();

  const [words, setWords] = useState<QuizWord[]>([]);
  const [current, setCurrent] = useState(0);
  const [answer, setAnswer] = useState('');
  const [result, setResult] = useState<AnswerResult | null>(null);
  const [score, setScore] = useState({ correct: 0, hint: 0, incorrect: 0 });
  const [finished, setFinished] = useState(false);
  const [showHint, setShowHint] = useState(false);
  const [usedHint, setUsedHint] = useState(false);
  const [loading, setLoading] = useState(true);
  const inputRef = useRef<HTMLInputElement>(null);
  const finishBtnRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    let url = '';
    if (mode === 'today') url = '/api/learning/today';
    else if (mode === 'review') url = `/api/learning/review?period=${period}`;
    else if (mode === 'weak') url = `/api/learning/weak?period=${period}`;
    api.get(url).then((res) => {
      setWords(res.data);
      setLoading(false);
    });
  }, [mode, period]);

  useEffect(() => {
    if (finished) {
      finishBtnRef.current?.focus();
    } else {
      inputRef.current?.focus();
    }
  }, [current, loading, finished]);

  if (loading) return <div>読み込み中...</div>;

  const word = words[current];

  const handleSubmit = async (e?: React.FormEvent) => {
    e?.preventDefault();
    if (result) {
      handleNext();
      return;
    }
    if (!answer.trim()) return;
    try {
      const res = await api.post('/api/learning/answer', {
        word_id: word.id,
        answer: answer.trim(),
        session_type: mode,
        used_hint: usedHint,
      });
      const data: AnswerResult = res.data;
      setResult(data);
      if (data.is_correct && !usedHint) {
        setScore((s) => ({ ...s, correct: s.correct + 1 }));
      } else if (data.is_correct && usedHint) {
        setScore((s) => ({ ...s, hint: s.hint + 1 }));
      } else {
        setScore((s) => ({ ...s, incorrect: s.incorrect + 1 }));
      }
    } catch {
      alert('通信エラーが発生しました。もう一度お試しください。');
    }
  };

  const handleNext = () => {
    if (current + 1 >= words.length) {
      setFinished(true);
      return;
    }
    setResult(null);
    setAnswer('');
    setShowHint(false);
    setUsedHint(false);
    setCurrent((c) => c + 1);
  };

  const handleHint = () => {
    setShowHint(true);
    setUsedHint(true);
    inputRef.current?.focus();
  };

  if (!word && !finished) {
    return (
      <div className="quiz-result">
        <h2>問題がありません</h2>
        <button className="btn-primary" onClick={() => navigate('/child')}>メニューに戻る</button>
      </div>
    )
  }
  if (finished) {
    return (
      <div className="quiz-result">
        <h2>お疲れ様でした！</h2>
        <p>正解数: {score.correct}</p>
        <p>ヒント正解数: {score.hint}</p>
        <p>不正解数: {score.incorrect}</p>
        <button
          ref={finishBtnRef}
          className="btn-primary"
          onClick={() => navigate('/child')}
        >
          メニューに戻る (Enter)
        </button>
      </div>
    );
  }


  const isCorrect = result?.is_correct && !usedHint;
  const isHintCorrect = result?.is_correct && usedHint;

  return (
    <div>
      <div className="quiz-header">
        <span>{current + 1} / {words.length}</span>
        <button className="btn-secondary" onClick={() => navigate('/child')}>やめる</button>
      </div>
      <div className="quiz-card">
        <div className="quiz-reading">
          {showHint || (result && !result.is_correct) ? (
            <span><span className="hint-color">読み: </span>{word.english_katakana}</span>
          ) : '\u00A0'}
        </div>
        <div className="quiz-japanese">{word.japanese}</div>
        <form onSubmit={handleSubmit}>
          <div className="quiz-input-row">
            <span style={{ color: '#1976d2' }}>英:</span>
            <input
              ref={inputRef}
              className={`quiz-input ${result ? (result.is_correct ? 'correct' : 'incorrect') : ''}`}
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              readOnly={!!result}
            />
            <span className="quiz-mark-inline">
              {result ? (
                result.is_correct
                  ? <span className="correct">&#9675;</span>
                  : <span className="incorrect">&#10005;</span>
              ) : '\u00A0'}
            </span>
          </div><div className="quiz-feedback">
            {result ? (
              <span>正解: {result.correct_answer}</span>
            ) : '\u00A0'}
          </div>
          <div className="quiz-actions">
            {!result && (
              <>
                <button type="submit" className="btn-primary">回答</button>
                <button type="button" className="btn-hint" onClick={handleHint}>ヒントを見る</button>
              </>
            )}
            {result && (
              <button type="submit" className="btn-primary">
                {current + 1 >= words.length ? '結果を見る (Enter)' : '次の問題 (Enter)'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
}
