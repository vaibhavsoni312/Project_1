import { Routes, Route } from "react-router-dom";

import Login from "./login";
import Dashboard from "./dashboard";
import Record from "./record";
import Activity from "./activity";
import Progress from "./progress";
import Analysis from "./analysis";

import "./App.css";

function App() {
  return (
    <Routes>

      {/* LOGIN */}
      <Route
        path="/"
        element={<Login />}
      />

      {/* DASHBOARD */}
      <Route
        path="/dashboard"
        element={<Dashboard />}
      />

      {/* RECORD */}
      <Route
        path="/record"
        element={<Record />}
      />

      {/* ANALYSIS */}
      <Route
        path="/analysis"
        element={<Analysis />}
      />

      {/* ACTIVITY */}
      <Route
        path="/activity"
        element={<Activity />}
      />

      {/* PROGRESS */}
      <Route
        path="/progress"
        element={<Progress />}
      />

    </Routes>
  );
}

export default App;