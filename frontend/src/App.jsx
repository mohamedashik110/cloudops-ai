import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import CloudAccounts from "./pages/CloudAccounts";
import CostRecords from "./pages/CostRecords";
import Copilot from "./pages/Copilot";
import ProtectedRoute from "./components/ProtectedRoute";

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Login />} />
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/accounts" element={<ProtectedRoute><CloudAccounts /></ProtectedRoute>} />
          <Route path="/records" element={<ProtectedRoute><CostRecords /></ProtectedRoute>} />
          <Route path="/copilot" element={<ProtectedRoute><Copilot /></ProtectedRoute>} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
