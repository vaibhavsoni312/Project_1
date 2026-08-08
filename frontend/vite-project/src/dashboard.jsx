import "./Dashboard.css";
import { useNavigate } from "react-router-dom";

function Dashboard() {

  const navigate = useNavigate();

  const userName =
    localStorage.getItem("vibecheckName") || "there";

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

          <span className="profile-name">
            {userName}
          </span>

          <span className="dropdown">
            ⌄
          </span>

        </div>

      </nav>


      {/* MAIN */}
      <main className="dashboard-main">

        <div className="welcome-section">

          <h1>
            Hey <span>{userName}</span>! 👋
          </h1>

          <p>
            What would you like to do today?
          </p>

        </div>


        {/* CARDS */}
        <div className="dashboard-cards">


          {/* RECORD */}
          <div className="dashboard-card record-card">

            <div className="card-icon">
              ◉
            </div>

            <h2>
              Record
            </h2>

            <p>
              Start a new practice session
              and record yourself.
            </p>

            <button
              className="card-button"
              onClick={() => navigate("/record")}
            >
              →
            </button>

          </div>


          {/* ACTIVITY */}
          <div className="dashboard-card activity-card">

            <div className="card-icon">
              ◷
            </div>

            <h2>
              Recent Activity
            </h2>

            <p>
              View your recent sessions
              and performance.
            </p>

            <button
              className="card-button"
              onClick={() => navigate("/activity")}
            >
              →
            </button>

          </div>


          {/* PROGRESS */}
          <div className="dashboard-card progress-card">

            <div className="card-icon">
              ↗
            </div>

            <h2>
              Progress
            </h2>

            <p>
              Track your improvement
              and see your growth.
            </p>

            <button
              className="card-button"
              onClick={() => navigate("/progress")}
            >
              →
            </button>

          </div>

        </div>

      </main>

    </div>
  );
}

export default Dashboard;