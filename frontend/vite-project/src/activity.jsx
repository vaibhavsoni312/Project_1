import "./activity.css";
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { getSessions } from "./api";

function Activity() {
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
        setSessions(data);
      })
      .catch((err) => {
        setError(err.message);
      })
      .finally(() => {
        setLoading(false);
      });
  }, [navigate]);

  const formatDate = (isoString) => {
    if (!isoString) return "—";
    const date = new Date(isoString);
    return date.toLocaleDateString("en-US", { month: "short", day: "2-digit" });
  };

  const formatTime = (isoString) => {
    if (!isoString) return "—";
    const date = new Date(isoString);
    return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit" });
  };

  const getStatusLabel = (overallScore) => {
    if (overallScore >= 75) return "Strong";
    if (overallScore >= 60) return "Good";
    return "Improving";
  };

  return (
    <div className="activity-page">

      {/* HEADER */}
      <header className="activity-header">
        <div className="activity-logo">
          VIBECHECK<span>.</span>
        </div>
        <div className="activity-header-title">
          SESSION HISTORY
        </div>
      </header>

      <main className="activity-main">
        <button
          className="activity-back-button"
          onClick={() => navigate("/dashboard")}
        >
          ← Back to Dashboard
        </button>

        {/* INTRO */}
        <section className="activity-intro">
          <div>
            <p className="eyebrow">YOUR SESSIONS</p>
            <h1>Everything you've practiced.</h1>
            <p>
              Revisit your recordings, understand your
              performance, and see how you've improved.
            </p>
          </div>

          <div className="total-sessions">
            <strong>{sessions.length}</strong>
            <span>SESSIONS</span>
          </div>
        </section>

        {/* LOADING / ERROR */}
        {loading && (
          <p style={{ textAlign: "center", color: "#8b8493", padding: "40px 0" }}>
            Loading your sessions...
          </p>
        )}

        {error && (
          <p style={{ textAlign: "center", color: "#d36b7c", padding: "40px 0" }}>
            {error}
          </p>
        )}

        {!loading && !error && sessions.length === 0 && (
          <p style={{ textAlign: "center", color: "#8b8493", padding: "40px 0" }}>
            No sessions yet — go record your first practice!
          </p>
        )}

        {/* SESSION LIST */}
        {!loading && !error && sessions.length > 0 && (
          <section className="sessions-list">
            {sessions.map((session, index) => {
              const scores = session.final_scores;

              if (!scores) {
                return null;
              }

              const highLevel = scores.high_level;
              const overallScore = Math.round(
                (highLevel.communication + highLevel.confidence + highLevel.body_language) / 3
              );
              const status = getStatusLabel(overallScore);

              return (
                <article className="session-card" key={session.id}>

                  <div className="session-main">
                    <div className="session-top">
                      <div>
                        <span className="session-number">
                          SESSION {String(sessions.length - index).padStart(2, "0")}
                        </span>
                        <h2>Practice Session</h2>
                        <p className="session-date">
                          {formatDate(session.uploaded_at)} · {formatTime(session.uploaded_at)}
                        </p>
                      </div>

                      <span className={`session-status status-${status.toLowerCase()}`}>
                        {status}
                      </span>
                    </div>

                    <div className="session-metrics">
                      <div className="session-metric score-metric">
                        <span>OVERALL</span>
                        <strong>{overallScore}</strong>
                        <small>/100</small>
                      </div>

                      <div className="session-metric">
                        <span>CONFIDENCE</span>
                        <strong>{Math.round(highLevel.confidence)}%</strong>
                      </div>

                      <div className="session-metric">
                        <span>EYE CONTACT</span>
                        <strong>{Math.round(scores.eye_contact.eye_contact_percentage)}%</strong>
                      </div>

                      <div className="session-metric">
                        <span>PACE</span>
                        <strong>{Math.round(scores.voice.rate_score)}%</strong>
                      </div>

                      <div className="session-metric filler-metric">
                        <span>FILLER WORDS</span>
                        <strong>{scores.voice.filler_rate}%</strong>
                      </div>
                    </div>

                    <div className="session-bottom">
                      <span className="moments-info">
                        <span className="moment-dot"></span>
                        Analysis complete
                      </span>
                      <span className="analysis-ready">
                        Analysis ready
                      </span>
                    </div>
                  </div>

                  <div className="recording-preview">
                    <div className="recording-screen">
                      <div className="recording-play">▶</div>
                      <span>RECORDING</span>
                    </div>
                    <div className="recording-time">
                      {formatTime(session.uploaded_at)}
                    </div>
                  </div>

                  <div className="session-action">
                    <button className="view-recording">
                      ▶
                      <span>Recording</span>
                    </button>

                    <button
                      className="view-analysis"
                      onClick={() => navigate("/analysis", { state: session })}
                    >
                      View Analysis
                      <span>→</span>
                    </button>
                  </div>

                </article>
              );
            })}
          </section>
        )}

        <div className="activity-footer">
          <span>Keep practicing to build your performance history.</span>
        </div>

      </main>
    </div>
  );
}

export default Activity;