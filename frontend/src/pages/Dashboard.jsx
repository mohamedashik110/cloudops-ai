import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const [summaryRes, forecastRes] = await Promise.all([
          api.get("/analytics/summary/?days=90"),
          api.get("/predictions/forecast/?days=30"),
        ]);
        setSummary(summaryRes.data);
        setForecast(forecastRes.data);
      } catch (err) {
        setError("Failed to load dashboard data.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="page-loading">Loading dashboard...</div>;
  if (error) return <div className="page-error">{error}</div>;

  const trendData = summary.trend.map((t) => ({
    date: t.date.slice(5),
    amount: t.amount,
  }));

  const pieData = summary.top_services.map((s) => ({
    name: s.service,
    value: s.amount,
  }));

  return (
    <div>
      <Navbar />
      <div className="dashboard-container">
        <h1>Dashboard</h1>

        <div className="stats-row">
          <div className="stat-card">
            <p className="stat-label">Total Cost (90d)</p>
            <p className="stat-value">${summary.total_cost.toFixed(2)}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Predicted (next 30d)</p>
            <p className="stat-value">${forecast.predicted_total.toFixed(2)}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Forecast Accuracy (MAE)</p>
            <p className="stat-value">${forecast.model_confidence.mae.toFixed(2)}</p>
          </div>
        </div>

        <div className="charts-row">
          <div className="chart-card">
            <h3>Daily Cost Trend</h3>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" fontSize={12} />
                <YAxis fontSize={12} />
                <Tooltip />
                <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="chart-card">
            <h3>Cost by Service</h3>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={80} label>
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    </div>
  );
}
