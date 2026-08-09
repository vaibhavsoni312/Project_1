import "./Dashboard.css";
import { useNavigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { getSessions } from "./api";

function Dashboard() {
  const navigate = useNavigate();
  const [sessionCount, setSessionCount] = useState(null);

  const userName =
    localStorage.getItem("vibecheckName") || "there";

  useEffect(() => {
    const token = localStorage.getItem("vibecheckToken");
    if (!token) return;

    getSessions(token)
      .then((sessions) => setSessionCount(sessions.length))
      .catch(() => setSessionCount(null));
  }, []);

  return (
    <div className="dashboard">

      {/* NAVBAR */}
      <nav className="dashboard-nav">
        <div className="dashboard-logo">
          VIBECHECK<span>.</span>
        </div>

        <div className="nav-right">
          <div className="profile-circle">
            {userName.charAt(0).toUpperCase()}
          </div>
          <span className="profile-name">{userName}</span>
          <span className="dropdown">⌄</span>
        </div>
      </nav>

      {/* MAIN */}
      <main className="dashboard-main">
        <div className="welcome-section">
          <h1>Hey <span>{userName}</span>! 👋</h1>
          <p>
            {sessionCount !== null
              ? `You've completed ${sessionCount} session${sessionCount === 1 ? "" : "s"}. What would you like to do today?`
              : "What would you like to do today?"}
          </p>
        </div>

        <div className="dashboard-cards">

          <div className="dashboard-card record-card">
            <div className="card-icon">◉</div>
            <h2>Record</h2>
            <p>Start a new practice session and record yourself.</p>
            <button className="card-button" onClick={() => navigate("/record")}>→</button>
          </div>

          <div className="dashboard-card activity-card">
            <div className="card-icon">◷</div>
            <h2>Recent Activity</h2>
            <p>View your recent sessions and performance.</p>
            <button className="card-button" onClick={() => navigate("/activity")}>→</button>
          </div>

          <div className="dashboard-card progress-card">
            <div className="card-icon">↗</div>
            <h2>Progress</h2>
            <p>Track your improvement and see your growth.</p>
            <button className="card-button" onClick={() => navigate("/progress")}>→</button>
          </div>

        </div>
      </main>
    </div>
  );
}

export default Dashboard;