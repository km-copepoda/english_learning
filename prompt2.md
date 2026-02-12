# 英単語学習アプリ プロンプト (改訂版)

以下の仕様通りに英単語学習アプリをフルスタックで構築してください。backendとfrontendの2ディレクトリ構成で、Docker対応、バックエンドのテスト付きで作成してください。

---

## 技術スタック

- **Backend**: Python 3.12, FastAPI, SQLAlchemy (ORM), SQLite, JWT認証 (python-jose), bcrypt (直接使用、passlibは使わない)
- **Frontend**: React 19, TypeScript, Vite, React Router v7, Axios, Recharts v3
- **デプロイ**: Docker Compose (backend: uvicorn, frontend: nginx マルチステージビルド)
- **テスト**: pytest + starlette.testclient.TestClient (**httpxのASGITransportではなくTestClientを使用すること。ASGITransportはsync clientでは動作しない**)

---

## backend/requirements.txt

```
fastapi==0.115.0
uvicorn==0.30.6
sqlalchemy==2.0.35
python-jose[cryptography]==3.3.0
bcrypt==4.0.0
python-multipart==0.0.12
email-validator==2.0.0
pytest==8.0.0
httpx==0.27.0
```

> **注意**: pytest は1回だけ記載すること (重複しない)。httpx は starlette.testclient の内部依存として必要。

---

## frontend/package.json

```json
{
  "name": "english-vocab-app",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "axios": "^1.13.5",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-router-dom": "^7.13.0",
    "recharts": "^3.7.0"
  },
  "devDependencies": {
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "~5.6.0",
    "vite": "^6.0.0"
  }
}
```

> **注意**: devDependencies は省略不可。TypeScript + Viteビルドに必須。

---

## ディレクトリ構成

```
backend/
  app/
    __init__.py
    main.py
    config.py
    database.py
    models.py
    schemas.py
    auth.py
    api/
      __init__.py
      auth.py
      parent.py
      learning.py
      admin.py
    tests/
      __init__.py
      conftest.py
      test_auth.py
      test_parent.py
      test_learning.py
      test_admin.py
    data/
      english_master.csv
  requirements.txt
  Dockerfile
  .dockerignore

frontend/
  src/
    api/
      client.ts
    components/
      ProtectedRoute.tsx
    contexts/
      AuthContext.tsx
    pages/
      Login.tsx
      Register.tsx
      ChildDashboard.tsx
      Quiz.tsx
      MyStats.tsx
      MyWeakWords.tsx
      ParentDashboard.tsx
      ChildStats.tsx
      ChildWeakWords.tsx
    types/
      index.ts
    App.tsx
    App.css
    main.tsx
    vite-env.d.ts        ← 必須 (import.meta.envのTS型定義)
  index.html             ← 必須 (Viteエントリー)
  package.json
  tsconfig.json
  vite.config.ts
  nginx.conf
  Dockerfile
  .env.production
  .dockerignore

docker-compose.yml
```

---

## データベース設計 (SQLAlchemy, SQLite)

### users テーブル

| カラム | 型 | 備考 |
|---|---|---|
| id | Integer | PK, indexed |
| email | String | **nullable=True** (子アカウントにはemailがないため) |
| username | String | unique, indexed, nullable=False |
| hashed_password | String | bcryptハッシュ, nullable=False |
| role | String | "parent" or "child", nullable=False |
| parent_id | Integer | FK(users.id), nullable |
| created_at | DateTime | デフォルト: datetime.now(timezone.utc) |

自己参照リレーション:
- `children`: list, back_populates="parent", foreign_keys=[parent_id]
- `parent`: single, remote_side=[id], foreign_keys=[parent_id]
- `progress`: ChildProgress, uselist=False, back_populates="child"
- `learning_records`: list, back_populates="child"

### words テーブル

| カラム | 型 | 備考 |
|---|---|---|
| id | Integer | PK, indexed |
| english | String | nullable=False |
| japanese | String | nullable=False |
| english_katakana | String | 発音カタカナ, nullable=False |
| section | Integer | indexed, nullable=False |

### child_progress テーブル

| カラム | 型 | 備考 |
|---|---|---|
| id | Integer | PK, indexed |
| child_id | Integer | FK(users.id), unique, nullable=False |
| current_section | Integer | デフォルト=1 |
| last_section_date | DateTime | nullable |

リレーション: child (User, back_populates="progress")

### learning_records テーブル

| カラム | 型 | 備考 |
|---|---|---|
| id | Integer | PK, indexed |
| child_id | Integer | FK(users.id), indexed, nullable=False |
| word_id | Integer | FK(words.id), nullable=False |
| is_correct | Boolean | nullable=False |
| used_hint | Boolean | デフォルト=False |
| answered_at | DateTime | デフォルト: datetime.now(timezone.utc) |
| session_type | String | "today" / "review" / "weak", nullable=False |

リレーション: child (User), word (Word)

---

## Pydantic スキーマ (schemas.py)

