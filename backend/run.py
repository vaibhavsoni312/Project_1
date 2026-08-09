import argparse
import json
import sys
 
 
def main():
    parser = argparse.ArgumentParser(
        description="Run the AI video-analysis pipeline on a real video."
    )
    parser.add_argument("video", help="Path to the video file (mp4/mov/etc).")
    parser.add_argument(
        "--out",
        default="video_analysis.json",
        help="Where to save the raw analysis JSON (default: video_analysis.json)",
    )
    parser.add_argument(
        "--insights",
        action="store_true",
        help="Also run insights.py (deltas + feedback) on top of the analysis.",
    )
    args = parser.parse_args()
 
    # ----------------------------------------------------------------
    # Import the pipeline. Adjust this import if your video_analyzer.py
    # lives somewhere other than app/services/video_analyzer.py
    # (e.g. app/ai/video_analyzer.py) - it's the same functions either way.
    # ----------------------------------------------------------------
    try:
        from app.services.video_analyzer import analyze_video, print_video_report, save_video_result
    except ModuleNotFoundError:
        from app.ai.video_analyzer import analyze_video, print_video_report, save_video_result
 
    print(f"Running pipeline on: {args.video}")
    print("(this will take a while - it's decoding every frame + running")
    print(" mediapipe + DeepFace on each sampled frame)\n")
 
    try:
        result = analyze_video(args.video)
    except Exception as e:
        print(f"\nAnalysis failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
 
    # Human-readable report (this is the function you'll actually want
    # to eyeball first)
    print_video_report(result)
 
    # Raw JSON, in case you want to inspect every field / feed it elsewhere
    save_video_result(result, args.out)
    print(f"\nFull raw result saved to: {args.out}")
 
    # ----------------------------------------------------------------
    # Optional: run insights.py (delta detection -> feedback lines)
    # on top of the same result, since it just needs result["timeline"]
    # ----------------------------------------------------------------
    if args.insights:
        try:
            from app.services.insights import generate_insights
        except ModuleNotFoundError:
            from app.ai.insights import generate_insights
 
        print("\n" + "=" * 65)
        print("             INSIGHTS / FEEDBACK")
        print("=" * 65)
 
        insights = generate_insights(result)
 
        print(f"\nDetected {len(insights['deltas'])} state changes, "
              f"{len(insights['feedback'])} feedback items:\n")
 
        for item in insights["feedback"]:
            print(f"  [{item['timestamp']:.1f}s] {item['feedback']}")
 
        insights_out = args.out.replace(".json", "_insights.json")
        with open(insights_out, "w", encoding="utf-8") as f:
            json.dump(insights, f, indent=2)
        print(f"\nInsights saved to: {insights_out}")
 
 
if __name__ == "__main__":
    main()