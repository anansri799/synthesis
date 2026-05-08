import { useState } from "react";

const API = "http://127.0.0.1:8000";

export default function App() {
  const [problem, setProblem] = useState(null);
  const [hintsUnlocked, setHintsUnlocked] = useState([]);
  const [answer, setAnswer] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);

  async function uploadFile(e) {
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    await fetch(`${API}/ingest`, { method: "POST", body: form });
    setUploading(false);
    alert("Material uploaded! Click Generate Problem.");
  }

  async function generateProblem() {
    setLoading(true);
    setProblem(null);
    setHintsUnlocked([]);
    setAnswer("");
    setFeedback(null);
    const res = await fetch(`${API}/generate`, { method: "POST" });
    const data = await res.json();
    setProblem(data);
    setLoading(false);
  }

  async function unlockHint(n) {
    const res = await fetch(`${API}/hint/${problem.problem_id}/${n}`);
    const data = await res.json();
    setHintsUnlocked([...hintsUnlocked, { number: n, text: data.hint }]);
  }

  async function submitAnswer() {
    setLoading(true);
    const res = await fetch(`${API}/submit/${problem.problem_id}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answer }),
    });
    const data = await res.json();
    setFeedback(data);
    setLoading(false);
  }

  return (
    <div style={{ maxWidth: 720, margin: "0 auto", padding: "40px 20px", fontFamily: "system-ui, sans-serif" }}>
      <h1 style={{ fontSize: 28, fontWeight: 700, marginBottom: 4 }}>Synthesis</h1>
      <p style={{ color: "#666", marginBottom: 32 }}>Problems generated from your material — not pulled from a bank.</p>

      {/* Upload */}
      <div style={{ marginBottom: 24, padding: 20, border: "1px solid #e0e0e0", borderRadius: 12 }}>
        <h2 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>Upload your notes or problem sets</h2>
        <input type="file" accept=".pdf" onChange={uploadFile} />
        {uploading && <p style={{ color: "#888", marginTop: 8 }}>Ingesting material...</p>}
      </div>

      {/* Generate */}
      <button
        onClick={generateProblem}
        disabled={loading}
        style={{ background: "#111", color: "#fff", border: "none", padding: "12px 24px", borderRadius: 8, cursor: "pointer", fontSize: 15, marginBottom: 32 }}
      >
        {loading ? "Generating..." : "Generate Problem"}
      </button>

      {/* Problem */}
      {problem && !problem.error && (
        <div>
          <div style={{ padding: 24, background: "#f9f9f9", borderRadius: 12, marginBottom: 20 }}>
            <p style={{ fontSize: 13, color: "#888", marginBottom: 8 }}>
              Concepts: {problem.concepts_tested?.join(" + ")}
            </p>
            <p style={{ fontSize: 17, lineHeight: 1.6 }}>{problem.problem}</p>
          </div>

          {/* Hints */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 10 }}>Hints</p>
            {[1, 2, 3].map((n) => {
              const unlocked = hintsUnlocked.find((h) => h.number === n);
              return (
                <div key={n} style={{ marginBottom: 8 }}>
                  {unlocked ? (
                    <div style={{ padding: "10px 16px", background: "#fff8e1", borderRadius: 8, fontSize: 14 }}>
                      <strong>Hint {n}:</strong> {unlocked.text}
                    </div>
                  ) : (
                    <button
                      onClick={() => unlockHint(n)}
                      disabled={n > 1 && !hintsUnlocked.find((h) => h.number === n - 1)}
                      style={{ padding: "8px 16px", borderRadius: 8, border: "1px solid #ddd", background: "#fff", cursor: "pointer", fontSize: 14, color: "#555" }}
                    >
                      Unlock Hint {n}
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          {/* Answer */}
          <div style={{ marginBottom: 20 }}>
            <p style={{ fontSize: 14, fontWeight: 600, marginBottom: 8 }}>Your Answer</p>
            <textarea
              value={answer}
              onChange={(e) => setAnswer(e.target.value)}
              placeholder="Write your approach and solution here..."
              style={{ width: "100%", height: 120, padding: 12, borderRadius: 8, border: "1px solid #ddd", fontSize: 14, resize: "vertical", boxSizing: "border-box" }}
            />
            <button
              onClick={submitAnswer}
              disabled={!answer || loading}
              style={{ marginTop: 10, background: "#111", color: "#fff", border: "none", padding: "10px 20px", borderRadius: 8, cursor: "pointer", fontSize: 14 }}
            >
              {loading ? "Checking..." : "Submit Answer"}
            </button>
          </div>

          {/* Feedback */}
          {feedback && (
            <div style={{ padding: 20, background: feedback.result === "correct" ? "#e8f5e9" : feedback.result === "partial" ? "#fff8e1" : "#fce4ec", borderRadius: 12 }}>
              <p style={{ fontWeight: 700, fontSize: 16, marginBottom: 8 }}>
                {feedback.result === "correct" ? "✓ Correct" : feedback.result === "partial" ? "~ Partially Correct" : "✗ Incorrect"} — {feedback.score}/100
              </p>
              <p style={{ fontSize: 14, marginBottom: 8 }}>{feedback.feedback}</p>
              {feedback.what_they_missed && (
                <p style={{ fontSize: 13, color: "#666" }}>Missed: {feedback.what_they_missed}</p>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}