```python
from datetime import datetime
from pydantic import BaseModel, EmailStr

# Auth
class ParentRegister(BaseModel):
    email: EmailStr
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserOut(BaseModel):
    id: int
    username: str
    role: str
    email: str | None = None
    model_config = {"from_attributes": True}

# Child Management
class ChildCreate(BaseModel):
    username: str
    password: str

class ChildPasswordUpdate(BaseModel):
    password: str

class ChildOut(BaseModel):
    id: int
    username: str
    created_at: datetime
    model_config = {"from_attributes": True}

# Words
class WordOut(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    section: int
    model_config = {"from_attributes": True}

# Learning
class AnswerSubmit(BaseModel):
    word_id: int
    answer: str
    session_type: str  # today, review, weak
    used_hint: bool = False

class AnswerResult(BaseModel):
    is_correct: bool
    correct_answer: str
    english_katakana: str

class QuizWord(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    model_config = {"from_attributes": True}

class MenuStatus(BaseModel):
    today: int
    review_week: int
    review_month: int
    review_over_month: int
    review_all: int
    weak_month: int
    weak_over_month: int
    weak_all: int

# Stats
class DailyStat(BaseModel):
    date: str
    today_correct: int
    today_hint: int          # ← ヒントフィールド必須
    today_incorrect: int
    review_correct: int
    review_hint: int         # ← ヒントフィールド必須
    review_incorrect: int
    weak_correct: int
    weak_hint: int           # ← ヒントフィールド必須
    weak_incorrect: int

class WeakWordOut(BaseModel):
    id: int
    english: str
    japanese: str
    english_katakana: str
    total_attempts: int
    correct_count: int
    hint_count: int
    accuracy: float
    model_config = {"from_attributes": True}
```

> **重要**: DailyStatには `today_hint`, `review_hint`, `weak_hint` の3フィールドが必須。TypeScript側のDailyStatインターフェースと一致させること。グラフの9本Barに対応。

---

## 設定 (config.py, 環境変数対応)

```python
import os
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24時間
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./vocab.db")
```

---

## データベース接続 (database.py)

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## main.py

- `Base.metadata.create_all(bind=engine)` でテーブル自動作成
- FastAPIアプリ作成: title="英単語学習アプリ API"
- CORS 設定: 環境変数 `CORS_ORIGINS` (カンマ区切り、デフォルト: `http://localhost:5173`)
- ルーター: auth, parent, learning, admin を include
- `GET /` → `{"message": "英単語学習アプリ API"}`

---

## 認証 (auth.py)

