
import "./progress.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getSessions } from "./api";

function Progress() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const token = localStorage.getItem("vibecheckToken");

    if (!token) {
      navigate("/");
      return;
    }

    getSessions(token)
      .then((data) => {
        // Sirf woh sessions jinka analysis complete hua ho
        const valid = data.filter((s) => s.final_scores);
        // Purane se naye order me (chronological — trend ke liye zaroori)
        const ordered = [...valid].reverse();
        setSessions(ordered);
      })
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, [navigate]);

  // ---------- LOADING / EMPTY STATES ----------

  if (loading) {
    return (
      <div className="progress-page">
        <header className="progress-header">
          <div className="progress-logo">VIBECHECK<span>.</span></div>
          <div className="progress-header-title">PROGRESS</div>
        </header>
        <main className="progress-main">
          <p style={{ textAlign: "center", color: "#8b8493", padding: "60px 0" }}>
            Loading your progress...
          </p>
        </main>
      </div>
    );
  }

  if (error) {
    return (
      <div className="progress-page">
        <header className="progress-header">
          <div className="progress-logo">VIBECHECK<span>.</span></div>
          <div className="progress-header-title">PROGRESS</div>
        </header>
        <main className="progress-main">
          <p style={{ textAlign: "center", color: "#d36b7c", padding: "60px 0" }}>
            {error}
          </p>
        </main>
      </div>
    );
  }

  if (sessions.length < 2) {
    return (
      <div className="progress-page">
        <header className="progress-header">
          <div className="progress-logo">VIBECHECK<span>.</span></div>
          <div className="progress-header-title">PROGRESS</div>
        </header>
        <main className="progress-main">
          <button className="progress-back-button" onClick={() => navigate("/dashboard")}>
            ← Back to Dashboard
          </button>
          <p style={{ textAlign: "center", color: "#8b8493", padding: "60px 0" }}>
            Complete at least 2 sessions to see your progress trend.
          </p>
        </main>
      </div>
    );
  }

  // ---------- DATA PREP ----------

  const mapped = sessions.map((s, index) => {
    const scores = s.final_scores;
    return {
      session: `Session ${index + 1}`,
      confidence: Math.round(scores.high_level.confidence),
      eyeContact: Math.round(scores.eye_contact.eye_contact_percentage),
      pace: Math.round(scores.voice.rate_score),
      fillerWords: Math.round(scores.voice.filler_rate),
    };
  });

  const latest = mapped[mapped.length - 1];
  const first = mapped[0];

  const improvements = [
    {
      label: "Confidence",
      value: `${latest.confidence - first.confidence >= 0 ? "+" : ""}${latest.confidence - first.confidence}%`,
      current: `${latest.confidence}%`,
      description: "You are becoming more composed and confident.",
      color: "#8062c2",
    },
    {
      label: "Eye Contact",
      value: `${latest.eyeContact - first.eyeContact >= 0 ? "+" : ""}${latest.eyeContact - first.eyeContact}%`,
      current: `${latest.eyeContact}%`,
      description: "Your eye contact is becoming more consistent.",
      color: "#63a8c9",
    },
    {
      label: "Speaking Pace",
      value: `${latest.pace - first.pace >= 0 ? "+" : ""}${latest.pace - first.pace}%`,
      current: `${latest.pace}%`,
      description: "Your delivery is becoming more controlled.",
      color: "#d69a63",
    },
    {
      label: "Filler Words",
      value: `${latest.fillerWords - first.fillerWords <= 0 ? "" : "+"}${latest.fillerWords - first.fillerWords}%`,
      current: `${latest.fillerWords}%`,
      description: "Tracks how often filler words show up in your speech.",
      color: "#d87591",
    },
  ];

  // Biggest wins — sirf positive improvements dikhao, sabse bade se
  const wins = [
    { label: "Confidence", diff: latest.confidence - first.confidence, unit: "%" },
    { label: "Eye Contact", diff: latest.eyeContact - first.eyeContact, unit: "%" },
    { label: "Speaking Pace", diff: latest.pace - first.pace, unit: "%" },
    { label: "Filler Words", diff: first.fillerWords - latest.fillerWords, unit: "" },
  ]
    .sort((a, b) => b.diff - a.diff)
    .slice(0, 3);

  const winColors = ["purple", "blue", "pink"];

  return (
    <div className="progress-page">

      {/* HEADER */}
      <header className="progress-header">
        <div className="progress-logo">VIBECHECK<span>.</span></div>
        <div className="progress-header-title">PROGRESS</div>
      </header>

      <main className="progress-main">
        <button className="progress-back-button" onClick={() => navigate("/dashboard")}>
          ← Back to Dashboard
        </button>

        {/* INTRO */}
        <section className="progress-intro">
          <div>
            <p className="eyebrow">YOUR GROWTH</p>
            <h1>You're getting better.</h1>
            <p>
              See how your communication has changed
              across every practice session.
            </p>
          </div>

          <div className="session-count">
            <strong>{mapped.length}</strong>
            <span>SESSIONS</span>
          </div>
        </section>

        {/* METRICS */}
        <section className="improvement-grid">
          {improvements.map((item) => (
            <div className="improvement-card" key={item.label}>
              <div className="improvement-top">
                <span className="metric-name">{item.label}</span>
                <span className="improvement-value" style={{ color: item.color }}>
                  {item.value}
                </span>
              </div>
              <div className="metric-current">{item.current}</div>
              <p>{item.description}</p>
            </div>
          ))}
        </section>

        {/* TREND GRAPH */}
        <section className="trend-card">
          <div className="trend-header">
            <div>
              <p className="eyebrow">PERFORMANCE OVER TIME</p>
              <h2>Your communication trend</h2>
            </div>
            <span className="trend-label">{mapped.length} practice sessions</span>
          </div>

          <div className="chart">
            <div className="chart-y-axis">
              <span>100</span>
              <span>80</span>
              <span>60</span>
              <span>40</span>
              <span>20</span>
              <span>0</span>
            </div>

            <div className="chart-area">
              <div className="grid-line line-100"></div>
              <div className="grid-line line-80"></div>
              <div className="grid-line line-60"></div>
              <div className="grid-line line-40"></div>
              <div className="grid-line line-20"></div>
              <div className="grid-line line-0"></div>

              <div className="trend-line confidence-line">
                {mapped.map((s, index) => (
                  <div
                    className="trend-point"
                    key={s.session}
                    style={{
                      left: `${(index / (mapped.length - 1)) * 100}%`,
                      bottom: `${s.confidence}%`,
                    }}
                  >
                    <span>{s.confidence}</span>
                  </div>
                ))}
              </div>

              <div className="trend-line eye-line">
                {mapped.map((s, index) => (
                  <div
                    className="trend-point"
                    key={s.session}
                    style={{
                      left: `${(index / (mapped.length - 1)) * 100}%`,
                      bottom: `${s.eyeContact}%`,
                    }}
                  ></div>
                ))}
              </div>

              <div className="trend-line pace-line">
                {mapped.map((s, index) => (
                  <div
                    className="trend-point"
                    key={s.session}
                    style={{
                      left: `${(index / (mapped.length - 1)) * 100}%`,
                      bottom: `${s.pace}%`,
                    }}
                  ></div>
                ))}
              </div>

              <div className="chart-labels">
                {mapped.map((s) => (
                  <span key={s.session}>{s.session.replace("Session ", "S")}</span>
                ))}
              </div>
            </div>
          </div>

          <div className="chart-legend">
            <span><i className="legend-confidence"></i>Confidence</span>
            <span><i className="legend-eye"></i>Eye Contact</span>
            <span><i className="legend-pace"></i>Speaking Pace</span>
          </div>
        </section>

        {/* FILLER WORD TREND */}
        <section className="filler-card">
          <div>
            <p className="eyebrow">FILLER WORDS</p>
            <h2>Tracking your filler word usage.</h2>
            <p className="filler-description">
              See how often filler words show up across your sessions.
            </p>
          </div>

          <div className="filler-bars">
            {mapped.map((s) => (
              <div className="filler-column" key={s.session}>
                <span>{s.fillerWords}</span>
                <div className="filler-bar-bg">
                  <div
                    className="filler-bar"
                    style={{ height: `${Math.min(s.fillerWords * 2.5, 100)}%` }}
                  ></div>
                </div>
                <small>{s.session.replace("Session ", "S")}</small>
              </div>
            ))}
          </div>
        </section>

        {/* BIGGEST WINS */}
        <section className="best-section">
          <div className="best-heading">
            <p className="eyebrow">BIGGEST WINS</p>
            <h2>What you've improved most.</h2>
          </div>

          <div className="wins-grid">
            {wins.map((win, index) => (
              <div className={`win-card ${winColors[index]}`} key={win.label}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <h3>{win.label}</h3>
                <strong>
                  {win.diff >= 0 ? "+" : ""}{win.diff}{win.unit}
                </strong>
                <p>
                  {win.diff >= 0
                    ? "Solid improvement across sessions."
                    : "Room to grow here — keep practicing."}
                </p>
              </div>
            ))}
          </div>
        </section>

      </main>
    </div>
  );
}

export default Progress;