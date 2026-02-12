import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Login from './pages/Login';
import Register from './pages/Register';
import ChildDashboard from './pages/ChildDashboard';
import Quiz from './pages/Quiz';
import MyStats from './pages/MyStats';
import MyWeakWords from './pages/MyWeakWords';
import ParentDashboard from './pages/ParentDashboard';
import ChildStats from './pages/ChildStats';
import ChildWeakWords from './pages/ChildWeakWords';

function RootRedirect() {
  const { user, loading } = useAuth();
  if (loading) return <div>読み込み中...</div>;
  if (!user) return <Navigate to="/login" />;
  if (user.role === 'parent') return <Navigate to="/parent" />;
  return <Navigate to="/child" />;
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <div className="app">
          <Routes>
            <Route path="/" element={<RootRedirect />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route path="/child" element={<ProtectedRoute role="child"><ChildDashboard /></ProtectedRoute>} />
            <Route path="/child/quiz" element={<ProtectedRoute role="child"><Quiz /></ProtectedRoute>} />
            <Route path="/child/stats" element={<ProtectedRoute role="child"><MyStats /></ProtectedRoute>} />
            <Route path="/child/weak-words" element={<ProtectedRoute role="child"><MyWeakWords /></ProtectedRoute>} />
            <Route path="/parent" element={<ProtectedRoute role="parent"><ParentDashboard /></ProtectedRoute>} />
            <Route path="/parent/child/:childId" element={<ProtectedRoute role="parent"><ChildStats /></ProtectedRoute>} />
            <Route path="/parent/child/:childId/weak-words" element={<ProtectedRoute role="parent"><ChildWeakWords /></ProtectedRoute>} />
          </Routes>
        </div>
      </AuthProvider>
    </BrowserRouter>
  );
}