bcrypt を直接使用 (passlibは使わない。bcrypt==4.0 との互換性問題のため):

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())
```

- `create_access_token(data: dict) -> str`: JWT生成 (expiry付き)
- `OAuth2PasswordBearer(tokenUrl="api/auth/login")`
- `get_current_user`: JWTデコード → sub から username取得 → DBからユーザー取得。失敗時401
- `require_parent`: role="parent" チェック。不一致で 403 "親アカウントのみ利用可能です"
- `require_child`: role="child" チェック。不一致で 403 "子アカウントのみ利用可能です"
- エラーメッセージは全て日本語

---

## API エンドポイント

### 認証 API (api/auth.py)

- **POST /api/auth/register** → UserOut
  - 親アカウント登録 (email, username, password)
  - username重複 → 400 "このユーザー名は既に使用されています"
  - email重複 → 400 "このメールアドレスは既に使用されています"

- **POST /api/auth/login** → Token
  - username + password → JWT access_token 返却
  - 認証失敗 → 401 "ユーザー名またはパスワードが正しくありません"

- **GET /api/auth/me** → UserOut
  - Bearer Token → ユーザー情報返却

### 子アカウント API (api/parent.py) → require_parent

- **GET /api/parent/children** → list[ChildOut]
  - 自分の子アカウント一覧 (User.parent_id == parent.id)

- **POST /api/parent/children** → ChildOut (201)
  - 子アカウント作成 (username, password)
  - ChildProgress も同時作成 (db.flush() で child.id 確保)
  - username 重複 → 400

- **DELETE /api/parent/children/{child_id}**
  - 子アカウント削除 (learning_records → child_progress → user の順に削除)
  - 他の親の子 → 404 "子アカウントが見つかりません"

- **PUT /api/parent/children/{child_id}/password**
  - パスワード変更

- **GET /api/parent/children/{child_id}/stats?year=&month=** → list[DailyStat]
  - 月単位の日別学習統計
  - session_type 別にカテゴリ集計:
    - 正解(ヒントなし): is_correct=True AND used_hint=False
    - ヒント正解(ヒントあり正解): is_correct=True AND used_hint=True
    - 不正解: is_correct=False
  - 9フィールド: today_correct, today_hint, today_incorrect, review_correct, review_hint, review_incorrect, weak_correct, weak_hint, weak_incorrect
  - SQLAlchemy `case()` と `and_()` で集計
  - JST変換: `func.date(LearningRecord.answered_at, '+9 hours')` で UTC→JST変換してからグルーピング・フィルタ
  - その月の全日付分のデータを作成 (学習なしの日は全フィールド0、`timedelta(days=1)` でループ)

- **GET /api/parent/children/{child_id}/weak-words?sort_by=accuracy&order=asc** → list[WeakWordOut]
  - "純正正解率" (ヒントなし正解 / 全回答数) が 90%未満の単語
  - accuracy = `round(pure_correct / total_attempts, 3)` (pure_correct = correct_count - hint_count)
  - sort_by: accuracy (default), total_attempts, english, japanese
  - order: asc (default) / desc

> **共通ヘルパー `_get_weak_words(db, child_id, sort_by, order)`**: parent.py に定義。learning.py からも import して共用する。

### 学習 API (api/learning.py) → require_child

- **GET /api/learning/today** → list[QuizWord]
  - 今日のセクションの単語一覧 (ランダム順: `order_by(func.random())`)
  - **セクション進行ロジック**:
    1. `last_section_date` が null → 日付をセット (セクションは進めない。初回はsection=1のまま)
    2. `last_section_date` のJST日付が今日と異なる → `current_section += 1` して日付更新
    3. 同日 → 更新なし
  - `_get_progress`: progress がなければ新規作成

- **GET /api/learning/review?period=week|month|over_month|all** → list[QuizWord]
  - 過去に学習した単語 (learning_records に存在する word_id, distinct)
  - フィルタ期間:
    - week: `answered_at >= now - 7日`
    - month: `answered_at >= now - 30日`
    - over_month: `answered_at < now - 30日`
    - all: フィルタなし
  - 最大10問、ランダム順

- **GET /api/learning/weak?period=month|over_month|all** → list[QuizWord]
  - "純正正解率" (ヒントなし正解 / 全回答数) が 90%未満の単語
  - period フィルタは review と同様
  - 最大10問、ランダム順

- **POST /api/learning/answer** → AnswerResult
  - リクエスト: AnswerSubmit (word_id, answer, session_type, used_hint)
  - 単語が見つからない → 404 "単語が見つかりません"
  - 判定: `answer.strip().lower() == word.english.lower()`
  - LearningRecord に used_hint, answered_at も含めて記録
  - レスポンス: {is_correct, correct_answer (word.english), english_katakana}

- **GET /api/learning/menu-status** → MenuStatus
  - today: current_section の単語数
  - review_week / review_month / review_over_month / review_all: 各期間の学習済み単語数
  - weak_month / weak_over_month / weak_all: 各期間の苦手単語数

- **GET /api/learning/stats?year=&month=** → list[DailyStat]
  - 子自身の統計 (parent の child_stats と同じ集計ロジック)
  - require_child

- **GET /api/learning/weak-words?sort_by=&order=** → list[WeakWordOut]
  - 子自身の苦手単語一覧
  - parent.py の `_get_weak_words` ヘルパーを共用

### 管理 API (api/admin.py) → require_parent

- **POST /api/admin/import-words**
  - CSVファイルアップロード (`UploadFile = File(...)`)
  - UTF-8 BOM対応: `content.decode("utf-8-sig")`
  - `csv.DictReader` でパース (ヘッダ: english, japanese, english_katakana, section)
  - 各行: `strip()` して Word 作成
  - 重複チェック: english + japanese が既に存在すればスキップ
  - レスポンス: `{"detail": "N件の単語を登録しました (M件は既登録のためスキップ)"}`

---

## フロントエンド

### TypeScript 型定義 (types/index.ts)

```typescript
export interface UserOut {
  id: number;
  username: string;
  role: 'parent' | 'child';
  email?: string;
}

export interface ChildOut {
  id: number;
  username: string;
  created_at: string;
}

export interface QuizWord {
  id: number;
  english: string;
  japanese: string;
  english_katakana: string;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: string;
  english_katakana: string;
}

export interface MenuStatus {
  today: number;
  review_week: number;
  review_month: number;
  review_over_month: number;
  review_all: number;
  weak_month: number;
  weak_over_month: number;
  weak_all: number;
}

export interface DailyStat {
  date: string;
  today_correct: number;
  today_hint: number;
  today_incorrect: number;
  review_correct: number;
  review_hint: number;
  review_incorrect: number;
  weak_correct: number;
  weak_hint: number;
  weak_incorrect: number;
}

export interface WeakWordOut {
  id: number;
  english: string;
  japanese: string;
  english_katakana: string;
  total_attempts: number;
  correct_count: number;
  hint_count: number;
  accuracy: number;
}
```

### vite-env.d.ts (必須ファイル)

```typescript
/// <reference types="vite/client" />
```

> **注意**: このファイルがないと `import.meta.env` で TypeScriptエラーになる。

### index.html (Viteエントリー、必須ファイル)

```html
<!DOCTYPE html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>英単語学習アプリ</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

> **注意**: `noUnusedLocals: false`, `noUnusedParameters: false` にすること。strictにするとビルドが不必要に失敗する。

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### ルーティング (App.tsx)

