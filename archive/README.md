# Legacy & Episode Archive Scripts

This folder contains one-off episode generation, publish, and batch execution scripts archived from the repository root to keep the workspace clean, modular, and maintainable.

### Core Active Entrypoints
For day-to-day operations, use the primary entrypoints in the root directory:
- `next_ep.py` / `next_ep.bat`: Automated next episode generator across active series.
- `app.py`: FastAPI server and Web UI backend.
- `run.py`: Production pipeline executor.
- `auto_produce_1h.py`: Continuous 1-hour automated video production loop.
- `doctor.py`: Diagnostics and system health verification.
- `publish_all.py` / `publish_all.bat`: Unified publishing runner.
- `publish_instagram.py`: Dedicated Instagram video publisher.
