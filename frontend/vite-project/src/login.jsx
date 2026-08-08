import "./App.css";
import { useNavigate } from "react-router-dom";

function Login() {
  const navigate = useNavigate();
  const handleLogin = (e) => {
    e.preventDefault();

    const name = document.getElementById("name").value.trim();
    const email = document.getElementById("email").value.trim();

    if (!name) {
      alert("Please enter your name");
      return;
    }

    if (!email) {
      alert("Please enter your email");
      return;
    }

    localStorage.setItem("vibecheckName", name);
    localStorage.setItem("vibecheckEmail", email);

    alert("Login successful!");
    navigate("/dashboard");
  };

  return (
    <div className="login-page">

      <div className="blob blob-one"></div>
      <div className="blob blob-two"></div>

      <main className="login-content">

        <h1 className="logo">
          VIBECHECK
        </h1>

        <p className="tagline">
          Know exactly why and where you lost the room
        </p>

        <div className="login-card">

          <div className="wave-icon">
            <span></span>
            <span></span>
            <span></span>
            <span></span>
            <span></span>
          </div>

          <h2>
            WELCOME BACK
          </h2>

          <p className="card-subtitle">
            Let's see how you're really coming across.
          </p>

          <form onSubmit={handleLogin}>

            <div className="input-group">
              <label htmlFor="name">
                NAME
              </label>

              <input
                id="name"
                type="text"
                placeholder="Enter your name"
              />
            </div>

            <div className="input-group">
              <label htmlFor="email">
                EMAIL
              </label>

              <input
                id="email"
                type="email"
                placeholder="Enter your email"
              />
            </div>

            <button
              type="submit"
              className="login-btn"
            >
              <span>LOGIN</span>
              <span className="arrow">→</span>
            </button>

          </form>

        </div>

      </main>

    </div>
  );
}

export default Login;