| パス | コンポーネント | ロール |
|---|---|---|
| / | RootRedirect (ロール別リダイレクト) | - |
| /login | Login | - |
| /register | Register | - |
| /child | ChildDashboard | child |
| /child/quiz | Quiz | child |
| /child/stats | MyStats | child |
| /child/weak-words | MyWeakWords | child |
| /parent | ParentDashboard | parent |
| /parent/child/:childId | ChildStats | parent |
| /parent/child/:childId/weak-words | ChildWeakWords | parent |

- RootRedirect: loading 中は "読み込み中..."、未認証→ /login 、認証済→ロール別に /parent, /child
- ルートを `<BrowserRouter>` → `<AuthProvider>` → `<div className="app">` → `<Routes>` で囲む
- 子/親専用ルートは `<ProtectedRoute role="child">`, `<ProtectedRoute role="parent">` でラップ

### API クライアント (api/client.ts)

- Axios instance, baseURL: `import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"`
- リクエストインターセプター: localStorage の token を Bearer ヘッダーに付与
- レスポンスインターセプター: 401エラー時 → `/api/auth/` で始まるURL以外なら token 削除 + `window.location.href = "/login"` でリダイレクト

### 認証コンテキスト (AuthContext.tsx)

- state: `user: UserOut | null`, `loading: boolean`
- `fetchMe()`: GET /api/auth/me → user 取得。失敗時 user=null, loading=false
- 初回マウント時: token があれば fetchMe()。なければ setLoading(false) のみ
- `login(username, password)`: POST /api/auth/login → localStorage.setItem → fetchMe()
- `logout()`: localStorage.removeItem("token") → setUser(null)

### Protected Route (components/ProtectedRoute.tsx)

- Props: `{ children: ReactNode, role?: "parent" | "child" }`
- loading 中 → "読み込み中..."
- user 不在 → `<Navigate to="/login" />`
- role 不一致 → 正しいダッシュボードにリダイレクト

### Login (ログインページ)

- className: `auth-page`
- フォーム: ユーザ名 & パスワード
- `useAuth().login(username, password)` → 成功時 navigate("/")
- 失敗時: "ユーザー名またはパスワードが正しくありません" 表示
- リンク: "アカウントをお持ちでない方はこちら" → /register

### Register (親アカウント登録ページ)

- className: `auth-page`
- フォーム: メールアドレス, ユーザ名, パスワード
- POST /api/auth/register → 成功時 navigate("/login")
- 失敗時: APIの detail メッセージを表示。なければ "登録に失敗しました"
- リンク: "アカウントをお持ちの方はこちら" → /login

### ChildDashboard (子メニュー画面)

- className: `dashboard`
- GET /api/learning/menu-status でメニュー情報取得
- ヘッダー: `{username} さん` + 学習メニュー + ログアウトボタン (btn-secondary)
- メニュー項目 (menu-list):
  1. "今日の単語学習": menu.today > 0 で有効、バッジ (N問) → /child/quiz?mode=today
  2. "これまでに学習した単語": アコーディオン
     - 1週間以内 / 1ヶ月以内 / 1ヶ月以上 / 全範囲 → /child/quiz?mode=review&period=...
  3. "苦手単語学習": アコーディオン
     - 1ヶ月以内 / 1ヶ月以上 / 全範囲 → /child/quiz?mode=weak&period=...
  4. "学習進捗" → /child/stats
  5. "苦手単語一覧" → /child/weak-words
- count == 0 の項目は disabled class
- `openGroup` state で2つのアコーディオンが別々に開閉 (同じクリックで閉じる)

### Quiz (クイズ画面)

- URLから mode (today/review/weak) と period を取得 (useSearchParams)
- state: words, current, answer, result, score ({correct, hint, incorrect}), finished, showHint, usedHint
- inputRef で Input へのフォーカスを保持。current 更新時に focus()
- URLに応じたAPIを呼び出し

**固定スロットレイアウト** (quiz-card): 回答前後で画面レイアウトが変わらないよう各要素を固定配置:

| スロット | 回答前 | 回答後 |
|---|---|---|
| quiz-reading | `\u00A0` (ヒント時: "読み: " + カタカナ) | 同左 |
| quiz-japanese | japanese (青) | 同左 |
| quiz-mark | `\u00A0` | ◯(緑) or ✕(赤) |
| quiz-feedback | `\u00A0` | 不正解時のみ "正解: english カタカナ: katakana" |
| quiz-input | 入力可能 | 入力不可(disabled)、正解=緑枠、不正解=赤枠 |
| quiz-actions | 回答ボタン + ヒントボタン | 次の問題/結果を見る (Enter) |

**handleSubmit**:
- result がある状態で Submit → handleNext()
- 未回答なら POST /api/learning/answer
- スコア: is_correct かつ !usedHint → correct++、is_correct かつ usedHint → hint++、不正解 → incorrect++

**handleNext**: result=null, answer="", showHint=false, usedHint=false にリセット。最後なら setFinished(true)

**結果画面** (quiz-result): 正解数、ヒント正解数、不正解数。ボタン「メニューに戻る (Enter)」→ /child

### MyStats (子の統計画面)

