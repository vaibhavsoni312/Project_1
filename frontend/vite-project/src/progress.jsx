import "./progress.css";
import { useNavigate } from "react-router-dom";

function Progress() {
  const navigate = useNavigate();
  const sessions = [
    { session: "Session 1", confidence: 61, eyeContact: 54, pace: 63, fillerWords: 31 },
    { session: "Session 2", confidence: 66, eyeContact: 59, pace: 67, fillerWords: 27 },
    { session: "Session 3", confidence: 70, eyeContact: 63, pace: 71, fillerWords: 24 },
    { session: "Session 4", confidence: 74, eyeContact: 68, pace: 75, fillerWords: 21 },
    { session: "Session 5", confidence: 78, eyeContact: 71, pace: 78, fillerWords: 19 },
    { session: "Session 6", confidence: 82, eyeContact: 74, pace: 81, fillerWords: 17 },
  ];

  const latest = sessions[sessions.length - 1];
  const first = sessions[0];

  const improvements = [
    {
      label: "Confidence",
      value: `+${latest.confidence - first.confidence}%`,
      current: `${latest.confidence}%`,
      description: "You are becoming more composed and confident.",
      color: "#8062c2",
    },
    {
      label: "Eye Contact",
      value: `+${latest.eyeContact - first.eyeContact}%`,
      current: `${latest.eyeContact}%`,
      description: "Your eye contact is becoming more consistent.",
      color: "#63a8c9",
    },
    {
      label: "Speaking Pace",
      value: `+${latest.pace - first.pace}%`,
      current: `${latest.pace}%`,
      description: "Your delivery is becoming more controlled.",
      color: "#d69a63",
    },
    {
      label: "Filler Words",
      value: `-${first.fillerWords - latest.fillerWords}`,
      current: `${latest.fillerWords}`,
      description: "You are using fewer filler words while speaking.",
      color: "#d87591",
    },
  ];

  return (
    <div className="progress-page">

      {/* HEADER */}
      <header className="progress-header">

        <div className="progress-logo">
          VIBECHECK<span>.</span>
        </div>

        <div className="progress-header-title">
          PROGRESS
        </div>

      </header>


      <main className="progress-main">
        <button
  className="progress-back-button"
  onClick={() => navigate("/dashboard")}
>
  ← Back to Dashboard
</button>

        {/* INTRO */}
        <section className="progress-intro">

          <div>
            <p className="eyebrow">
              YOUR GROWTH
            </p>

            <h1>
              You're getting better.
            </h1>

            <p>
              See how your communication has changed
              across every practice session.
            </p>
          </div>

          <div className="session-count">
            <strong>{sessions.length}</strong>
            <span>SESSIONS</span>
          </div>

        </section>


        {/* METRICS */}
        <section className="improvement-grid">

          {improvements.map((item) => (
            <div
              className="improvement-card"
              key={item.label}
            >

              <div className="improvement-top">

                <span className="metric-name">
                  {item.label}
                </span>

                <span
                  className="improvement-value"
                  style={{ color: item.color }}
                >
                  {item.value}
                </span>

              </div>

              <div className="metric-current">
                {item.current}
              </div>

              <p>
                {item.description}
              </p>

            </div>
          ))}

        </section>


        {/* TREND GRAPH */}
        <section className="trend-card">

          <div className="trend-header">

            <div>
              <p className="eyebrow">
                PERFORMANCE OVER TIME
              </p>

              <h2>
                Your communication trend
              </h2>
            </div>

            <span className="trend-label">
              {sessions.length} practice sessions
            </span>

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


              {/* Confidence */}
              <div className="trend-line confidence-line">
                {sessions.map((session, index) => (
                  <div
                    className="trend-point"
                    key={session.session}
                    style={{
                      left: `${index * 20}%`,
                      bottom: `${session.confidence}%`,
                    }}
                  >
                    <span>{session.confidence}</span>
                  </div>
                ))}
              </div>


              {/* Eye Contact */}
              <div className="trend-line eye-line">
                {sessions.map((session, index) => (
                  <div
                    className="trend-point"
                    key={session.session}
                    style={{
                      left: `${index * 20}%`,
                      bottom: `${session.eyeContact}%`,
                    }}
                  ></div>
                ))}
              </div>


              {/* Pace */}
              <div className="trend-line pace-line">
                {sessions.map((session, index) => (
                  <div
                    className="trend-point"
                    key={session.session}
                    style={{
                      left: `${index * 20}%`,
                      bottom: `${session.pace}%`,
                    }}
                  ></div>
                ))}
              </div>


              <div className="chart-labels">
                {sessions.map((session) => (
                  <span key={session.session}>
                    {session.session.replace("Session ", "S")}
                  </span>
                ))}
              </div>

            </div>

          </div>


          <div className="chart-legend">

            <span>
              <i className="legend-confidence"></i>
              Confidence
            </span>

            <span>
              <i className="legend-eye"></i>
              Eye Contact
            </span>

            <span>
              <i className="legend-pace"></i>
              Speaking Pace
            </span>

          </div>

        </section>


        {/* FILLER WORD TREND */}
        <section className="filler-card">

          <div>
            <p className="eyebrow">
              FILLER WORDS
            </p>

            <h2>
              You're saying less without saying less.
            </h2>

            <p className="filler-description">
              Your filler word usage has consistently
              decreased across your sessions.
            </p>
          </div>


          <div className="filler-bars">

            {sessions.map((session) => (

              <div
                className="filler-column"
                key={session.session}
              >

                <span>
                  {session.fillerWords}
                </span>

                <div className="filler-bar-bg">
                  <div
                    className="filler-bar"
                    style={{
                      height: `${session.fillerWords * 2.5}%`,
                    }}
                  ></div>
                </div>

                <small>
                  {session.session.replace("Session ", "S")}
                </small>

              </div>

            ))}

          </div>

        </section>


        {/* BEST IMPROVEMENTS */}
        <section className="best-section">

          <div className="best-heading">

            <p className="eyebrow">
              BIGGEST WINS
            </p>

            <h2>
              What you've improved most.
            </h2>

          </div>


          <div className="wins-grid">

            <div className="win-card purple">
              <span>01</span>
              <h3>Confidence</h3>
              <strong>+21%</strong>
              <p>
                Your strongest improvement across sessions.
              </p>
            </div>

            <div className="win-card blue">
              <span>02</span>
              <h3>Eye Contact</h3>
              <strong>+20%</strong>
              <p>
                You're holding attention more consistently.
              </p>
            </div>

            <div className="win-card pink">
              <span>03</span>
              <h3>Filler Words</h3>
              <strong>-14</strong>
              <p>
                Fewer unnecessary words in your answers.
              </p>
            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default Progress;