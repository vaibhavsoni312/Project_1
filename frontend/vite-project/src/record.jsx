import "./record.css";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";

function Record() {
  const navigate = useNavigate();
  const videoRef = useRef(null);

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [stream, setStream] = useState(null);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      videoRef.current.srcObject = mediaStream;
      setStream(mediaStream);
    } catch (error) {
      alert("Camera and microphone permission is required.");
      console.error(error);
    }
  };

  const startRecording = async () => {
    if (!stream) {
      await startCamera();
    }

    setIsRecording(true);
    setIsPaused(false);
  };

  const pauseRecording = () => {
    setIsPaused(true);
  };

  const resumeRecording = () => {
    setIsPaused(false);
  };

  const endRecording = () => {

  setIsRecording(false);
  setIsPaused(false);

  if (stream) {
    stream.getTracks().forEach((track) => track.stop());
    setStream(null);
  }

  if (videoRef.current) {
    videoRef.current.srcObject = null;
  }

  navigate("/analysis");
};

  return (
    <div className="record-page">

      {/* HEADER */}
      <header className="record-header">

        <div className="record-logo">
          VIBECHECK<span>.</span>
        </div>

        <div className="record-title">
          <h1>New Practice Session</h1>
          <p>Let's see how you're really coming across.</p>
        </div>

      </header>

<button
  className="back-button"
  onClick={() => navigate("/dashboard")}
>
  ← Back to Dashboard
</button>
      {/* CAMERA SECTION */}
      <main className="record-main">

        <div className="camera-card">

          <div className="camera-top">

            <span className="camera-label">
              CAMERA PREVIEW
            </span>

            {isRecording && (
              <span className="recording-indicator">
                <span className="record-dot"></span>
                {isPaused ? "PAUSED" : "RECORDING"}
              </span>
            )}

          </div>


          <div className="camera-container">

            {!stream && (
              <div className="camera-placeholder">

                <div className="camera-icon">
                  ◉
                </div>

                <h2>
                  Camera Ready
                </h2>

                <p>
                  Start your session when you're ready.
                </p>

              </div>
            )}

            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className={`camera-video ${
                stream ? "camera-active" : ""
              }`}
            />

          </div>


          {/* CONTROLS */}
          <div className="record-controls">

            {!isRecording ? (

              <button
                className="start-record-btn"
                onClick={startRecording}
              >
                <span className="record-circle"></span>
                START RECORDING
              </button>

            ) : (

              <div className="active-controls">

                {!isPaused ? (
                  <button
                    className="pause-btn"
                    onClick={pauseRecording}
                  >
                    ❚❚ PAUSE
                  </button>
                ) : (
                  <button
                    className="resume-btn"
                    onClick={resumeRecording}
                  >
                    ▶ RESUME
                  </button>
                )}

                <button
                  className="end-btn"
                  onClick={endRecording}
                >
                  ■ END
                </button>

              </div>

            )}

          </div>

        </div>


        {/* SESSION INFO */}
        <div className="session-info">

          <div className="info-item">
            <span>SESSION TYPE</span>
            <strong>Practice Session</strong>
          </div>

          <div className="info-item">
            <span>VIDEO</span>
            <strong>Camera + Audio</strong>
          </div>

          <div className="info-item">
            <span>STATUS</span>
            <strong>
              {isRecording
                ? isPaused
                  ? "Paused"
                  : "Recording"
                : "Ready"}
            </strong>
          </div>

        </div>

      </main>

    </div>
  );
}

export default Record;