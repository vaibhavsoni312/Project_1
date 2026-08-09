import "./analysis.css";
import { useNavigate, useLocation } from "react-router-dom";

function Analysis() {
  const navigate = useNavigate();
  const location = useLocation();

  const result = location.state;

  // Agar koi seedha /analysis URL pe aa gaya bina record kiye,
  // to result null hoga — us case ko handle karo
  if (!result || !result.final_scores) {
    return (
      <div className="analysis-page">
        <main className="analysis-main" style={{ textAlign: "center", paddingTop: "80px" }}>
          <h1>No analysis data found.</h1>
          <p style={{ marginTop: "12px", color: "#8b8493" }}>
            Please record a session first.
          </p>
          <button
            className="back-button"
            style={{ marginTop: "20px" }}
            onClick={() => navigate("/record")}
          >
            ← Go to Record
          </button>
        </main>
      </div>
    );
  }

  const scores = result.final_scores;
  const feedback = result.feedback || [];

  const voice = scores.voice;
  const eye = scores.eye_contact;
  const emotion = scores.emotion;
  const head = scores.head_pose;
  const highLevel = scores.high_level;

  const overallScore = Math.round(
    (highLevel.communication + highLevel.confidence + highLevel.body_language) / 3
  );

  const metrics = [
    {
      label: "Confidence",
      value: `${Math.round(highLevel.confidence)}%`,
      score: highLevel.confidence,
      color: "#8b6ed8",
    },
    {
      label: "Eye Contact",
      value: `${Math.round(eye.eye_contact_percentage)}%`,
      score: eye.eye_contact_score,
      color: "#63a8c9",
    },
    {
      label: "Speaking Pace",
      value: `${Math.round(voice.rate_score)}%`,
      score: voice.rate_score,
      color: "#d69a63",
    },
    {
      label: "Filler Words",
      value: `${voice.filler_rate}%`,
      score: voice.filler_score,
      color: "#d87591",
    },
  ];

  return (
    <div className="analysis-page">

      {/* HEADER */}
      <header className="analysis-header">

        <div className="analysis-logo">
          VIBECHECK<span>.</span>
        </div>

        <div className="analysis-header-right">
          <span>SESSION ANALYSIS</span>
          <span className="session-duration">
            {Math.floor(voice.duration / 60)}:{String(Math.round(voice.duration % 60)).padStart(2, "0")}
          </span>
        </div>

      </header>

      <button
        className="back-button"
        onClick={() => navigate("/dashboard")}
      >
        ← Back to Dashboard
      </button>


      <main className="analysis-main">

        {/* ================= TOP ================= */}

        <section className="analysis-intro">

          <div>
            <p className="eyebrow">
              SESSION COMPLETE
            </p>

            <h1>
              Here's how you came across.
            </h1>

            <p className="intro-text">
              Your strongest moments, your weak spots,
              and exactly where things changed.
            </p>
          </div>

          <div className="overall-score">

            <div className="score-number">
              {overallScore}
              <span>/100</span>
            </div>

            <p>OVERALL SCORE</p>

          </div>

        </section>


        {/* ================= METRICS ================= */}

        <section className="metrics-grid">

          {metrics.map((metric) => (
            <div
              className="metric-card"
              key={metric.label}
            >

              <div className="metric-top">

                <span className="metric-label">
                  {metric.label}
                </span>

                <span
                  className="metric-value"
                  style={{ color: metric.color }}
                >
                  {metric.value}
                </span>

              </div>

              <div className="metric-bar">

                <div
                  className="metric-fill"
                  style={{
                    width: `${metric.score}%`,
                    background: metric.color,
                  }}
                ></div>

              </div>

            </div>
          ))}

        </section>


        {/* ================= INSIGHT / FEEDBACK ================= */}

        <section className="analysis-content">

          <div className="insight-card" style={{ gridColumn: "1 / -1" }}>

            <div className="insight-header">

              <div>
                <p className="eyebrow">
                  AI FEEDBACK
                </p>

                <h2>
                  What we noticed.
                </h2>
              </div>

            </div>

            <div className="ai-feedback">
              <span className="feedback-label">
                SUGGESTIONS
              </span>

              {feedback.map((line, index) => (
                <p key={index} style={{ marginTop: index === 0 ? "8px" : "10px" }}>
                  {line}
                </p>
              ))}
            </div>

          </div>

        </section>


        {/* ================= SUMMARY ================= */}

        <section className="summary-grid">

          <div className="summary-card">

            <p className="eyebrow">
              DOMINANT EMOTION
            </p>

            <h2 style={{ textTransform: "capitalize" }}>
              {emotion.dominant_emotion}
            </h2>

            <ul>
              <li>Confidence: {Math.round(emotion.emotion_confidence)}%</li>
              <li>Emotion score: {Math.round(emotion.emotion_score)}/100</li>
            </ul>

          </div>


          <div className="summary-card improvement">

            <p className="eyebrow">
              VOICE DETAILS
            </p>

            <h2>
              Speaking breakdown.
            </h2>

            <ul>
              <li>Speaking rate: {voice.speaking_rate} wpm</li>
              <li>Pauses: {voice.pause_count}</li>
              <li>Filler rate: {voice.filler_rate}%</li>
            </ul>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Analysis;