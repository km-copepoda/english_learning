import { ReactNode } from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

interface Props {
  children: ReactNode;
  role?: 'parent' | 'child';
}

export default function ProtectedRoute({ children, role }: Props) {
  const { user, loading } = useAuth();

  if (loading) return <div>読み込み中...</div>;
  if (!user) return <Navigate to="/login" />;

  if (role && user.role !== role) {
    if (user.role === 'parent') return <Navigate to="/parent" />;
    if (user.role === 'child') return <Navigate to="/child" />;
  }

  return <>{children}</>;
}
