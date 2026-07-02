"""测试数据库插入"""
import sys
sys.path.insert(0, '.')
from app.core.database import SessionLocal
from app.models.user import UserProfile
from app.core.security import hash_password

db = SessionLocal()
try:
    user = UserProfile(
        username='testdirect8',
        email='testdirect8@test.com',
        password_hash=hash_password('Pass1234'),
        age=25,
        age_group='青少年',
        learning_goal='日常交流',
        interests=['music'],
        role='learner',
        assessment_completed=0,
    )
    db.add(user)
    db.commit()
    print('SUCCESS')
    db.refresh(user)
    print(f'User ID: {user.id}')
except Exception as e:
    db.rollback()
    print(f'ERROR: {type(e).__name__}: {e}')
finally:
    db.close()