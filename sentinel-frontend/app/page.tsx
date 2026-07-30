"use client";

import { useState } from "react";
import styles from "./page.module.css";

export default function Dashboard() {
  const [deviceId, setDeviceId] = useState("dev_10");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setData(null);
    setSearched(true);

    try {
      const response = await fetch(`/api/investigate/${deviceId}`);
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API returned status ${response.status}`);
      }
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header & Search */}
      <div className={styles.headerCard}>
        <div>
          <h1 className={styles.title}>Sentinel</h1>
          <p className={styles.subtitle}>Real-Time Fraud Network Investigator</p>
        </div>
        <form onSubmit={handleSearch} className={styles.searchForm}>
          <input
            type="text"
            value={deviceId}
            onChange={(e) => setDeviceId(e.target.value)}
            placeholder="Enter Device ID..."
            className={styles.searchInput}
          />
          <button 
            type="submit" 
            disabled={loading || !deviceId}
            className={styles.searchBtn}
          >
            Investigate
          </button>
        </form>
      </div>

      {error && <div className={styles.errorBanner}>{error}</div>}

      {/* Loading Skeletons */}
      {loading && (
        <div className={styles.dashboardGrid}>
          <div className={styles.kpiColumn}>
            {[1, 2, 3].map((i) => (
              <div key={i} className={styles.card}>
                <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '40%' }}></div>
                <div className={`${styles.skeleton} ${styles.skeletonBlock}`}></div>
              </div>
            ))}
          </div>
          <div className={styles.kpiColumn}>
            <div className={`${styles.card} ${styles.aiCard}`} style={{ height: '150px' }}>
              <div className={`${styles.skeleton} ${styles.skeletonText}`}></div>
              <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '80%' }}></div>
              <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '60%' }}></div>
            </div>
            <div className={`${styles.card} ${styles.tableCard}`} style={{ height: '400px' }}>
               <div style={{ padding: '1.5rem' }}>
                 <div className={`${styles.skeleton} ${styles.skeletonText}`} style={{ width: '30%', marginBottom: '2rem' }}></div>
                 {[1, 2, 3, 4, 5].map((i) => (
                   <div key={i} className={`${styles.skeleton} ${styles.skeletonText}`} style={{ height: '2rem', marginBottom: '1rem' }}></div>
                 ))}
               </div>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {!loading && !data && !error && (
        <div className={styles.emptyState}>
          <div className={styles.emptyIcon}>🛡️</div>
          <h2 className={styles.emptyTitle}>Ready to Investigate</h2>
          <p>Enter a Device ID above to scan the threat network and analyze risk.</p>
        </div>
      )}

      {/* Dashboard Content */}
      {!loading && data && (
        <div className={styles.dashboardGrid}>
          
          {/* Left Column: KPIs */}
          <div className={styles.kpiColumn}>
            <div className={styles.card}>
              <h3 className={styles.kpiLabel}>Risk Score</h3>
              <p className={`${styles.kpiValue} ${data.risk_score > 80 ? styles.scoreDanger : data.risk_score > 50 ? styles.scoreWarning : styles.scoreSafe}`}>
                {data.risk_score}/100
              </p>
            </div>
            <div className={styles.card}>
              <h3 className={styles.kpiLabel}>Connected Accounts</h3>
              <p className={styles.kpiValue}>{data.total_accounts}</p>
            </div>
            <div className={styles.card}>
              <h3 className={styles.kpiLabel}>Financial Exposure</h3>
              <p className={styles.kpiValue}>
                ${data.total_value_at_risk.toLocaleString(undefined, {minimumFractionDigits: 2, maximumFractionDigits: 2})}
              </p>
            </div>
          </div>

          {/* Right Column: AI Summary & Transactions */}
          <div className={styles.kpiColumn}>
            
            {/* Gemini AI Copilot Box */}
            <div className={`${styles.card} ${styles.aiCard}`}>
              <div className={styles.aiHeader}>
                <span className={styles.aiIcon}>✨</span>
                <h2 className={styles.aiTitle}>Gemini Investigation Copilot</h2>
              </div>
              <p className={styles.aiContent}>
                {data.ai_summary || "AI summarization unavailable. Please set GEMINI_API_KEY."}
              </p>
            </div>

            {/* Transactions Table */}
            <div className={`${styles.card} ${styles.tableCard}`}>
              <div className={styles.tableHeader}>
                <h3 className={styles.tableTitle}>Recent Connected Transactions</h3>
              </div>
              <table className={styles.txnTable}>
                <thead>
                  <tr>
                    <th>Txn ID</th>
                    <th>User ID</th>
                    <th>Amount</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {data.transactions?.map((txn: any) => (
                    <tr key={txn.txn_id} className={styles.txnRow}>
                      <td className={styles.mono}>{txn.txn_id.substring(0, 8)}...</td>
                      <td>{txn.user_id}</td>
                      <td className={styles.mono}>${txn.amount.toFixed(2)}</td>
                      <td>
                        <span className={`${styles.statusBadge} ${txn.status === 'flagged' ? styles.statusFlagged : styles.statusCleared}`}>
                          {txn.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

          </div>
        </div>
      )}
    </div>
  );
}
