import sys

from app.ai.video_analyzer import (
    analyze_video,
    print_video_report,
    save_video_result
)


# ============================================================
# INPUT
# ============================================================

if len(sys.argv) < 2:

    print()
    print(
        "Usage:"
    )

    print(
        "python test_video_analysis.py "
        "<video_path>"
    )

    print()

    sys.exit(1)


video_path = sys.argv[1]


# ============================================================
# ANALYZE
# ============================================================

try:

    result = analyze_video(
        video_path
    )


    # --------------------------------------------------------
    # Report
    # --------------------------------------------------------

    print_video_report(
        result
    )


    # --------------------------------------------------------
    # JSON
    # --------------------------------------------------------

    save_video_result(
        result,
        "video_analysis.json"
    )


    print(
        "JSON saved as:"
    )

    print(
        "video_analysis.json"
    )


except Exception as e:

    print()

    print(
        "ERROR:"
    )

    print(e)

    print()

    sys.exit(1)