- **データ取得**: GET `/api/learning/stats?year=&month=` (子自身用のエンドポイント)
- ヘッダー: `{username} さん 学習進捗` + 戻るボタン → /child
- 月間ナビ: < {year}年{month}月 > (月変更: 1月→前年12月、12月→翌年1月)

**サマリーカード** (stats-summary, 6項目):

| カード | 値 | 色 |
|---|---|---|
| 今日の学習 正解 | sum(today_correct) | #4caf50 |
| 復習 正解 | sum(review_correct) | #2e7d32 |
| 苦手 正解 | sum(weak_correct) | #81c784 |
| ヒント正解 | sum(today_hint + review_hint + weak_hint) | #ffb300 |
| 不正解 | sum(today_incorrect + review_incorrect + weak_incorrect) | #d32f2f |
| 正解率 | (totalCorrect / (totalCorrect + totalHint + totalIncorrect) * 100).toFixed(1)% | - |

> 分母0なら "-" 表示

**棒グラフ** (Recharts BarChart):
- ResponsiveContainer width="100%" height={250}
- XAxis: dataKey="date"
- Tooltip:
  - labelFormatter: `(v) => String(v).slice(5).replace('-', '/')` (**注意**: Recharts v3ではlabelの型がReactNodeなので `String(v)` でキャストが必要)
  - wrapperStyle: { zIndex: 20 }
  - itemSorter: 明示的な順序でインデックス返却

```typescript
const order = [
  "today_correct", "today_hint", "today_incorrect",
  "review_correct", "review_hint", "review_incorrect",
  "weak_correct", "weak_hint", "weak_incorrect",
];
return order.indexOf(item.dataKey as string);
```

- Legend: `content` プロップでカスタムレンダリング

**9本の Bar** (セクション種類ごとにスタック):

| dataKey | name | stackId | fill |
|---|---|---|---|
| today_correct | 正解 | today | #4caf50 |
| today_hint | ヒント正解 | today | #ffb300 |
| today_incorrect | 不正解 | today | #d32f2f |
| review_correct | 復習 正解 | review | #2e7d32 |
| review_hint | 復習 ヒント正解 | review | #ffb300 |
| review_incorrect | 復習 不正解 | review | #c62828 |
| weak_correct | 苦手 正解 | weak | #81c784 |
| weak_hint | 苦手 ヒント正解 | weak | #ffb300 |
| weak_incorrect | 苦手 不正解 | weak | #ef9a9a |

### ChildStats (親が子の成績を見る)

- useParams<{ childId: string }>() で childId 取得
- 「戻る」 → /parent
- MyStats と同じグラフ構成 **※サマリーカードなし！**
- GET /api/parent/children/{childId}/stats?year=&month=

### MyWeakWords (子が自分の苦手単語を見る)

- className: `weak-words-page`
- 戻る (btn-secondary) → /child
- GET /api/learning/weak-words?sort_by={sort.by}&order={sort.order}
- toggleSort(key): 同じキーなら order 反転、違うキーなら asc + キー更新
- テーブル (div className="table-wrap" で囲む):

| 列 | ソート | 表示 |
|---|---|---|
| 日本語 | sortable (japanese) | w.japanese |
| 英語 | sortable (english) | w.english |
| カタカナ読み | - | w.english_katakana |
| 全回答数 | sortable (total_attempts) | w.total_attempts |
| 正解数 | - | w.correct_count |
| ヒント使用 | - | w.hint_count |
| 正解率 | sortable (accuracy) | (w.accuracy * 100).toFixed(1)% |

- 苦手単語なし → "苦手単語はありません"
- ソートインジケーター: ▲ (asc) / ▼ (desc)

### ChildWeakWords (親が子の苦手単語を見る)

- useParams で childId 取得
- 「戻る」 → /parent
- テーブル表示は MyWeakWords と完全に同一
- データ取得元が `/api/parent/children/{childId}/weak-words` になる点のみ異なる

### ParentDashboard (親ダッシュボード)

- className: `dashboard`
- ヘッダー: `{username} さん 管理メニュー` + ログアウトボタン

**セクション1: 子アカウント管理**
- 0件: `<p>子アカウントがありません</p>`
- テーブル: ユーザ名、作成日(`new Date(created_at).toLocaleString()`)、操作
- 操作: 統計表示, 苦手単語, 削除 (btn-danger, confirm()で確認)

**セクション2: 子アカウント作成**
- インラインフォーム: ユーザー名 & パスワード + 作成ボタン
- POST /api/parent/children → 成功時フォームクリア + fetchChildren()

**セクション3: 単語CSVインポート**
- `<h3>単語CSVインポート</h3>`
- `<input type="file" accept=".csv" />` + インポートボタン (disabled={!selectedFile})
- POST /api/admin/import-words (FormData) → data.detail を表示
- エラー → "インポートに失敗しました"

---

## CSS (App.css)

### グローバル
- `* { box-sizing: border-box; margin: 0; padding: 0; }`
- `body`: font-family: "Helvetica Neue", Arial, "Hiragino Sans", sans-serif; background: #f5f5f5; color: #333; line-height: 1.6;
- `.app`: max-width: 800px, margin: 0 auto, padding: 20px

