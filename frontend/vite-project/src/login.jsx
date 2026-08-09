import "./App.css";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { signup, login } from "./api";

function Login() {
  const navigate = useNavigate();
  const [isSignup, setIsSignup] = useState(true);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();

    const name = document.getElementById("name")?.value.trim();
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    if (!email || !password) {
      alert("Please enter email and password");
      return;
    }

    if (isSignup && !name) {
      alert("Please enter your name");
      return;
    }

    setLoading(true);

    try {
      const data = isSignup
        ? await signup(name, email, password)
        : await login(email, password);

      localStorage.setItem("vibecheckToken", data.access_token);
      localStorage.setItem("vibecheckName", name || email.split("@")[0]);
      localStorage.setItem("vibecheckEmail", email);

      navigate("/dashboard");
    } catch (err) {
      alert(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">

      <div className="blob blob-one"></div>
      <div className="blob blob-two"></div>

      <main className="login-content">

        <h1 className="logo">VIBECHECK</h1>

        <p className="tagline">
          Know exactly why and where you lost the room
        </p>

        <div className="login-card">

          <div className="wave-icon">
            <span></span><span></span><span></span><span></span><span></span>
          </div>

          <h2>{isSignup ? "CREATE ACCOUNT" : "WELCOME BACK"}</h2>

          <p className="card-subtitle">
            Let's see how you're really coming across.
          </p>

          <form onSubmit={handleSubmit}>

            {isSignup && (
              <div className="input-group">
                <label htmlFor="name">NAME</label>
                <input id="name" type="text" placeholder="Enter your name" />
              </div>
            )}

            <div className="input-group">
              <label htmlFor="email">EMAIL</label>
              <input id="email" type="email" placeholder="Enter your email" />
            </div>

            <div className="input-group">
              <label htmlFor="password">PASSWORD</label>
              <input id="password" type="password" placeholder="Enter your password" />
            </div>

            <button type="submit" className="login-btn" disabled={loading}>
              <span>{loading ? "PLEASE WAIT..." : isSignup ? "SIGN UP" : "LOGIN"}</span>
              <span className="arrow">→</span>
            </button>

          </form>

          <p
            style={{ textAlign: "center", marginTop: "16px", fontSize: "12px", cursor: "pointer", color: "#8064bd" }}
            onClick={() => setIsSignup(!isSignup)}
          >
            {isSignup ? "Already have an account? Login" : "New here? Sign up"}
          </p>

        </div>

      </main>

    </div>
  );
}

export default Login;

