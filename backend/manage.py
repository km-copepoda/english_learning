"""テスト用の日付操作スクリプト

使い方:
  # 日付を1日戻す(次回アクセスでセクションが進む)
  python manage.py shift kazuki -1

  # 日付を3日戻す
  python manage.py shift kazuki -3

  # 日付を1日進める
  python manage.py shift kazuki 1

  # 現在の状態を確認
  python manage.py status kazuki
"""

import sys
from datetime import timedelta

from app.database import SessionLocal
from app.models import ChildProgress, LearningRecord, User


def get_child(db, username):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        print(f"ユーザ '{username}'が見つかりません")
        sys.exit(1)
    if user.role != "child":
        print(f"'{username}' は子アカウントではありません (role={user.role})")
        sys.exit(1)
    return user


def show_status(db, username):
    user = get_child(db, username)
    progress = (
        db.query(ChildProgress)
        .filter(ChildProgress.child_id == user.id)
        .first()
    )
    if not progress:
        print("進捗データがありません")
        return
    
    print(f"ユーザ: {username} (id={user.id})")
    print(f"現在のセクション: {progress.current_section}")
    if progress.last_section_date:
        jst = progress.last_section_date + timedelta(hours=9)
        print(f"最終学習日時 (UTC): {progress.last_section_date}")
        print(f"最終学習日時 (JST): {jst}")
    else:
        print("最終学習日時: なし")
    
    record_count = (
        db.query(LearningRecord)
        .filter(LearningRecord.child_id == user.id)
        .count()
    )
    print(f"学習レコード数: {record_count}")


def shift_date(db, username, days):
    user = get_child(db, username)
    progress = (
        db.query(ChildProgress)
        .filter(ChildProgress.child_id == user.id)
        .first()
    )
    if not progress:
        print("進捗データがありません")
        return
    
    if progress.last_section_date is None:
        print("最終学習日時が未設定です")
        return
    
    old = progress.last_section_date
    progress.last_section_date = old + timedelta(days=days)

    records = (
        db.query(LearningRecord)
        .filter(LearningRecord.child_id == user.id)
        .all()
    )
    for r in records:
        r.answered_at = r.answered_at + timedelta(days=days)

    db.commit()

    direction = f"{days}日進めました" if days > 0 else f"{abs(days)}日戻しました"
    print(f"ユーザ '{username}'の日付を{direction}")
    print(f" last_section*date: {old} -> {progress.last_section_date}")
    print(f" 学習レコード {len(records)}件の日付も更新しました")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1]
    username = sys.argv[2]

    db = SessionLocal()
    try:
        if command == "status":
            show_status(db, username)
        elif command == "shift":
            if len(sys.argv) < 4:
                print("日数を指定してください (ex: -1, 1, -3)")
                sys.exit(1)
            days = int(sys.argv[3])
            shift_date(db, username, days)
        else:
            print(f"不明なコマンド: {command}")
            print(__doc__)
            sys.exit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()