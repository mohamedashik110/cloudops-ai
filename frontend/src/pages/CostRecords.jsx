import { useEffect, useState } from "react";
import api from "../api/axios";
import Navbar from "../components/Navbar";

export default function CostRecords() {
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [serviceFilter, setServiceFilter] = useState("");

  useEffect(() => {
    loadRecords();
  }, [serviceFilter]);

  async function loadRecords() {
    setLoading(true);
    try {
      const query = serviceFilter ? `?service=${encodeURIComponent(serviceFilter)}` : "";
      const res = await api.get(`/cost-records/${query}`);
      setRecords(res.data);
    } catch (err) {
      setError("Failed to load cost records.");
    } finally {
      setLoading(false);
    }
  }

  const uniqueServices = [...new Set(records.map((r) => r.service))];

  return (
    <div>
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Cost Records</h1>
          <select
            value={serviceFilter}
            onChange={(e) => setServiceFilter(e.target.value)}
            className="filter-select"
          >
            <option value="">All Services</option>
            {uniqueServices.map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {error && <p className="page-error">{error}</p>}

        {loading ? (
          <p className="empty-note">Loading records...</p>
        ) : (
          <table className="data-table">
            <thead>
              <tr>
                <th>Service</th>
                <th>Amount</th>
                <th>Currency</th>
                <th>Date</th>
                <th>Region</th>
                <th>Source</th>
              </tr>
            </thead>
            <tbody>
              {records.length === 0 ? (
                <tr>
                  <td colSpan="6" className="empty-note">No cost records found.</td>
                </tr>
              ) : (
                records.slice(0, 100).map((r) => (
                  <tr key={r.id}>
                    <td>{r.service}</td>
                    <td>${parseFloat(r.amount).toFixed(2)}</td>
                    <td>{r.currency}</td>
                    <td>{r.date}</td>
                    <td>{r.region || "-"}</td>
                    <td>
                      <span className={`status-badge ${r.is_synthetic ? "status-pending" : "status-connected"}`}>
                        {r.is_synthetic ? "Demo" : "Real"}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        )}

        {records.length > 100 && (
          <p className="empty-note">Showing first 100 of {records.length} records.</p>
        )}
      </div>
    </div>
  );
}
