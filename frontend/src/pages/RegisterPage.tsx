import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useAuthStore } from '../store/useAuthStore';

const pageStyle = {
  width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column' as const,
  alignItems: 'center', justifyContent: 'center',
  fontFamily: "'JetBrains Mono', monospace", background: '#fafafa',
  backgroundImage: 'radial-gradient(circle, #e0e0e0 0.8px, transparent 0.8px)', backgroundSize: '20px 20px',
};

const cardStyle = {
  background: '#fff', borderRadius: '6px',
  border: '1px solid #e8e8e8', boxShadow: '0 2px 12px rgba(0,0,0,0.04)',
  padding: '28px 32px', width: '340px',
};

const inputStyle = {
  width: '100%', padding: '8px 10px', fontSize: '13px',
  fontFamily: 'inherit', border: '1px solid #e0e0e0', borderRadius: '3px',
  outline: 'none', color: '#333', boxSizing: 'border-box' as const,
  marginTop: '6px',
};

const btnStyle = {
  width: '100%', padding: '10px', fontSize: '12px', fontWeight: 600,
  fontFamily: 'inherit', letterSpacing: '2px',
  background: '#333', color: '#fff', border: 'none',
  borderRadius: '20px', cursor: 'pointer',
  marginTop: '16px',
};

export function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);
  const register = useAuthStore((s) => s.register);
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setSuccess(false);
    setLoading(true);
    const result = await register(email, password);
    setLoading(false);
    if (result.success) {
      setSuccess(true);
      setTimeout(() => navigate('/login'), 1500);
    } else {
      setError(result.error || 'Registration failed');
    }
  };

  return (
    <div style={pageStyle}>
      <div style={{ fontSize: '10px', fontWeight: 700, letterSpacing: '3px', color: '#ccc', marginBottom: '32px' }}>
        TRAIN MY OWN GPT
      </div>
      <div style={cardStyle}>
        <div style={{ fontSize: '11px', fontWeight: 600, letterSpacing: '2px', color: '#333', marginBottom: '20px', textTransform: 'uppercase' }}>
          Register
        </div>
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: '9px', color: '#999', marginTop: '8px' }}>email</div>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
            required style={inputStyle} placeholder="user@example.com" autoFocus />
          <div style={{ fontSize: '9px', color: '#999', marginTop: '14px' }}>password</div>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
            required style={inputStyle} placeholder="••••••••" />
          {error && <div style={{ fontSize: '10px', color: '#ef4444', marginTop: '12px' }}>{error}</div>}
          {success && <div style={{ fontSize: '10px', color: '#22c55e', marginTop: '12px' }}>Registration successful! Redirecting to login...</div>}
          <button type="submit" disabled={loading || success} style={btnStyle}>
            {loading ? '...' : 'REGISTER'}
          </button>
        </form>
        <div style={{ fontSize: '10px', color: '#bbb', marginTop: '16px', textAlign: 'center' }}>
          Already have an account?{' '}
          <Link to="/login" style={{ color: '#555', textDecoration: 'underline' }}>Log in</Link>
        </div>
      </div>
    </div>
  );
}
