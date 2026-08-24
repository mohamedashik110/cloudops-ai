import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import api from "../api/axios";
import Navbar from "../components/Navbar";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444"];

export default function Dashboard() {
  const [summary, setSummary] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [forecastError, setForecastError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadData() {
      try {
        const summaryRes = await api.get("/analytics/summary/?days=90");
        setSummary(summaryRes.data);
      } catch (err) {
        setError("Failed to load cost summary.");
        setLoading(false);
        return;
      }

      try {
        const forecastRes = await api.get("/predictions/forecast/?days=30");
        const data = forecastRes.data;

        // predicted_total comes back as a string (DecimalField serialization),
        // and mae is a flat field, not nested - normalize both here.
        const hasUsableData =
          data && data.predicted_total !== undefined && data.mae !== undefined;

        if (hasUsableData) {
          setForecast({
            predicted_total: parseFloat(data.predicted_total),
            mae: parseFloat(data.mae),
          });
        } else {
          setForecastError("Forecast data was in an unexpected format.");
        }
      } catch (err) {
        setForecastError(
          err.response?.data?.error ||
            "Forecast unavailable (not enough data yet)."
        );
      }

      setLoading(false);
    }

    loadData();
  }, []);

  if (loading) return <div className="page-loading">Loading dashboard...</div>;
  if (error) return <div className="page-error">{error}</div>;

  const trendData = (summary?.trend || []).map((t) => ({
    date: t.date.slice(5),
    amount: t.amount,
  }));

  const pieData = (summary?.top_services || []).map((s) => ({
    name: s.service,
    value: s.amount,
  }));

  function formatMoney(value) {
    return typeof value === "number" ? `$${value.toFixed(2)}` : "N/A";
  }

  return (
    <div>
      <Navbar />
      <div className="dashboard-container">
        <h1>Dashboard</h1>

        <div className="stats-row">
          <div className="stat-card">
            <p className="stat-label">Total Cost (90d)</p>
            <p className="stat-value">{formatMoney(summary?.total_cost)}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Predicted (next 30d)</p>
            <p className="stat-value">{formatMoney(forecast?.predicted_total)}</p>
          </div>
          <div className="stat-card">
            <p className="stat-label">Forecast Accuracy (MAE)</p>
            <p className="stat-value">{formatMoney(forecast?.mae)}</p>
          </div>
        </div>

        {forecastError && <p className="forecast-warning">Note: {forecastError}</p>}

        <div className="charts-row">
          <div className="chart-card">
            <h3>Daily Cost Trend</h3>
            {trendData.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                  <XAxis dataKey="date" fontSize={12} />
                  <YAxis fontSize={12} />
                  <Tooltip />
                  <Line type="monotone" dataKey="amount" stroke="#3b82f6" strokeWidth={2} dot={false} />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <p className="empty-note">No trend data available.</p>
            )}
          </div>

          <div className="chart-card">
            <h3>Cost by Service</h3>
            {pieData.length > 0 ? (
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
            ) : (
              <p className="empty-note">No service data available.</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
