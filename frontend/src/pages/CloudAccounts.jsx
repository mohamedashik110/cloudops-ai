import { useEffect, useState } from "react";
import api from "../api/axios";
import { useAuth } from "../context/AuthContext";
import Navbar from "../components/Navbar";
import { Plus } from "lucide-react";

export default function CloudAccounts() {
  const { user } = useAuth();
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showForm, setShowForm] = useState(false);

  const [name, setName] = useState("");
  const [roleArn, setRoleArn] = useState("");
  const [region, setRegion] = useState("us-east-1");
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState("");

  const canManage = user?.role === "admin" || user?.role === "manager";

  useEffect(() => {
    loadAccounts();
  }, []);

  async function loadAccounts() {
    try {
      const res = await api.get("/cloud-accounts/");
      setAccounts(res.data);
    } catch (err) {
      setError("Failed to load cloud accounts.");
    } finally {
      setLoading(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");
    setSubmitting(true);

    try {
      await api.post("/cloud-accounts/", {
        name,
        role_arn: roleArn,
        aws_region: region,
      });
      setName("");
      setRoleArn("");
      setShowForm(false);
      loadAccounts();
    } catch (err) {
      setFormError(
        err.response?.data?.detail || "Failed to connect account."
      );
    } finally {
      setSubmitting(false);
    }
  }

  if (loading) return <div className="page-loading">Loading...</div>;

  return (
    <div>
      <Navbar />
      <div className="page-container">
        <div className="page-header">
          <h1>Cloud Accounts</h1>
          {canManage && (
            <button className="btn-primary" onClick={() => setShowForm(!showForm)}>
              <Plus size={16} /> Connect Account
            </button>
          )}
        </div>

        {error && <p className="page-error">{error}</p>}

        {showForm && canManage && (
          <form className="inline-form" onSubmit={handleSubmit}>
            <div className="form-row">
              <input
                placeholder="Account name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
              <input
                placeholder="Role ARN (arn:aws:iam::...)"
                value={roleArn}
                onChange={(e) => setRoleArn(e.target.value)}
                required
              />
              <input
                placeholder="Region"
                value={region}
                onChange={(e) => setRegion(e.target.value)}
              />
              <button type="submit" disabled={submitting}>
                {submitting ? "Connecting..." : "Connect"}
              </button>
            </div>
            {formError && <p className="error-msg">{formError}</p>}
          </form>
        )}

        <table className="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Provider</th>
              <th>Status</th>
              <th>Region</th>
              <th>Last Synced</th>
            </tr>
          </thead>
          <tbody>
            {accounts.length === 0 ? (
              <tr>
                <td colSpan="5" className="empty-note">
                  No cloud accounts connected yet.
                </td>
              </tr>
            ) : (
              accounts.map((acc) => (
                <tr key={acc.id}>
                  <td>{acc.name}</td>
                  <td>{acc.provider.toUpperCase()}</td>
                  <td>
                    <span className={`status-badge status-${acc.status}`}>
                      {acc.status}
                    </span>
                  </td>
                  <td>{acc.aws_region}</td>
                  <td>{acc.last_synced_at ? new Date(acc.last_synced_at).toLocaleString() : "Never"}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
