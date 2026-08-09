import "./record.css";
import { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { uploadVideo } from "./api";

function Record() {
  const navigate = useNavigate();
  const videoRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);

  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [stream, setStream] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  const startCamera = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true,
      });

      videoRef.current.srcObject = mediaStream;
      setStream(mediaStream);
      return mediaStream;
    } catch (error) {
      alert("Camera and microphone permission is required.");
      console.error(error);
      return null;
    }
  };

  const startRecording = async () => {
    let activeStream = stream;

    if (!activeStream) {
      activeStream = await startCamera();
    }

    if (!activeStream) {
      // camera permission fail ho gayi
      return;
    }

    chunksRef.current = [];

    const recorder = new MediaRecorder(activeStream, {
      mimeType: "video/webm",
    });

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) {
        chunksRef.current.push(e.data);
      }
    };

    recorder.start();
    mediaRecorderRef.current = recorder;

    setIsRecording(true);
    setIsPaused(false);
  };

  const pauseRecording = () => {
    mediaRecorderRef.current?.pause();
    setIsPaused(true);
  };

  const resumeRecording = () => {
    mediaRecorderRef.current?.resume();
    setIsPaused(false);
  };

  const endRecording = async () => {
    const recorder = mediaRecorderRef.current;

    if (!recorder) {
      navigate("/dashboard");
      return;
    }

    // Recorder ke stop hone ka wait karo taaki last chunk bhi mil jaye
    const stopped = new Promise((resolve) => {
      recorder.onstop = resolve;
    });

    recorder.stop();
    await stopped;

    setIsRecording(false);
    setIsPaused(false);

    if (stream) {
      stream.getTracks().forEach((track) => track.stop());
      setStream(null);
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }

    const videoBlob = new Blob(chunksRef.current, { type: "video/webm" });
    const token = localStorage.getItem("vibecheckToken");

    if (!token) {
      alert("Please login again.");
      navigate("/");
      return;
    }

    setIsUploading(true);

    try {
      const result = await uploadVideo(videoBlob, token);
      // Analysis page ko real data ke sath bhejo
      navigate("/analysis", { state: result });
    } catch (err) {
      alert("Upload failed: " + err.message);
    } finally {
      setIsUploading(false);
    }
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
                disabled={isUploading}
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
                  disabled={isUploading}
                >
                  {isUploading ? "UPLOADING..." : "■ END"}
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
              {isUploading
                ? "Uploading & Analyzing"
                : isRecording
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