import "./activity.css";
import { useNavigate } from "react-router-dom";

function Activity() {
  const navigate = useNavigate();
  const sessions = [
    {
      id: 6,
      date: "Today",
      time: "08:42",
      title: "Interview Practice",
      score: 78,
      confidence: 82,
      eyeContact: 74,
      pace: 81,
      fillerWords: 17,
      moments: 4,
      status: "Strong",
    },
    {
      id: 5,
      date: "Yesterday",
      time: "06:31",
      title: "Technical Interview",
      score: 74,
      confidence: 78,
      eyeContact: 71,
      pace: 78,
      fillerWords: 19,
      moments: 5,
      status: "Good",
    },
    {
      id: 4,
      date: "Aug 07",
      time: "09:12",
      title: "Presentation Practice",
      score: 70,
      confidence: 74,
      eyeContact: 68,
      pace: 75,
      fillerWords: 21,
      moments: 6,
      status: "Good",
    },
    {
      id: 3,
      date: "Aug 05",
      time: "07:48",
      title: "HR Interview",
      score: 66,
      confidence: 70,
      eyeContact: 63,
      pace: 71,
      fillerWords: 24,
      moments: 7,
      status: "Improving",
    },
    {
      id: 2,
      date: "Aug 03",
      time: "05:26",
      title: "Self Introduction",
      score: 63,
      confidence: 66,
      eyeContact: 59,
      pace: 67,
      fillerWords: 27,
      moments: 8,
      status: "Improving",
    },
    {
      id: 1,
      date: "Aug 01",
      time: "06:14",
      title: "First Practice",
      score: 61,
      confidence: 61,
      eyeContact: 54,
      pace: 63,
      fillerWords: 31,
      moments: 9,
      status: "First Session",
    },
  ];

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

            <p className="eyebrow">
              YOUR SESSIONS
            </p>

            <h1>
              Everything you've practiced.
            </h1>

            <p>
              Revisit your recordings, understand your
              performance, and see how you've improved.
            </p>

          </div>

          <div className="total-sessions">

            <strong>
              {sessions.length}
            </strong>

            <span>
              SESSIONS
            </span>

          </div>

        </section>


        {/* FILTER */}
        <div className="activity-toolbar">

          <div className="filter-left">

            <button className="filter-button active">
              All Sessions
            </button>

            <button className="filter-button">
              Interviews
            </button>

            <button className="filter-button">
              Presentations
            </button>

          </div>

          <span className="latest-label">
            Latest first
          </span>

        </div>


        {/* SESSION LIST */}
        <section className="sessions-list">

          {sessions.map((session) => (

            <article
              className="session-card"
              key={session.id}
            >

              {/* SESSION LEFT */}
              <div className="session-main">

                <div className="session-top">

                  <div>

                    <span className="session-number">
                      SESSION {String(session.id).padStart(2, "0")}
                    </span>

                    <h2>
                      {session.title}
                    </h2>

                    <p className="session-date">
                      {session.date} · {session.time}
                    </p>

                  </div>

                  <span
                    className={`session-status status-${session.status
                      .toLowerCase()
                      .replace(" ", "-")}`}
                  >
                    {session.status}
                  </span>

                </div>


                {/* METRICS */}
                <div className="session-metrics">

                  <div className="session-metric score-metric">

                    <span>
                      OVERALL
                    </span>

                    <strong>
                      {session.score}
                    </strong>

                    <small>
                      /100
                    </small>

                  </div>


                  <div className="session-metric">

                    <span>
                      CONFIDENCE
                    </span>

                    <strong>
                      {session.confidence}%
                    </strong>

                  </div>


                  <div className="session-metric">

                    <span>
                      EYE CONTACT
                    </span>

                    <strong>
                      {session.eyeContact}%
                    </strong>

                  </div>


                  <div className="session-metric">

                    <span>
                      PACE
                    </span>

                    <strong>
                      {session.pace}%
                    </strong>

                  </div>


                  <div className="session-metric filler-metric">

                    <span>
                      FILLER WORDS
                    </span>

                    <strong>
                      {session.fillerWords}
                    </strong>

                  </div>

                </div>


                {/* MOMENTS */}
                <div className="session-bottom">

                  <span className="moments-info">
                    <span className="moment-dot"></span>

                    {session.moments} important moments detected
                  </span>

                  <span className="analysis-ready">
                    Analysis ready
                  </span>

                </div>

              </div>


              {/* RECORDING */}
              <div className="recording-preview">

                <div className="recording-screen">

                  <div className="recording-play">
                    ▶
                  </div>

                  <span>
                    RECORDING
                  </span>

                </div>

                <div className="recording-time">
                  {session.time}
                </div>

              </div>


              {/* ACTION */}
              <div className="session-action">

                <button className="view-recording">
                  ▶
                  <span>Recording</span>
                </button>

               <button
  className="view-analysis"
  onClick={() => navigate("/analysis")}
>
  View Analysis
  <span>→</span>
</button>

              </div>

            </article>

          ))}

        </section>


        {/* EMPTY FUTURE MESSAGE */}
        <div className="activity-footer">

          <span>
            Keep practicing to build your performance history.
          </span>

        </div>

      </main>

    </div>
  );
}

export default Activity;