### 認証ページ (.auth-page)
- max-width: 400px, margin: 60px auto, 白背景, padding: 32px, border-radius: 12px, box-shadow: 0 2px 8px rgba(0,0,0,0.1)
- h1: text-align: center, margin-bottom: 24px
- .form-group: margin-bottom: 16px, label (display: block, font-weight: 600, font-size: 14px), input (width: 100%, padding: 10px 12px, border: 1px solid #ddd, border-radius: 8px, font-size: 16px)
- a: color: #1976d2

### エラー・情報メッセージ
- `.error`: color: #d32f2f, font-size: 14px, margin-bottom: 12px
- `.info`: color: #1976d2, font-size: 14px, margin-bottom: 12px

### ボタン
- `.btn-primary`: background: #1976d2, color: #fff, border: none, padding: 10px 20px, border-radius: 8px, font-size: 16px; hover: #1565c0; disabled: #bbb
- `.btn-secondary`: background: #fff, color: #333, border: 1px solid #ddd, padding: 10px 20px, border-radius: 8px, font-size: 14px; hover: #f5f5f5
- `.btn-danger`: background: #d32f2f, color: #fff, padding: 8px 16px, border-radius: 8px, font-size: 13px; hover: #c62828
- `.btn-hint`: background: #fff, color: #ff9800, border: 2px solid #ff9800, padding: 10px 20px, border-radius: 8px; hover: border-color #ff8e00, background #fff8e1

### ダッシュボード (.dashboard)
- .header: flex, space-between, align-items: center, margin-bottom: 24px
- h1: font-size: 22px
- .section: margin-bottom: 32px
- .menu-list: flex column, gap: 12px
- .menu-item: padding: 16px 20px, 白背景, border: 1px solid #ddd, border-radius: 8px, cursor: pointer, transition: background 0.2s
- .menu-item:hover:not(.disabled): background: #e3f2fd, border-color: #1976d2
- .menu-item.disabled: background: #eee, color: #aaa, cursor: not-allowed
- .menu-item-header: flex, align-items: center, justify-content: space-between
- .badge: font-size: 12px, color: #1976d2, background: #e3f2fd, padding: 2px 8px, border-radius: 12px, font-weight: 600

### アコーディオン
- .accordion-header: flex, space-between, align-items: center
- .accordion-header .arrow: transition: transform 0.2s, color: #aaa
- .accordion-header .arrow.open: transform: rotate(90deg)
- .accordion-body: flex column, gap: 8px, padding-top: 12px
- .menu-item-sub: padding: 12px 16px, font-size: 15px, border-radius: 8px

### 統計
- .stats-summary: display: flex, flex-wrap: wrap, gap: 16px, margin-bottom: 24px
- .stat-card: flex: 1, min-width: 100px, background: #fff, border-radius: 12px, padding: 16px, box-shadow: 0 1px 4px rgba(0,0,0,0.08)
- .stat-label: font-size: 13px, color: #666, margin-bottom: 4px
- .stat-value: font-size: 24px, font-weight: 700
- .month-nav: display: flex, gap: 20px, align-items: center, justify-content: center, padding: 16px, background: #fafafa, border-radius: 10px, margin-bottom: 24px
- .month-nav button: padding: 8px 12px, border: 1px solid #ddd, border-radius: 8px, background: #fff, font-size: 18px

### チャート
- .chart-container: display: flex, justify-content: center, margin-top: 24px
- .chart-box: width: 100%, position: relative, z-index: 1

### テーブル
- .table-wrap: width: 100%, overflow-x: auto, -webkit-overflow-scrolling: touch
- table: width: 100%, border-collapse: collapse
- th, td: padding: 12px, border-bottom: 1px solid #eee, text-align: center, font-size: 14px
- th: font-weight: 600, background: #fafafa
- th.sortable: cursor: pointer, user-select: none; hover: #f0f0f0
- .actions: display: flex, gap: 8px, justify-content: center

### インラインフォーム (.inline-form)
- display: flex, gap: 10px, align-items: center, flex-wrap: wrap
- input: width: auto, flex: 1, min-width: 140px, padding: 10px 12px, border: 1px solid #ddd, border-radius: 8px, font-size: 14px

### クイズ
- .quiz-header: flex, space-between, align-items: center, margin-bottom: 16px, font-size: 18px
- .quiz-card: 白背景, border-radius: 12px, box-shadow: 0 2px 8px, padding: 32px, text-align: center, margin-bottom: 24px
- .quiz-reading: display: flex, height: 28px, justify-content: center, align-items: center, font-size: 18px, margin-bottom: 8px
- .hint-color: color: #ff9800, font-weight: 700
- .quiz-japanese: font-size: 28px, color: #1976d2, margin-bottom: 20px, font-weight: 600
- .quiz-mark: font-size: 40px, font-weight: 700, min-height: 48px
- .quiz-mark .correct: color: #4caf50
- .quiz-mark .incorrect: color: #d32f2f
- .quiz-feedback: margin-top: 16px, background: #fafafa, padding: 12px, border-radius: 8px, min-height: 44px
- .quiz-input-row: flex, align-items: center, justify-content: center, gap: 12px, margin-top: 16px
- .quiz-input: font-size: 24px, padding: 8px 16px, width: 200px, text-align: center, border: 2px solid #ddd, border-radius: 8px
- .quiz-input.correct: border-color: #4caf50, color: #4caf50
- .quiz-input.incorrect: border-color: #d32f2f, color: #d32f2f
- .quiz-actions: flex, justify-content: center, gap: 12px, margin-top: 24px
- .quiz-result: text-align: center, 白背景, border-radius: 12px, box-shadow, padding: 32px

### レスポンシブ

**@media (max-width: 768px) -- タブレット:**
- .app: padding: 16px 12px
- .stat-card: flex: 1 1 calc(33.3% - 8px), min-width: 0, padding: 12px 8px
- .stat-value: font-size: 20px
- .quiz-card: padding: 24px 16px
- .quiz-japanese: font-size: 24px
- .quiz-input: font-size: 20px, width: 100%, max-width: 280px
- .quiz-mark: font-size: 32px
- th, td: padding: 8px 10px, font-size: 13px, white-space: nowrap
- .auth-page: margin: 30px 12px, padding: 24px 20px
- .month-nav: flex-wrap: wrap, gap: 12px

**@media (max-width: 480px) -- スマホ:**
- .app: padding: 12px 10px
- .header: flex-direction: column, align-items: flex-start, gap: 8px
- .dashboard h1: font-size: 20px
- .stat-card: flex: 1 1 calc(50% - 6px) (2列)
- .quiz-reading: font-size: 16px
- .quiz-japanese: font-size: 22px
- .quiz-input: font-size: 18px, width: 100%
- .quiz-mark: font-size: 28px
- th, td: padding: 8px 6px, font-size: 12px
- .inline-form input: width: 100%, flex: none

---

## Docker

### backend/Dockerfile

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile (マルチステージ)

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

### frontend/nginx.conf

```nginx
server {
    listen 80;
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location / {
        root /usr/share/nginx/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }
}
```

### frontend/.env.production

```
VITE_API_BASE_URL=/api
```

### docker-compose.yml

```yaml
services:
  backend:
    build: ./backend
    volumes:
      - db-data:/app/data
    environment:
      - DATABASE_URL=sqlite:////app/data/vocab.db
      - SECRET_KEY=change-me-in-production
      - CORS_ORIGINS=*
  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - backend
volumes:
  db-data:
```

### .dockerignore

- backend: `__pycache__`, `.pytest_cache`, `.venv`, `.env`, `vocab.db`, `tests/`, `pytest_cache`
- frontend: `node_modules`, `dist`, `.vite`

---

## テスト (pytest)

### conftest.py

> **重要**: テストクライアントは `starlette.testclient.TestClient` を使用すること。httpx の `ASGITransport` + `Client` は同期テストでは動作しない (`__enter__` ではなく `__aenter__` を持つため)。

```python
from starlette.testclient import TestClient
```

- SQLite in-memory DB: `create_engine("sqlite:///:memory:", poolclass=StaticPool)`
- `app.dependency_overrides[get_db]` でテスト用DBを注入
- `@pytest.fixture(scope="session") setup_db`: テスト前に create_all → テスト後 drop_all

**フィクスチャ:**
- `client`: `TestClient(app)` (with ステートメント)
- `parent_user`: username="testparent", email="parent@test.com", role="parent", password="parentpass"
- `parent_token`, `parent_headers`: JWT + Authorizationヘッダー
- `child_user`: username="testchild", role="child", parent_id=parent_user.id, password="childpass" (ChildProgressも作成)
- `child_token`, `child_headers`: JWT + Authorizationヘッダー
- `child_id`: child_user.id
- `sample_words`: 5問登録
  - section 1: apple/りんご/アップル, banana/バナナ/バナナ, cat/猫/キャット
  - section 2: dog/犬/ドッグ, egg/卵/エッグ

### test_auth.py (9テスト)

1. `test_register_parent`: 親アカウント作成 → 200, username/role/email確認
2. `test_register_duplicate_username`: 二重登録 → 400, "ユーザー名" 含むメッセージ
3. `test_register_duplicate_email`: 二重メール → 400, "メールアドレス" 含むメッセージ
4. `test_login_success`: 正しい認証 → JWT取得, access_token + token_type="bearer"
5. `test_login_wrong_password`: 不正パスワード → 401
6. `test_login_nonexistent_user`: 存在しないユーザー → 401
7. `test_get_me_no_token`: トークンなし → 401
8. `test_get_me_success`: 親トークン → ユーザー情報取得
9. `test_get_me_child`: 子トークン → 情報取得確認

### test_parent.py (12テスト)

1. `test_list_children`: 自分の子アカウント一覧
2. `test_list_children_empty`: 子なし → 空配列
3. `test_create_child_success`: 子アカウント作成 → 201
4. `test_create_child_duplicate_username`: 重複 → 400
5. `test_delete_child`: 削除成功 → 一覧から消滅
6. `test_delete_other_parent_child`: 他の親の子 → 404
7. `test_update_child_password`: パスワード変更 → 新パスワードでログイン成功
8. `test_child_stats`: session_type別の集計 (2025-02-28 06:00 UTC = 2025-02-28 15:00 JST)
9. `test_child_stats_empty`: 学習なし → 全日0埋め
10. `test_child_weak_words_limit`: accuracy < 0.9 の単語のみ
11. `test_child_weak_words_has_hint_count`: hint_count=2, total=5, correct=3
12. `test_parent_endpoints_require_parent_role`: childロール → 403

### test_learning.py (18テスト)

1. `test_today_words_initial`: 初回セクション1 → 3単語 (apple, banana, cat)
2. `test_today_words_section_advance`: yesterday設定 → セクション2に進行 → 2単語 (dog, egg)
3. `test_today_words_no_advance`: 同日 → 進行なし
4. `test_review_words_empty`: 記録なし → 空
5. `test_review_words_all`: 全範囲で抽出
6. `test_weak_words_none_when_all_correct`: 全正解(ヒントなし) → 空
7. `test_weak_words_with_hint`: ヒント使用 → 苦手判定
8. `test_answer_correct`: "Apple" → 正解 (大文字小文字無視)
9. `test_answer_correct_with_hint`: ヒントあり正解
10. `test_answer_incorrect`: "orange" → 不正解
11. `test_answer_nonexistent_word`: 存在しないID → 404
12. `test_menu_status`: 各件数確認
13. `test_stats`: 4レコード → 3月15日/3月31日の各件数確認
14. `test_my_weak_words`: 子自身の苦手一覧
15. `test_my_weak_words_sort`: ソート確認
16. `test_weak_words_accuracy_calc`: accuracy=0.167 (1/6)
17. `test_learning_endpoints_require_child_role`: parentロール → 403 (today, review, weak, answer)
18. `test_menu_status_require_child`: parentロール → menu-status 403

### test_admin.py (4テスト)

1. `test_import_words`: CSV登録 → "3件" 含むメッセージ
2. `test_import_words_duplicate_skip`: 再登録 → "スキップ" 含むメッセージ
3. `test_import_words_require_parent`: childロール → 403
4. `test_import_words_no_auth`: 未認証 → 401

---

## 学習用英単語CSVデータ (backend/app/data/english_master.csv)

> **注意**: japanese フィールドにカンマを含めないこと。CSVパースが壊れる。

```csv
english,japanese,english_katakana,section
boy,少年,ボーイ,1
girl,少女,ガール,1
teacher,先生,ティーチャー,1
student,学生,ステューデント,1
friend,友達,フレンド,1
man,男,マン,1
woman,女,ウーマン,1
child,子供,チャイルド,1
baby,赤ちゃん,ベイビー,1
family,家族,ファミリィ,1
day,日,デイ,2
hour,1時間,アウア,2
minute,分,ミニット,2
morning,朝,モーニング,2
afternoon,午後,アフタヌーン,2
evening,夕方,イーブニング,2
week,週,ウィーク,2
month,月,マンス,2
year,年,イヤー,2
season,季節,シーズン,2
night,夜,ナイト,2
noon,正午,ヌーン,2
```

---

## 起動方法

### ローカル開発

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend (別ターミナル):**
```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker-compose up --build
# http://localhost:3000
```

### テスト

```bash
cd backend
pytest
```

期待結果: 43テスト全通過

---

## 実装時の注意事項まとめ

1. **DailyStat hintフィールド**: Python側スキーマとTypeScript側の両方に `today_hint`, `review_hint`, `weak_hint` を含めること
2. **テストクライアント**: `starlette.testclient.TestClient` を使用。httpx の `ASGITransport` + 同期 `Client` は不可
3. **User.email**: `nullable=True` にすること (子アカウントにはemailがない)
4. **vite-env.d.ts**: `/// <reference types="vite/client" />` を `src/` に配置必須
5. **index.html**: `frontend/` 直下に配置必須 (Viteのエントリー)
6. **devDependencies**: TypeScript, @types/react, @types/react-dom, @vitejs/plugin-react, vite を含むこと
7. **CSVデータ**: japanese フィールドにカンマを含めない (CSV破損防止)
8. **Tooltip labelFormatter**: Recharts v3では `(v) => String(v).slice(5)...` と型キャストが必要
9. **子自身のエンドポイント**: `/api/learning/stats` と `/api/learning/weak-words` を追加すること
10. **_get_weak_words ヘルパー**: parent.py に定義して learning.py から import して共用
11. **セクション進行**: 初回(last_section_date=null)はsection=1のまま日付セットのみ。翌日以降に+1
12. **requirements.txt**: pytest の重複記載に注意
13. **tsconfig.json**: noUnusedLocals と noUnusedParameters は false にする
