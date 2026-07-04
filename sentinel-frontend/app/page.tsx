"use client";

import { useState } from "react";

export default function Dashboard() {
  const [deviceId, setDeviceId] = useState("dev_10");
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setData(null);

    try {
      const response = await fetch(`https://sentinel-api-859134894750.us-central1.run.app/api/investigate/${deviceId}`);
      if (!response.ok) throw new Error("Device not found or API error.");
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-sans">
      <div className="max-w-6xl mx-auto space-y-6">
        
        {/* Header & Search */}
        <div className="flex items-center justify-between bg-gray-900 p-6 rounded-xl border border-gray-800">
          <div>
            <h1 className="text-2xl font-bold text-blue-400">Sentinel</h1>
            <p className="text-gray-400 text-sm">Real-Time Fraud Network Investigator</p>
          </div>
          <form onSubmit={handleSearch} className="flex gap-2">
            <input
              type="text"
              value={deviceId}
              onChange={(e) => setDeviceId(e.target.value)}
              placeholder="Enter Device ID..."
              className="bg-gray-800 border border-gray-700 rounded-lg px-4 py-2 focus:outline-none focus:border-blue-500"
            />
            <button 
              type="submit" 
              disabled={loading}
              className="bg-blue-600 hover:bg-blue-500 px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Scanning..." : "Investigate"}
            </button>
          </form>
        </div>

        {error && <div className="p-4 bg-red-900/50 border border-red-500 text-red-200 rounded-lg">{error}</div>}

        {/* Dashboard Content */}
        {data && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            
            {/* Left Column: KPIs */}
            <div className="col-span-1 space-y-4">
              <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Risk Score</h3>
                <p className={`text-5xl font-bold ${data.network_data.risk_score > 80 ? 'text-red-500' : 'text-green-500'}`}>
                  {data.network_data.risk_score}/100
                </p>
              </div>
              <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Connected Accounts</h3>
                <p className="text-4xl font-bold text-orange-400">{data.network_data.total_accounts}</p>
              </div>
              <div className="bg-gray-900 p-6 rounded-xl border border-gray-800">
                <h3 className="text-gray-400 text-sm font-semibold uppercase tracking-wider mb-2">Financial Exposure</h3>
                <p className="text-4xl font-bold text-gray-100">
                  ${data.network_data.total_value_at_risk.toLocaleString()}
                </p>
              </div>
            </div>

            {/* Right Column: AI Summary & Transactions */}
            <div className="col-span-2 space-y-6">
              
              {/* Gemini AI Copilot Box */}
              <div className="bg-gradient-to-r from-blue-900/40 to-purple-900/40 p-6 rounded-xl border border-blue-500/30">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-xl">✨</span>
                  <h2 className="text-lg font-semibold text-blue-300">Gemini Investigation Copilot</h2>
                </div>
                <p className="text-gray-200 leading-relaxed text-lg">
                  {/* Ideally, you'd fetch the AI summary here or it would be included in the backend response. */}
                  {data.ai_summary || "Please run a separate request to fetch AI Summary or update backend to include it."}
                </p>
              </div>

              {/* Transactions Table */}
              <div className="bg-gray-900 rounded-xl border border-gray-800 overflow-hidden">
                <div className="p-4 border-b border-gray-800 bg-gray-900/50">
                  <h3 className="font-semibold text-gray-200">Recent Connected Transactions</h3>
                </div>
                <table className="w-full text-left">
                  <thead className="bg-gray-800/50 text-gray-400 text-sm">
                    <tr>
                      <th className="p-4 font-medium">Txn ID</th>
                      <th className="p-4 font-medium">User ID</th>
                      <th className="p-4 font-medium">Amount</th>
                      <th className="p-4 font-medium">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-800 text-gray-300">
                    {data.network_data.transactions?.map((txn: any) => (
                      <tr key={txn.txn_id} className="hover:bg-gray-800/30 transition-colors">
                        <td className="p-4">{txn.txn_id}</td>
                        <td className="p-4">{txn.user_id}</td>
                        <td className="p-4 font-mono">${txn.amount.toFixed(2)}</td>
                        <td className="p-4">
                          <span className="px-2 py-1 text-xs rounded bg-red-500/20 text-red-400 border border-red-500/30 uppercase tracking-wider">
                            FLAGGED
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
    </div>
  );
}
