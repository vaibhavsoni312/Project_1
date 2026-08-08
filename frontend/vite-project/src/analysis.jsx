import "./analysis.css";
import { useNavigate } from "react-router-dom";

function Analysis() {
  const navigate = useNavigate();
  const metrics = [
    {
      label: "Confidence",
      value: "82%",
      score: 82,
      color: "#8b6ed8",
    },
    {
      label: "Eye Contact",
      value: "74%",
      score: 74,
      color: "#63a8c9",
    },
    {
      label: "Speaking Pace",
      value: "81%",
      score: 81,
      color: "#d69a63",
    },
    {
      label: "Filler Words",
      value: "17",
      score: 63,
      color: "#d87591",
    },
  ];

  const moments = [
    {
      time: "00:48",
      type: "Filler spike",
      color: "#d87591",
    },
    {
      time: "02:14",
      type: "Confidence drop",
      color: "#d96c7c",
      active: true,
    },
    {
      time: "03:42",
      type: "Pace increase",
      color: "#d69a63",
    },
    {
      time: "05:18",
      type: "Eye contact drop",
      color: "#63a8c9",
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
          <span className="session-duration">08:42</span>
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
              78
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


        {/* ================= TIMELINE ================= */}

        <section className="timeline-section">

          <div className="section-heading">

            <div>
              <p className="eyebrow">
                SHARED TIMELINE
              </p>

              <h2>
                Your performance, moment by moment.
              </h2>
            </div>

            <span className="timeline-duration">
              00:00 — 08:42
            </span>

          </div>


          <div className="timeline">

            <div className="timeline-line"></div>

            {moments.map((moment, index) => (
              <div
                className={`timeline-moment ${
                  moment.active ? "active" : ""
                }`}
                key={moment.time}
                style={{
                  left: `${12 + index * 23}%`,
                }}
              >

                <div
                  className="moment-dot"
                  style={{
                    background: moment.color,
                  }}
                ></div>

                <div className="moment-label">
                  <strong>{moment.time}</strong>
                  <span>{moment.type}</span>
                </div>

              </div>
            ))}

            <div className="timeline-times">
              <span>00:00</span>
              <span>02:00</span>
              <span>04:00</span>
              <span>06:00</span>
              <span>08:42</span>
            </div>

          </div>

        </section>


        {/* ================= VIDEO + INSIGHT ================= */}

        <section className="analysis-content">

          {/* VIDEO */}

          <div className="video-card">

            <div className="card-heading">

              <div>
                <p className="eyebrow">
                  SESSION PLAYBACK
                </p>

                <h2>
                  Watch the moment.
                </h2>
              </div>

              <span className="time-badge">
                02:14
              </span>

            </div>


            <div className="video-placeholder">

              <div className="video-icon">
                ▶
              </div>

              <span>
                Video preview
              </span>

              <small>
                Selected moment: 02:14
              </small>

            </div>


            <div className="video-controls">

              <button>
                ▶
              </button>

              <div className="play-line">
                <div className="play-progress"></div>
              </div>

              <span>
                02:14 / 08:42
              </span>

            </div>

          </div>


          {/* INSIGHT */}

          <div className="insight-card">

            <div className="insight-header">

              <div>
                <p className="eyebrow">
                  MOMENT INSIGHT
                </p>

                <h2>
                  02:14
                </h2>
              </div>

              <div className="warning-icon">
                !
              </div>

            </div>


            <h3>
              Your confidence dipped here.
            </h3>

            <p className="insight-description">
              Your speaking pace increased while filler
              words spiked and eye contact dropped.
            </p>


            <div className="delta-list">

              <div className="delta-item">
                <span>Speaking pace</span>
                <strong className="positive">
                  +23%
                </strong>
              </div>

              <div className="delta-item">
                <span>Filler words</span>
                <strong className="negative">
                  +41%
                </strong>
              </div>

              <div className="delta-item">
                <span>Eye contact</span>
                <strong className="negative">
                  -17%
                </strong>
              </div>

            </div>


            <div className="ai-feedback">

              <span className="feedback-label">
                AI FEEDBACK
              </span>

              <p>
                You rushed this answer. Try taking a
                1–2 second pause before responding to
                difficult questions.
              </p>

            </div>

          </div>

        </section>


        {/* ================= BOTTOM SUMMARY ================= */}

        <section className="summary-grid">

          <div className="summary-card">

            <p className="eyebrow">
              WHAT WENT WELL
            </p>

            <h2>
              Strong foundation.
            </h2>

            <ul>
              <li>Strong opening delivery</li>
              <li>Clear explanation of your ideas</li>
              <li>Good overall posture</li>
            </ul>

          </div>


          <div className="summary-card improvement">

            <p className="eyebrow">
              WHAT TO IMPROVE
            </p>

            <h2>
              Focus on consistency.
            </h2>

            <ul>
              <li>Slow down under pressure</li>
              <li>Reduce “um” and “like”</li>
              <li>Hold eye contact longer</li>
            </ul>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Analysis;