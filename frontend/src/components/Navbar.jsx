import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { LogOut } from "lucide-react";

export default function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  function handleLogout() {
    logout();
    navigate("/");
  }

  return (
    <nav className="navbar">
      <div className="navbar-brand">CloudOps AI</div>
      <div className="navbar-links">
        <a href="/dashboard">Dashboard</a>
        <a href="/accounts">Cloud Accounts</a>
        <a href="/records">Cost Records</a>
        <a href="/copilot">Copilot</a>
      </div>
      <div className="navbar-user">
        <span>{user?.username} ({user?.role})</span>
        <button onClick={handleLogout}>
          <LogOut size={16} /> Logout
        </button>
      </div>
    </nav>
  );
}
